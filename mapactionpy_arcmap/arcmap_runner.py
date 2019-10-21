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
from map_chef import MapChef
from map_cookbook import MapCookbook
import arcpy
from shutil import copyfile
from slugify import slugify


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
    gisFolder="GIS"
    arcGisVersion="arcgis_10_6"
    mappingDir="3_Mapping"
    templateDirectoryName="32_MXD_Templates"
    mapDirectoryName="33_MXD_Maps"

    # Need to get the theme from the recipe to get the path to the MXD
    cookbook = MapCookbook(cookbookFile)
    recipe = cookbook.products[productName]

    templateDirectoryPath = os.path.join(crashMoveFolder, gisFolder, mappingDir, templateDirectoryName, arcGisVersion)

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

    mapDirectoryPath = os.path.join(crashMoveFolder, gisFolder, mappingDir, mapDirectoryName)

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
    cookbookFile = args.cookbookFile
    layerPropertiesFile = args.layerConfig
    crashMoveFolder = args.crashMoveFolder
    layerDirectory = args.layerDirectory
    productName = args.productName
    countryName = args.countryName

    orientation = "landscape"

    mxdTemplate = None
    if args.templateFile:
        mxdTemplate = args.templateFile
    else:
        orientation = getOrientation(countryName)
        mxdTemplate = getTemplate(orientation, cookbookFile, crashMoveFolder, productName)
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
    parser.add_argument("-b", "--cookbook", dest="cookbookFile", required=True,
                        help="path to cookbook json file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-l", "--layerConfig", dest="layerConfig", required=True,
                        help="path to layer config json file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-t", "--template", dest="templateFile", required=False,
                        help="path to MXD file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-cmf", "--cmf", dest="crashMoveFolder", required=True,
                        help="path the Crash Move Folder", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=True,
                        help="path to layer directory", metavar="FILE",
                        type=lambda x: is_valid_directory(parser, x))
    parser.add_argument("-p", "--product", dest="productName", required=True,
                        help="Name of product")
    parser.add_argument("-c", "--country", dest="countryName", required=True,
                        help="Name of country")
    parser.add_argument("-v", "--version", dest="versionNumber", required=False,
                        help="Version number", default="1")
    parser.add_argument("-d", "--dryRun", dest="dryRun", required=False,
                        help="Dry Run - Execute, but don't produce map", default=False)
    args = parser.parse_args()
    main(args)
