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
import json
import os
import urllib2
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

def getTemplate(orientation, cookbookFile, crashMoveFolder, productName):
    arcGisVersion=crashMoveFolder.arcgis_version

    # Need to get the theme from the recipe to get the path to the MXD
    cookbook = MapCookbook(cookbookFile)
    recipe = cookbook.products[productName]

    templateDirectoryPath = os.path.join(crashMoveFolder.path, crashMoveFolder.mxd_templates)

    if not(os.path.isdir(templateDirectoryPath)):
        print("Error: Could not find source template directory: " + templateDirectoryPath)
        print("Exiting.")
        sys.exit(1)

    if (recipe.category.lower() == "reference"):
        templateFileName=arcGisVersion + "_" + recipe.category + "_" + orientation + "_bottom.mxd"
    elif (recipe.category.lower() == "thematic"):
        templateFileName=arcGisVersion + "_" + recipe.category + "_" + orientation + ".mxd"
    else:
        print("Error: Could not get source MXD from: " + templateDirectoryPath)
        print("Exiting.")
        sys.exit(1)

    mapDirectoryPath = os.path.join(crashMoveFolder.path, crashMoveFolder.mxd_products)

    if not(os.path.isdir(mapDirectoryPath)):
        print("Error: Could not find target directory: " + mapDirectoryPath)
        print("Exiting.")
        sys.exit(1)

    srcTemplateFile = os.path.join(templateDirectoryPath, templateFileName)

    mapNumberDirectory=os.path.join(mapDirectoryPath, recipe.mapnumber)

    if not(os.path.isdir(mapNumberDirectory)):
        os.mkdir(mapNumberDirectory)

    mapFileName=recipe.mapnumber+"_"+ slugify(productName) + ".mxd"

    copiedFile= os.path.join(mapNumberDirectory, mapFileName)
    copyfile(srcTemplateFile, copiedFile)
    return (copiedFile)


def getOrientation(countryName):
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
    if extentsSet == True:
        D = decimal.Decimal

        minx = D(boundingbox[2])
        miny = D(boundingbox[0])
        maxx = D(boundingbox[3])
        maxy = D(boundingbox[1])

        orientation = "portrait"

        # THIS DOESN'T WORK FOR FIJI/ NZ
        xdiff=abs(maxx-minx)
        ydiff=abs(maxy-miny)

        #print("http://bboxfinder.com/#<miny>,<minx>,<maxy>,<maxx>")
        #print("http://bboxfinder.com/#" + str(miny) + ","+ str(minx) + ","+ str(maxy) + ","+ str(maxx))

        if xdiff > ydiff:
            orientation = "landscape"
        return orientation
    else:
        print("Error: Could not derive country extent from " + url)
        print("Exiting.")
        sys.exit(1)
           

def main(args):
    args = parser.parse_args()

    # Construct a Crash Move Folder object if the cmf_description.json exists
    crashMoveFolder = args.crashMoveFolder
    cmfFilePath= os.path.join(crashMoveFolder, "cmf_description.json")

    cmf=None
    event=None

    if os.path.exists(cmfFilePath):
        cmf = CrashMoveFolder(cmfFilePath)
        event=Event(cmf)

    productName = args.productName

    # If no country name supplied, need to find it from the event_description.json
    if args.countryName:
        countryName = args.countryName
    else:
        if event is not None: 
            country=pycountry.countries.get(alpha_3=event.affected_country_iso3.upper())
            countryName = country.name
        else:
            print("Error: Could not derive country from " + os.path.join(crashMoveFolder,cmf.event_description_file))
            print("Exiting.")
            sys.exit(1)

    if args.cookbookFile:
        cookbookFile = args.cookbookFile
    else:
        if cmf is not None: 
            cookbookFile=os.path.join(crashMoveFolder,cmf.map_definitions)
        else:
            print("Error: Could not derive cookbook file from " + crashMoveFolder)
            print("Exiting.")
            sys.exit(1)

    if args.layerConfig:
        layerPropertiesFile = args.layerConfig
    else:
        if cmf is not None: 
            layerPropertiesFile=os.path.join(crashMoveFolder,cmf.layer_properties)
        else:
            print("Error: Could not derive layer config file from " + crashMoveFolder)
            print("Exiting.")
            sys.exit(1)

    if args.layerDirectory:
        layerDirectory = args.layerDirectory
    else:
        if cmf is not None: 
            layerDirectory=os.path.join(crashMoveFolder,cmf.layer_rendering)
        else:
            print("Error: Could not derive layer rendering directory from " + crashMoveFolder)
            print("Exiting.")
            sys.exit(1)

    # Determine orientation
    orientation = "landscape"
    mxdTemplate = None
    if args.templateFile:
        mxdTemplate = args.templateFile
    else:
        orientation = getOrientation(countryName)
        mxdTemplate = getTemplate(orientation, cookbookFile, cmf, productName)
    mxd = arcpy.mapping.MapDocument(mxdTemplate)

    chef = MapChef(mxd, cookbookFile, layerPropertiesFile, crashMoveFolder, layerDirectory)
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
