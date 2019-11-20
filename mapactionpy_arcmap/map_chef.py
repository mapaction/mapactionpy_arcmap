import os
import arcpy
import jsonpickle
import re
from map_cookbook import MapCookbook
from map_report import MapReport
from map_result import MapResult
from mapactionpy_controller.event import Event
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.name_convention import NamingConvention
from layer_properties import LayerProperties
from datetime import datetime


class MapChef:
    """
    Worker which creates a Map based on a predefined "recipe" from a cookbook
    """

    def __init__(self,
                 mxd,
                 cookbookJsonFile,
                 layerPropertiesJsonFile,
                 crashMoveFolder,
                 layerDirectory,
                 versionNumber=1):
        """
        Arguments:
           mxd {MXD file} -- MXD file.
           cookbookJsonFile {str} -- Path to Map Cookbook json file
           layerPropertiesJsonFile {str} -- Path to Layer Properties json file
           crashMoveFolder {str} -- Path to Crash Move Folder json file
           layerDirectory {str} -- Path to Layer (.lyr) files
           versionNumber {int} -- version number of map
        """
        self.mxd = mxd

        self.layerPropertiesJsonFile = layerPropertiesJsonFile
        self.cookbookJsonFile = cookbookJsonFile
        self.crashMoveFolder = crashMoveFolder
        self.layerDirectory = layerDirectory
        self.cookbook = MapCookbook(self.cookbookJsonFile)
        self.layerProperties = LayerProperties(self.layerPropertiesJsonFile)
        self.legendEntriesToRemove = list()
        eventFilePath = os.path.join(crashMoveFolder, "event_description.json")
        cmfFilePath = os.path.join(crashMoveFolder, "cmf_description.json")

        self.event = None
        self.cmfConfig = None
        self.namingConvention = None
        self.summary = "Insert summary here"
        self.dataSources = set()
        self.versionNumber = versionNumber

        if os.path.exists(eventFilePath):
            self.event = Event(eventFilePath)
        if os.path.exists(cmfFilePath):
            self.cmfConfig = CrashMoveFolder(cmfFilePath)
            self.namingConvention = NamingConvention(self.cmfConfig.data_nc_definition)

    def disableLayers(self):
        """
        Makes all layers invisible for all data-frames
        """
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                lyr.visible = False

    def returnScale(self, dfscale):
        # https://community.esri.com/thread/163596
        scalebar = [2, 3, 4, 5, 6, 10]
        dfscale = dfscale/12
        dfscale = str(int(dfscale))
        dfscaleLen = len(dfscale)
        numcheck = int(dfscale[0])
        for each in scalebar:
            if numcheck < each:
                multi = '1'
                while dfscaleLen > 1:
                    multi = multi + '0'
                    dfscaleLen = dfscaleLen - 1
                scalebar = each * int(multi)
                dataframescale = scalebar * 12
                return scalebar, dataframescale
                break

    def scale(self):
        newScale = ""
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            if df.name.lower() == "main map":
                intValue = '{:,}'.format(int(df.scale))
                newScale = "1: " + intValue + " (At A3)"
                break
        return newScale

    def spatialReference(self):
        spatialReferenceString = ""
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            if df.name.lower() == "main map":
                spatialReferenceString = df.spatialReference.datumName
                spatialReferenceString = spatialReferenceString[2:]
                spatialReferenceString = spatialReferenceString.replace('_', ' ')
                break
        return spatialReferenceString

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
            if (len(recipe.summary) > 0):
                self.summary = recipe.summary
            for layer in recipe.layers:
                self.processLayer(layer, countryName)
        self.enableLayers()
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        arcpy.env.addOutputsToMap = True
        self.showLegendEntries()
        self.mxd.save()

        if (recipe is not None):
            self.updateTextElements(productName, countryName, recipe.mapnumber)
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

    def addDataToLayer(self,
                       dataFrame,
                       dataFile,
                       layer,
                       definitionQuery,
                       datasetName,
                       labelClasses,
                       countryName,
                       addToLegend):
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
                            lblClass.SQLQuery = labelClass.SQLQuery.replace('{COUNTRY_NAME}', countryName)
                            lblClass.expression = labelClass.expression
            if lyr.supports("DATASOURCE"):  # An annotation layer does not support DATASOURCE
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
                        if addToLegend is False:
                            self.legendEntriesToRemove.append(lyr.name)
                            if (self.namingConvention is not None):
                                dnr = self.namingConvention.validate(datasetName)
                                # We want to capture Description:
                                if 'Description' in dnr.source._fields:
                                    if (dnr.source.Description.lower() not in ('unknown', 'undefined', 'mapaction')):
                                        self.dataSources.add(dnr.source.Description)
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
                # If it's not a File Geodatabase (gdb) the regexp won't contain ".gdb/"
                if (".gdb/" not in properties.regExp):
                    dataFiles = self.find(self.cmfConfig.active_data, properties.regExp)
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
                                                              countryName,
                                                              properties.addToLegend)
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
                    geoDatabases = self.find(self.cmfConfig.active_data, gdbPath, True)
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
                                                                      countryName,
                                                                      properties.addToLegend)
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
                                                                      countryName,
                                                                      properties.addToLegend)
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

    """
    Updates Text Elements in Marginalia

    Arguments:
        productName {str} -- Name of map product.  Used as map title.
        countryName {str} -- Country name
        mapNumber   {str} -- Map Action Map Number
    """

    def updateTextElements(self, productName, countryName, mapNumber):
        for elm in arcpy.mapping.ListLayoutElements(self.mxd, "TEXT_ELEMENT"):
            if elm.name == "country":
                elm.text = countryName
            if elm.name == "title":
                elm.text = productName
            if elm.name == "create_date_time":
                elm.text = datetime.utcnow().strftime("%d-%b-%Y %H:%M UTC")
            if elm.name == "summary":
                elm.text = self.summary
            if elm.name == "map_no":
                elm.text = mapNumber
            if elm.name == "mxd_name":
                elm.text = os.path.basename(self.mxd.filePath)
            if elm.name == "scale":
                elm.text = self.scale()
            if elm.name == "data_sources":
                iter = 0
                dataSourcesString = "<BOL>Data Sources:</BOL>" + os.linesep + os.linesep
                for ds in self.dataSources:
                    if (iter > 0):
                        dataSourcesString = dataSourcesString + ", "
                    dataSourcesString = dataSourcesString + ds
                    iter = iter + 1
                elm.text = dataSourcesString
            if elm.name == "map_version":
                versionNumberString = "v" + str(self.versionNumber).zfill(2)
                elm.text = versionNumberString
            if elm.name == "spatial_reference":
                elm.text = self.spatialReference()
            if elm.name == "glide_no":
                if (self.event is not None):
                    elm.text = self.event.glide_number
            if elm.name == "donor_credit":
                if (self.event is not None):
                    elm.text = self.event.default_donor_credits
            if elm.name == "disclaimer":
                if (self.event is not None):
                    elm.text = self.event.default_disclaimer_text
            if elm.name == "map_producer":
                if (self.event is not None):
                    elm.text = "Produced by " + \
                        self.event.default_source_organisation + \
                        os.linesep + \
                        self.event.deployment_primary_email + \
                        os.linesep + \
                        self.event.default_source_organisation_url
        self.mxd.save()

    def showLegendEntries(self):
        for legend in arcpy.mapping.ListLayoutElements(self.mxd, "LEGEND_ELEMENT"):
            layerNames = list()
            for lyr in legend.listLegendItemLayers():
                if ((lyr.name in self.legendEntriesToRemove) or (lyr.name in layerNames)):
                    legend.removeItem(lyr)
                else:
                    layerNames.append(lyr.name)
        self.mxd.save()

    def alignLegend(self, orientation):
        for legend in arcpy.mapping.ListLayoutElements(self.mxd, "LEGEND_ELEMENT"):
            if orientation == "landscape":
                # Resize
                legend.elementWidth = 60
                legend.elementPositionX = 248.9111
                legend.elementPositionY = 40
        self.mxd.save()

    def resizeScaleBar(self):
        elm = arcpy.mapping.ListLayoutElements(self.mxd, "MAPSURROUND_ELEMENT", "Scale Bar")[0]
        elm.elementWidth = 51.1585
        self.mxd.save()
