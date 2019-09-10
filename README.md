
# MapChef

Master branch [![Build Status](https://travis-ci.org/mapaction/mapactionpy_arcmap.svg?branch=master)](https://travis-ci.org/mapaction/mapactionpy_arcmap) [![Coverage Status](https://coveralls.io/repos/github/mapaction/mapactionpy_arcmap/badge.svg?branch=pep8-and-travis)](https://coveralls.io/github/mapaction/mapactionpy_arcmap?branch=master)

Adds geospatial data to an ArcMap MXD file based on a recipe from a cookbook configuration file and a product name.

### Prerequisites

Python and ArcPy

```python -m pip install jsonpickle```

```
C:\Python27\ArcGIS10.6\python.exe
```

## Packaging

```python setup.py bdist_wheel```

## Installing

To install for development purposes:
Clone the github repo then from the root of your local clone:
```
python -m pip install --user -e .
```

To install for use non-development purposes:
Clone the github repo then from the root of your local clone:
```
python -m pip install .
```

todo:
[] enable installation via pypi.


## Configuration Files

### Cookbook File

The [mapCookbook.json](mapactionpy_arcmap/Config/mapCookbook.json) file is a static configuration file which contains "recipes" for each map product.

This example cookbook only contains a single product: ```Country Overview```.
```
{
  "recipes": [
    {
      "product": "Country Overview",
      "classification": "Core",
      "layers": [
        "Settlements - Places",
        "Provinces",
        "Cartography - Feather",
        "Transport - Airports",
        "Transport - Seaports",
        "Elevation - Coastline",
        "Borders - Admin 0",
        "Borders - Admin 1",
        "Transport - Rail",
        "Transport - Roads",
        "Physical - Lakes",
        "Physical - Rivers",
        "Admin - Ad 1 Polygon",
        "Admin 0 - Affected Country",
        "Elevation - DEM",
        "Physical - Sea",
        "Location Map - Admin 0 Polygon"
      ]
    }
  ]
}
```

The layer names in the "```layers```" array MUST correlate to layer files (```.lyr```) in the specified layer directory.

### layerConfig File

The Layer Config file ([layerProperties.json](mapactionpy_arcmap/Config/layerProperties.json)) is a static file which defines how to add a particular layer.

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

#### Fields   
#|Field | Description|
-|------------ | -------------|
1|```MapFrame``` | Name of the Map Frame that the layer is to be added to|
2|```LayerGroup``` | Layer Group (:warning: NOT CURRENTLY IN USE)|
3|```LayerName``` | Name of the Layer.  This must correlate with the ```layerFile.Name``` field in the ```recipe.json``` file.  |
4|```SourceFolder``` | Folder under the &lt;root&gt;```/GIS/2_Active_Data``` directory|
5|```RegExp``` | Regular Expression.  Used when selecting files to display|
6|```DefinitionQuery``` | Definition Query|
7|```Display``` | Shows if set to 'Yes'|

## Execution

### Parameters

#|Field | Description|
-|------------ | -------------|
1|```--cookbook`` | Path to the cookbook ```mapCookbook.json``` file.|
2|```--layerConfig``` | Path to the ```layerProperties.json``` file.|
3|```--cmf``` | Path to the Crash Move Folder root. |
4|```--template``` | Path to the ```MXD``` file.|
6|```--product``` | Name of product (must correlate with a product in the cookbook file). |
7|```--country``` | Name of country. |

### Example

```
C:\Python27\ArcGIS10.6\python.exe main.py \
   --cookbook "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\316_Automation\mapCookbook.json" \ 
   --layerConfig "C:\Users\steve\Source\Repos\mapactionpy_arcmap\poc\MapChef\Config\layerProperties.json" \
   --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador" \ 
   --template "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\32_MXD_Templates\arcgis_10_2\MapAction\01 Reference mapping\arcgis_10_2_ma000_reference_landscape_bottom_DEV.mxd" \
   --product "Country Overview" \
   --country "El Salvador"
```

### Result

This ```Country Overview``` map was generated:

![alt text](Images/Result.png)

### File Types

The current implementation supports the following geospatial file types:

* Shape files       (.shp)
* TIF files         (.TIF)
* File Geodatabases (.gdb)


## Integration with MapAction Toolbar

In order to integrate this `MapActionPy_ArcMap` module with the MapAction Toolbar, the following steps need to be carried out:

:information_source: The "Automation" add-in is in development in the `automation` branch at: https://github.com/mapaction/mapaction-toolbox/tree/automation):

1) A copy of all layer `.lyr` files from the directories under `\GIS\3_Mapping\38_Initial_Maps_Layer_Files\*` were copied to a folder named `All` under the crash move folder at the following location:
`\GIS\3_Mapping\38_Initial_Maps_Layer_Files\All`
2) Layer properties file [layerProperties.json](mapactionpy_arcmap/Config/layerProperties.json) copied to new directory under the crash move folder at the following location:
`\GIS\3_Mapping\31_Resources\316_Automation`
3) Map cookbook file [mapCookbook.json](mapactionpy_arcmap/Config/mapCookbook.json) copied to directory under the crash move folder at the following location:
`\GIS\3_Mapping\31_Resources\316_Automation`


## Authors

* **Steve Hurst** - [https://github.com/mapaction/mapactionpy_arcmap](https://github.com/mapaction/mapactionpy_arcmap)

