'''

Usage:
        C:\Python27\ArcGIS10.6\python.exe 
            --recipeFile "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\recipe.json" 
            --layerConfig "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\layerProperties.json" 
            --cmf "D:\MapAction\2018-11-16-SierraCobre" 
            --template "D:\MapAction\2018-11-16-SierraCobre\GIS\3_Mapping\33_MXD_Maps\MA001_scb_country_overview_DEV.mxd" 
            --layerDirectory "D:\MapAction\2018-11-16-SierraCobre\GIS\3_Mapping\38_Initial_Maps_Layer_Files\Admin Map"
'''

import argparse
import os
from os.path import isfile, join
from MapChef import MapChef

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--cookbook", dest="cookbookFile", required=True, help="path to cookbook json file", metavar="FILE", type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-l", "--layerConfig", dest="layerConfig", required=True, help="path to layer config json file", metavar="FILE", type=lambda x: is_valid_file(parser, x)) 
    parser.add_argument("-t", "--template", dest="templateFile", required=True, help="path to MXD file", metavar="FILE", type=lambda x: is_valid_file(parser, x)) 
    parser.add_argument("-c", "--cmf", dest="crashMoveFolder", required=True, help="path the Crash Move Folder", metavar="FILE", type=lambda x: is_valid_directory(parser, x)) 
    parser.add_argument("-ld", "--layerDirectory", dest="layerDirectory", required=True, help="path to layer directory", metavar="FILE", type=lambda x: is_valid_directory(parser, x)) 
    parser.add_argument("-p", "--product", dest="productName", required=True, help="Name of product") 
 
    args = parser.parse_args()
    cookbookFile=args.cookbookFile
    layerPropertiesFile=args.layerConfig    
    mxdTemplate=args.templateFile    
    crashMoveFolder=args.crashMoveFolder
    layerDirectory=args.layerDirectory
    productName=args.productName

    mxd = arcpy.mapping.MapDocument(mxdTemplate)

    chef = MapChef(mxd, cookbookFile, layerPropertiesFile, crashMoveFolder, layerDirectory)
    
    chef.cook(productName)

if __name__ == '__main__':
    main()
