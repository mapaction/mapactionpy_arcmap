from LabelClass import LabelClass

class MapLayer:
    def __init__(self, row):
       """Constructor.  Creates an instance of layer properties 

       Arguments:
           row {dict} -- From the layerProperties.json file
       """
       self.mapFrame = row["MapFrame"]
       self.layerGroup = row["LayerGroup"]
       self.layerName = row["LayerName"]
       self.sourceFolder = row["SourceFolder"]
       self.regExp = row["RegExp"]
       self.definitionQuery = row["DefinitionQuery"]
       self.display = row["Display"]
       self.labelClasses = list()
       for labelClass in row["LabelClasses"]:
           self.labelClasses.append(LabelClass(labelClass))
