# """
# Usage:
# C:\Python27\ArcGIS10.6\python.exe
# --recipeFile "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\recipe.json"
# --layerConfig "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\layerProperties.json"
# --cmf "D:\MapAction\2018-11-16-SierraCobre"
# --template "D:\MapAction\2018-11-16-SierraCobre\GIS\3_Mapping\33_MXD_Maps\MA001_scb_country_overview_DEV.mxd"
# --layerDirectory "D:\MapAction\2018-11-16-SierraCobre\GIS\3_Mapping\38_Initial_Maps_Layer_Files\Admin Map"
# --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador"
# --t "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\32_MXD_Templates\arcgis_10_2\
# MapAction\01 Reference mapping\arcgis_10_2_ma000_reference_landscape_bottom_DEV.mxd"
# --layerDirectory "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\38_Initial_Maps_Layer_Files\All"
# -p "Country Overview" --country "El Salvador"
# """

import argparse
import decimal
import os
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


def get_template(orientation, cookbookFile, crashMoveFolder, productName):
    arcGisVersion = crashMoveFolder.arcgis_version

    # Need to get the theme from the recipe to get the path to the MXD
    cookbook = MapCookbook(cookbookFile)
    recipe = cookbook.products[productName]

    if (recipe.category.lower() == "reference"):
        templateFileName = arcGisVersion + "_" + recipe.category + "_" + orientation + "_bottom.mxd"
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
    versionNumber = get_map_version_number(mapNumberDirectory, recipe.mapnumber, mapFileName)
    mapFileName = recipe.mapnumber + "-v" + str(versionNumber).zfill(2) + "_" + mapFileName + ".mxd"
    copiedFile = os.path.join(mapNumberDirectory, mapFileName)
    copyfile(srcTemplateFile, copiedFile)
    return copiedFile, versionNumber


def get_map_version_number(mapNumberDirectory, mapNumber, mapFileName):
    versionNumber = 0
    files = glob.glob(mapNumberDirectory + "/" + mapNumber+'-v[0-9][0-9]_' + mapFileName + '.mxd')
    for file in files:
        versionNumber = int(os.path.basename(file).replace(mapNumber + '-v', '').replace(('_' + mapFileName+'.mxd'), '')) # noqa
    versionNumber = versionNumber + 1
    if (versionNumber > 99):
        versionNumber = 1
    return versionNumber


def get_orientation(countryName):
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


def main(args):
    args = parser.parse_args()

    # Construct a Crash Move Folder object if the cmf_description.json exists
    crashMoveFolder = args.crashMoveFolder
    eventFilePath = os.path.join(crashMoveFolder, "event_description.json")

    cmf = None
    event = None

    if os.path.exists(eventFilePath):
        event = Event(eventFilePath)
        cmf = CrashMoveFolder(os.path.join(event.cmf_descriptor_path, "cmf_description.json"))

    productName = args.productName

    # If no country name supplied, need to find it from the event_description.json
    if args.countryName:
        countryName = args.countryName
    else:
        if event is not None:
            country = pycountry.countries.get(alpha_3=event.affected_country_iso3.upper())
            countryName = country.name
        else:
            raise Exception("Error: Could not derive country from " + eventFilePath)

    # The following checks are used if the CMF description is over-ridden by the command line parameters
    if args.cookbookFile:
        cookbookFile = args.cookbookFile
    else:
        if cmf is not None:
            cookbookFile = cmf.map_definitions
        else:
            raise Exception("Error: Could not derive cookbook file from " + crashMoveFolder)

    if args.layerConfig:
        layerPropertiesFile = args.layerConfig
    else:
        if cmf is not None:
            layerPropertiesFile = cmf.layer_properties
        else:
            raise Exception("Error: Could not derive layer config file from " + crashMoveFolder)

    if args.layerDirectory:
        layerDirectory = args.layerDirectory
    else:
        if cmf is not None:
            layerDirectory = cmf.layer_rendering
        else:
            raise Exception("Error: Could not derive layer rendering directory from " + crashMoveFolder)

    # Determine orientation
    orientation = "landscape"
    versionNumber = 1
    mxdTemplate = None
    if args.templateFile:
        mxdTemplate = args.templateFile
    else:
        orientation = get_orientation(countryName)
        mxdTemplate, versionNumber = get_template(orientation, cookbookFile, cmf, productName)
    mxd = arcpy.mapping.MapDocument(mxdTemplate)

    chef = MapChef(mxd, cookbookFile, layerPropertiesFile, crashMoveFolder, layerDirectory, versionNumber)
    chef.cook(productName, countryName)
    chef.alignLegend(orientation)
    reportJson = chef.report()
    print(reportJson)


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
    main(args)
