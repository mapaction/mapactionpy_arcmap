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
        #self.mxd = arcpy.mapping.MapDocument(self.recipe.root + "/GIS/3_Mapping/33_MXD_Maps/" + self.recipe.template)
        if (self.clean == True):
            self.removeLayers()
        for layer in self.recipe.layers:
            print ("Get shape file for layer \'" + layer.name + "\'")
            properties = self.layerProperties.get(layer.name)
            if (properties is not None):
                dataFilePath= self.root + "/GIS/2_Active_Data/" +  properties.sourceFolder
                if (os.path.isdir(dataFilePath)):
                    onlyfiles = [f for f in listdir(dataFilePath) if isfile(join(dataFilePath, f))]
                    for fileName in onlyfiles:
                        if re.match(properties.regExp, fileName):
                            #print ("File name: " + fileName)
                            self.mxd = arcpy.mapping.MapDocument(self.mxdTemplateFile)
                            self.dataFrame = arcpy.mapping.ListDataFrames(self.mxd, properties.mapFrame)[0]

                            dataFile = dataFilePath + "/" + fileName
                            self.addLayer(self.dataFrame, dataFile, (layer.name + ".lyr"))    

    def addLayer(self, dataFrame, dataFile, layerName):
        print ("Adding \'" + dataFile + "\' to layer \'" + layerName + "\'")
        # Make a layer from the feature class
        arcpy.MakeFeatureLayer_management(dataFile, layerName)
        layer = arcpy.mapping.Layer(layerName)
        layer.visible = True
        arcpy.mapping.AddLayer(dataFrame, layer, "BOTTOM")
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        self.mxd.save()