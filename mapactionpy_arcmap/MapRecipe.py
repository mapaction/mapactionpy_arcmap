"""
MapRecipe - Ordered list of layers for each Map Product 
"""

class MapRecipe:
    def __init__(self, product, layers):
        self.product = product
        self.layers = layers
