import os
from os import listdir
from os.path import isfile, join
import arcpy
import re
from MapCookbook import MapCookbook
from MapReport import MapReport
from MapResult import MapResult
from LayerProperties import LayerProperties


class MapChef:
    def __init__(self, mxd, cookbookJsonFile, layerPropertiesJsonFile, crashMoveFolder, layerDirectory):
        self.mxd = mxd
        self.cookbookJsonFile = cookbookJsonFile
        self.layerPropertiesJsonFile = layerPropertiesJsonFile
        self.crashMoveFolder = crashMoveFolder
        self.layerDirectory = layerDirectory
        self.cookbook = self.readCookbook()
        self.root = crashMoveFolder
        self.layerProperties = self.readLayerPropertiesFile()

    def readCookbook(self):
        cookbook = MapCookbook(self.cookbookJsonFile)
        cookbook.parse()
        return cookbook

    def readLayerPropertiesFile(self):
        layerProperties = LayerProperties(self.layerPropertiesJsonFile)
        layerProperties.parse()
        return layerProperties

    def disableLayers(self):
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                lyr.visible = False

    def enableLayers(self):
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                lyr.visible = True

    def removeLayers(self):
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                arcpy.mapping.RemoveLayer(df, lyr)
        self.mxd.save()

    def cook(self, productName, countryName):
        arcpy.env.addOutputsToMap = False
        self.disableLayers()
        self.removeLayers()
        self.mapReport = MapReport(productName)
        for layer in self.cookbook.layers(productName):
            properties = self.layerProperties.get(layer)
            # Add layer to the report for later
            mapResult = MapResult(layer)
            if (properties is not None):
                layerFilePath = os.path.join(self.layerDirectory, (properties.layerName + ".lyr"))
                if (os.path.exists(layerFilePath)):
                    self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                    layerToAdd = arcpy.mapping.Layer(layerFilePath)
                    dataFilePath = os.path.join(self.root, "GIS", "2_Active_Data", properties.sourceFolder)
                    if (os.path.isdir(dataFilePath)):
                        if ("/" not in properties.regExp):
                            onlyfiles = [f for f in listdir(dataFilePath) if isfile(join(dataFilePath, f))]
                            for fileName in onlyfiles:
                                if re.match(properties.regExp, fileName):
                                    self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                    dataFile = os.path.join(dataFilePath, fileName)
                                    mapResult.added = self.addToLayer(
                                        self.dataFrame, dataFile, layerToAdd, properties.definitionQuery,
                                        properties.display, properties.labelClasses, countryName)
                                    mapResult.dataSource = dataFile
                                    if mapResult.added:
                                        mapResult.message = "Layer added successfully"
                                    else:
                                        mapResult.message = ("Unexpected schema.  Could not evaluate expression: "
                                                             + properties.definitionQuery)
                                    break
                        else:
                            # It's a File Geodatabase
                            parts = properties.regExp.split("/")
                            for root, dirs, files in os.walk(dataFilePath):
                                for gdb in dirs:
                                    if re.match(parts[0], gdb):
                                        rasterFile = (dataFilePath + "/" + gdb).replace("/", os.sep)
                                        arcpy.env.workspace = rasterFile
                                        rasters = arcpy.ListRasters("*")
                                        for raster in rasters:
                                            if re.match(parts[1], raster):
                                                self.dataFrame = arcpy.mapping.ListDataFrames(
                                                    self.mxd, properties.mapFrame)[0]
                                                self.addRasterToLayer(self.dataFrame, rasterFile,
                                                                      layerToAdd, raster, properties.display)
                                                mapResult.dataSource = rasterFile
                                                mapResult.added = True
                        # If a file hasn't been added, and no other reason given, report what was expected

                        if ((mapResult.added is False) and (len(mapResult.message) == 0)):
                            mapResult.message = ("Could not find file matching "
                                                 + properties.sourceFolder + "/" + properties.regExp)
                    else:
                        mapResult.added = False
                        mapResult.message = "Could not find directory: " + dataFilePath
                else:
                    mapResult.added = False
                    mapResult.message = "Layer file could not be found"
            else:
                mapResult.added = False
                mapResult.message = "Layer property definition could not be found in the cookbook"
            self.mapReport.add(mapResult)

        # Make all layers visible
        self.enableLayers()

        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        arcpy.env.addOutputsToMap = True
        self.mxd.save()

    def addRasterToLayer(self, dataFrame, rasterFile, layer, raster, display):
        for lyr in arcpy.mapping.ListLayers(layer):
            lyr.replaceDataSource(rasterFile, "FILEGDB_WORKSPACE", raster)
            lyr.visible = False
            arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")

    def addToLayer(self, dataFrame, dataFile, layer, definitionQuery, display, labelClasses, countryName):
        added = True
        dataDirectory = os.path.dirname(os.path.realpath(dataFile))
        for lyr in arcpy.mapping.ListLayers(layer):
            # https://community.esri.com/thread/60097
            base = os.path.basename(dataFile)
            extension = os.path.splitext(base)[1]
            if lyr.supports("LABELCLASSES"):
                for labelClass in labelClasses:
                    for lblClass in lyr.labelClasses:
                        if (lblClass.className == labelClass.className):
                            lblClass.SQLQuery = labelClass.SQLQuery
                            lblClass.expression = labelClass.expression
            if (extension.upper() == ".SHP"):
                lyr.replaceDataSource(dataDirectory, "SHAPEFILE_WORKSPACE", os.path.splitext(base)[0])
            if ((extension.upper() == ".TIF") or (extension.upper() == ".IMG")):
                lyr.replaceDataSource(dataDirectory, "RASTER_WORKSPACE", os.path.splitext(base)[0])
            if (definitionQuery):
                definitionQuery = definitionQuery.replace('{COUNTRY_NAME}', countryName)
                # https://gis.stackexchange.com/questions/90736/setting-definition-query-on-arcpy-layer-from-shapefile
                lyr.definitionQuery = definitionQuery
                try:
                    arcpy.SelectLayerByAttribute_management(lyr, "SUBSET_SELECTION", definitionQuery)
                except Exception:
                    added = False

            lyr.visible = False
            if (added):
                arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")
        return added

    def report(self):
        return self.mapReport.dump()
