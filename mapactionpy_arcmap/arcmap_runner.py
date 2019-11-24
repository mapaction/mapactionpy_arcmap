import decimal
import os
import errno
import glob
import requests
import pycountry
from map_chef import MapChef
from map_cookbook import MapCookbook
import arcpy
from shutil import copyfile
from slugify import slugify
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.event import Event
from PIL import Image


class ArcMapRunner:
    """
    ArcMapRunner - 
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
            self.mxdTemplate, self.mapNumber, self.versionNumber = self.get_template(self.orientation, self.cookbookFile, self.cmf, self.productName)
        mxd = arcpy.mapping.MapDocument(self.mxdTemplate)


        chef = MapChef(mxd, self.cookbookFile, self.layerPropertiesFile, self.crashMoveFolder, self.layerDirectory, self.versionNumber)
        chef.cook(self.productName, self.countryName)
        chef.alignLegend(self.orientation)
        reportJson = chef.report()
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
            versionNumber = int(os.path.basename(file).replace(mapNumber + '-v', '').replace(('_' + mapFileName+'.mxd'), '')) # noqa
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

            minx = D(boundingbox[2])
            miny = D(boundingbox[0])
            maxx = D(boundingbox[3])
            maxy = D(boundingbox[1])

            orientation = "portrait"

            # THIS DOESN'T WORK FOR FIJI/ NZ
            xdiff = abs(maxx-minx)
            ydiff = abs(maxy-miny)

            # print("http://bboxfinder.com/#<miny>,<minx>,<maxy>,<maxx>")
            # print("http://bboxfinder.com/#" + str(miny) + ","+ str(minx) + ","+ str(maxy) + ","+ str(maxx))

            if xdiff > ydiff:
                orientation = "landscape"
            return orientation
        else:
            raise Exception("Error: Could not derive country extent from " + url)

    def export(self):
        versionString="v" + str(self.versionNumber).zfill(2)
        exportDirectory=os.path.join(self.cmf.export_dir, self.mapNumber, versionString)

        try:
            os.makedirs(exportDirectory)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(exportDirectory):
                pass
            else:
                raise

        mxd = arcpy.mapping.MapDocument(self.mxdTemplate)

        coreFileName=os.path.splitext(os.path.basename(self.mxdTemplate))[0]

        #DDP
        if mxd.isDDPEnabled:
            dppFileLocation=os.path.join(exportDirectory, coreFileName)
            mxd.dataDrivenPages.exportToPDF(dppFileLocation, page_range_type='ALL',multiple_files='PDF_MULTIPLE_FILES_PAGE_NAME')

        # PDF
        pdfFileName = coreFileName+"-"+str(self.event.default_pdf_res_dpi) + ".pdf"
        pdfFileLocation=os.path.join(exportDirectory, pdfFileName)
        arcpy.mapping.ExportToPDF(mxd, pdfFileLocation)
        pdfFileSize = os.path.getsize(pdfFileLocation)
        #print(str(pdfFileSize))

        #JPEG
        jpgFileName = coreFileName+"-"+str(self.event.default_jpeg_res_dpi) + ".jpg"
        jpgFileLocation=os.path.join(exportDirectory, jpgFileName)
        arcpy.mapping.ExportToJPEG(mxd, jpgFileLocation)
        jpgFileSize = os.path.getsize(jpgFileLocation)
        #print(str(jpgFileSize))

        im = Image.open(jpgFileLocation)
        #print 'width: %d - height: %d' % im.size

        jpgWidth,jpgHeight = im.size

        thumbWidth=int(round(jpgWidth/10))
        thumbHeight=int(round(jpgHeight/10))
        #PNG Thumbnail
        df = arcpy.mapping.ListDataFrames(mxd, "Main map")[0]
        pngThumbNailFileName = coreFileName+"-thumbnail.png"
        pngThumbNailFileLocation=os.path.join(exportDirectory, pngThumbNailFileName)
        arcpy.mapping.ExportToPNG(mxd, pngThumbNailFileLocation, df, df_export_width=thumbWidth, df_export_height=thumbHeight)
        pngThumbNailFileSize = os.path.getsize(pngThumbNailFileLocation)
        #print(str(pngThumbNailFileSize))

