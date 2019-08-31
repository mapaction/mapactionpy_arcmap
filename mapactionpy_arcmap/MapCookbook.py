from MapRecipe import MapRecipe
import json


class MapCookbook:
    def __init__(self, cookbookJsonFile):
        self.cookbookJsonFile = cookbookJsonFile
        self.products = list()

    def parse(self):
        with open(self.cookbookJsonFile) as json_file:
            jsonContents = json.load(json_file)
            for recipe in jsonContents['recipes']:
                rec = MapRecipe(recipe['product'], recipe['layers'])
                self.products.append(rec)

    def layers(self, productName):
        result = list()
        for product in self.products:
            if (product.product == productName):
                result = product.layers
                break
        return result

    def get_products(self):
        return self.products
