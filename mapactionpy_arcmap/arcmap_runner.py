import arcpy
import argparse
import decimal
import errno
import glob
import os
import requests
import pycountry
from shutil import copyfile
from slugify import slugify
from PIL import Image
from zipfile import ZipFile
from resizeimage import resizeimage
from map_chef import MapChef
from map_cookbook import MapCookbook
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.event import Event
from map_doc import MapDoc
from map_data import MapData


class ArcMapRunner:
    """
    ArcMapRunner - Executes the ArcMap automation methods
    """

    def __init__(self,
                 cookbookFile,
                 layerConfig,
                 templateFile,
                 crashMoveFolder,
                 layerDirectory,
                 productName,
                 countryName):
        self.cookbookFile = cookbookFile
        self.layerPropertiesFile = layerConfig
        self.mxdTemplate = templateFile
        self.crashMoveFolder = crashMoveFolder
        self.layerDirectory = layerDirectory
        self.productName = productName
        self.countryName = countryName
        self.eventFilePath = os.path.join(crashMoveFolder, "event_description.json")
        self.cmf = None
        self.event = None

        # Determine orientation
        self.orientation = "landscape"
        self.versionNumber = 1
        self.mxdTemplate = None
        self.mapNumber = "MA001"
        self.exportMap = False
        self.minx = 0
        self.miny = 0
        self.maxx = 0
        self.maxy = 0
        self.chef = None

        if os.path.exists(self.eventFilePath):
            self.event = Event(self.eventFilePath)
            self.cmf = CrashMoveFolder(os.path.join(self.event.cmf_descriptor_path, "cmf_description.json"))

        # If no country name supplied, need to find it from the event_description.json
        if self.countryName is None:
            if self.event is not None:
                country = pycountry.countries.get(alpha_3=self.event.affected_country_iso3.upper())
                self.countryName = country.name
            else:
                raise Exception("Error: Could not derive country from " + self.eventFilePath)

        # The following checks are used if the CMF description is over-ridden by the command line parameters
        if self.cookbookFile is None:
            if self.cmf is not None:
                self.cookbookFile = self.cmf.map_definitions
            else:
                raise Exception("Error: Could not derive cookbook file from " + self.crashMoveFolder)

        if self.layerPropertiesFile is None:
            if self.cmf is not None:
                self.layerPropertiesFile = self.cmf.layer_properties
            else:
                raise Exception("Error: Could not derive layer config file from " + self.crashMoveFolder)

        if self.layerDirectory is None:
            if self.cmf is not None:
                self.layerDirectory = self.cmf.layer_rendering
            else:
                raise Exception("Error: Could not derive layer rendering directory from " + self.crashMoveFolder)

    def generate(self):
        # Construct a Crash Move Folder object if the cmf_description.json exists

        if self.mxdTemplate is None:
            self.orientation = self.get_orientation(self.countryName)
            self.mxdTemplate, self.mapNumber, self.versionNumber = self.get_template(
                self.orientation, self.cookbookFile, self.cmf, self.productName)
        mxd = arcpy.mapping.MapDocument(self.mxdTemplate)

        self.chef = MapChef(mxd, self.cookbookFile, self.layerPropertiesFile,
                            self.crashMoveFolder, self.layerDirectory, self.versionNumber)
        self.chef.cook(self.productName, self.countryName)
        self.chef.alignLegend(self.orientation)
        reportJson = self.chef.report()
        print(reportJson)
        if self.exportMap:
            self.export()

    def get_template(self, orientation, cookbookFile, crashMoveFolder, productName):
        arcGisVersion = crashMoveFolder.arcgis_version

        # Need to get the theme from the recipe to get the path to the MXD
        cookbook = MapCookbook(cookbookFile)
        recipe = cookbook.products[productName]

        self.exportMap = recipe.export
        if (recipe.category.lower() == "reference"):
            templateFileName = arcGisVersion + "_" + recipe.category + "_" + orientation + "_bottom.mxd"
        elif (recipe.category.lower() == "ddp reference"):
            templateFileName = arcGisVersion + "_ddp_reference_" + orientation + ".mxd"
        elif (recipe.category.lower() == "thematic"):
            templateFileName = arcGisVersion + "_" + recipe.category + "_" + orientation + ".mxd"
        else:
            raise Exception("Error: Could not get source MXD from: " + crashMoveFolder.mxd_templates)

        srcTemplateFile = os.path.join(crashMoveFolder.mxd_templates, templateFileName)

        mapNumberDirectory = os.path.join(crashMoveFolder.mxd_products, recipe.mapnumber)

        if not(os.path.isdir(mapNumberDirectory)):
            os.mkdir(mapNumberDirectory)

        # Construct MXD name
        mapFileName = slugify(productName)
        versionNumber = self.get_map_version_number(mapNumberDirectory, recipe.mapnumber, mapFileName)
        mapFileName = recipe.mapnumber + "-v" + str(versionNumber).zfill(2) + "_" + mapFileName + ".mxd"
        copiedFile = os.path.join(mapNumberDirectory, mapFileName)
        copyfile(srcTemplateFile, copiedFile)
        return copiedFile, recipe.mapnumber, versionNumber

    def get_map_version_number(self, mapNumberDirectory, mapNumber, mapFileName):
        versionNumber = 0
        files = glob.glob(mapNumberDirectory + "/" + mapNumber+'-v[0-9][0-9]_' + mapFileName + '.mxd')
        for file in files:
            versionNumber = int(os.path.basename(file).replace(mapNumber + '-v', '').replace(('_' + mapFileName+'.mxd'), ''))  # noqa
        versionNumber = versionNumber + 1
        if (versionNumber > 99):
            versionNumber = 1
        return versionNumber

    def get_orientation(self, countryName):
        url = "https://nominatim.openstreetmap.org/search?country=" + countryName.replace(" ", "+") + "&format=json"
        resp = requests.get(url=url)

        jsonObject = resp.json()

        extentsSet = False
        boundingbox = [0, 0, 0, 0]
        for country in jsonObject:
            if country['class'] == "boundary" and country['type'] == "administrative":
                boundingbox = country['boundingbox']
                extentsSet = True
                break
        if extentsSet:
            D = decimal.Decimal

            self.minx = D(boundingbox[2])
            self.miny = D(boundingbox[0])
            self.maxx = D(boundingbox[3])
            self.maxy = D(boundingbox[1])

            orientation = "portrait"

            # THIS DOESN'T WORK FOR FIJI/ NZ
            xdiff = abs(self.maxx-self.minx)
            ydiff = abs(self.maxy-self.miny)

            # print("http://bboxfinder.com/#<miny>,<minx>,<maxy>,<maxx>")
            # print("http://bboxfinder.com/#" + str(miny) + ","+ str(minx) + ","+ str(maxy) + ","+ str(maxx))

            if xdiff > ydiff:
                orientation = "landscape"
            return orientation
        else:
            raise Exception("Error: Could not derive country extent from " + url)

    """
    Generates all file for export
    """

    def export(self):
        # Accumulate parameters for export XML
        exportParams = {}
        versionString = "v" + str(self.versionNumber).zfill(2)
        exportDirectory = os.path.join(self.cmf.export_dir, self.mapNumber, versionString)
        exportParams["exportDirectory"] = exportDirectory
        try:
            os.makedirs(exportDirectory)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(exportDirectory):
                pass
            else:
                raise

        mxd = arcpy.mapping.MapDocument(self.mxdTemplate)

        coreFileName = os.path.splitext(os.path.basename(self.mxdTemplate))[0]
        exportParams["coreFileName"] = coreFileName
        productType = "mapsheet"

        # DDP
        if mxd.isDDPEnabled:
            productType = "atlas"
            dppFileLocation = os.path.join(exportDirectory, coreFileName)
            mxd.dataDrivenPages.exportToPDF(dppFileLocation,
                                            page_range_type='ALL',
                                            multiple_files='PDF_MULTIPLE_FILES_PAGE_NAME',
                                            resolution=int(self.event.default_pdf_res_dpi))

        exportParams["productType"] = productType
        # PDF
        pdfFileName = coreFileName+"-"+str(self.event.default_pdf_res_dpi) + "dpi.pdf"
        pdfFileLocation = os.path.join(exportDirectory, pdfFileName)
        exportParams["pdfFileName"] = pdfFileName
        arcpy.mapping.ExportToPDF(mxd, pdfFileLocation, resolution=int(self.event.default_pdf_res_dpi))
        pdfFileSize = os.path.getsize(pdfFileLocation)
        exportParams["pdfFileSize"] = pdfFileSize

        # JPEG
        jpgFileName = coreFileName+"-"+str(self.event.default_jpeg_res_dpi) + "dpi.jpg"
        jpgFileLocation = os.path.join(exportDirectory, jpgFileName)
        exportParams["jpgFileName"] = jpgFileName
        arcpy.mapping.ExportToJPEG(mxd, jpgFileLocation)
        jpgFileSize = os.path.getsize(jpgFileLocation)
        exportParams["jpgFileSize"] = jpgFileSize

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

        # Create Export XML
        exportXmlFileLocation = self.generateXml(exportParams)

        # And now Zip
        zipFileName = coreFileName+".zip"
        zipFileLocation = os.path.join(exportDirectory, zipFileName)

        with ZipFile(zipFileLocation, 'w') as zipObj:
            zipObj.write(exportXmlFileLocation, os.path.basename(exportXmlFileLocation))
            zipObj.write(jpgFileLocation, os.path.basename(jpgFileLocation))
            zipObj.write(pngThumbNailFileLocation, os.path.basename(pngThumbNailFileLocation))

            for pdf in os.listdir(exportDirectory):
                if pdf.endswith(".pdf"):
                    zipObj.write(os.path.join(exportDirectory, pdf),
                                 os.path.basename(os.path.join(exportDirectory, pdf)))
        print ("Export complete to " + exportDirectory)

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

    def generateXml(self, params):
        # Set up dictionary for all the values required for the export XML file
        row = {}
        row["versionNumber"] = self.versionNumber
        row["mapNumber"] = self.mapNumber
        row["operationID"] = self.event.operation_id
        row["sourceorg"] = self.event.default_source_organisation
        row["pdffilename"] = params["pdfFileName"]
        row["jpgfilename"] = params["jpgFileName"]
        row["pdffilesize"] = params["pdfFileSize"]
        row["jpgfilesize"] = params["jpgFileSize"]
        row["glideno"] = self.event.glide_number
        row["title"] = self.productName
        row["countries"] = self.countryName
        row["xmin"] = self.minx
        row["ymin"] = self.miny
        row["xmax"] = self.maxx
        row["ymax"] = self.maxy
        row["ref"] = params["coreFileName"]
        row["mxdfilename"] = params["coreFileName"]
        row["paperxmax"] = ""
        row["paperxmin"] = ""
        row["paperymax"] = ""
        row["paperymin"] = ""
        row["pdfresolutiondpi"] = self.event.default_pdf_res_dpi
        row["jpgresolutiondpi"] = self.event.default_jpeg_res_dpi
        if (self.versionNumber == 1):
            row["status"] = "New"
        else:
            row["status"] = "Update"

        row["language-iso2"] = self.event.language_iso2
        language = pycountry.languages.get(alpha_2=self.event.language_iso2)
        row["language"] = language.name
        row["createdate"] = self.chef.createDate
        row["createtime"] = self.chef.createTime
        row["imagerydate"] = ""
        row["summary"] = self.chef.summary
        row["product-type"] = params["productType"]
        row["papersize"] = "A3"
        row["scale"] = self.chef.scale()
        row["access"] = "MapAction"  # Until we work out how to get the values for this
        row["accessnotes"] = ""
        row["location"] = ""
        row["qclevel"] = "Local"
        row["qcname"] = ""
        row["themes"] = {}
        row["proj"] = ""
        row["datum"] = self.chef.spatialReference()
        row["datasource"] = ""
        row["kmlresolutiondpi"] = ""

        exportData = MapData(row)
        md = MapDoc(exportData)

        exportXmlFileName = params["coreFileName"]+".xml"
        exportXmlFileLocation = os.path.join(params["exportDirectory"], exportXmlFileName)

        f = open(exportXmlFileLocation, "w")
        f.write(md.xml())
        f.close()

        return exportXmlFileLocation


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


if __name__ == '__main__':
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
    parser.add_argument("-cmf", "--cmf", dest="crashMoveFolder", required=True,
                        help="path the Crash Move Folder", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=False,
                        help="path to layer directory", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-p", "--product", dest="productName", required=True,
                        help="Name of product")
    parser.add_argument("-c", "--country", dest="countryName", required=False,
                        help="Name of country")
    args = parser.parse_args()

    runner = ArcMapRunner(args.cookbookFile,
                          args.layerConfig,
                          args.templateFile,
                          args.crashMoveFolder,
                          args.layerDirectory,
                          args.productName,
                          args.countryName)
    runner.generate()
