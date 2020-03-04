# TODO: asmith 2020/03/04
#
# 1) I'm afraid I do not understand the purpose/value of this class. The only place I can see it is
# used is in ArcMapRunner.export(). The export() method builds up a dict containing the various bits
# of metadata which gets past to the constructor to MapData and then the MapData object gets past to
# the MapDoc object. Is there a reason why the ArcMapRunner.export() method couldn't pass its dict
# directly to the MapDoc constructor (possibly as kwargs)?
#
# 2) If this file is to be kept then it should be moved to the mapactionpy_controller module.


class MapData:
    def __init__(self, row):
        # Constructor.  Creates an instance of MapData for the Export XML

        self.versionNumber = row["versionNumber"]
        self.mapNumber = row["mapNumber"]
        self.operationID = row["operationID"]
        self.sourceorg = row["sourceorg"]
        self.glideno = row["glideno"]

        self.jpgfilename = row["jpgfilename"]
        self.pdffilename = row["pdffilename"]
        self.jpgfilesize = row["jpgfilesize"]
        self.pdffilesize = row["pdffilesize"]

        self.title = row["title"]
        self.ref = row["ref"]
        self.language = row["language"]
        self.countries = row["countries"]
        self.createdate = row["createdate"]
        self.createtime = row["createtime"]
        self.status = row["status"]
        self.xmin = row["xmin"]
        self.ymin = row["ymin"]
        self.xmax = row["xmax"]
        self.ymax = row["ymax"]
        self.proj = row["proj"]
        self.datum = row["datum"]
        self.qclevel = row["qclevel"]
        self.qcname = row["qcname"]
        self.access = row["access"]
        self.summary = row["summary"]
        self.imagerydate = row["imagerydate"]
        self.datasource = row["datasource"]
        self.location = row["location"]
        self.themes = row["themes"]
        self.scale = row["scale"]
        self.papersize = row["papersize"]
        self.jpgresolutiondpi = row["jpgresolutiondpi"]
        self.pdfresolutiondpi = row["pdfresolutiondpi"]
        self.kmlresolutiondpi = row["kmlresolutiondpi"]
        self.mxdfilename = row["mxdfilename"]
        self.paperxmax = row["paperxmax"]
        self.paperxmin = row["paperxmin"]
        self.paperymax = row["paperymax"]
        self.paperymin = row["paperymin"]
        self.accessnotes = row["accessnotes"]
        self.product_type = row["product-type"]  # Name contains hyphen "-"
        self.language_iso2 = row["language-iso2"]  # Name contains hyphen "-"
