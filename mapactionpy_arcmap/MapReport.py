class MapReport:
    def __init__(self, productName):
        self.result = "Success"
        self.summary = ""
        self.productName = productName
        self.classification = ""
        self.results = list()

    def add(self, mapResult):
        self.results.append(mapResult)

    def dump(self):
        self.summary = self.productName + " generated successfully."
        resultJson = "{\"result\":\"" + self.result + "\", \"productName\":\"" + self.productName + "\", \"summary\":\"" + self.summary + "\", \"classification\":\"" + self.classification + "\", \"results\":["
        reportIter = 0
        for report in self.results:
            if (reportIter > 0):
                resultJson = resultJson + ","
            resultJson = resultJson + report.toJSON()    
            reportIter = reportIter + 1
        resultJson = resultJson + "]}"

        return resultJson
