# TODO: asmith 2020/03/04
# There are no arcpy dependancies in this class, which would imply that it could be moved to the
# mapactionpy_controller module. However is it so closely aligned with the data model for ArcMap
# that it could be meaningfully shared with a QGIS implenmentation?
class LabelClass:
    """
    Enables selection of properties to support labels in a Layer
    """

    def __init__(self, row):
        self.className = row["className"]
        self.expression = row["expression"]
        self.SQLQuery = row["SQLQuery"]
        self.showClassLabels = row["showClassLabels"]
