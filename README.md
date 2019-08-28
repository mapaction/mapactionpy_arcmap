
# MapChef

Master branch [![Build Status](https://travis-ci.org/mapaction/mapactionpy_arcmap.svg?branch=master)](https://travis-ci.org/mapaction/mapactionpy_arcmap) [![Coverage Status](https://coveralls.io/repos/github/mapaction/mapactionpy_arcmap/badge.svg?branch=pep8-and-travis)](https://coveralls.io/github/mapaction/mapactionpy_arcmap?branch=master)

Adds geospatial data to an ArcMap MXD file based on a recipe from a cookbook configuration file and a product name.

### Prerequisites

Python and ArcPy

```
C:\Python27\ArcGIS10.6\python.exe
```

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

##### Progress

#|Tested|MapFrame|LayerGroup|LayerName|SourceFolder|RegExp|DefinitionQuery|Display||
-|-|--------|----------|---------|------------|------|---------------|-------|-|
1|:heavy_check_mark:|Main Map|None|Settlements - Places|229_stle|^[a-z]{3}_stle_stl_pt_(.*?)_(.*?)_([phm][phm])_(.*?).shp$|"place IN ('national_capital', 'city')"||Yes|
2|:heavy_check_mark:|Main Map|Transport Points|Transport - Seaports|232_tran|^[a-z]{3}_tran_sea_pt_(.*?)_(.*?)_([phm][phm])_(.*?).shp$||Yes|
3|:heavy_check_mark:|Main Map|Admin - lines|Elevation - Coastline|211_elev|^[a-z]{3}_elev_cst_ln_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
4|:heavy_check_mark:|Main Map|Provinces|Provinces|202_admn|^[a-z]{3}_admn_ad1_py_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
5|:heavy_check_mark:|Main Map|Admin Lines|Borders - Admin 0|202_admn|^[a-z]{3}_admn_ad0_ln_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
6|:heavy_check_mark:|Main Map|Admin Lines|Borders - Admin 1|202_admn|^[a-z]{3}_admn_ad1_ln_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
7|:heavy_check_mark:|Location Map|Admin Lines|Borders - Admin 2|202_admn|^[a-z]{3}_admn_ad2_ln_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
8|:heavy_check_mark:|Main Map|Transport Lines|Transport - Rail|232_tran|^[a-z]{3}_tran_rrd_ln_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
9|:heavy_check_mark:|Main Map|Transport Points|Transport - Airports|232_tran|^[a-z]{3}_tran_air_pt_(.*?)_(.*?)_([phm][phm])_(.*?).shp$||Yes|
10|:heavy_check_mark:|Main Map|None|Cartography - Feather|207_carto|^[a-z]{3}_carto_fea_py_(.*?)_(.*?)_pp.shp$||Yes|
11|:heavy_check_mark:|Main Map|Physical|Physical - Lakes|221_phys|^[a-z]{3}_phys_lak_py_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
12|:heavy_check_mark:|Main Map|Physical|Physical - Rivers|221_phys|^[a-z]{3}_phys_riv_ln_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
13|:heavy_check_mark:|Main Map|Admin Polygons|Admin - Ad 1 Polygon|202_admn|^[a-z]{3}_admn_ad1_py_(.*?).shp$||Yes|
14|:heavy_check_mark:|Main Map|Admin Polygons|Admin - Ad 2 Polygon|202_admn|^[a-z]{3}_admn_ad2_py_(.*?).shp$||Yes|
15|:heavy_check_mark:|Main Map|Admin Polygons|Admin - Ad 3 Polygon|202_admn|^[a-z]{3}_admn_ad3_py_(.*?).shp$||Yes|
16|:heavy_check_mark:|Main Map|Admin Polygons|Admin - Ad 4 Polygon|202_admn|^[a-z]{3}_admn_ad4_py_(.*?).shp$||Yes|
17|:heavy_check_mark:|Main Map|Admin Polygons|Admin 0 - Affected Country|202_admn|^[a-z]{3}_admn_ad0_py_(.*?)_(.*?)_([phm][phm]).shp$|"""ADM0_NAME"" = '{COUNTRY_NAME}'"|Yes|
18|:heavy_check_mark:|Main Map|Admin Polygons|Admin 0 - Surrounding Country|202_admn|^[a-z]{3}_admn_ad0_py_(.*?)_(.*?)_([phm][phm]).shp$|"NOT ""ADM0_NAME"" = '{COUNTRY_NAME}'"|Yes|
19|:heavy_check_mark:|Main Map|Elevation|Physical - Sea|221_phys|^[a-z]{3}_phys_sea_py_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
20|:heavy_check_mark:|Main Map|Imagery|Imagery - Imagery|216_imgy|^[a-z]{3}_img_aer_ras_su_unknown_mp_tile_\d*.TIF$||Yes|
21||Main Map|Elevation|Elevation - DEM|211_elev|^Rasters.gdb/[a-z]{3}_elev_dem_ras_(.*?)$||Yes|
22|:heavy_check_mark:|Main Map|Elevation|Elevation - DEM|211_elev|^[a-z]{3}_elev_dem_ras_(.*?).tif$||Yes|
23|:heavy_check_mark:|Main Map|Elevation|Elevation - Hillshade|211_elev|^[a-z]{3}_elev_hsh_ras_(.*?)_(.*?)_([phm][phm])(_(.+)).tif$||Yes|
24|:heavy_check_mark:|Main Map|Elevation|Elevation - Curvature|211_elev|^[a-z]{3}_elev_cur_ras_(.*?)_(.*?)_([phm][phm])(_(.+)).tif$||Yes|
25|:heavy_check_mark:|Main Map|Transport Lines|Transport - Roads|232_tran|^[a-z]{3}_tran_rds_ln_(.*?)_(.*?)_([phm][phm]).shp$|highway = 'primary'|Yes|
26|:heavy_check_mark:|Main Map|Population|Population|223_popu|^[a-z]{3}_popu_pop_ras_(.*?)_(.*?)_([phm][phm]).tif$||Yes|
27||Main Map|Legend|Legend - Roads|232_tran|^[a-z]{3}_tran_rds_ln_(.*?)_(.*?)_([phm][phm])(_(.+))||No|
28||Main Map|Legend|Legend - Water|221_phys|tbd||No|
29|:heavy_check_mark:|Location Map|None|Location Map - Admin 0 Polygon|202_admn|^[a-z]{3}_admn_ad0_py_(.*?)_(.*?)_([phm][phm]).shp$||Yes|
30|:heavy_check_mark:|Location Map|None|Location - Surrounding Country|202_admn|^[a-z]{3}_admn_ad0_py_(.*?)_(.*?)_([phm][phm])(_(.+))||Yes|

## Execution

### Parameters

#|Field | Description|
-|------------ | -------------|
1|```--cookbook`` | Path to the cookbook ```mapCookbook.json``` file.|
2|```--layerConfig``` | Path to the ```layerProperties.json``` file.|
3|```--cmf``` | Path to the Crash Move Folder root. |
4|```--template``` | Path to the ```MXD``` file.|
5|```--layerDirectory``` | Path to the Layer File directory. |
6|```--product``` | Name of product (must correlate with a product in the cookbook file). |
7|```--country``` | Name of country. |

### Example

```
C:\Python27\ArcGIS10.6\python.exe main.py \
   --cookbook "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\316_Automation\mapCookbook.json" \ 
   --layerConfig "C:\Users\steve\Source\Repos\mapactionpy_arcmap\poc\MapChef\Config\layerProperties.json" \
   --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador" \ 
   --template "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\32_MXD_Templates\arcgis_10_2\MapAction\01 Reference mapping\arcgis_10_2_ma000_reference_landscape_bottom_DEV.mxd" \
   --layerDirectory "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\38_Initial_Maps_Layer_Files\All" \
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

