"""
MapResult - result for adding a layer to the Map Product
"""

import json
from datetime import datetime

class MapResult:
    """
    Constructor, initialises new Map Result for the layer

    Arguments:
       layerName {str} -- name of the map layer being added
    """
    def __init__(self, layerName):
        self.layerName = layerName
        self.dataSource = ""
        now = datetime.now()
        # dd/mm/YY H:M:S
        self.timeStamp = now.strftime("%d/%m/%Y %H:%M:%S")
        self.added = False
        self.message = ""

    """
    Returns:
       Json formatted string
    """

    def toJSON(self):
        result = {
            "layerName": self.layerName,
            "dataSource": self.dataSource,
            "dateStamp": self.timeStamp,
            "added": self.added,
            "message": self.message
        }
        return (json.dumps(result))
