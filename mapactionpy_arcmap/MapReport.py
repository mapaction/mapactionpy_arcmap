"""
MapReport - Report accumulated while the Map Product is generated.
Contains overall summary and a status for each layer.
"""

class MapReport:
    """
    Initialise to success for the product

    Arguments:
       productName {str} -- Map product name    
    """
    def __init__(self, productName):
        self.result = "Success"
        self.summary = ""
        self.productName = productName
        self.classification = "" # Not used
        self.results = list()

    """
    Appends the result for a given layer to the report 

    Arguments:
       mapResult {MapResult} -- result summary for a given layer    
    """
    def add(self, mapResult):
        self.results.append(mapResult)

    """
    Outputs report in json format

    Returns:
       str -- report in json format    
    """
    def dump(self):
        reportIter = 0
        failCount = 0
        resultJson = ""
        for report in self.results:
            if (reportIter > 0):
                resultJson = resultJson + ","
            resultJson = resultJson + report.toJSON()
            if not report.added:
                failCount = failCount + 1
            reportIter = reportIter + 1

        resultJson = resultJson + "]}"

        if (reportIter == 0):
            self.result = "Failure"
            self.summary = "No layers provided in recipe for '" + self.productName + "' product."
        else:
            if (failCount == 0):
                self.result = "Success"
                self.summary = "'" + self.productName + "' product generated successfully."
            else:
                self.result = "Warning"
                self.summary = str(failCount) + " / " + str(reportIter) + \
                    " layers could not be added to '" + self.productName + "' product."

        resultJson = "{\"result\":\"" + self.result + \
            "\", \"productName\":\"" + self.productName + \
            "\", \"summary\":\"" + self.summary + \
            "\", \"classification\":\"" + self.classification + \
            "\", \"results\":[" + resultJson

        return resultJson
