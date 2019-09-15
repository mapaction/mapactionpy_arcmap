import os
import arcpy
import jsonpickle
import re
from map_cookbook import MapCookbook
from map_report import MapReport
from map_result import MapResult
from layer_properties import LayerProperties


class MapChef:
    """
    Worker which creates a Map based on a predefined "recipe" from a cookbook
    """

    def __init__(self, mxd, cookbookJsonFile, layerPropertiesJsonFile, crashMoveFolder, layerDirectory):
        """
        Arguments:
           mxd {MXD file} -- MXD file.
           cookbookJsonFile {str} -- Path to Map Cookbook json file
           layerPropertiesJsonFile {str} -- Path to Layer Properties json file
           crashMoveFolder {str} -- Path to Crash Move Folder json file
        """
        self.mxd = mxd
        self.layerPropertiesJsonFile = layerPropertiesJsonFile
        self.cookbookJsonFile = cookbookJsonFile
        self.crashMoveFolder = crashMoveFolder
        self.layerDirectory = layerDirectory
        self.cookbook = MapCookbook(self.cookbookJsonFile)
        self.layerProperties = LayerProperties(self.layerPropertiesJsonFile)

    def disableLayers(self):
        """
        Makes all layers invisible for all data-frames
        """
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                lyr.visible = False

    def enableLayers(self):
        """
        Makes all layers visible for all data-frames
        """
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                lyr.visible = True

    def removeLayers(self):
        """
        Removes all layers for all data-frames
        """
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                arcpy.mapping.RemoveLayer(df, lyr)
        self.mxd.save()

    def cook(self, productName, countryName):
        arcpy.env.addOutputsToMap = False
        self.disableLayers()
        self.removeLayers()
        self.mapReport = MapReport(productName)
        recipe = self.cookbook.products.get(productName, None)
        if (recipe is not None):
            for layer in recipe.layers:
                self.processLayer(layer, countryName)
        self.enableLayers()
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        arcpy.env.addOutputsToMap = True
        self.mxd.save()

    """
    Adds data file to map layer

    Can handle the following file types:
        * Shapefiles
        * IMG files
        * TIF files

    Arguments:
        dataFrame {str} -- Name of data frame to add data source file to
        dataFile {str}  -- Full path to data file
        layer {arcpy._mapping.Layer} -- Layer to which data is added
        definitionQuery {str} -- Some layers have a definition query which select specific features from a SQL query
        labelClasses {list} -- List of LabelClass objects
        countryName {str} -- Country name

    Returns:
        boolean -- added (true if successful)
    """

    def addDataToLayer(self, dataFrame, dataFile, layer, definitionQuery, datasetName, labelClasses, countryName):
        datasetTypes = ["SHAPEFILE_WORKSPACE",
                        "RASTER_WORKSPACE",
                        "FILEGDB_WORKSPACE",
                        "ACCESS_WORKSPACE",
                        "ARCINFO_WORKSPACE",
                        "CAD_WORKSPACE",
                        "EXCEL_WORKSPACE",
                        "OLEDB_WORKSPACE",
                        "PCCOVERAGE_WORKSPACE",
                        "SDE_WORKSPACE",
                        "TEXT_WORKSPACE",
                        "TIN_WORKSPACE",
                        "VPF_WORKSPACE"]
        added = False
        for lyr in arcpy.mapping.ListLayers(layer):
            if lyr.supports("LABELCLASSES"):
                for labelClass in labelClasses:
                    for lblClass in lyr.labelClasses:
                        if (lblClass.className == labelClass.className):
                            lblClass.SQLQuery = labelClass.SQLQuery
                            lblClass.expression = labelClass.expression
            if lyr.supports("DATASOURCE"):  # An annotation layer does notsupport DATASOURCE
                for datasetType in datasetTypes:
                    #
                    try:
                        lyr.replaceDataSource(dataFile, datasetType, datasetName)
                        added = True
                    except Exception:
                        pass

                    if ((added is True) and (definitionQuery)):
                        definitionQuery = definitionQuery.replace('{COUNTRY_NAME}', countryName)
                        lyr.definitionQuery = definitionQuery
                        try:
                            arcpy.SelectLayerByAttribute_management(lyr, "SUBSET_SELECTION", definitionQuery)
                        except Exception:
                            added = False

                    if (added is True):
                        arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")
                        break
                lyr.visible = False
        return added

    """
    Returns map report in json format
    """

    def report(self):
        return(jsonpickle.encode(self.mapReport, unpicklable=False))

    def processLayer(self, layer, countryName):
        mapResult = MapResult(layer)
        properties = self.layerProperties.properties.get(layer, None)
        if (properties is not None):
            layerFilePath = os.path.join(self.layerDirectory, (properties.layerName + ".lyr"))
            if (os.path.exists(layerFilePath)):
                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                layerToAdd = arcpy.mapping.Layer(layerFilePath)
                searchDirectory = os.path.join(self.crashMoveFolder, "GIS", "2_Active_Data")
                # If it's not a File Geodatabase (gdb) the regexp won't contain ".gdb/"
                if (".gdb/" not in properties.regExp):
                    dataFiles = self.find(searchDirectory, properties.regExp)
                    for dataFile in (dataFiles):
                        self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                        base = os.path.basename(dataFile)
                        datasetName = os.path.splitext(base)[0]
                        dataDirectory = os.path.dirname(os.path.realpath(dataFile))
                        mapResult.added = self.addDataToLayer(self.dataFrame,
                                                              dataDirectory,
                                                              layerToAdd,
                                                              properties.definitionQuery,
                                                              datasetName,
                                                              properties.labelClasses,
                                                              countryName)
                        mapResult.dataSource = dataFile
                        if mapResult.added:
                            mapResult.message = "Layer added successfully"
                        else:
                            mapResult.message = "Possibly due to schema error or other cause: " + \
                                properties.definitionQuery
                else:
                    # It's a File Geodatabase
                    parts = properties.regExp.split("/")
                    gdbPath = parts[0]
                    geoDatabases = self.find(searchDirectory, gdbPath, True)
                    for geoDatabase in geoDatabases:
                        arcpy.env.workspace = geoDatabase
                        rasters = arcpy.ListRasters("*")
                        for raster in rasters:
                            if re.match(parts[1], raster):
                                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                mapResult.added = self.addDataToLayer(self.dataFrame,
                                                                      geoDatabase,
                                                                      layerToAdd,
                                                                      properties.definitionQuery,
                                                                      raster,
                                                                      properties.
                                                                      labelClasses,
                                                                      countryName)
                                mapResult.dataSource = geoDatabase + os.sep + raster
                                break
                        featureClasses = arcpy.ListFeatureClasses()
                        for featureClass in featureClasses:
                            if re.match(parts[1], featureClass):
                                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                mapResult.added = self.addDataToLayer(self.dataFrame,
                                                                      geoDatabase,
                                                                      layerToAdd,
                                                                      properties.definitionQuery,
                                                                      featureClass,
                                                                      properties.labelClasses,
                                                                      countryName)
                                mapResult.dataSource = geoDatabase + os.sep + featureClass
                                # Found Geodatabase.  Stop iterating.
                                break
                        if mapResult.added:
                            mapResult.message = "Layer added successfully"
                            break
                        else:
                            if (len(mapResult.dataSource) > 0):
                                mapResult.message = "Possibly due to schema error or other cause: " + \
                                    properties.definitionQuery
                                break
                            # Otherwise, whizz around again
                # If a file hasn't been added, and no other reason given, report what was expected
                if ((mapResult.added is False) and (len(mapResult.message) == 0)):
                    mapResult.message = "Could not find file matching " + properties.regExp
            else:
                mapResult.added = False
                mapResult.message = "Layer file could not be found"
        else:
            mapResult.added = False
            mapResult.message = "Layer property definition could not be found in the cookbook"
        self.mapReport.add(mapResult)

    def find(self, rootdir, regexp, gdb=False):
        returnPaths = list()
        regexp = regexp.replace("^", "\\\\")
        regexp = regexp.replace("/", "\\\\")
        regexp = ".*" + regexp
        re.compile(regexp)
        for root, dirs, files in os.walk(os.path.abspath(rootdir)):
            if (gdb is False):
                for file in files:
                    filePath = os.path.join(root, file)
                    z = re.match(regexp, filePath)
                    if (z):
                        if not(filePath.endswith("lock")):
                            returnPaths.append(filePath)
            else:
                for dir in dirs:
                    dirPath = os.path.join(root, dir)
                    z = re.match(regexp, dirPath)
                    if (z):
                        returnPaths.append(dirPath)
        return returnPaths
