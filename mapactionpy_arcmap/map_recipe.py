class MapRecipe:
    """
    MapRecipe - Ordered list of layers for each Map Product
    """

    def __init__(self, row):
        self.mapnumber = row["mapnumber"]
        self.category = row["category"]
        self.export = row["export"]
        self.product = row["product"]
        self.layers = row["layers"]
        self.summary = row["summary"]
