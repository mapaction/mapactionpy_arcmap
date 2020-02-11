import os
import arcpy
import jsonpickle
import re
from map_cookbook import MapCookbook
from map_report import MapReport
from map_result import MapResult
from data_source import DataSource
from mapactionpy_controller.event import Event
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
# from mapactionpy_controller.name_convention import NamingConvention
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
        self.countryName = None
        eventFilePath = os.path.join(crashMoveFolder, "event_description.json")
        cmfFilePath = os.path.join(crashMoveFolder, "cmf_description.json")

        self.datasetTypes = ["SHAPEFILE_WORKSPACE",
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

        self.replaceDataSourceOnly = False
        self.event = None
        self.cmfConfig = None
        self.namingConvention = None
        self.summary = "Insert summary here"
        self.dataSources = set()
        self.versionNumber = versionNumber
        self.createDate = datetime.utcnow().strftime("%d-%b-%Y")
        self.createTime = datetime.utcnow().strftime("%H:%M")
        self.export = False

        if os.path.exists(eventFilePath):
            self.event = Event(eventFilePath)
        if os.path.exists(cmfFilePath):
            self.cmfConfig = CrashMoveFolder(cmfFilePath)
            # self.namingConvention = NamingConvention(self.cmfConfig.data_nc_definition)

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

    def scale(self):
        newScale = ""
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            if df.name.lower() == "main map":
                intValue = '{:,}'.format(int(df.scale))
                newScale = "1: " + intValue + " (At A3)"
                break
        return newScale

    def spatialReference(self):
        spatialReferenceString = "Unknown"
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            if df.name.lower() == "main map":
                if (len(df.spatialReference.datumName) > 0):
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
                if (lyr.longName != "Data Driven Pages"):
                    arcpy.mapping.RemoveLayer(df, lyr)
        self.mxd.save()

    def cook(self, productName, countryName, replaceDataSourceOnly=False):
        self.countryName = countryName
        self.replaceDataSourceOnly = replaceDataSourceOnly
        arcpy.env.addOutputsToMap = False
        if not replaceDataSourceOnly:
            self.disableLayers()
            self.removeLayers()
        self.mapReport = MapReport(productName)
        recipe = self.cookbook.products.get(productName, None)
        if (recipe is not None):
            self.export = recipe.export
            if (len(recipe.summary) > 0):
                self.summary = recipe.summary
            for layer in recipe.layers:
                self.processLayer(layer)
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
                       addToLegend,
                       zoomMultiplier=0):
        added = False
        for lyr in arcpy.mapping.ListLayers(layer):
            if lyr.supports("LABELCLASSES"):
                for labelClass in labelClasses:
                    for lblClass in lyr.labelClasses:
                        if (lblClass.className == labelClass.className):
                            lblClass.SQLQuery = labelClass.SQLQuery.replace('{COUNTRY_NAME}', countryName)
                            lblClass.expression = labelClass.expression
                            lblClass.showClassLabels = labelClass.showClassLabels
            if lyr.supports("DATASOURCE"):  # An annotation layer does not support DATASOURCE
                for datasetType in self.datasetTypes:
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

                        if (self.replaceDataSourceOnly):
                            self.mxd.save()
                        else:
                            arcpy.mapping.AddLayer(dataFrame, lyr, "BOTTOM")
                        break
                lyr.visible = False
                self.applyZoom(dataFrame, lyr, zoomMultiplier)

        return added

    """
    Returns map report in json format
    """

    def report(self):
        return(jsonpickle.encode(self.mapReport, unpicklable=False))

    """
    Updates or Adds a layer of data.  Maintains the Map Report.
    """

    def processLayer(self, layer):
        mapResult = MapResult(layer["name"])
        properties = self.layerProperties.properties.get(layer["name"], None)
        if (properties is not None):
            layerFilePath = os.path.join(self.layerDirectory, (properties.layerName + ".lyr"))
            if (os.path.exists(layerFilePath)):
                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                try:
                    updateLayer = arcpy.mapping.ListLayers(self.mxd, properties.layerName, self.dataFrame)[0]
                    # Replace existing layer
                    mapResult = self.updateLayer(updateLayer, properties, layerFilePath)
                except Exception as ex:  # noqa
                    # Layer doesn't exist, add new layer
                    mapResult = self.addLayer(properties, layerFilePath, layer)

                if (mapResult.added):
                    try:
                        newLayer = arcpy.mapping.ListLayers(self.mxd, properties.layerName, self.dataFrame)[0]
                        self.applyZoom(self.dataFrame, newLayer, layer.get('zoomMultiplier', 0))
                    except Exception:
                        pass

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
                elm.text = self.createDate + " " + self.createTime
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

    def applyZoom(self, dataFrame, lyr, zoomMultiplier):
        if (zoomMultiplier != 0):
            buffer = zoomMultiplier
            arcpy.env.overwriteOutput = "True"
            extent = lyr.getExtent(True)  # visible extent of layer

            extBuffDist = ((int(abs(extent.lowerLeft.X - extent.lowerRight.X))) * buffer)
            newExtentPts = arcpy.Array()
            newExtentPts.add(arcpy.Point(extent.lowerLeft.X-extBuffDist,
                                         extent.lowerLeft.Y-extBuffDist,
                                         extent.lowerLeft.Z,
                                         extent.lowerLeft.M,
                                         extent.lowerLeft.ID))

            newExtentPts.add(arcpy.Point(extent.lowerRight.X+extBuffDist,
                                         extent.lowerRight.Y-extBuffDist,
                                         extent.lowerRight.Z,
                                         extent.lowerRight.M,
                                         extent.lowerRight.ID))

            newExtentPts.add(arcpy.Point(extent.upperRight.X+extBuffDist,
                                         extent.upperRight.Y+extBuffDist,
                                         extent.upperRight.Z,
                                         extent.upperRight.M,
                                         extent.upperRight.ID))

            newExtentPts.add(arcpy.Point(extent.upperLeft.X-extBuffDist,
                                         extent.upperLeft.Y+extBuffDist,
                                         extent.upperLeft.Z,
                                         extent.upperLeft.M,
                                         extent.upperLeft.ID))

            newExtentPts.add(arcpy.Point(extent.lowerLeft.X-extBuffDist,
                                         extent.lowerLeft.Y-extBuffDist,
                                         extent.lowerLeft.Z,
                                         extent.lowerLeft.M,
                                         extent.lowerLeft.ID))
            polygonTmp2 = arcpy.Polygon(newExtentPts)
            dataFrame.extent = polygonTmp2
            self.mxd.save()

    def updateLayer(self, layerToUpdate, layerProperties, layerFilePath):
        mapResult = None

        if (".gdb/" not in layerProperties.regExp):
            mapResult = self.updateLayerWithFile(layerProperties, layerToUpdate, layerFilePath)
        else:
            mapResult = self.updateLayerWithGdb(layerProperties)
        return mapResult

    def addLayer(self, layerProperties, layerFilePath, cookbookLayer):
        mapResult = MapResult(layerProperties.layerName)
        layerToAdd = arcpy.mapping.Layer(layerFilePath)
        if (".gdb/" not in layerProperties.regExp):
            mapResult = self.addLayerWithFile(layerProperties, layerToAdd, cookbookLayer)
        else:
            mapResult = self.addLayerWithGdb(layerProperties, layerToAdd, cookbookLayer)
        return mapResult

    def updateLayerWithFile(self, layerProperties, updateLayer, layerFilePath):
        mapResult = MapResult(layerProperties.layerName)

        dataFiles = self.find(self.cmfConfig.active_data, layerProperties.regExp)
        for dataFile in (dataFiles):
            base = os.path.basename(dataFile)
            datasetName = os.path.splitext(base)[0]
            dataDirectory = os.path.dirname(os.path.realpath(dataFile))

            sourceLayer = arcpy.mapping.Layer(layerFilePath)
            arcpy.mapping.UpdateLayer(self.dataFrame, updateLayer, sourceLayer, False)

            newLayer = arcpy.mapping.ListLayers(self.mxd, updateLayer.name, self.dataFrame)[0]
            if newLayer.supports("DATASOURCE"):
                for datasetType in self.datasetTypes:
                    try:
                        if (newLayer.supports("DEFINITIONQUERY") and (layerProperties.definitionQuery)):
                            newLayer.definitionQuery = layerProperties.definitionQuery.replace(
                                '{COUNTRY_NAME}', self.countryName)
                        newLayer.replaceDataSource(dataDirectory, datasetType, datasetName)
                        mapResult.message = "Layer updated successfully"
                        mapResult.added = True
                        ds = DataSource(dataFile)
                        mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.replace("\\", "/"), "")   # noqa
                        mapResult.hash = ds.calculate_checksum()
                        break
                    except Exception:
                        pass

            if (mapResult.added is True):
                self.mxd.save()
                break
        return mapResult

    def updateLayerWithGdb(self, layerProperties):
        mapResult = MapResult(layerProperties.layerName)
        mapResult.message = "Update layer for a GeoDatabase not yet implemented"
        return mapResult

    def addLayerWithFile(self, layerProperties, layerToAdd, cookBookLayer):
        mapResult = MapResult(layerProperties.layerName)
        dataFiles = self.find(self.cmfConfig.active_data, layerProperties.regExp)

        for dataFile in (dataFiles):
            base = os.path.basename(dataFile)
            datasetName = os.path.splitext(base)[0]
            dataDirectory = os.path.dirname(os.path.realpath(dataFile))

            if layerToAdd.supports("LABELCLASSES"):
                for labelClass in layerProperties.labelClasses:
                    for lblClass in layerToAdd.labelClasses:
                        if (lblClass.className == labelClass.className):
                            lblClass.SQLQuery = labelClass.SQLQuery.replace('{COUNTRY_NAME}', self.countryName)
                            lblClass.expression = labelClass.expression
                            lblClass.showClassLabels = labelClass.showClassLabels

            if layerToAdd.supports("DATASOURCE"):
                for datasetType in self.datasetTypes:
                    try:
                        layerToAdd.replaceDataSource(dataDirectory, datasetType, datasetName)
                        mapResult.message = "Layer added successfully"
                        mapResult.added = True
                        ds = DataSource(dataFile)
                        mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.replace("\\", "/"), "")   # noqa
                        mapResult.hash = ds.calculate_checksum()
                        break
                    except Exception:
                        pass

            if ((mapResult.added is True) and (layerProperties.definitionQuery)):
                definitionQuery = layerProperties.definitionQuery.replace('{COUNTRY_NAME}', self.countryName)
                layerToAdd.definitionQuery = definitionQuery
                try:
                    arcpy.SelectLayerByAttribute_management(layerToAdd,
                                                            "SUBSET_SELECTION",
                                                            layerProperties.definitionQuery)
                except Exception:
                    mapResult.added = False
                    mapResult.message = "Selection query failed: " + layerProperties.definitionQuery
                    self.mxd.save()

            if (mapResult.added is True):
                self.applyZoom(self.dataFrame, layerToAdd, cookBookLayer.get('zoomMultiplier', 0))

                if layerProperties.addToLegend is False:
                    self.legendEntriesToRemove.append(layerToAdd.name)
                arcpy.mapping.AddLayer(self.dataFrame, layerToAdd, "BOTTOM")
                self.mxd.save()
                break

        return mapResult

    def addLayerWithGdb(self, layerProperties, layerToAdd, cookBookLayer):
        mapResult = MapResult(layerProperties.layerName)

        # It's a File Geodatabase
        parts = layerProperties.regExp.split("/")
        gdbPath = parts[0]
        geoDatabases = self.find(self.cmfConfig.active_data, gdbPath, True)
        for geoDatabase in geoDatabases:
            arcpy.env.workspace = geoDatabase
            rasters = arcpy.ListRasters("*")
            for raster in rasters:
                if re.match(parts[1], raster):
                    self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, layerProperties.mapFrame)[0]
                    mapResult.added = self.addDataToLayer(self.dataFrame,
                                                          geoDatabase,
                                                          layerToAdd,
                                                          layerProperties.definitionQuery,
                                                          raster,
                                                          layerProperties.labelClasses,
                                                          self.countryName,
                                                          layerProperties.addToLegend)

                    dataFile = geoDatabase + os.sep + raster
                    ds = DataSource(dataFile)
                    mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.replace("\\", "/"), "")  # noqa
                    mapResult.hash = ds.calculate_checksum()
                    break
            featureClasses = arcpy.ListFeatureClasses()
            for featureClass in featureClasses:
                if re.match(parts[1], featureClass):
                    # Found Geodatabase.  Stop iterating.
                    self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, layerProperties.mapFrame)[0]
                    mapResult.added = self.addDataToLayer(self.dataFrame,
                                                          geoDatabase,
                                                          layerToAdd,
                                                          layerProperties.definitionQuery,
                                                          featureClass,
                                                          layerProperties.labelClasses,
                                                          self.countryName,
                                                          layerProperties.addToLegend)
                    dataFile = geoDatabase + os.sep + featureClass
                    ds = DataSource(dataFile)
                    mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.replace("\\", "/"), "")  # noqa
                    mapResult.hash = ds.calculate_checksum()
                    break

        return mapResult
