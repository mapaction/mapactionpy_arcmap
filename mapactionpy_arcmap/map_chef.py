import os
from os import listdir
from os.path import isfile, join
import arcpy
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

    # APS 06/09/2019 The `cook()` method is much too long and has too many nested `if`s and `for`s. Please split this
    # into the several separate private methods for handling the different scenarios, data types, error conditions
    # etc. This refactoring would benefit from adding some unittests surrounding it.
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
    Add File Geodatabase to layer 

    Arguments: 
        dataFrame {str} -- Name of data frame to add data source file to
        dataFile {str}  -- Full path to data file
        layer {arcpy._mapping.Layer} -- Layer to which data is added
        datasetName {str} -- Dataset name
        labelClasses {list} -- List of LabelClass objects
        countryName {str} -- Name of country
    """
    def addFileGeodatabaseToLayer(self, dataFrame, dataFile, layer, definitionQuery, datasetName, labelClasses, countryName):
        datasetTypes = ["ACCESS_WORKSPACE", "ARCINFO_WORKSPACE", "CAD_WORKSPACE", "EXCEL_WORKSPACE", "FILEGDB_WORKSPACE", "OLEDB_WORKSPACE", "PCCOVERAGE_WORKSPACE", "RASTER_WORKSPACE", "SDE_WORKSPACE", "SHAPEFILE_WORKSPACE", "TEXT_WORKSPACE", "TIN_WORKSPACE", "VPF_WORKSPACE"]
        added = False
        for lyr in arcpy.mapping.ListLayers(layer):
            if lyr.supports("LABELCLASSES"):
                for labelClass in labelClasses:
                    for lblClass in lyr.labelClasses:
                        if (lblClass.className == labelClass.className):
                            lblClass.SQLQuery = labelClass.SQLQuery
                            lblClass.expression = labelClass.expression
            if lyr.supports("DATASOURCE"): # An annotation layer does notsupport DATASOURCE
                for datasetType in datasetTypes: 
                    try:
                        lyr.replaceDataSource(dataFile, datasetType, datasetName)
                        added = True
                        if (definitionQuery):
                            definitionQuery = definitionQuery.replace('{COUNTRY_NAME}', countryName)
                            # https://gis.stackexchange.com/questions/90736/setting-definition-query-on-arcpy-layer-from-shapefile
                            lyr.definitionQuery = definitionQuery
                            # @TODO SORT THIS OUT. THIS IS BAD - Nest Try Except!!
                            try:
                                arcpy.SelectLayerByAttribute_management(lyr, "SUBSET_SELECTION", definitionQuery)
                            except Exception:
                                added = False            
                        arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")            
                        break
                    except Exception, e:
                        pass
                lyr.visible = False 
        return added

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
        definitionQuery {str} -- Some layers have a definition query which select specific features based on a SQL query
        labelClasses {list} -- List of LabelClass objects
        countryName {str} -- Country name

    Returns:
        boolean -- added (true if successful)
    """
    def addDataToLayer(self, dataFrame, dataFile, layer, definitionQuery, labelClasses, countryName):
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

    """
    Returns map report in json format 
    """
    def report(self):
        return self.mapReport.dump()

    def processLayer(self, layer, countryName):
        mapResult = MapResult(layer)
        properties = self.layerProperties.properties.get(layer, None)
        if (properties is not None):             
            layerFilePath = os.path.join(self.layerDirectory, (properties.layerName + ".lyr"))
            if (os.path.exists(layerFilePath)):
                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                layerToAdd = arcpy.mapping.Layer(layerFilePath)
                dataFilePath = os.path.join(self.crashMoveFolder, "GIS", "2_Active_Data", properties.sourceFolder)
                # @TODO Use Data Search
                if (os.path.isdir(dataFilePath)):
                    # If it's not a File Geodatabase (gdb) the regexp won't contain ".gdb/"
                    if (".gdb/" not in properties.regExp):
                        onlyfiles = [f for f in listdir(dataFilePath) if isfile(join(dataFilePath, f))]
                        for fileName in onlyfiles:
                            if re.match(properties.regExp, fileName):
                                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                dataFile = os.path.join(dataFilePath, fileName)
                                mapResult.added = self.addDataToLayer(self.dataFrame, dataFile, layerToAdd, properties.definitionQuery, properties.labelClasses, countryName)
                                mapResult.dataSource = dataFile
                                if mapResult.added:
                                    mapResult.message = "Layer added successfully"
                                else:
                                    mapResult.message = "Possibly due to schema error or other cause: " + properties.definitionQuery
                                break
                    else:
                        # It's a File Geodatabase
                        parts = properties.regExp.split("/")
                        for root, dirs, files in os.walk(dataFilePath):
                            for gdb in dirs:
                                if re.match(parts[0], gdb):
                                    geoDatabase = (dataFilePath + "/" + gdb).replace("/", os.sep)
                                    arcpy.env.workspace = geoDatabase
                                    rasters = arcpy.ListRasters("*")
                                    for raster in rasters:
                                        if re.match(parts[1], raster):
                                            self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                            mapResult.added = self.addFileGeodatabaseToLayer(self.dataFrame, geoDatabase, layerToAdd, properties.definitionQuery, raster, properties.labelClasses, countryName)    
                                            mapResult.dataSource = geoDatabase + os.sep + raster
                                        
                                    featureClasses = arcpy.ListFeatureClasses()
                                    for featureClass in featureClasses:
                                        if re.match(parts[1], featureClass):
                                            self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                            mapResult.added = self.addFileGeodatabaseToLayer(self.dataFrame, geoDatabase, layerToAdd, properties.definitionQuery, featureClass, properties.labelClasses, countryName)    
                                            mapResult.dataSource = geoDatabase + os.sep + featureClass
                                            if mapResult.added:
                                                mapResult.message = "Layer added successfully"
                                            else:
                                                mapResult.message = "Possibly due to schema error or other cause: " + properties.definitionQuery
                                            # Found Geodatabase.  Stop iterating.          
                                            break
                    # If a file hasn't been added, and no other reason given, report what was expected
                    if ((mapResult.added is False) and (len(mapResult.message) == 0)):
                        mapResult.message = "Could not find file matching " + properties.sourceFolder + "/" + properties.regExp
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


    def _processLayer(self, layer, countryName):
        # Add layer to the report for later
        mapResult = MapResult(layer)
        properties = self.layerProperties.get(layer)
        if (properties is not None):
            layerFilePath = os.path.join(self.crashMoveFolder, (properties.layerName + ".lyr"))
            if (os.path.exists(layerFilePath)):
                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                layerToAdd = arcpy.mapping.Layer(layerFilePath)
                # APS 06/09/2019 Please remove hardcoded path. See github comment
                # @TODO use CrashMoveFolder object - This would point to "2_ACTIVE folder
                #dataFilePath = os.path.join(self.root, "GIS", "2_Active_Data", properties.sourceFolder)
                dataFilePath = self.crashMoveFolder.active_data
                # @TODO Use Data Search
                if (os.path.isdir(dataFilePath)):
                    # APS 06/09/2019 I do not understand what you are testing here
                    # (eg ` if ("/" not in properties.regExp):`).
                    # Why is a forward slash required in a regex for a filename/featureclass name?
                    # @TODO - Add comment for if gdb
                    if (".gdb/" not in properties.regExp):
                        onlyfiles = [f for f in listdir(dataFilePath) if isfile(join(dataFilePath, f))]
                        for fileName in onlyfiles:
                            if re.match(properties.regExp, fileName):
                                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                dataFile = os.path.join(dataFilePath, fileName)
                                mapResult.added = self.addDataToLayer(self.dataFrame, dataFile, layerToAdd, properties.definitionQuery, properties.labelClasses, countryName)
                                mapResult.dataSource = dataFile
                                if mapResult.added:
                                    mapResult.message = "Layer added successfully"
                                else:
                                    # APS 06/09/2019 Are you sure that this error can only be reached due to a
                                    # schema error? Would an error message along the lines of
                                    # "Error adding {layerName}. Possibly due to schema error or other cause"
                                    # be appropriate? See github comment
                                    # @TODO!!
                                    mapResult.message = "Unexpected schema.  Could not evaluate expression: " + properties.definitionQuery
                                break
                    else:
                        # It's a File Geodatabase
                        parts = properties.regExp.split("/")
                        for root, dirs, files in os.walk(dataFilePath):
                            for gdb in dirs:
                                if re.match(parts[0], gdb):
                                    geoDatabase = (dataFilePath + "/" + gdb).replace("/", os.sep)
                                    arcpy.env.workspace = geoDatabase
                                    rasters = arcpy.ListRasters("*")
                                    for raster in rasters:
                                        if re.match(parts[1], raster):
                                            self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                            mapResult.added = self.addFileGeodatabaseToLayer(self.dataFrame, geoDatabase, layerToAdd, properties.definitionQuery, raster, properties.labelClasses, countryName)    
                                            mapResult.dataSource = geoDatabase + os.sep + raster
                                        
                                    featureClasses = arcpy.ListFeatureClasses()
                                    for featureClass in featureClasses:
                                        if re.match(parts[1], featureClass):
                                            self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                            mapResult.added = self.addFileGeodatabaseToLayer(self.dataFrame, geoDatabase, layerToAdd, properties.definitionQuery, featureClass, properties.labelClasses, countryName)    
                                            mapResult.dataSource = geoDatabase + os.sep + featureClass
                                            if mapResult.added:
                                                mapResult.message = "Layer added successfully"
                                            else:
                                                # APS 06/09/2019 Are you sure that this error can only be reached due to a
                                                # schema error? Would an error message along the lines of
                                                # "Error adding {layerName}. Possibly due to schema error or other cause"
                                                # be appropriate? See github comment
                                                mapResult.message = "Unexpected schema.  Could not evaluate expression: " + properties.definitionQuery
                                            # Found Geodatabase.  Stop iterating.          
                                            break
                    # If a file hasn't been added, and no other reason given, report what was expected
                    if ((mapResult.added is False) and (len(mapResult.message) == 0)):
                        mapResult.message = "Could not find file matching " + properties.sourceFolder + "/" + properties.regExp
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
