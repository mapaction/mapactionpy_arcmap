import arcpy
import argparse
import json
import errno
import glob
import os
from shutil import copyfile
from slugify import slugify
from PIL import Image
from zipfile import ZipFile
from resizeimage import resizeimage
from map_chef import MapChef
from mapactionpy_controller.map_cookbook import MapCookbook
from mapactionpy_controller.data_source import DataSource
from mapactionpy_controller.layer_properties import LayerProperties
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.event import Event
from mapactionpy_controller.xml_exporter import XmlExporter


class ArcMapRunner:
    """
    ArcMapRunner - Executes the ArcMap automation methods
    """

    # TODO: asmith 2020/03/03
    #
    # 1) I think that this constructor could be made much simpler by only requiring either
    # an Event object or an event_description.json file. Nearly all of the other parameters
    # could be detrived from oue of those.
    #
    # 2) If the path to the event_description.json file is used, make it the path to the file
    # itself and not the containing directory. That would avoid the need to hardcode the filename
    # of the event_description.json file.
    #
    # 4) I do not see the need for the ArcMapRunner to have it's own members which duplicate those
    # of the Event object or the CMF object. Eg. `myrunner.cmf.layer_properties` is fine.
    #
    # 5) If there is a case for allowing the user to manaually specify or override all of the values
    # that are typically included in the cmf_description.json file and/or the event_description.json
    # file than the wrangling and validation of those commandline args should be done outside of this
    # class and in the mapactionpy_controller module.
    def __init__(self,
                 templateFile,
                 eventConfig,
                 productName):
        self.mxdTemplate = templateFile
        self.cookbookFile = None
        self.layerPropertiesFile = None
        self.productName = productName
        self.event = eventConfig
        self.replaceOnly = False

        # TODO: asmith 2020/03/03
        # Do not hard code "real" values. Setting to `None` would seem safer here as that
        # ensures that if the versionNumber or mapNumber are not set correctly later in the
        # code, these default values do not accidently result in real outputs being overwritten
        self.versionNumber = 1
        self.mapNumber = "MA001"
        self.exportMap = False
        self.minx = 0
        self.miny = 0
        self.maxx = 0
        self.maxy = 0
        self.chef = None
        self.crashMoveFolder = CrashMoveFolder(self.event.cmf_descriptor_path)

        # TODO: asmith 2020/03/03
        # Much of here to line 132 is unrequired, as the CrashMoveFolder class already has a method
        # for verifying the existence of all of the relevant files and directories. By default this
        # happens when a CrashMoveFolder object is created. For the paranoid these two lines:
        # ```
        # if not self.cmf.verify_paths():
        #    raise ValueError("Cannot find paths and directories referenced by cmf {}".format(self.cmf.path))
        # ```

        # The following checks are used if the CMF description is over-ridden by the command line parameters
        if self.cookbookFile is None:
            if self.crashMoveFolder is not None:
                self.cookbookFile = self.crashMoveFolder.map_definitions
            else:
                raise Exception("Error: Could not derive cookbook file from " + self.event.cmf_descriptor_path)

        self.cookbook = MapCookbook(self.cookbookFile)
        self.recipe = self.cookbook.products[productName]

        if self.layerPropertiesFile is None:
            if self.crashMoveFolder is not None:
                self.layerPropertiesFile = self.crashMoveFolder.layer_properties
            else:
                raise Exception("Error: Could not derive layer config file from " + self.event.cmf_descriptor_path)
        # OLD 132
        # TODO: asmith 2020/03/03
        # The name `self.layerDefinition` is unclear and should be changed.
        #   * As far as I can see this object encapsulates the properties of multiple layers
        #     (not merely multiple properties of a single layer).
        #   * Also `layerDefinition` is easily confused with the DefinitionQuery of a layer (which
        #     it's not).
        self.layerDefinition = LayerProperties(self.crashMoveFolder, '.lyr')

    # TODO: asmith 2020/03/03
    # method name is unclear. Generate what? How does this relate to
    # the `generateXml` method?

    def generate(self):
        # Construct a Crash Move Folder object if the cmf_description.json exists
        generationRequired = False
        if self.mxdTemplate is None:
            self.mxdTemplate, self.mapNumber, self.versionNumber, generationRequired = self.get_template(
                self.cookbookFile, self.crashMoveFolder, self.productName)
        if (generationRequired):
            mxd = arcpy.mapping.MapDocument(self.mxdTemplate)

            self.chef = MapChef(mxd,
                                self.cookbook,
                                self.layerDefinition,
                                self.crashMoveFolder,
                                self.event,
                                self.versionNumber)
            self.chef.cook(self.recipe, self.replaceOnly)
            self.chef.alignLegend(self.event.orientation)

            # Output the Map Generation report alongside the MXD
            reportJsonFile = self.mxdTemplate.replace(".mxd", ".json")
            with open(reportJsonFile, 'w') as outfile:
                outfile.write(self.chef.report_as_json())
        return generationRequired

    # TODO: asmith 2020/03/03
    # There is a lot going on in this method and I'm not sure I understand all of it. However here
    # are some thoughts:
    #
    # 1) If the MapCookbook class had a method that validated the existance of all of the
    # templates it refers to then this method could be simplied somewhat. eg `self.recipe.template_mxd`
    # This would also make it simpler for the Cookbook to be tested/validated earlier and without
    # requiring any data; See https://wiki.mapaction.org/display/orgdev/Automatable+tests+of+CMF+contents
    #
    # 2) Why is the arcGisVersion required? Is this just to navigate the naming convention for mxd templates?
    # Would it be appropriate and/or simpler to ammend the name of the template files? They are already in a
    # dir called 'arcgis_10_6'. Or is there another arcpy related reason why it is required? Without it, it
    # would be possible to move this whole method over to the controller where it could be re-used for the
    # QGIS implementation.
    #
    # 3) I think it would be more consistent to use the naming convention classes for the mxd template; eg
    # https://github.com/mapaction/mapactionpy_controller/pull/38 This helps avoid the need to hardcode the
    # naming convention for input mxd templates.
    #
    # 4) Is it possible to aviod the need to hardcode the naming convention for the output mxds? Eg could a
    # String.Template be specified within the Cookbook?
    # https://docs.python.org/2/library/string.html#formatspec
    # https://www.python.org/dev/peps/pep-3101/
    def get_template(self, cookbookFile, crashMoveFolder, productName):
        arcGisVersion = crashMoveFolder.arcgis_version

        # Need to get the theme from the recipe to get the path to the MXD

        mapNumberTemplateFileName = self.recipe.mapnumber + "_" + self.event.orientation + ".mxd"
        mapNumberTemplateFilePath = os.path.join(crashMoveFolder.mxd_templates, mapNumberTemplateFileName)
        if os.path.exists(mapNumberTemplateFilePath):
            srcTemplateFile = mapNumberTemplateFilePath
            # In this instance, we only want to replace the datasource, everything else should say as is
            self.replaceOnly = True
        else:
            self.exportMap = self.recipe.export
            # TODO: asmith 2020/03/03
            # This will fail is the category is specified in the recipe in a different case to the
            # the case used in for the template filename.
            if (self.recipe.category.lower() == "reference"):
                templateFileName = arcGisVersion + "_" + \
                                   self.recipe.category + \
                                   "_" + \
                                   self.event.orientation + \
                                   "_bottom.mxd"
            elif (self.recipe.category.lower() == "ddp reference"):
                templateFileName = arcGisVersion + "_ddp_reference_" + self.event.orientation + ".mxd"
            elif (self.recipe.category.lower() == "thematic"):
                templateFileName = arcGisVersion + "_" + self.recipe.category + "_" + self.event.orientation + ".mxd"
            else:
                raise Exception("Error: Could not get source MXD from: " + crashMoveFolder.mxd_templates)

            srcTemplateFile = os.path.join(crashMoveFolder.mxd_templates, templateFileName)

        mapNumberDirectory = os.path.join(crashMoveFolder.mxd_products, self.recipe.mapnumber)

        if not(os.path.isdir(mapNumberDirectory)):
            os.mkdir(mapNumberDirectory)

        # Construct MXD name
        mapFileName = slugify(unicode(productName))
        versionNumber = self.get_next_map_version_number(mapNumberDirectory, self.recipe.mapnumber, mapFileName)
        previousReportFile = self.recipe.mapnumber + "-v" + str((versionNumber-1)).zfill(2) + "_" + mapFileName + ".json"  # noqa
        copiedFile = "NOT SET"
        generationRequired = True
        if (os.path.exists(os.path.join(mapNumberDirectory, previousReportFile))):
            generationRequired = self.haveDataSourcesChanged(os.path.join(mapNumberDirectory, previousReportFile))

        if (generationRequired is True):
            mapFileName = self.recipe.mapnumber + "-v" + str(versionNumber).zfill(2) + "_" + mapFileName + ".mxd"
            copiedFile = os.path.join(mapNumberDirectory, mapFileName)
            copyfile(srcTemplateFile, copiedFile)

        return copiedFile, self.recipe.mapnumber, versionNumber, generationRequired

    # TODO: asmith 2020/03/03
    # Instinctively I would like to see this moved to the MapReport class with an __eq__ method which
    # would look very much like this one.
    def haveDataSourcesChanged(self, previousReportFile):
        returnValue = False
        with open(previousReportFile, 'r') as myfile:
            data = myfile.read()
            # parse file
            obj = json.loads(data)
            for result in obj['results']:
                dataFile = os.path.join(self.event.path, (result['dataSource'].strip('/')))
                previousHash = result.get('hash', "")
                ds = DataSource(dataFile)
                latestHash = ds.calculate_checksum()
                if (latestHash != previousHash):
                    returnValue = True
                    break
        return returnValue

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
        files = glob.glob(mapNumberDirectory + os.sep + mapNumber+'-v[0-9][0-9]_' + mapFileName + '.mxd')
        for file in files:
            versionNumber = int(os.path.basename(file).replace(mapNumber + '-v', '').replace(('_' + mapFileName+'.mxd'), ''))  # noqa
        versionNumber = versionNumber + 1
        if (versionNumber > 99):
            versionNumber = 1
        return versionNumber

    """
    Generates all file for export
    """
    # TODO: asmith 2020/03/03
    # This method is very long. Separate into multiple method. Some fo these will can be entirely
    # functional with no side-effects (eg wrangling parameters) whilst other will be highly proceedural
    # where the actual files writen to the filesystem.
    #
    # As a suggestion; it could be broken up something like this:
    #
    # export(self)
    #   """
    #   Accumulate parameters for export XML, then calls _do_export(....)
    #   """
    #
    #
    # _do_export(self, lots, of, specific, args)
    #   """
    #   Does the exporting of the PDF, Jpeg and thumbnail files.
    #   """
    #
    #
    # _process_query_column_name(...)
    #   """
    #   Accumulate parameters for export XML, then calls _do_export(....)
    #   """
    #
    # _zip_exported_files(....)
    #   """
    #   Accumulate parameters for export XML, then calls _do_export(....)
    #   """
    #
    # Other comments have been added thoughout the method.

    def export(self):
        # TODO: asmith 2020/03/03
        # 1) Separate the section "Accumulate parameters for export XML" into it's own method
        # 2) Please avoid hardcoding the naming convention for the output mxds.

        # Accumulate parameters for export XML
        exportParams = {}
        versionString = "v" + str(self.versionNumber).zfill(2)
        exportDirectory = os.path.join(self.crashMoveFolder.export_dir,
                                       self.mapNumber,
                                       versionString).replace('/', '\\')
        exportParams["exportDirectory"] = exportDirectory
        try:
            os.makedirs(exportDirectory)
        except OSError as exc:  # Python >2.5
            # Note 'errno.EEXIST' is not a typo. There should be two 'E's.
            # https://docs.python.org/2/library/errno.html#errno.EEXIST
            if exc.errno == errno.EEXIST and os.path.isdir(exportDirectory):
                pass
            else:
                raise

        # TODO: asmith 2020/03/03
        # End of method for the section "Accumulate parameters for export XML"

        # TODO: asmith 2020/03/03
        # Separate this section into a method named something like
        # _do_export(self, lots, of, specific, args)
        mxd = arcpy.mapping.MapDocument(self.mxdTemplate)

        coreFileName = os.path.splitext(os.path.basename(self.mxdTemplate))[0]
        exportParams["coreFileName"] = coreFileName
        productType = "mapsheet"
        exportParams["productType"] = productType

        pdfFileLocation = self.exportPdf(coreFileName, exportDirectory, mxd, exportParams)
        jpgFileLocation = self.exportJpeg(coreFileName, exportDirectory, mxd, exportParams)
        pngThumbNailFileLocation = self.exportPngThumbNail(coreFileName, exportDirectory, mxd, exportParams)

        # TODO: asmith 2020/03/03
        # End of method named something like
        # _do_export(self, lots, of, specific, args)

        #######################################################################################################
        # TODO: asmith 2020/03/03
        # Seperate this section into a method nameded something like
        # _process_query_column_name(...)
        if self.recipe.hasQueryColumnName:
            # TODO: asmith 2020/03/03
            #
            # 1) Please do not hard code layer file names! If a particular layer needs to have a special
            # meaning then this should be explict in the structure of the mapCookBook.json and/or
            # layerProperties.json files.
            #
            # 2) It looks like this is a workaround for the fact that this isn't an easy way to programatically
            # identify specific mapFrames without hardcoding the name of the mapFrame. Is there anywhere a
            # datamodel or class which encapsulates all of the elemnts which must be present within an mxd
            # in order for the automation tools to work? (eg:
            #     * title Text Element
            #     * description Text Element
            #     * datasources Text Element
            #     * map_map Map Frame
            #     * location_map Map Frame
            #     * legend Legend Element
            #     * etc.....
            #
            # It ought to be possible to have a method somewhere within the module like this:
            # ```
            #     is_suitable_for_automation(mxd)  # Returns Boolean
            # ```

            # Disable view of Affected Country
            locationMapLayerName = "locationmap-s0-py-affectedcountry"  # Hard-coded
            layerDefinition = self.layerDefinition.properties.get(locationMapLayerName)
            locationMapDataFrameName = layerDefinition.mapFrame
            locationMapDataFrame = arcpy.mapping.ListDataFrames(mxd, locationMapDataFrameName)[0]
            locationMapLyr = arcpy.mapping.ListLayers(mxd, locationMapLayerName, locationMapDataFrame)[0]
            locationMapDataFrame.extent = locationMapLyr.getExtent()
            locationMapLyr.visible = False

            # TODO: asmith 2020/03/03
            # Why is it necessary to have two loops through the layers in a recipe? eg
            # ```
            #     for layer in self.recipe.layers:
            # ```
            # There is this one here and a seperate one within the `cook` method of the MapChef class.
            # In the MapChef.cook() method the mxd is altered and then saved afterwards. It looks like
            # the mxd can be altered in ArcMapRunner.export() [specificly the zoom extent altered] but
            # then not saved afterwards. Is this intentional?
            for layer in self.recipe.layers:
                # TODO: asmith 2020/03/03
                #
                # 1) The snip-it `if (layer.get('columnName', None) is not None):` occurs in a couple of
                # locations (here and in MapRecipe.containsQueryColumn()). As a double negitive it is not
                # clear what is meant (I cannot find a `columnName` entry in the example mapCookbook.json).
                # Would it help to expand the object model for the `layer` class to encapsulate this?
                if (layer.get('columnName', None) is not None):
                    layerName = layer.get('name')
                    queryColumn = layer.get('columnName')
                    fieldNames = [queryColumn]
                    # For each layer and column name, export a regional map
                    layerDefinition = self.layerDefinition.properties.get(layerName)
                    df = arcpy.mapping.ListDataFrames(mxd, layerDefinition.mapFrame)[0]
                    lyr = arcpy.mapping.ListLayers(mxd, layerName, df)[0]

                    # TODO: asmith 2020/03/03
                    #
                    # Presumably `regions` here means admin1 boundaries or some other internal
                    # administrative devision?
                    regions = list()
                    with arcpy.da.UpdateCursor(lyr.dataSource, fieldNames) as cursor:
                        for row in cursor:
                            regions.append(row[0])

                    # TODO: asmith 2020/03/03
                    # This loop appear to simulate the behaviour of Data Driven Pages - is that right?
                    # Simulating Data Driven Pages to fine given the limitations in the arcpy API for
                    # controlling them.
                    #
                    # 1) If this is DDP, then I presume that this is triggered by the
                    # `if (layer.get('columnName', None) is not None):` line above? If so then please
                    # could we change the format of the mapCookBook.json so that this is more apparent
                    # to the reader of the mapCookBook.json file?
                    #
                    # 2) There appear to be a lot of hardcoded elements (eg the title and the map number)
                    # Is it possible to eliminate (or at least minimse these)?
                    for region in regions:
                        # TODO: asmith 2020/03/03
                        # Please do not hardcode mapFrame names. If a particular mapframe as a special
                        # meaning then this should be explicit in the structure of the mapCookBook.json
                        # and/or layerProperties.json files.
                        dataFrameName = "Main map"
                        df = arcpy.mapping.ListDataFrames(mxd, dataFrameName)[0]

                        # Select the next region
                        query = "\"" + queryColumn + "\" = \'" + region + "\'"
                        arcpy.SelectLayerByAttribute_management(lyr, "NEW_SELECTION", query)

                        # Get the extent of the selected area
                        df.extent = lyr.getSelectedExtent()

                        # Create a polygon using the bounding box
                        array = arcpy.Array()
                        array.add(df.extent.lowerLeft)
                        array.add(df.extent.lowerRight)
                        array.add(df.extent.upperRight)
                        array.add(df.extent.upperLeft)
                        # ensure the polygon is closed
                        array.add(df.extent.lowerLeft)
                        # Create the polygon object
                        polygon = arcpy.Polygon(array, df.extent.spatialReference)

                        array.removeAll()

                        # Export the extent to a shapefile
                        shapeFileName = "extent_" + slugify(unicode(region)).replace('-', '')
                        shpFile = shapeFileName + ".shp"

                        if arcpy.Exists(os.path.join(exportDirectory, shpFile)):
                            arcpy.Delete_management(os.path.join(exportDirectory, shpFile))
                        arcpy.CopyFeatures_management(polygon, os.path.join(exportDirectory, shpFile))

                        # For the 'extent' layer...
                        locationMapDataFrameName = "Location map"
                        locationMapDataFrame = arcpy.mapping.ListDataFrames(mxd, locationMapDataFrameName)[0]
                        extentLayerName = "locationmap-s0-py-extent"
                        extentLayer = arcpy.mapping.ListLayers(mxd, extentLayerName, locationMapDataFrame)[0]

                        # Update the layer
                        extentLayer.replaceDataSource(exportDirectory, 'SHAPEFILE_WORKSPACE', shapeFileName)
                        arcpy.RefreshActiveView()

                        # In Main map, zoom to the selected region
                        dataFrameName = "Main map"
                        df = arcpy.mapping.ListDataFrames(mxd, dataFrameName)[0]
                        arcpy.SelectLayerByAttribute_management(lyr, "NEW_SELECTION", query)
                        df.extent = lyr.getSelectedExtent()

                        for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
                            if elm.name == "title":
                                elm.text = self.recipe.category + " map of " + self.event.country_name +\
                                    '\n' +\
                                    "<CLR red = '255'>Sheet - " + region + "</CLR>"
                            if elm.name == "map_no":
                                elm.text = self.recipe.mapnumber + "_Sheet_" + region.replace(' ', '_')

                        # Clear selection, otherwise the selected feature is highlighted in the exported map
                        arcpy.SelectLayerByAttribute_management(lyr, "CLEAR_SELECTION")
                        # Export to PDF
                        pdfFileName = coreFileName + "-" + \
                            slugify(unicode(region)) + "-" + str(self.event.default_pdf_res_dpi) + "dpi.pdf"
                        pdfFileLocation = os.path.join(exportDirectory, pdfFileName)

                        arcpy.mapping.ExportToPDF(mxd, pdfFileLocation, resolution=int(self.event.default_pdf_res_dpi))
                        if arcpy.Exists(os.path.join(exportDirectory, shpFile)):
                            arcpy.Delete_management(os.path.join(exportDirectory, shpFile))

        # TODO: asmith 2020/03/03
        # End of method nameded something like
        # _process_query_column_name(...)
        xmlExporter = XmlExporter(self.event, self.chef)
        exportParams['versionNumber'] = self.versionNumber
        exportParams['mapNumber'] = self.mapNumber
        exportParams['productName'] = self.productName
        exportParams['versionNumber'] = self.versionNumber
        exportParams["xmin"] = self.minx
        exportParams["ymin"] = self.miny
        exportParams["xmax"] = self.maxx
        exportParams["ymax"] = self.maxy
        exportXmlFileLocation = xmlExporter.write(exportParams)

        # TODO: asmith 2020/03/03
        # Seperate this section into a method named something like
        # _zip_exported_files(....)

        # And now Zip
        zipFileName = coreFileName+".zip"
        zipFileLocation = os.path.join(exportDirectory, zipFileName)

        with ZipFile(zipFileLocation, 'w') as zipObj:
            zipObj.write(exportXmlFileLocation, os.path.basename(exportXmlFileLocation))
            zipObj.write(jpgFileLocation, os.path.basename(jpgFileLocation))
            zipObj.write(pngThumbNailFileLocation, os.path.basename(pngThumbNailFileLocation))

            # TODO: asmith 2020/03/03
            # Given we are explictly setting the pdfFileName for each page within the DDPs
            # it is possible return a list of all of the filenames for all of the PDFs. Please
            # can we use this list to include in the zip file. There are edge cases where just
            # adding all of the pdfs in a particular directory might not behave correctly (eg if
            # the previous run had crashed midway for some reason)
            for pdf in os.listdir(exportDirectory):
                if pdf.endswith(".pdf"):
                    zipObj.write(os.path.join(exportDirectory, pdf),
                                 os.path.basename(os.path.join(exportDirectory, pdf)))
        print("Export complete to " + exportDirectory)

        # TODO: asmith 2020/03/03
        # End of method named something like
        # _zip_exported_files(....)

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


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
        return False
    else:
        return arg


def is_valid_directory(parser, arg):
    if os.path.isdir(arg):
        return arg
    else:
        parser.error("The directory %s does not exist!" % arg)
        return False


def add_bool_arg(parser, name, default=False):
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--' + name, dest=name, action='store_true')
    group.add_argument('--no-' + name, dest=name, action='store_false')
    parser.set_defaults(**{name: default})


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
def main():
    parser = argparse.ArgumentParser(
        description='This component accepts a template MXD file, a list of the'
        'relevant datasets along with other information required to create an'
        'event specific instance of a map.',
    )
    parser.add_argument("-b", "--cookbook", dest="cookbookFile", required=False,
                        help="path to cookbook json file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-l", "--layerConfig", dest="layerConfig", required=False,
                        help="path to layer config json file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-t", "--template", dest="templateFile", required=False,
                        help="path to MXD file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-e", "--e", dest="eventConfigFile", required=True,
                        help="path the Event Config File", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=False,
                        help="path to layer directory", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-p", "--product", dest="productName", required=True,
                        help="Name of product")
    parser.add_argument("-o", "--orientation", dest="orientation", default=None, required=False,
                        help="landscape|portrait")

    add_bool_arg(parser, 'export')

    args = parser.parse_args()
    orientation = None
    if (args.orientation is not None):
        if args.orientation.lower() == "landscape":
            orientation = args.orientation
        else:
            orientation = "portrait"

    eventConfig = Event(args.eventConfigFile, orientation)
    runner = ArcMapRunner(args.templateFile,
                          eventConfig,
                          args.productName)

    productGenerated = runner.generate()
    if (productGenerated and args.export):
        runner.export()
    else:
        print("No product generated.  No changes since last execution.")


if __name__ == '__main__':
    main()
