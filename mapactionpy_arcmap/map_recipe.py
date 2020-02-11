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
        self.hasQueryColumnName = self.containsQueryColumn()

    def containsQueryColumn(self):
        hasQueryColumnName = False
        for layer in self.layers:
            if (layer.get('columnName', None) is not None):
                hasQueryColumnName = True
                break
        return hasQueryColumnName
