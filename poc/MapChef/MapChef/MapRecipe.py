from MapSpec import MapSpec
import json 

class MapRecipe:
    def __init__(self, recipeJsonFile):
        self.recipeJsonFile=recipeJsonFile
        self.title = ""
        self.layers = set();

    def parse(self):
        with open(self.recipeJsonFile) as json_file:  
            jsonContents = json.load(json_file)
            self.title=jsonContents['title']
            for layer in jsonContents['layers']:
                specification = MapSpec(layer['layerFile'])
                self.layers.add(specification)