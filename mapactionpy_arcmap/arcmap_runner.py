import arcpy
import logging
import os
from PIL import Image
from resizeimage import resizeimage
from slugify import slugify
from map_chef import MapChef
from mapactionpy_controller.xml_exporter import XmlExporter
from mapactionpy_controller.plugin_base import BaseRunnerPlugin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(module)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)-8s %(message)s'
)


class ArcMapRunner(BaseRunnerPlugin):
    """
    ArcMapRunner - Executes the ArcMap automation methods
    """

    def __init__(self,
                 hum_event):
        super(ArcMapRunner, self).__init__(hum_event)

        self.exportMap = False
        self.minx = 0
        self.miny = 0
        self.maxx = 0
        self.maxy = 0
        self.chef = None

    def build_project_files(self, **kwargs):
        # Construct a Crash Move Folder object if the cmf_description.json exists
        recipe = kwargs['state']
        mxd = arcpy.mapping.MapDocument(recipe.map_project_path)

        self.chef = MapChef(mxd, self.cmf, self.hum_event)
        self.chef.cook(recipe)
        self.chef.alignLegend(self.hum_event.orientation)

        # Output the Map Generation report alongside the MXD
        reportJsonFile = recipe.map_project_path.replace(".mxd", ".json")
        with open(reportJsonFile, 'w') as outfile:
            outfile.write(self.chef.report_as_json())

        return recipe

    def get_projectfile_extension(self):
        return '.mxd'

    def get_lyr_render_extension(self):
        return '.lyr'

    def _get_largest_map_frame(self, data_frames):
        """
        This returns the dataframe occupying the largest area on the page.
        * If two data frames have identical areas then the widest is returned.
        * If two data frames have identical heights and widths returned then the alphabetically last (by `.name`)
          is returned.

        @param data_frames: a list of DataFrame objects, typically returned by `arcpy.mapping.ListDataFrames(mxd, "*")`
        @return: a single DataFrame object from the list.
        @raises ValueError: if there are two DataFrames in the list, which have identical `width`, `height` and `name`.
        """
        # df, area, width, name
        full_details = [{
            'df': df,
            'area': df.elementHeight*df.elementWidth,
            'width': df.elementWidth,
            'name': df.name} for df in data_frames]

        # select just the largest if there is a single largest
        # keep drilling down using different metrics until a single aspect ratio is discovered
        for metric_key in ['area', 'width', 'name']:
            max_size = max([df_detail[metric_key] for df_detail in full_details])
            sub_list = [df_detail for df_detail in full_details if df_detail[metric_key] == max_size]
            if len(sub_list) == 1:
                return sub_list[0]['df']

            # reduce the list of possible data frames for the next iteration
            full_details = sub_list

        # This means that there are two or more data frames with the same name and this is an error condition
        raise ValueError('There are two or more data frames with the same name')

    def get_aspect_ratio_of_target_area(self, recipe):
        pass

    def get_aspect_ratios_of_templates(self, possible_templates):
        """
        Calculates the aspect ratio of the largest* map frame within the list of templates.

        @param possible_templates: A list of paths to possible templates
        @returns: A list of tuples. For each tuple the first element is the path to the template. The second
                  element is the aspect ratio of the largest* map frame within that template.
                  See `_get_largest_map_frame` for the description of hour largest is determined.
        """
        logging.debug('Calculating the aspect ratio of the largest map frame within the list of templates.')
        results = []
        for template in possible_templates:
            mxd = arcpy.mapping.MapDocument(template)
            map_frame = self._get_largest_map_frame(arcpy.mapping.ListDataFrames(mxd, "*"))

            aspect_ratio = float(map_frame.elementWidth)/map_frame.elementHeight
            results.append((template, aspect_ratio))
            logging.debug('Calculated aspect ratio= {} for template={}'.format(aspect_ratio, template))

        return results

    # TODO: asmith 2020/03/03
    # Instinctively I would like to see this moved to the MapReport class with an __eq__ method which
    # would look very much like this one.

    def haveDataSourcesChanged(self, previousReportFile):
        # previousReportFile = '{}-v{}_{}.json'.format(
        #     recipe.mapnumber,
        #     str((version_num-1)).zfill(2),
        #     output_mxd_base
        # )
        # generationRequired = True
        # if (os.path.exists(os.path.join(output_dir, previousReportFile))):
        #     generationRequired = self.haveDataSourcesChanged(os.path.join(output_dir, previousReportFile))

        # returnValue = False
        # with open(previousReportFile, 'r') as myfile:
        #     data = myfile.read()
        #     # parse file
        #     obj = json.loads(data)
        #     for result in obj['results']:
        #         dataFile = os.path.join(self.event.path, (result['dataSource'].strip('/')))
        #         previousHash = result.get('hash', "")
        #         ds = DataSource(dataFile)
        #         latestHash = ds.calculate_checksum()
        #         if (latestHash != previousHash):
        #             returnValue = True
        #             break
        # return returnValue
        return True

    def _do_export(self, export_params, recipe):
        """
        Does the actual work of exporting of the PDF, Jpeg and thumbnail files.
        """
        export_dir = export_params["exportDirectory"]
        arc_mxd = arcpy.mapping.MapDocument(recipe.map_project_path)

        core_file_name = os.path.splitext(os.path.basename(recipe.map_project_path))[0]
        export_params["coreFileName"] = core_file_name
        productType = "mapsheet"
        export_params["productType"] = productType
        export_params['themes'] = export_params.get('themes', set())
        export_params['pdfFileLocation'] = self.exportPdf(core_file_name, export_dir, arc_mxd, export_params)
        export_params['jpgFileLocation'] = self.exportJpeg(core_file_name, export_dir, arc_mxd, export_params)
        export_params['pngThumbNailFileLocation'] = self.exportPngThumbNail(
            core_file_name, export_dir, arc_mxd, export_params)

        if recipe.atlas:
            self._export_atlas(recipe, arc_mxd, export_dir, core_file_name)

        xmlExporter = XmlExporter(self.hum_event, self.chef)
        export_params['mapNumber'] = recipe.mapnumber
        export_params['productName'] = recipe.product
        export_params['versionNumber'] = recipe.version_num
        export_params['summary'] = recipe.summary
        export_params["xmin"] = self.minx
        export_params["ymin"] = self.miny
        export_params["xmax"] = self.maxx
        export_params["ymax"] = self.maxy
        export_params['exportXmlFileLocation'] = xmlExporter.write(export_params)

        return export_params

    def _export_atlas(self, recipe_with_atlas, arc_mxd, export_dir, core_file_name):
        """
        Exports each individual page for recipes which contain an atlas definition
        """
        if not recipe_with_atlas.atlas:
            raise ValueError('Cannot export atlas. The specified recipe does not contain an atlas definition')

        # Disable view of Affected Country
        # TODO: create a seperate method _disable_view_of_affected_polygon
        # locationMapLayerName = "locationmap-admn-ad0-py-s0-locationmaps"  # Hard-coded
        # layerDefinition = self.layerDefinition.properties.get(locationMapLayerName)
        # locationMapDataFrameName = layerDefinition.mapFrame
        # locationMapDataFrame = arcpy.mapping.ListDataFrames(arc_mxd, locationMapDataFrameName)[0]
        # locationMapLyr = arcpy.mapping.ListLayers(arc_mxd, locationMapLayerName, locationMapDataFrame)[0]
        # locationMapDataFrame.extent = locationMapLyr.getExtent()
        # locationMapLyr.visible = False

        # recipe_frame = [mf for mf in recipe_with_atlas.map_frames if mf.name
        #    == recipe_with_atlas.atlas.map_frame][0]
        #
        # recipe_lyr = [recipe_lyr for recipe_lyr in recipe_frame.layers if
        #     recipe_lyr.name == recipe_with_atlas.atlas.layer_name][0]

        recipe_frame = recipe_with_atlas.get_frame(recipe_with_atlas.atlas.map_frame)
        recipe_lyr = recipe_frame.get_layer(recipe_with_atlas.atlas.layer_name)
        queryColumn = recipe_with_atlas.atlas.column_name

        lyr_index = recipe_frame.layers.index(recipe_lyr)
        arc_df = arcpy.mapping.ListDataFrames(arc_mxd, recipe_frame.name)[0]
        arc_lyr = arcpy.mapping.ListLayers(arc_mxd, None, arc_df)[lyr_index]

        # TODO: asmith 2020/03/03
        #
        # Presumably `regions` here means admin1 boundaries or some other internal
        # administrative devision? Replace with a more generic name.

        # For each layer and column name, export a regional map
        regions = list()
        # UpdateCursor requires that the queryColumn must be passed as a list or tuple
        with arcpy.da.UpdateCursor(arc_lyr.dataSource, [queryColumn]) as cursor:
            for row in cursor:
                regions.append(row[0])

        # This loop simulates the behaviour of Data Driven Pages. This is because of the
        # limitations in the arcpy API for maniplulating DDPs.
        for region in regions:
            # TODO: asmith 2020/03/03
            # Please do not hardcode mapFrame names. If a particular mapframe as a special
            # meaning then this should be explicit in the structure of the mapCookBook.json
            # and/or layerProperties.json files.arc_mxd, dataFrameName)[0]

            # Select the next region
            query = "\"" + queryColumn + "\" = \'" + region + "\'"
            arcpy.SelectLayerByAttribute_management(arc_lyr, "NEW_SELECTION", query)

            # Set the extent mapframe to the selected area
            arc_df.extent = arc_lyr.getSelectedExtent()

            # # Create a polygon using the bounding box
            # bounds = arcpy.Array()
            # bounds.add(arc_df.extent.lowerLeft)
            # bounds.add(arc_df.extent.lowerRight)
            # bounds.add(arc_df.extent.upperRight)
            # bounds.add(arc_df.extent.upperLeft)
            # # ensure the polygon is closed
            # bounds.add(arc_df.extent.lowerLeft)
            # # Create the polygon object
            # polygon = arcpy.Polygon(bounds, arc_df.extent.spatialReference)

            # bounds.removeAll()

            # # Export the extent to a shapefile
            # shapeFileName = "extent_" + slugify(unicode(region)).replace('-', '')
            # shpFile = shapeFileName + ".shp"

            # if arcpy.Exists(os.path.join(export_dir, shpFile)):
            #     arcpy.Delete_management(os.path.join(export_dir, shpFile))
            # arcpy.CopyFeatures_management(polygon, os.path.join(export_dir, shpFile))

            # # For the 'extent' layer...
            # locationMapDataFrameName = "Location map"
            # locationMapDataFrame = arcpy.mapping.ListDataFrames(arc_mxd, locationMapDataFrameName)[0]
            # extentLayerName = "locationmap-s0-py-extent"
            # extentLayer = arcpy.mapping.ListLayers(arc_mxd, extentLayerName, locationMapDataFrame)[0]

            # # Update the layer
            # extentLayer.replaceDataSource(export_dir, 'SHAPEFILE_WORKSPACE', shapeFileName)
            # arcpy.RefreshActiveView()

            # # In Main map, zoom to the selected region
            # dataFrameName = "Main map"
            # df = arcpy.mapping.ListDataFrames(arc_mxd, dataFrameName)[0]
            # arcpy.SelectLayerByAttribute_management(arc_lyr, "NEW_SELECTION", query)
            # df.extent = arc_lyr.getSelectedExtent()

            for elm in arcpy.mapping.ListLayoutElements(arc_mxd, "TEXT_ELEMENT"):
                if elm.name == "title":
                    elm.text = recipe_with_atlas.category + " map of " + self.hum_event.country_name +\
                        '\n' +\
                        "<CLR red = '255'>Sheet - " + region + "</CLR>"
                if elm.name == "map_no":
                    elm.text = recipe_with_atlas.mapnumber + "_Sheet_" + region.replace(' ', '_')

            # Clear selection, otherwise the selected feature is highlighted in the exported map
            arcpy.SelectLayerByAttribute_management(arc_lyr, "CLEAR_SELECTION")
            # Export to PDF
            pdfFileName = core_file_name + "-" + \
                slugify(unicode(region)) + "-" + str(self.hum_event.default_pdf_res_dpi) + "dpi.pdf"
            pdfFileLocation = os.path.join(export_dir, pdfFileName)

            arcpy.mapping.ExportToPDF(arc_mxd, pdfFileLocation, resolution=int(self.hum_event.default_pdf_res_dpi))
            # if arcpy.Exists(os.path.join(export_dir, shpFile)):
            #     arcpy.Delete_management(os.path.join(export_dir, shpFile))

    def exportJpeg(self, coreFileName, exportDirectory, mxd, exportParams):
        # JPEG
        jpgFileName = coreFileName+"-"+str(self.hum_event.default_jpeg_res_dpi) + "dpi.jpg"
        jpgFileLocation = os.path.join(exportDirectory, jpgFileName)
        exportParams["jpgFileName"] = jpgFileName
        arcpy.mapping.ExportToJPEG(mxd, jpgFileLocation)
        jpgFileSize = os.path.getsize(jpgFileLocation)
        exportParams["jpgFileSize"] = jpgFileSize
        return jpgFileLocation

    def exportPdf(self, coreFileName, exportDirectory, mxd, exportParams):
        # PDF
        pdfFileName = coreFileName+"-"+str(self.hum_event.default_pdf_res_dpi) + "dpi.pdf"
        pdfFileLocation = os.path.join(exportDirectory, pdfFileName)
        exportParams["pdfFileName"] = pdfFileName
        arcpy.mapping.ExportToPDF(mxd, pdfFileLocation, resolution=int(self.hum_event.default_pdf_res_dpi))
        pdfFileSize = os.path.getsize(pdfFileLocation)
        exportParams["pdfFileSize"] = pdfFileSize
        return pdfFileLocation

    def exportPngThumbNail(self, coreFileName, exportDirectory, mxd, exportParams):
        # PNG Thumbnail.  Need to create a larger image first.
        # If this isn't done, the thumbnail is pixelated amd doesn't look good
        pngTmpThumbNailFileName = "tmp-thumbnail.png"
        pngTmpThumbNailFileLocation = os.path.join(exportDirectory, pngTmpThumbNailFileName)
        arcpy.mapping.ExportToPNG(mxd, pngTmpThumbNailFileLocation)

        pngThumbNailFileName = "thumbnail.png"
        pngThumbNailFileLocation = os.path.join(exportDirectory, pngThumbNailFileName)

        # Resize the thumbnail
        fd_img = open(pngTmpThumbNailFileLocation, 'r+b')
        img = Image.open(fd_img)
        img = resizeimage.resize('thumbnail', img, [140, 99])
        img.save(pngThumbNailFileLocation, img.format)
        fd_img.close()

        # Remove the temporary larger thumbnail
        os.remove(pngTmpThumbNailFileLocation)
        return pngThumbNailFileLocation
