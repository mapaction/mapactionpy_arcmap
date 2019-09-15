from datetime import datetime


class MapResult:
    """
    MapResult - result for adding a layer to the Map Product
    """

    def __init__(self, layerName):
        """
        Constructor, initialises new Map Result for the layer

        Arguments:
           layerName {str} -- name of the map layer being added
        """
        self.layerName = layerName
        self.dataSource = ""
        now = datetime.now()
        # dd/mm/YY H:M:S
        self.dateStamp = now.strftime("%d/%m/%Y %H:%M:%S")
        self.added = False
        self.message = ""
