# MapChef

Adds geospatial data to an ArcMap MXD file as separate layers based on a supplied recipe configuration file.

### Prerequisites

Python and ArcPy

```
C:\Python27\ArcGIS10.6\python.exe
```

## Layers


### Recipe File

The recipe file is a collection of layers.  The intention is that each Map would have it's own recipe json file.
Layers are added in the index order from the recipe file.
The following excerpt is taken from a [recipe.json](Config/recipe.json) file:
```
...
    {
      "index": "8",
      "layerFile": {
        "name": "Physical - Sea - py",
        "level": "",
        "detail": "Sea"
      },
      "source": "National, COD (HDX) or GADM",
      "include": []
    },
...
```

At present, the only fields which are actually used are:

#|Field | Description|
-|------------ | --------------------------------------------------------------|
1|```index``` | Layer index|
2|```layerFile.Name``` | Layer Name  - Must correlate with a row from the Layer Config file|


### layerConfig File

The Layer Config file ([layerProperties.json](Config/layerProperties.json)) is a static file which defines how to add a particular layer.

```
    {
      "MapFrame": "Main Map",
      "LayerGroup": "Elevation",
      "LayerName": "Physical - Sea - py",
      "SourceFolder": "220_phys",
      "RegExp": "^[a-z]{3}_phys_ocn_py_(.*?).shp$",
      "DefinitionQuery": "None",
      "Display": "Yes"
    },
```

:warning: Not all the Regular expressions in the [layerProperties.json](Config/layerProperties.json file "work".  These will be updated in due course.__
:warning: Only shapefiles are handled in this version.
   
    #|Field | Description|
-|------------ | -------------|
1|```MapFrame``` | Name of the Map Frame that the layer is to be added to|
2|```LayerGroup``` | Layer Group (:warning: NOT CURRENTLY IN USE)|
3|```LayerName``` | Name of the Layer.  This must correlate with the ```layerFile.Name``` field in the ```recipe.json``` file.  |
4|```SourceFolder``` | Folder under the &lt;root&gt;```/GIS/2_Active_Data``` directory|
5|```RegExp``` | Regular Expression.  Used when selecting files to display|
6|```DefinitionQuery``` | Definition Query - (:warning: NOT CURRENTLY IN USE)|
7|```Display``` | :warning: NOT CURRENTLY IN USE)|

After executing, the layers are generated and added to the MXD file, for example:
![alt text](Images/TableOfContents.png)

## Execution

### Parameters

#|Field | Description|
-|------------ | -------------|
1|```--recipeFile``` | Path to the ```recipe.json``` file.|
2|```--layerConfig``` | Path to the ```layerProperties.json``` file.|
3|```--cmf``` | Path to the Crash Move Folder root. |
4|```--template``` | Path to the ```MXD``` file.|

### Example


```
C:\Python27\ArcGIS10.6\python.exe main.py \
   --recipeFile "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\recipe.json" \
   --layerConfig "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\layerProperties.json" \
   --cmf "D:\MapAction\2018-11-16-SierraCobre" \
   --template "D:\MapAction\2018-11-16-SierraCobre\GIS\3_Mapping\33_MXD_Maps\MA001_scb_country_overview_DEV.mxd" 
```

## Authors

* **Steve Hurst** - *Initial work* - [poc](https://github.com/mapaction/mapactionpy_arcmap/poc)

