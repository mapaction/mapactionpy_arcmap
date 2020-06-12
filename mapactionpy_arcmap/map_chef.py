import os
import arcpy
import jsonpickle
import logging
import re
from mapactionpy_controller.map_report import MapReport
from mapactionpy_controller.map_result import MapResult
from mapactionpy_controller.data_source import DataSource
from datetime import datetime

# TODO asmith 2020/03/06
# What is the separation of responsiblities between MapChef and ArcMapRunner? Why is the boundary
# between the two classes where it is? If I was to add a new function how would I know whether it
# should be added to MapChef or ArcMapRunner?
#
# Is it intended that the `cook()` method might be called multiple times in the life of a MapChef
# object? At present it looks to me like `cook()` can only be called once. In which case why have
# `cook()` as a public method and why not call it directly from the constructor.


class MapChef:
    """
    Worker which creates a Map based on a predefined "recipe" from a cookbook
    """
    # TODO asmith 2020/03/06
    # This constructor seem unnecessarily complicated. In the ArcMapRunner these objects are already
    # created:
    #   * MapCookbook object,
    #   * CrashMoveFolder object
    #   * LayerProperties object
    #   * Event object
    # It is already known that the various file and directory paths are valid etc. Why not just pass
    # those objects in as parameters to the MapChef constructor?
    #
    # Depending on whether or not it is indented that the `cook()` method might be called multiple
    # times in the life of a MapChef object, it would be worth reviewing

    def __init__(self,
                 mxd,
                 crashMoveFolder,
                 eventConfiguration):
        """
        Arguments:
           mxd {MXD file} -- MXD file.
           crashMoveFolder {CrashMoveFolder} -- CrashMoveFolder Object
           eventConfiguration {Event} -- Event Object
        """
        # TODO asmith 2020/03/06
        # See comment on the `cook()` method about where and when the `mxd` parameter should be
        # passed.
        self.mxd = mxd
        self.crashMoveFolder = crashMoveFolder

        self.eventConfiguration = eventConfiguration
        # self.cookbook = cookbook
        self.legendEntriesToRemove = list()

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
        # It appears that this is not used - therefore should be removed. If it is used, then it
        # TODO asmith 2020/03/06
        # needs a more specific name. There exist Data, Layerfile, MXD and Template Naming
        # Conventions (and possibly more)
        self.namingConvention = None
        # TODO asmith 2020/03/06
        # I suspect it would be more robust to set
        # self.summary = None
        self.summary = "Insert summary here"
        self.dataSources = set()
        self.createDate = datetime.utcnow().strftime("%d-%b-%Y")
        self.createTime = datetime.utcnow().strftime("%H:%M")
        self.export = False

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

    # TODO asmith 2020/0306
    # Do we need to accommodate a use case where we would want to add layers but not make them
    # visible? If so is this something that we deal with when we get to it?
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

    # TODO asmith 2020/03/06
    # I would suggest that:
    #   * If `cook() only gets called once in the life of a MapChef object, then it should be
    #     entire procedural, with no parameters (everything set via the constructor) and
    #     subsequent attempt to call `cook()` should result in an exception
    #   * If `cook()` can be called multiple times, then the `mxd` and the `map_version_number`
    #     should be parameters for the cook method and not for the constructor.
    #
    # Not with standing the above, the relevant Recipe object has already be identified and
    # validated in the ArcMapRunner object. Why not just pass that instead of the productName?

    def cook(self, recipe, replaceDataSourceOnly=False):
        self.recipe = recipe
        self.replaceDataSourceOnly = replaceDataSourceOnly
        arcpy.env.addOutputsToMap = False
        if not replaceDataSourceOnly:
            self.disableLayers()
            self.removeLayers()

        self.mapReport = MapReport(self.recipe.product)
        if (self.recipe is not None):
            if len(self.recipe.summary):
                self.summary = self.recipe.summary
            for mf in self.recipe.map_frames:
                for layer in mf.layers:
                    self.process_layer(layer, mf)

        self.enableLayers()
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        arcpy.env.addOutputsToMap = True
        self.showLegendEntries()
        self.mxd.save()

        if (recipe is not None):
            self.updateTextElements()
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
                       addToLegend,
                       zoomMultiplier=0):
        added = False
        for lyr in arcpy.mapping.ListLayers(layer):
            if lyr.supports("LABELCLASSES"):
                for labelClass in labelClasses:
                    for lblClass in lyr.label_classes:
                        if (lblClass.className == labelClass.className):
                            lblClass.SQLQuery = labelClass.sql_query.replace('{COUNTRY_NAME}',
                                                                             self.eventConfiguration.country_name)
                            lblClass.expression = labelClass.expression
                            lblClass.showClassLabels = labelClass.show_class_labels
            if lyr.supports("DATASOURCE"):  # An annotation layer does not support DATASOURCE
                for datasetType in self.datasetTypes:
                    try:
                        lyr.replaceDataSource(dataFile, datasetType, datasetName)
                        added = True
                    except Exception:
                        pass

                    if ((added is True) and (definitionQuery)):
                        definitionQuery = definitionQuery.replace('{COUNTRY_NAME}',
                                                                  self.eventConfiguration.country_name)
                        lyr.definition_query = definitionQuery
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

    def report_as_json(self):
        """
        Returns map report in json format
        """
        return(jsonpickle.encode(self.mapReport, unpicklable=False))

    def process_layer(self, recipe_lyr, recipe_frame):
        """
        Updates or Adds a layer of data.  Maintains the Map Report.
        """
        mapResult = MapResult(recipe_lyr.name)
        arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
        try:
            # BUG
            # The layer name in the TOC is not necessarily == recipe_lyr.name
            # arc_lyr_to_update = arcpy.mapping.ListLayers(self.mxd, recipe_lyr.name, self.dataFrame)[0]
            # Try this instead
            lyr_index = recipe_frame.layers.index(recipe_lyr)
            arc_lyr_to_update = arcpy.mapping.ListLayers(self.mxd, None, arc_data_frame)[lyr_index]

            # Replace existing layer
            mapResult = self.updateLayer(arc_lyr_to_update, recipe_lyr, recipe_frame)
        except IndexError:
            # Layer doesn't exist, add new layer
            mapResult = self.addLayer(recipe_lyr, arc_data_frame)

        if mapResult.added:
            try:
                # Seperate the next two lines so that the cause of any exceptions is more easily
                # appartent from the stack trace.
                # BUG
                # The layer name in the TOC is not necessarily == recipe_lyr.name
                # lyr_list = arcpy.mapping.ListLayers(self.mxd, recipe_lyr.name, self.dataFrame)
                # new_layer = lyr_list[0]
                # Try this instead
                lyr_index = recipe_frame.layers.index(recipe_lyr)
                new_layer = arcpy.mapping.ListLayers(self.mxd, None, arc_data_frame)[lyr_index]
                self.applyZoom(arc_data_frame, new_layer, 0)
            except IndexError:
                pass

        self.mapReport.add(mapResult)

    def find(self, rootdir, regexp, gdb=False):
        returnPaths = list()
        # TODO asmith 2020/03/06
        # What is the purpose of wrangling the regexps here?
        # The regexs in the layerProperties.json just match the filenames. The purpose of this
        # seems to be to change the regexs to work on the full path, and then later join the full
        # filename with the directory path before attempting to match the regexs.
        # I suspect there are some edge cases where incorrectly named files could inadvertantly
        # matched here.
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
                        # TODO asmith 2020/03/06
                        # Is this necessary? Having a `$` at the end of the regex would have the
                        # effect of as excluding the lock files.
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

    """

    def updateTextElements(self):
        for elm in arcpy.mapping.ListLayoutElements(self.mxd, "TEXT_ELEMENT"):
            if elm.name == "country":
                elm.text = self.eventConfiguration.country_name
            if elm.name == "title":
                elm.text = self.recipe.product
            if elm.name == "create_date_time":
                elm.text = self.createDate + " " + self.createTime
            if elm.name == "summary":
                elm.text = self.summary
            if elm.name == "map_no":
                elm.text = self.recipe.mapnumber
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
                versionNumberString = "v" + str(self.recipe.version_num).zfill(2)
                elm.text = versionNumberString
            if elm.name == "spatial_reference":
                elm.text = self.spatialReference()
            if elm.name == "glide_no":
                if self.eventConfiguration and self.eventConfiguration.glide_number:
                    elm.text = self.eventConfiguration.glide_number
            if elm.name == "donor_credit":
                if (self.eventConfiguration is not None):
                    elm.text = self.eventConfiguration.default_donor_credits
            if elm.name == "disclaimer":
                if (self.eventConfiguration is not None):
                    elm.text = self.eventConfiguration.default_disclaimer_text
            if elm.name == "map_producer":
                if (self.eventConfiguration is not None):
                    elm.text = "Produced by " + \
                        self.eventConfiguration.default_source_organisation + \
                        os.linesep + \
                        self.eventConfiguration.deployment_primary_email + \
                        os.linesep + \
                        self.eventConfiguration.default_source_organisation_url
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

    # TODO asmith 2020/03/06
    # Please don't hard code size and location of elements on the template
    def alignLegend(self, orientation):
        for legend in arcpy.mapping.ListLayoutElements(self.mxd, "LEGEND_ELEMENT"):
            if orientation == "landscape":
                # Resize
                legend.elementWidth = 60
                legend.elementPositionX = 248.9111
                legend.elementPositionY = 40
        self.mxd.save()

    # TODO asmith 2020/03/06
    # Please don't hard code size and location of elements on the template
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

            # TODO asmith 2020/03/06
            # This is untested but possibly much terser:
            # ```
            #        x_min = extent.XMin - extBuffDist
            #        y_min = extent.YMin - extBuffDist
            #        x_max = extent.XMax + extBuffDist
            #        y_max = extent.YMax + extBuffDist
            #        new_extent = arcpy.Extent(x_min, y_min, x_max, y_max)
            #        dataFrame.extent = new_extent
            # ```

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

    # TODO: asmith 2020/03/06
    # `updateLayer()` and `addLayer()` seem very similar. Is it possible to refactor to reduce
    # duplication?
    def updateLayer(self, arc_lyr_to_update, recipe_lyr, recipe_frame):
        mapResult = None

        if (".gdb/" not in recipe_lyr.reg_exp):
            mapResult = self.updateLayerWithFile(recipe_lyr, arc_lyr_to_update,
                                                 recipe_lyr.layer_file_path, recipe_frame)
        else:
            mapResult = self.updateLayerWithGdb(recipe_lyr, recipe_frame)
        return mapResult

    # TODO: asmith 2020/03/06
    # `updateLayer()` and `addLayer()` seem very similar. Is it possible to refactor to reduce
    # duplication?
    def addLayer(self, recipe_lyr, recipe_frame):
        # addLayer(recipe_lyr, recipe_lyr.layer_file_path, recipe_lyr.name)
        mapResult = MapResult(recipe_lyr.name)
        logging.debug('Attempting to add layer; {}'.format(recipe_lyr.layer_file_path))
        arc_lyr_to_add = arcpy.mapping.Layer(recipe_lyr.layer_file_path)
        if (".gdb/" not in recipe_lyr.reg_exp):
            mapResult = self.addLayerWithFile(recipe_lyr, arc_lyr_to_add, recipe_lyr.name, recipe_frame)
        else:
            mapResult = self.addLayerWithGdb(recipe_lyr, arc_lyr_to_add, recipe_lyr.name, recipe_frame)
        return mapResult

    # TODO: asmith 2020/03/06
    # These three methods appear very similar:
    #   * `addLayerWithFile()`
    #   * `addLayerWithGdb()`
    #   * `updateLayerWithFile()`
    # Is it possible to refactor to reduce duplication?
    def updateLayerWithFile(self, layerProperties, updateLayer, layerFilePath, recipe_frame):
        mapResult = MapResult(layerProperties.name)

        dataFiles = self.find(self.crashMoveFolder.active_data, layerProperties.reg_exp)
        for dataFile in (dataFiles):
            base = os.path.basename(dataFile)
            datasetName = os.path.splitext(base)[0]
            dataDirectory = os.path.dirname(os.path.realpath(dataFile))

            sourceLayer = arcpy.mapping.Layer(layerFilePath)
            arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
            arcpy.mapping.UpdateLayer(arc_data_frame, updateLayer, sourceLayer, False)

            # BUG
            # The layer name in the TOC is not necessarily == recipe_lyr.name
            # newLayer = arcpy.mapping.ListLayers(self.mxd, updateLayer.name, self.dataFrame)[0]
            # Try this instead
            lyr_index = recipe_frame.layers.index(updateLayer)
            newLayer = arcpy.mapping.ListLayers(self.mxd, None, arc_data_frame)[lyr_index]

            if newLayer.supports("DATASOURCE"):
                for datasetType in self.datasetTypes:
                    try:
                        if (newLayer.supports("DEFINITIONQUERY") and (layerProperties.definition_query)):
                            newLayer.definition_query = layerProperties.definition_query.replace(
                                '{COUNTRY_NAME}', self.eventConfiguration.country_name)
                        newLayer.replaceDataSource(dataDirectory, datasetType, datasetName)
                        mapResult.message = "Layer updated successfully"
                        mapResult.added = True
                        ds = DataSource(dataFile)
                        mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.path.replace("\\", "/"), "")   # noqa
                        mapResult.hash = ds.calculate_checksum()
                        break
                    except Exception:
                        pass

            if (mapResult.added is True):
                self.mxd.save()
                break
        return mapResult

    def updateLayerWithGdb(self, layerProperties, recipe_frame):
        mapResult = MapResult(layerProperties.name)
        mapResult.message = "Update layer for a GeoDatabase not yet implemented"
        return mapResult

    # TODO: asmith 2020/03/06
    # These three methods appear very similar:
    #   * `addLayerWithFile()`
    #   * `addLayerWithGdb()`
    #   * `updateLayerWithFile()`
    # Is it possible to refactor to reduce duplication?
    def addLayerWithFile(self, layerProperties, layerToAdd, cookBookLayer, recipe_frame):
        mapResult = MapResult(layerProperties.name)
        dataFiles = self.find(self.crashMoveFolder.active_data, layerProperties.reg_exp)

        for dataFile in (dataFiles):
            base = os.path.basename(dataFile)
            datasetName = os.path.splitext(base)[0]
            dataDirectory = os.path.dirname(os.path.realpath(dataFile))

            if layerToAdd.supports("LABELCLASSES"):
                for labelClass in layerProperties.label_classes:
                    for lblClass in layerToAdd.labelClasses:
                        if (lblClass.className == labelClass.class_name):
                            lblClass.SQLQuery = labelClass.sql_query.replace('{COUNTRY_NAME}',
                                                                             self.eventConfiguration.country_name)
                            lblClass.expression = labelClass.expression
                            lblClass.showClassLabels = labelClass.show_class_labels

            if layerToAdd.supports("DATASOURCE"):
                for datasetType in self.datasetTypes:
                    try:
                        layerToAdd.replaceDataSource(dataDirectory, datasetType, datasetName)
                        mapResult.message = "Layer added successfully"
                        mapResult.added = True
                        ds = DataSource(dataFile)
                        mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.path.replace("\\", "/"), "")   # noqa
                        mapResult.hash = ds.calculate_checksum()
                        break
                    except Exception:
                        pass

            if ((mapResult.added is True) and (layerProperties.definition_query)):
                definitionQuery = layerProperties.definition_query.replace('{COUNTRY_NAME}',
                                                                           self.eventConfiguration.country_name)
                layerToAdd.definition_query = definitionQuery
                try:
                    arcpy.SelectLayerByAttribute_management(layerToAdd,
                                                            "SUBSET_SELECTION",
                                                            layerProperties.definition_query)
                except Exception:
                    mapResult.added = False
                    mapResult.message = "Selection query failed: " + layerProperties.definition_query
                    self.mxd.save()

            if (mapResult.added is True):
                arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
                # TODO add proper fix for applyZoom in line with these two cards
                # https: // trello.com/c/Bs70ru1s/145-design-criteria-for-selecting-zoom-extent
                # https://trello.com/c/piE3tKRp/146-implenment-rules-for-selection-zoom-extent
                # self.applyZoom(self.dataFrame, layerToAdd, cookBookLayer.get('zoomMultiplier', 0))
                self.applyZoom(arc_data_frame, layerToAdd, 0)

                if layerProperties.add_to_legend is False:
                    self.legendEntriesToRemove.append(layerToAdd.name)
                arcpy.mapping.AddLayer(arc_data_frame, layerToAdd, "BOTTOM")
                self.mxd.save()
                break

        return mapResult

    # TODO: asmith 2020/03/06
    # These three methods appear very similar:
    #   * `addLayerWithFile()`
    #   * `addLayerWithGdb()`
    #   * `updateLayerWithFile()`
    # Is it possible to refactor to reduce duplication?
    def addLayerWithGdb(self, layerProperties, layerToAdd, cookBookLayer, recipe_frame):
        mapResult = MapResult(layerProperties.name)

        # It's a File Geodatabase
        parts = layerProperties.reg_exp.split("/")
        gdbPath = parts[0]
        geoDatabases = self.find(self.crashMoveFolder.active_data, gdbPath, True)
        for geoDatabase in geoDatabases:
            arcpy.env.workspace = geoDatabase
            rasters = arcpy.ListRasters("*")
            for raster in rasters:
                if re.match(parts[1], raster):
                    arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
                    mapResult.added = self.addDataToLayer(arc_data_frame,
                                                          geoDatabase,
                                                          layerToAdd,
                                                          layerProperties.definition_query,
                                                          raster,
                                                          layerProperties.label_classes,
                                                          layerProperties.add_to_legend)

                    dataFile = geoDatabase + os.sep + raster
                    ds = DataSource(dataFile)
                    mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.path.replace("\\", "/"), "")  # noqa
                    mapResult.hash = ds.calculate_checksum()
                    break
            featureClasses = arcpy.ListFeatureClasses()
            for featureClass in featureClasses:
                if re.match(parts[1], featureClass):
                    # Found Geodatabase.  Stop iterating.
                    arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
                    mapResult.added = self.addDataToLayer(arc_data_frame,
                                                          geoDatabase,
                                                          layerToAdd,
                                                          layerProperties.definition_query,
                                                          featureClass,
                                                          layerProperties.label_classes,
                                                          layerProperties.add_to_legend)
                    dataFile = geoDatabase + os.sep + featureClass
                    ds = DataSource(dataFile)
                    mapResult.dataSource = dataFile.replace("\\", "/").replace(self.crashMoveFolder.path.replace("\\", "/"), "")  # noqa
                    mapResult.hash = ds.calculate_checksum()
                    break

        return mapResult
