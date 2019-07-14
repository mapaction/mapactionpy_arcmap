import os
from os import listdir
from os.path import isfile, join
import arcpy
from arcpy import env
import re
from MapRecipe import MapRecipe
from LayerProperties import LayerProperties

class MapChef:
    def __init__(self, recipeJsonFile, layerPropertiesFile, mxdTemplate, crashMoveFolder, layerDirectory, clean = False):
        self.mxd = None
        self.clean = clean
        self.recipeJsonFile = recipeJsonFile
        self.recipe = self.readRecipe()
        self.mxdTemplateFile = mxdTemplate
        self.root = crashMoveFolder
        self.layerPropertiesFile = layerPropertiesFile
        self.layerDirectory = layerDirectory
        self.layerProperties = self.readLayerPropertiesFile()

    def readRecipe(self):
        recipe = MapRecipe(self.recipeJsonFile) 
        recipe.parse()
        return recipe

    def readLayerPropertiesFile(self):
        layerProperties = LayerProperties(self.layerPropertiesFile) 
        layerProperties.parse()
        return layerProperties

    def removeLayers(self):
        print ("Removing existing layers")
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                arcpy.mapping.RemoveLayer(df, lyr)
        self.mxd.save()

    def cook(self):
        print ("cooking...")
        self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
        if (self.clean == True):
            self.removeLayers()
        for layer in self.recipe.layers:
            print ("Get data source for layer \'" + layer.name + "\'")
            properties = self.layerProperties.get(layer.name)
            if (properties is not None):             
                layerFilePath= self.root + "/GIS/3_Mapping/38_Initial_Maps_Layer_Files/Reference Map/" +  properties.layerName + ".lyr"
                if (os.path.exists(layerFilePath)):
                    self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
                    self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                    layerToAdd = arcpy.mapping.Layer(layerFilePath)
                    arcpy.RefreshTOC()
                    arcpy.RefreshActiveView()
                    self.mxd.save()
                    dataFilePath= self.root + "/GIS/2_Active_Data/" +  properties.sourceFolder
                    if (os.path.isdir(dataFilePath)):
                        if ("/" not in properties.regExp):
                            onlyfiles = [f for f in listdir(dataFilePath) if isfile(join(dataFilePath, f))]
                            for fileName in onlyfiles:
                                if re.match(properties.regExp, fileName):
                                    self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
                                    self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                    dataFile = dataFilePath + "/" + fileName
                                    self.addToLayer(self.dataFrame, dataFile, layerToAdd, properties.definitionQuery, properties.display)
                        else:
                            parts = properties.regExp.split("/")
                            for root, dirs, files in os.walk(dataFilePath):
                                for gdb in dirs:
                                    if re.match(parts[0], gdb):
                                        rasterFile = (dataFilePath + "/" + gdb).replace("/", os.sep)
                                        arcpy.env.workspace = rasterFile
                                        rasters = arcpy.ListRasters("*")
                                        for raster in rasters:
                                           if re.match(parts[1], raster):
                                               rasterLayer = (rasterFile + "\\" + raster)
                                               self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
                                               self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                               self.addRasterToLayer(self.dataFrame, rasterFile, layerToAdd, raster, properties.display)    

    def addRasterToLayer(self, dataFrame, rasterFile, layer, raster, display):
        print ("Adding \'" + rasterFile + os.sep + raster + "\' to layer \'" + layer.name + "\'")
        for lyr in arcpy.mapping.ListLayers(layer):                  #THIS IS THE MISSING PIECE  
            lyr.replaceDataSource(rasterFile, "FILEGDB_WORKSPACE", raster)

            if (display.upper() == "YES"):
                lyr.visible = True
            else:
                lyr.visible = False
            arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")            
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        self.mxd.save()

    def addToLayer(self, dataFrame, dataFile, layer, definitionQuery, display):
        dataDirectory = os.path.dirname(os.path.realpath(dataFile))
        for lyr in arcpy.mapping.ListLayers(layer):
            print (lyr.name + " " + layer.name)  
            # https://community.esri.com/thread/60097
            base=os.path.basename(dataFile)
            extension = os.path.splitext(base)[1]

            if (extension.upper() == ".SHP"):
                lyr.replaceDataSource(dataDirectory, "SHAPEFILE_WORKSPACE", os.path.splitext(base)[0])  
            if (extension.upper() == ".TIF"):
                lyr.replaceDataSource(dataDirectory, "RASTER_WORKSPACE", os.path.splitext(base)[0])  
            if (definitionQuery):
               # https://gis.stackexchange.com/questions/90736/setting-definition-query-on-arcpy-layer-from-shapefile
                lyr.definitionQuery = definitionQuery
                arcpy.SelectLayerByAttribute_management(lyr, "SUBSET_SELECTION", definitionQuery)
            if (display.upper() == "YES"):
                lyr.visible = True
            else:
                lyr.visible = False
            arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        self.mxd.save()

    def addLayer(self, dataFrame, dataFile, layerName, definitionQuery, display):
        print ("Adding \'" + dataFile + "\' to layer \'" + layerName + "\'")
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(dataFile, layerName)
        layer = arcpy.mapping.Layer(layerName)
        if (definitionQuery):
            # https://gis.stackexchange.com/questions/90736/setting-definition-query-on-arcpy-layer-from-shapefile
            layer.definitionQuery = definitionQuery
            arcpy.SelectLayerByAttribute_management(layerName, "SUBSET_SELECTION", definitionQuery)
        if (display.upper() == "YES"):
            layer.visible = True
        else:
            layer.visible = False

        arcpy.mapping.AddLayer(dataFrame, layer, "BOTTOM")
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        self.mxd.save()

