import os
import arcpy
for root, dirs, files in os.walk("D:/mapaction"):
    for file in files:
        if file.endswith(".mxd"):
            mxdfile = os.path.join(root, file)
            try:
                mapDoc = arcpy.mapping.MapDocument(mxdfile)
                if (mapDoc.isDDPEnabled):
                    print(mxdfile)
                    # print("YAY")
            except:
                pass
