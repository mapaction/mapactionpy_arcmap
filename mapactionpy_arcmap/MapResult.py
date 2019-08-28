import json
from datetime import datetime


class MapResult:
    def __init__(self, layerName):
        self.layerName = layerName
        self.dataSource = ""
        now = datetime.now()
        # dd/mm/YY H:M:S
        self.timeStamp = now.strftime("%d/%m/%Y %H:%M:%S")
        self.added = False
        self.message = ""

    def toJSON(self):
        result = {
            "layerName": self.layerName,
            "dataSource": self.dataSource,
            "dateStamp": self.timeStamp,
            "added": self.added,
            "message": self.message
        }
        return (json.dumps(result))
