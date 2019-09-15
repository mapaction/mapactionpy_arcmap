from map_recipe import MapRecipe
import json


class MapCookbook:
    """
    MapCookbook - Contains recipes for Map Products
    """

    def __init__(self, cookbookJsonFile):
        """
        Sets path for Map Cookbook json file.
        Creates empty list of of products.

        Arguments:
           cookbookJsonFile {str} -- path to Map Cookbook json file "mapCookbook.json"
        """
        # @TODO Add validation +
        # pass in LayerProperties object, and validate
        self.cookbookJsonFile = cookbookJsonFile
        self.products = {}
        self._parse()

    def _parse(self):
        """
        Reads product "recipes" from Map Cookbook json file
        """
        with open(self.cookbookJsonFile) as json_file:
            jsonContents = json.load(json_file)
            for recipe in jsonContents['recipes']:
                rec = MapRecipe(recipe['product'], recipe['layers'])
                self.products[recipe['product']] = rec

    def get_product_layers(self, productName):
        """
        Iterates through the cookbook and returns the layers for the required product

        Arguments:
           productName {str} -- name of product taken from the cookbook.
        Returns:
           layers for a given product
        """
        # @TODO use Set. get()...
        result = list()
        for product in self.products:
            if (product.product == productName):
                result = product.layers
                break
        return result

    def recipe(self, productName):
        result = None
        for product in self.products:
            if (product.product == productName):
                result = product
                break
        return result
