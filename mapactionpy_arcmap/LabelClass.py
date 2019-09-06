"""
    Class to enable selection of properties to support labels in a Layer 
"""
class LabelClass:
    def __init__(self, row):
        self.className = row["className"]
        self.expression = row["expression"]
        self.SQLQuery = row["SQLQuery"]
