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


ESRI_DATASET_TYPES = [
    "SHAPEFILE_WORKSPACE",
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
    "VPF_WORKSPACE"
]


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

        self.replaceDataSourceOnly = False
        # It appears that this is not used - therefore should be removed. If it is used, then it
        # TODO asmith 2020/03/06
        # needs a more specific name. There exist Data, Layerfile, MXD and Template Naming
        # Conventions (and possibly more)
        self.namingConvention = None

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

    def get_map_scale(self, mxd, recipe):
        """
        Returns a human-readable string representing the map scale of the
        principal map frame of the mxd.

        @param mxd: The MapDocument object of the map being produced.
        @param recipe: The MapRecipe object being used to produced it.
        @returns: The string representing the map scale.
        """
        scale_str = ""
        for df in arcpy.mapping.ListDataFrames(mxd, recipe.principal_map_frame):
            if df.name == recipe.principal_map_frame:
                scale_str = '1: {:,} (At A3)'.format(int(df.scale))
                break
        return scale_str

    def get_map_spatial_ref(self, mxd, recipe):
        """
        Returns a human-readable string representing the spatial reference used to display the
        principal map frame of the mxd.

        @param mxd: The MapDocument object of the map being produced.
        @param recipe: The MapRecipe object being used to produced it.
        @returns: The string representing the spatial reference. If the spatial reference cannot be determined
                  then the value "Unknown" is returned.
        """
        data_frames = [df for df in arcpy.mapping.ListDataFrames(mxd) if df.name == recipe.principal_map_frame]

        if not data_frames:
            err_msg = 'MXD does not have a MapFrame (aka DataFrame) with the name "{}"'.format(
                recipe.principal_map_frame)
            raise ValueError(err_msg)

        if len(data_frames) > 1:
            err_msg = 'MXD has more than one MapFrames (aka DataFrames) with the name "{}"'.format(
                recipe.principal_map_frame)
            raise ValueError(err_msg)

        df = data_frames.pop()
        spatial_ref_str = "Unknown"

        if (len(df.spatialReference.datumName) > 0):
            spatial_ref_str = df.spatialReference.datumName
            spatial_ref_str = spatial_ref_str[2:]
            spatial_ref_str = spatial_ref_str.replace('_', ' ')

        return spatial_ref_str

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
    #   * If `cook()` only gets called once in the life of a MapChef object, then it should be
    #     entire procedural, with no parameters (everything set via the constructor) and
    #     subsequent attempt to call `cook()` should result in an exception
    #   * If `cook()` can be called multiple times, then the `mxd` and the `map_version_number`
    #     should be parameters for the cook method and not for the constructor.
    def cook(self, recipe):
        arcpy.env.addOutputsToMap = False

        self.disableLayers()
        self.removeLayers()

        self.mapReport = MapReport(recipe.product)
        if recipe:
            for recipe_frame in recipe.map_frames:
                arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name).pop()

                for recipe_lyr in recipe_frame.layers:
                    # Do things at an individual layer level
                    self.process_layer(recipe_lyr, arc_data_frame)

                # Do things at an map/data frame level
                self.apply_frame_crs_and_extent(arc_data_frame, recipe_frame)

        # Do things at a map layout level
        self.enableLayers()
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        arcpy.env.addOutputsToMap = True
        self.showLegendEntries()
        self.mxd.save()

        if recipe:
            self.updateTextElements(recipe)
            self.mxd.save()

    def report_as_json(self):
        """
        Returns map report in json format
        """
        return(jsonpickle.encode(self.mapReport, unpicklable=False))

    def process_layer(self, recipe_lyr, arc_data_frame):
        """
        Updates or Adds a layer of data.  Maintains the Map Report.
        """
        mapResult = MapResult(recipe_lyr.name)
        # arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
        # Try just using add Layer (no update layer option)
        mapResult = self.addLayer(recipe_lyr, arc_data_frame)

        self.mapReport.add(mapResult)

    def updateTextElements(self, recipe):
        """
        Updates Text Elements in Marginalia
        """
        for elm in arcpy.mapping.ListLayoutElements(self.mxd, "TEXT_ELEMENT"):
            if elm.name == "country":
                elm.text = self.eventConfiguration.country_name
            if elm.name == "title":
                elm.text = recipe.product
            if elm.name == "create_date_time":
                elm.text = self.createDate + " " + self.createTime
            if elm.name == "summary":
                elm.text = recipe.summary
            if elm.name == "map_no":
                elm.text = recipe.mapnumber
            if elm.name == "mxd_name":
                elm.text = os.path.basename(self.mxd.filePath)
            if elm.name == "scale":
                elm.text = self.get_map_scale(self.mxd, recipe)
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
                versionNumberString = "v" + str(recipe.version_num).zfill(2)
                elm.text = versionNumberString
            if elm.name == "spatial_reference":
                elm.text = self.get_map_spatial_ref(self.mxd, recipe)
            if elm.name == "glide_no":
                if self.eventConfiguration and self.eventConfiguration.glide_number:
                    elm.text = self.eventConfiguration.glide_number
            if elm.name == "donor_credit":
                if self.eventConfiguration:
                    elm.text = self.eventConfiguration.default_donor_credits
            if elm.name == "disclaimer":
                if self.eventConfiguration:
                    elm.text = self.eventConfiguration.default_disclaimer_text
            if elm.name == "map_producer":
                if self.eventConfiguration:
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

    def apply_frame_crs_and_extent(self, arc_data_frame, recipe_frame):
        """
        """
        # minx, miny, maxx, maxy = recipe_frame.extent
        # First set the spatial reference
        if not recipe_frame.crs[:5].lower() == 'epsg:':
            raise ValueError('unrecognised `recipe_frame.crs` value "{}". String does not begin with "EPSG:"'.format(
                recipe_frame.crs))

        prj_wkid = int(recipe_frame.crs[5:])
        arc_data_frame.spatialReference = arcpy.SpatialReference(prj_wkid)

        if recipe_frame.extent:
            new_extent = arcpy.Extent(*recipe_frame.extent)
            arc_data_frame.extent = new_extent
        self.mxd.save()

    def addLayer(self, recipe_lyr, recipe_frame):
        # addLayer(recipe_lyr, recipe_lyr.layer_file_path, recipe_lyr.name)
        mapResult = MapResult(recipe_lyr.name)
        logging.debug('Attempting to add layer; {}'.format(recipe_lyr.layer_file_path))
        arc_lyr_to_add = arcpy.mapping.Layer(recipe_lyr.layer_file_path)
        # if (".gdb/" not in recipe_lyr.reg_exp):
        #     mapResult = self.addLayerWithFile(recipe_lyr, arc_lyr_to_add,  recipe_frame)
        # else:
        #     mapResult = self.addLayerWithGdb(recipe_lyr, arc_lyr_to_add,  recipe_frame)

        # Apply Label Classes
        try:
            self.apply_layer_visiblity(arc_lyr_to_add, recipe_lyr)
            self.apply_label_classes(arc_lyr_to_add, recipe_lyr)
            mapResult = self.addLayerWithFile(recipe_lyr, arc_lyr_to_add,  recipe_frame)
            # Apply Definition Query
            self.apply_definition_query(arc_lyr_to_add, recipe_lyr)
            recipe_lyr.success = True
        except Exception:
            recipe_lyr.success = False

        return mapResult

    def apply_layer_visiblity(self, arc_lyr_to_add, recipe_lyr):
        if arc_lyr_to_add.supports('VISIBLE'):
            try:
                arc_lyr_to_add.visible = recipe_lyr.visible
            except Exception as exp:
                recipe_lyr.error_messages.append('Error whilst applying layer visiblity: {}'.format(
                    exp.message))

    def apply_label_classes(self, arc_lyr_to_add, recipe_lyr):
        if arc_lyr_to_add.supports("LABELCLASSES"):
            for labelClass in recipe_lyr.label_classes:
                for lblClass in arc_lyr_to_add.labelClasses:
                    if (lblClass.className == labelClass.class_name):
                        lblClass.SQLQuery = labelClass.sql_query
                        lblClass.expression = labelClass.expression
                        lblClass.showClassLabels = labelClass.show_class_labels

    def apply_definition_query(self, arc_lyr_to_add, recipe_lyr):
        if recipe_lyr.definition_query and arc_lyr_to_add.supports('DEFINITIONQUERY'):
            try:
                arc_lyr_to_add.definition_query = recipe_lyr.definition_query
            except Exception as exp:
                recipe_lyr.error_messages.append('Error whilst applying definition query: "{}"\n{}'.format(
                    recipe_lyr.definition_query, exp.message))

            # try:
            #     arcpy.SelectLayerByAttribute_management(arc_lyr_to_add,
            #                                             "SUBSET_SELECTION",
            #                                             recipe_lyr.definition_query)
            # except Exception as exp:
            #     recipe_lyr.success = False
            #     recipe_lyr.error_messages.append('Selection query failed: {}\n{}'.format(
            #         recipe_lyr.definition_query, exp.message))
            #     raise exp

    def get_dataset_type_from_path(self, f_path):
        """
        * '.shp' at the end of a path name
        * '.img' at the end of a path name
        * '.tif' at the end of a path name
        * '.gdb\' in teh middle of a path name
        """
        dataset_type_lookup = [
            (r'\.shp$', 'SHAPEFILE_WORKSPACE'),
            (r'\.img$', 'RASTER_WORKSPACE'),
            (r'\.tif$', 'RASTER_WORKSPACE'),
            (r'\.gdb\\.+', 'FILEGDB_WORKSPACE')
        ]

        for reg_ex, dataset_type in dataset_type_lookup:
            if re.search(reg_ex, f_path):
                return dataset_type

        raise ValueError('"Unsupported dataset type with path: {}'.format(f_path))

    def addLayerWithFile(self, recipe_lyr, arc_lyr_to_add, recipe_frame):
        mapResult = MapResult(recipe_lyr.name)

        # Skip past any layer which didn't already have a source file located
        try:
            recipe_lyr.data_source_path
        except AttributeError:
            return mapResult

        r_path = os.path.realpath(recipe_lyr.data_source_path)
        data_src_dir = os.path.dirname(r_path)
        dataset_type = self.get_dataset_type_from_path(r_path)

        # Apply Data Source
        if arc_lyr_to_add.supports("DATASOURCE"):
            try:
                arc_lyr_to_add.replaceDataSource(data_src_dir, dataset_type, recipe_lyr.data_name)
                mapResult.message = "Layer added successfully"
                mapResult.added = True
                ds = DataSource(recipe_lyr.data_name)
                mapResult.dataSource = recipe_lyr.data_source_path
                mapResult.hash = ds.calculate_checksum()
            except Exception as exp:
                raise exp

        if mapResult.added:
            arc_data_frame = arcpy.mapping.ListDataFrames(self.mxd, recipe_frame.name)[0]
            # TODO add proper fix for applyZoom in line with these two cards
            # https: // trello.com/c/Bs70ru1s/145-design-criteria-for-selecting-zoom-extent
            # https://trello.com/c/piE3tKRp/146-implenment-rules-for-selection-zoom-extent
            # self.applyZoom(self.dataFrame, arc_lyr_to_add, cookBookLayer.get('zoomMultiplier', 0))

            # Is this even required after adding each layer?
            # self.apply_frame_crs_and_extent(arc_data_frame, recipe_frame)

            if recipe_lyr.add_to_legend is False:
                self.legendEntriesToRemove.append(arc_lyr_to_add.name)
            arcpy.mapping.AddLayer(arc_data_frame, arc_lyr_to_add, "BOTTOM")
            self.mxd.save()
            # break

        return mapResult
