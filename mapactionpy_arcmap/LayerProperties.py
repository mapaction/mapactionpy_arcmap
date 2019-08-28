import json
from LayerProperty import LayerProperty


class LayerProperties:
    def __init__(self, layerPropertiesJsonFile):
        self.layerPropertiesJsonFile = layerPropertiesJsonFile
        self.properties = set()

    def parse(self):
        with open(self.layerPropertiesJsonFile) as json_file:
            jsonContents = json.load(json_file)
            for layer in jsonContents['layerProperties']:
                property = LayerProperty(layer)
                # print (property.layerName)
                self.properties.add(property)

    def get(self, layerName):
        for property in self.properties:
            if (property.layerName == layerName):
                # Find shape file if it exists
                return property
        return None
