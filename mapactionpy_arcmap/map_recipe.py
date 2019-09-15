class MapRecipe:
    """
    MapRecipe - Ordered list of layers for each Map Product
    """

    def __init__(self, product, layers):
        self.product = product
        self.layers = layers
