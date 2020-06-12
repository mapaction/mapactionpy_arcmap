import arcpy
import errno
import glob
import logging
import os
from shutil import copyfile
from slugify import slugify
from PIL import Image
from zipfile import ZipFile
from resizeimage import resizeimage
from map_chef import MapChef
from mapactionpy_controller.xml_exporter import XmlExporter
from mapactionpy_controller.runner import BaseRunnerPlugin


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(module)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)-8s %(message)s',
                    )

# logger = logging.getLogger(__name__)
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# # create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s
#  (%(module)s +ln%(lineno)s) ;- %(message)s')
# formatter = logging.Formatter('%(asctime)s %(module)s %(name)s.%(funcName)s
#  +%(lineno)s: %(levelname)-8s [%(process)d] %(message)s')
# ch.setFormatter(formatter)
# # add the handlers to the logger
# logger.addHandler(ch)


class ArcMapRunner(BaseRunnerPlugin):
    """
    ArcMapRunner - Executes the ArcMap automation methods
    """

    def __init__(self,
                 eventConfig):
        self.event = eventConfig
        super(ArcMapRunner, self).__init__(self.event.cmf_descriptor_path)

        self.replaceOnly = False
        self.exportMap = False
        self.minx = 0
        self.miny = 0
        self.maxx = 0
        self.maxy = 0
        self.chef = None
        # self.cmf = CrashMoveFolder(self.event.cmf_descriptor_path)

    def build_project_files(self, **kwargs):
        # Construct a Crash Move Folder object if the cmf_description.json exists
        recipe = kwargs['recipe']
        mxd = arcpy.mapping.MapDocument(recipe.map_project_path)

        self.chef = MapChef(mxd, self.cmf, self.event)
        self.chef.cook(recipe, self.replaceOnly)
        self.chef.alignLegend(self.event.orientation)

        # Output the Map Generation report alongside the MXD
        reportJsonFile = recipe.map_project_path.replace(".mxd", ".json")
        with open(reportJsonFile, 'w') as outfile:
            outfile.write(self.chef.report_as_json())

        return recipe

    def get_projectfile_extension(self):
        return '.mxd'

    def get_lyr_render_extension(self):
        return '.lyr'

    # TODO: asmith 2020/03/03
    # There is a lot going on in this method and I'm not sure I understand all of it. However here
    # are some thoughts:
    #

    #
    # 3) I think it would be more consistent to use the naming convention classes for the mxd template; eg
    # https://github.com/mapaction/mapactionpy_controller/pull/38 This helps avoid the need to hardcode the
    # naming convention for input mxd templates.
    #
    # 4) Is it possible to aviod the need to hardcode the naming convention for the output mxds? Eg could a
    # String.Template be specified within the Cookbook?
    # https://docs.python.org/2/library/string.html#formatspec
    # https://www.python.org/dev/peps/pep-3101/

    def get_aspect_ratios_of_templates(self, possible_templates):
        # TODO: pending https://trello.com/c/AQrn4InI/150-implement-selection-of-template
        selected_template = possible_templates.pop()
        logging.debug('selected template files; {}'.format(selected_template))
        return selected_template

    def create_ouput_map_project(self, **kwargs):
        recipe = kwargs['recipe']
        # Create `mapNumberDirectory` for output
        output_dir = os.path.join(self.cmf.map_projects, recipe.mapnumber)

        if not(os.path.isdir(output_dir)):
            os.mkdir(output_dir)

        # Construct output MXD name
        output_map_base = slugify(unicode(recipe.product))
        recipe.version_num = self.get_next_map_version_number(output_dir, recipe.mapnumber, output_map_base)
        output_map_name = '{}-v{}-{}{}'.format(
            recipe.mapnumber, str(recipe.version_num).zfill(2), output_map_base, self.get_projectfile_extension())
        recipe.map_project_path = os.path.abspath(os.path.join(output_dir, output_map_name))
        logging.debug('MXD path for new map; {}'.format(recipe.map_project_path))
        logging.debug('Map Version number; {}'.format(recipe.version_num))

        # Copy `src_template` to `recipe.map_project_path`
        copyfile(recipe.template_path, recipe.map_project_path)

        return recipe

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

    # TODO: asmith 2020/03/03
    #
    # 1) Please avoid hardcoding the naming convention for the mxds wherever possible. The Naming Convention
    # classes can avoid the need to hardcode the naming convention for the input mxd templates. It might be
    # possible to avoid the need to hardcode the naming convention for the output mxds using a
    # String.Template be specified within the Cookbook?
    # https://docs.python.org/2/library/string.html#formatspec
    # https://www.python.org/dev/peps/pep-3101/
    #
    # 2) This only checks the filename for the mxd - it doesn't check the values within the text element of
    # the map layout view (and hence the output metadata).
    def get_next_map_version_number(self, mapNumberDirectory, mapNumber, mapFileName):
        versionNumber = 0
        files = glob.glob(mapNumberDirectory + os.sep + mapNumber+'-v[0-9][0-9]-' + mapFileName + '.mxd')
        for file in files:
            versionNumber = int(os.path.basename(file).replace(mapNumber + '-v', '').replace(('-' + mapFileName+'.mxd'), ''))  # noqa
        versionNumber = versionNumber + 1
        if (versionNumber > 99):
            versionNumber = 1
        return versionNumber

    """
    Generates all file for export
    """

    def export_maps(self, **kwargs):
        """
        Accumulate some of the parameters for export XML, then calls
        _do_export(....) to do that actual work
        """
        recipe = kwargs['recipe']
        export_params = {}
        export_params = self._create_export_dir(export_params, recipe)
        export_params = self._do_export(export_params, recipe)
        self._zip_exported_files(export_params)

    def _create_export_dir(self, export_params, recipe):
        # Accumulate parameters for export XML
        version_str = "v" + str(recipe.version_num).zfill(2)
        export_directory = os.path.abspath(
            os.path.join(self.cmf.export_dir, recipe.mapnumber, version_str))
        export_params["exportDirectory"] = export_directory

        try:
            os.makedirs(export_directory)
        except OSError as exc:  # Python >2.5
            # Note 'errno.EEXIST' is not a typo. There should be two 'E's.
            # https://docs.python.org/2/library/errno.html#errno.EEXIST
            if exc.errno == errno.EEXIST and os.path.isdir(export_directory):
                pass
            else:
                raise

        return export_params

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

        export_params['pdfFileLocation'] = self.exportPdf(core_file_name, export_dir, arc_mxd, export_params)
        export_params['jpgFileLocation'] = self.exportJpeg(core_file_name, export_dir, arc_mxd, export_params)
        export_params['pngThumbNailFileLocation'] = self.exportPngThumbNail(
            core_file_name, export_dir, arc_mxd, export_params)

        if recipe.atlas:
            self._export_atlas(recipe, arc_mxd, export_dir, core_file_name)

        xmlExporter = XmlExporter(self.event, self.chef)
        export_params['mapNumber'] = recipe.mapnumber
        export_params['productName'] = recipe.product
        export_params['versionNumber'] = recipe.version_num
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
                    elm.text = recipe_with_atlas.category + " map of " + self.event.country_name +\
                        '\n' +\
                        "<CLR red = '255'>Sheet - " + region + "</CLR>"
                if elm.name == "map_no":
                    elm.text = recipe_with_atlas.mapnumber + "_Sheet_" + region.replace(' ', '_')

            # Clear selection, otherwise the selected feature is highlighted in the exported map
            arcpy.SelectLayerByAttribute_management(arc_lyr, "CLEAR_SELECTION")
            # Export to PDF
            pdfFileName = core_file_name + "-" + \
                slugify(unicode(region)) + "-" + str(self.event.default_pdf_res_dpi) + "dpi.pdf"
            pdfFileLocation = os.path.join(export_dir, pdfFileName)

            arcpy.mapping.ExportToPDF(arc_mxd, pdfFileLocation, resolution=int(self.event.default_pdf_res_dpi))
            # if arcpy.Exists(os.path.join(export_dir, shpFile)):
            #     arcpy.Delete_management(os.path.join(export_dir, shpFile))

    def _zip_exported_files(self, export_params):
        # Get key params as local variables
        core_file_name = export_params['coreFileName']
        export_dir = export_params['exportDirectory']
        mdr_xml_file_path = export_params['exportXmlFileLocation']
        jpg_path = export_params['jpgFileLocation']
        png_thumbnail_path = export_params['pngThumbNailFileLocation']
        # And now Zip
        zipFileName = core_file_name+".zip"
        zipFileLocation = os.path.join(export_dir, zipFileName)

        with ZipFile(zipFileLocation, 'w') as zipObj:
            zipObj.write(mdr_xml_file_path, os.path.basename(mdr_xml_file_path))
            zipObj.write(jpg_path, os.path.basename(jpg_path))
            zipObj.write(png_thumbnail_path, os.path.basename(png_thumbnail_path))

            # TODO: asmith 2020/03/03
            # Given we are explictly setting the pdfFileName for each page within the DDPs
            # it is possible return a list of all of the filenames for all of the PDFs. Please
            # can we use this list to include in the zip file. There are edge cases where just
            # adding all of the pdfs in a particular directory might not behave correctly (eg if
            # the previous run had crashed midway for some reason)
            for pdf in os.listdir(export_dir):
                if pdf.endswith(".pdf"):
                    zipObj.write(os.path.join(export_dir, pdf),
                                 os.path.basename(os.path.join(export_dir, pdf)))
        print("Export complete to " + export_dir)

    def exportJpeg(self, coreFileName, exportDirectory, mxd, exportParams):
        # JPEG
        jpgFileName = coreFileName+"-"+str(self.event.default_jpeg_res_dpi) + "dpi.jpg"
        jpgFileLocation = os.path.join(exportDirectory, jpgFileName)
        exportParams["jpgFileName"] = jpgFileName
        arcpy.mapping.ExportToJPEG(mxd, jpgFileLocation)
        jpgFileSize = os.path.getsize(jpgFileLocation)
        exportParams["jpgFileSize"] = jpgFileSize
        return jpgFileLocation

    def exportPdf(self, coreFileName, exportDirectory, mxd, exportParams):
        # PDF
        pdfFileName = coreFileName+"-"+str(self.event.default_pdf_res_dpi) + "dpi.pdf"
        pdfFileLocation = os.path.join(exportDirectory, pdfFileName)
        exportParams["pdfFileName"] = pdfFileName
        arcpy.mapping.ExportToPDF(mxd, pdfFileLocation, resolution=int(self.event.default_pdf_res_dpi))
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

    """
    Generates Export XML file

    Arguments:
        params {dict} -- Must contain the following parameters:
            * pdfFileName
            * pdfFileSize
            * jpgFileName
            * jpgFileSize
            * coreFileName
            * productType
            * exportDirectory

    Returns:
        Path to export XML file
    """


# def is_valid_file(parser, arg):
#     if not os.path.exists(arg):
#         parser.error("The file %s does not exist!" % arg)
#         return False
#     else:
#         return arg


# def is_valid_directory(parser, arg):
#     if os.path.isdir(arg):
#         return arg
#     else:
#         parser.error("The directory %s does not exist!" % arg)
#         return False


# def add_bool_arg(parser, name, default=False):
#     group = parser.add_mutually_exclusive_group(required=False)
#     group.add_argument('--' + name, dest=name, action='store_true')
#     group.add_argument('--no-' + name, dest=name, action='store_false')
#     parser.set_defaults(**{name: default})


# TODO: asmith 2020/03/03
# 1) Personally I am not convinced by the need to allow the user to manually specify or override
# all of the values that are typically included in the cmf_description.json file and/or the
# event_description.json (unless it is necessary for the ArcMap esriAddin).
#
# If this is desirable/required, then the wrangling and validation of those commandline args
# should be done outside of this class and in the mapactionpy_controller module.
#
# 2) I believe that there is a bug in the handling of the `--product` parameter. Also I take a
# different view as to what the default behaviour should be.
# BUG: At present the `--product` parameter is marked as optional, though I'm pretty sure that
# that a value of None would cause problems later on. I can't seen if a a string which ISN'T a
# product name in the mapCookbook.json is handled gracefully or not.
# Default behaviour: My prefered behaviour if no productName is specified, would be that that
# tool should attempt to create *all* of the products listed in the mapCookbook.json. Let's
# automate everything!
# def main():
    # parser = argparse.ArgumentParser(
    #     description='This component accepts a template MXD file, a list of the'
    #     'relevant datasets along with other information required to create an'
    #     'event specific instance of a map.',
    # )
    # parser.add_argument("-b", "--cookbook", dest="cookbookFile", required=False,
    #                     help="path to cookbook json file", metavar="FILE",
    #                     type=lambda x: is_valid_file(parser, x))
    # parser.add_argument("-l", "--layerConfig", dest="layerConfig", required=False,
    #                     help="path to layer config json file", metavar="FILE",
    #                     type=lambda x: is_valid_file(parser, x))
    # parser.add_argument("-t", "--template", dest="templateFile", required=False,
    #                     help="path to MXD file", metavar="FILE",
    #                     type=lambda x: is_valid_file(parser, x))
    # parser.add_argument("-e", "--eventConfigFile", dest="eventConfigFile", required=True,
    #                     help="path the Event Config File", metavar="FILE",
    #                     type=lambda x: is_valid_file(parser, x))
    # parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=False,
    #                     help="path to layer directory", metavar="FILE",
    #                     type=lambda x: is_valid_directory(parser, x))
    # parser.add_argument("-p", "--product", dest="productName", required=True,
    #                     help="Name of product")
    # parser.add_argument("-o", "--orientation", dest="orientation", default=None, required=False,
    #                     help="landscape|portrait")

    # add_bool_arg(parser, 'export')

    # args = parser.parse_args()
    # orientation = None
    # if (args.orientation is not None):
    #     if args.orientation.lower() == "landscape":
    #         orientation = args.orientation
    #     else:
    #         orientation = "portrait"

    # eventConfig = Event(args.eventConfigFile, orientation)
    # runner = ArcMapRunner(args.templateFile,
    #                       eventConfig,
    #                       args.productName)

    # templateUpdated = runner.build_project_files()
    # if (templateUpdated):
    #     if (args.export):
    #         runner.export_maps()
    #     else:
    #         print("Template updated.  No product export requested.")
    # else:
    #     print("No product generated.  No changes since last execution.")


# if __name__ == '__main__':
#     main()
