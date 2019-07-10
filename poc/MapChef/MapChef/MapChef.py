import os
from os import listdir
from os.path import isfile, join
import arcpy
from arcpy import env
import re
from MapRecipe import MapRecipe
from LayerProperties import LayerProperties

class MapChef:
    def __init__(self, recipeJsonFile, layerPropertiesFile, mxdTemplate, crashMoveFolder, clean = False):
        self.mxd = None
        self.clean = clean
        self.recipeJsonFile = recipeJsonFile
        self.recipe = self.readRecipe()
        self.mxdTemplateFile = mxdTemplate
        self.root = crashMoveFolder
        self.layerPropertiesFile = layerPropertiesFile
        self.layerProperties = self.readLayerPropertiesFile()

    def readRecipe(self):
        recipe = MapRecipe(self.recipeJsonFile) 
        recipe.parse()
        return recipe

    def readLayerPropertiesFile(self):
        layerProperties = LayerProperties(self.layerPropertiesFile) 
        layerProperties.parse()
        return layerProperties

    def removeLayers(self):
        print ("Removing existing layers")
        for df in arcpy.mapping.ListDataFrames(self.mxd):
            for lyr in arcpy.mapping.ListLayers(self.mxd, "", df):
                arcpy.mapping.RemoveLayer(df, lyr)
        self.mxd.save()

    def cook(self):
        print ("cooking...")
        self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
        if (self.clean == True):
            self.removeLayers()
        for layer in self.recipe.layers:
            print ("Get shape file for layer \'" + layer.name + "\'")
            properties = self.layerProperties.get(layer.name)
            if (properties is not None):
                dataFilePath= self.root + "/GIS/2_Active_Data/" +  properties.sourceFolder
                if (os.path.isdir(dataFilePath)):
                    if ("/" not in properties.regExp):
                        onlyfiles = [f for f in listdir(dataFilePath) if isfile(join(dataFilePath, f))]
                        for fileName in onlyfiles:
                            if re.match(properties.regExp, fileName):
                                #print ("File name: " + fileName)
                                self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
                                self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                dataFile = dataFilePath + "/" + fileName
                                self.addLayer(self.dataFrame, dataFile, (layer.name + ".lyr"), properties.definitionQuery, properties.display)    
                    else:
                        parts = properties.regExp.split("/")
                        for root, dirs, files in os.walk(dataFilePath):
                            for gdb in dirs:
                                if re.match(parts[0], gdb):
                                    rasterFile = (dataFilePath + "/" + gdb).replace("/", os.sep)
                                    arcpy.env.workspace = rasterFile
                                    rasters = arcpy.ListRasters("*")
                                    for raster in rasters:
                                        if re.match(parts[1], raster):
                                            print(raster)
                                            rasterLayer = (rasterFile + "\\" + raster)
                                            self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
                                            self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]
                                            self.addRasterToLayer(self.dataFrame, rasterLayer, (layer.name + ".lyr"))    

    def addLayer(self, dataFrame, dataFile, layerName, definitionQuery, display):
        print ("Adding \'" + dataFile + "\' to layer \'" + layerName + "\'")
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(dataFile, layerName)
        layer = arcpy.mapping.Layer(layerName)
        if (definitionQuery):
            # https://gis.stackexchange.com/questions/90736/setting-definition-query-on-arcpy-layer-from-shapefile
            layer.definitionQuery = definitionQuery
            arcpy.SelectLayerByAttribute_management(layerName, "SUBSET_SELECTION", definitionQuery)
        if (display.upper() == "YES"):
            layer.visible = True
        else:
            layer.visible = False

        arcpy.mapping.AddLayer(dataFrame, layer, "BOTTOM")
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
        self.mxd.save()

    def addRasterToLayer(self, dataFrame, dataFile, layerName):
        print ("Adding \'" + dataFile + "\' to layer \'" + layerName + "\'")
        # Make a layer from the feature class
        # https://pro.arcgis.com/en/pro-app/arcpy/classes/result.htm
        result = arcpy.MakeRasterLayer_management(dataFile, layerName)
        msgIndex=0
        while (msgIndex < result.messageCount):
            print (result.getMessage(msgIndex))
            msgIndex = msgIndex+1       
        layer = result.getOutput(0)
        layer.visible = True
        arcpy.mapping.AddLayer(dataFrame, layer, "BOTTOM")
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        self.mxd.save()
