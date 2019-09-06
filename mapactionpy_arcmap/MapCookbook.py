"""
MapCookbook - Contains recipes for Map Products 
"""

from MapRecipe import MapRecipe
import json

class MapCookbook:
    """
    Sets path for Map Cookbook json file.
    Creates empty list of of products.

    Arguments:
       cookbookJsonFile {str} -- path to Map Cookbook json file "mapCookbook.json"
    """
    def __init__(self, cookbookJsonFile):
        self.cookbookJsonFile = cookbookJsonFile
        self.products = list()

    """
    Reads product "recipes" from Map Cookbook json file
    """
    def parse(self):
        with open(self.cookbookJsonFile) as json_file:
            jsonContents = json.load(json_file)
            for recipe in jsonContents['recipes']:
                rec = MapRecipe(recipe['product'], recipe['layers'])
                self.products.append(rec)

    """
    Iterates through the cookbook and returns the layers for the required product

    Arguments:
       productName {str} -- name of product taken from the cookbook.
    Returns:
       layers for a given product
    """
    def layers(self, productName):
        result = list()
        for product in self.products:
            if (product.product == productName):
                result = product.layers
                break
        return result
