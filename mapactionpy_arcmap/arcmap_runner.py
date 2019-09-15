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
import os
from map_chef import MapChef
import arcpy


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


def main(args):
    args = parser.parse_args()
    cookbookFile = args.cookbookFile
    layerPropertiesFile = args.layerConfig
    mxdTemplate = args.templateFile
    crashMoveFolder = args.crashMoveFolder
    layerDirectory = args.layerDirectory
    productName = args.productName
    countryName = args.countryName

    mxd = arcpy.mapping.MapDocument(mxdTemplate)

    chef = MapChef(mxd, cookbookFile, layerPropertiesFile, crashMoveFolder, layerDirectory)
    chef.cook(productName, countryName)
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
    parser.add_argument("-t", "--template", dest="templateFile", required=True,
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
    args = parser.parse_args()
    main(args)
