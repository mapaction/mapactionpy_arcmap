import arcpy
import logging
import os
import json
from PIL import Image
from resizeimage import resizeimage
from slugify import slugify
from map_chef import MapChef, get_map_scale, get_map_spatial_ref
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
        # Output the Map Generation report alongside the MXD
        final_recipe_file = recipe.map_project_path.replace(".mxd", ".json")
        with open(final_recipe_file, 'w') as outfile:
            outfile.write(str(recipe))

        return recipe

    def get_projectfile_extension(self):
        return '.mxd'

    def get_lyr_render_extension(self):
        return '.lyr'

    def get_aspect_ratios_of_templates(self, possible_templates, recipe):
        """
        Calculates the aspect ratio of the principal map frame within the list of templates.

        @param possible_templates: A list of paths to possible templates.
        @param recipe: A MapRecipe which is used to determine the principal map frame.
        @returns: A list of tuples. For each tuple the first element is the path to the template. The second
                  element is the aspect ratio of the largest* map frame within that template.
                  See `_get_largest_map_frame` for the description of hour largest is determined.
        """
        logging.debug('Calculating the aspect ratio of the largest map frame within the list of templates.')
        results = []
        for template in possible_templates:
            mxd = arcpy.mapping.MapDocument(template)
            arc_frame = arcpy.mapping.ListDataFrames(mxd, recipe.principal_map_frame).pop()

            aspect_ratio = float(arc_frame.elementWidth)/float(arc_frame.elementHeight)
            results.append((template, aspect_ratio))
            logging.debug('Calculated aspect ratio= {} for template={}'.format(aspect_ratio, template))

        return results

    def get_lyr_extents(self, recipe_lyr):
        print('arcmap_runner.get_lyr_extents')
        desc = arcpy.Describe(recipe_lyr.data_source_path)
        recipe_lyr.extent = json.loads(desc.extent.JSON)

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

    def _do_export(self, recipe):
        """
        Does the actual work of exporting of the PDF, Jpeg and thumbnail files.
        """
        arc_mxd = arcpy.mapping.MapDocument(recipe.map_project_path)

        # PDF export
        pdf_path = self.export_pdf(recipe, arc_mxd)
        recipe.zip_file_contents.append(pdf_path)
        recipe.export_metadata['pdffilename'] = os.path.basename(pdf_path)

        # JPEG export
        jpeg_path = self.export_jpeg(recipe, arc_mxd)
        recipe.zip_file_contents.append(jpeg_path)
        recipe.export_metadata['jpgfilename'] = os.path.basename(jpeg_path)

        # Thumbnail
        tb_nail_path = self.export_png_thumbnail(recipe, arc_mxd)
        recipe.zip_file_contents.append(tb_nail_path)
        recipe.export_metadata['pngThumbNailFileLocation'] = tb_nail_path

        # Atlas (if required)
        if recipe.atlas:
            export_dir = recipe.export_path
            self._export_atlas(recipe, arc_mxd, export_dir)

        # Update export metadata and return
        return self._update_export_metadata(recipe, arc_mxd)

    def _update_export_metadata(self, recipe, arc_mxd):
        """
        Populates the `recipe.export_metadata` dict
        """
        recipe.export_metadata["coreFileName"] = recipe.core_file_name
        recipe.export_metadata["product-type"] = "mapsheet"
        recipe.export_metadata['themes'] = recipe.export_metadata.get('themes', set())

        recipe.export_metadata['mapNumber'] = recipe.mapnumber
        recipe.export_metadata['title'] = recipe.product
        recipe.export_metadata['versionNumber'] = recipe.version_num
        recipe.export_metadata['summary'] = recipe.summary
        recipe.export_metadata["xmin"] = self.minx
        recipe.export_metadata["ymin"] = self.miny
        recipe.export_metadata["xmax"] = self.maxx
        recipe.export_metadata["ymax"] = self.maxy

        recipe.export_metadata["createdate"] = recipe.creation_time_stamp.strftime("%d-%b-%Y")
        recipe.export_metadata["createtime"] = recipe.creation_time_stamp.strftime("%H:%M")
        recipe.export_metadata["scale"] = get_map_scale(arc_mxd, recipe)
        recipe.export_metadata["datum"] = get_map_spatial_ref(arc_mxd, recipe)
        return recipe

    def _export_atlas(self, recipe_with_atlas, arc_mxd, export_dir):
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
            pdfFileName = recipe_with_atlas.core_file_name + "-" + \
                slugify(unicode(region)) + "-" + str(self.hum_event.default_pdf_res_dpi) + "dpi.pdf"
            pdfFileLocation = os.path.join(export_dir, pdfFileName)
            recipe_with_atlas.zip_file_contents.append(pdfFileLocation)

            logging.info('About to export atlas page for region; {}.'.format(region))
            arcpy.mapping.ExportToPDF(arc_mxd, pdfFileLocation, resolution=int(self.hum_event.default_pdf_res_dpi))
            logging.info('Completed exporting atlas page for for region; {}.'.format(region))

            # if arcpy.Exists(os.path.join(export_dir, shpFile)):
            #     arcpy.Delete_management(os.path.join(export_dir, shpFile))

    def export_jpeg(self, recipe, arc_mxd):
        # JPEG
        jpeg_fname = recipe.core_file_name+"-"+str(self.hum_event.default_jpeg_res_dpi) + "dpi.jpg"
        jpeg_fpath = os.path.join(recipe.export_path, jpeg_fname)
        recipe.export_metadata["jpgfilename"] = jpeg_fname
        arcpy.mapping.ExportToJPEG(arc_mxd, jpeg_fpath)
        jpeg_fsize = os.path.getsize(jpeg_fpath)
        recipe.export_metadata["jpgfilesize"] = jpeg_fsize
        return jpeg_fpath

    def export_pdf(self, recipe, arc_mxd):
        # recipe.core_file_name, recipe.export_path, arc_mxd, recipe.export_metadata

        # PDF
        pdf_fname = recipe.core_file_name+"-"+str(self.hum_event.default_pdf_res_dpi) + "dpi.pdf"
        pdf_fpath = os.path.join(recipe.export_path, pdf_fname)
        recipe.export_metadata["pdffilename"] = pdf_fname
        arcpy.mapping.ExportToPDF(arc_mxd, pdf_fpath, resolution=int(self.hum_event.default_pdf_res_dpi))
        pdf_fsize = os.path.getsize(pdf_fpath)
        recipe.export_metadata["pdffilesize"] = pdf_fsize
        return pdf_fpath

    def export_png_thumbnail(self, recipe, arc_mxd):
        # PNG Thumbnail.  Need to create a larger image first.
        # If this isn't done, the thumbnail is pixelated amd doesn't look good
        tmp_fname = "tmp-thumbnail.png"
        tmp_fpath = os.path.join(recipe.export_path, tmp_fname)
        arcpy.mapping.ExportToPNG(arc_mxd, tmp_fpath)

        png_fname = "thumbnail.png"
        png_fpath = os.path.join(recipe.export_path, png_fname)

        # Resize the thumbnail
        fd_img = open(tmp_fpath, 'r+b')
        img = Image.open(fd_img)
        img = resizeimage.resize('thumbnail', img, [140, 99])
        img.save(png_fpath, img.format)
        fd_img.close()

        # Remove the temporary larger thumbnail
        os.remove(tmp_fpath)
        return png_fpath
