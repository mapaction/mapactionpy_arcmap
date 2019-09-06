import json
from MapLayer import MapLayer

class LayerProperties:
    def __init__(self, layerPropertiesJsonFile):
        self.layerPropertiesJsonFile = layerPropertiesJsonFile
        self.properties = set()
    """
    Iterates through the cookbook and returns the layers for the required product

    Arguments:
       productName {str} -- name of product taken from the cookbook.
    Returns:
       layers for a given product
    """

    def parse(self):
        with open(self.layerPropertiesJsonFile) as json_file:
            jsonContents = json.load(json_file)
            for layer in jsonContents['layerProperties']:
                mapLayer = MapLayer(layer)
                # print (property.layerName)
                self.properties.add(mapLayer)

    """
    Iterates through the cookbook and returns the layers for the required product

    Arguments:
       productName {str} -- name of product taken from the cookbook.
    Returns:
       layers for a given product
    """
    def get(self, layerName):
        for property in self.properties:
            if (property.layerName == layerName):
                # Find shape file if it exists
                return property
        return None
