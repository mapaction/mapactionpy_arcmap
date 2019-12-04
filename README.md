
# MapChef

Master branch [![Build Status](https://travis-ci.org/mapaction/mapactionpy_arcmap.svg?branch=master)](https://travis-ci.org/mapaction/mapactionpy_arcmap) [![Coverage Status](https://coveralls.io/repos/github/mapaction/mapactionpy_arcmap/badge.svg?branch=pep8-and-travis)](https://coveralls.io/github/mapaction/mapactionpy_arcmap?branch=master)

Adds geospatial data to an ArcMap MXD file based on a recipe from a cookbook configuration file and a product name.

### Prerequisites

* Python v2.7 and ArcPy v10.6.1

    ```
    C:\Python27\ArcGIS10.6\python.exe
    ```
* ArcMap MapAction templates and Crash Move Folder as setout here https://github.com/mapaction/default-crash-move-folder
* For the Crash Move Folder to have been populated by the Data Scramble process.

Installing
---------
To install the lastest stable release via PyPi:
```
pip install mapactionpy-controller
pip install mapactionpy-arcmap
```

To install a specific version for testing see the relevant commandline from here:
https://pypi.org/project/mapactionpy-arcmap/#history


Optional Installation of ArcMap ESRI Addin
------------------------------------------
In additiona to the commandline the MapChef tool can also optionally be driven from an ArcMap Addin. To install this:
1) If required, uninstall any previous version of the ArcMap Esri Add-In.
2) Reinstall ArcMap Esri Add-In using file here:
    [https://drive.google.com/drive/u/0/folders/1qzR6UvqA_RjxK9D2U9_AXi3EW4cXnuP7](https://drive.google.com/drive/u/0/folders/1qzR6UvqA_RjxK9D2U9_AXi3EW4cXnuP7)
3) Restart ArcMap and ensure the 'Map Generation Tool' is available within the MapAction toolbar.
4) To run the 'Map Generation Tool' the standardised Crash Move Folder must be in place, see:

  [https://github.com/mapaction/default-crash-move-folder/blob/master/20YYiso3nn](https://github.com/mapaction/default-crash-move-folder/blob/master/20YYiso3nn)

## Integration with MapAction Toolbar

In order to integrate this `MapActionPy_ArcMap` module with the MapAction Toolbar, the following steps need to be carried out:

## Configuration Files

### Cookbook File

The [mapCookbook.json](https://github.com/mapaction/default-crash-move-folder/blob/master/20YYiso3nn/GIS/3_Mapping/31_Resources/316_Automation/mapCookbook.json) file is a static configuration file which contains "recipes" for each map product, e.g.:

```
{ 
   "recipes":[ 
      { 
         "mapnumber":"MA001",
         "category":"Reference",
         "product":"Country Overview with Admin 1 Boundaries & P-Codes",
         "export": true,
         "layers":[ 
            "mainmap-s0-pt-settlements",
            "mainmap-s0-py-surroundingcountries",
            "mainmap-s0-ln-admin1",
            "mainmap-s0-ln-coastline",
            "mainmap-s0-py-feather",
            "mainmap-s0-py-surroundingcountries",
            "mainmap-s0-py-admin1",
            "mainmap-s0-py-sea",
            "locationmap-s0-ln-admin1",
            "locationmap-s0-ln-affectedcountry",
            "locationmap-s0-ln-coastline",
            "locationmap-s0-py-surroundingcountries"
         ]
      },
...
    }
  ]
}
```

The layer names in the "```layers```" array MUST correlate to layer files (```.lyr```) in the specified layer directory:

[GIS/3_Mapping/31_Resources/312_Layer_files] (https://github.com/mapaction/default-crash-move-folder/tree/master/20YYiso3nn/GIS/3_Mapping/31_Resources/312_Layer_files)

### layerConfig File

The Layer Config file ([layerProperties.json](https://github.com/mapaction/default-crash-move-folder/blob/master/20YYiso3nn/GIS/3_Mapping/31_Resources/316_Automation/layerProperties.json)) is a static file which defines how to add a particular layer.

```{
      "MapFrame": "Main Map",
      "LayerName": "mainmap-s0-pt-settlements",
      "RegExp": "^[a-z]{3}_stle_stl_pt_(.*?)_(.*?)_([phm][phm])(.*?).shp$",
      "DefinitionQuery": "place IN ('national_capital', 'city', 'capital')",
      "Display": true,
      "AddToLegend": true,
      "LabelClasses": [
        {
          "className": "National Capital",
          "expression": "[name]",
          "SQLQuery": "(\"place\" = 'national_capital')"
        },
        {
          "className": "Admin 1 Capital",
          "expression": "[name]",
          "SQLQuery": "(\"place\" = 'city')"
        }
      ]
    },
```

#### Fields

| # | Field           |Description     |
|---|-----------------|----------------------------|
| 1 | MapFrame        | Name of the Map Frame that the layer is to be added to |
| 2 | LayerName       | Name of the Layer.  This must correlate with the names of the layers in the ```layers``` field in the ```mapCookbook.json``` file. |
| 3 | RegExp          | Regular Expression.  Used when selecting files to display |
| 4 | DefinitionQuery | Definition Query |
| 5 | AddToLegend     | Includes this layer in the legend if set to true |
| 6 | Display         | Shows if set to true |
| 7 | LabelClasses    | Details for displaying labels |
## Execution

### Key
| # | Icon         |Meaning                                                           |
|---|---------------|-----------------------------------------------------------------------|
| 1 | :heavy_check_mark:| Must always be supplied
| 2 | :zap:| If not supplied, this parameter can be inferred if the `cmf_description.json` and the `event_description.json` files are in he root of the Crash Move Folder.

### Parameters


| # | Field         |Mandatory|Description                                                           |
|---|---------------|-|-----------------------------------------------------------------------|
| 1 | --cookbook    |:zap:| Path to the cookbook ```mapCookbook.json``` file.                     |
| 2 | --layerConfig |:zap:| Path to the ```layerProperties.json``` file.                          |
| 3 | --cmf         |:heavy_check_mark:| Path to the Crash Move Folder root.                                   |
| 4 | --template    |:zap:| Path to the ```MXD``` file.                                           |
| 5 | --product     |:heavy_check_mark:| Name of product (must correlate with a product in the cookbook file). |
| 6 | --country     |:zap:| Name of country.                                                      |

### Example 1

For a specified MXD using the ```--template``` parameter:

```C:\Python27\ArcGIS10.6\python.exe -m mapactionpy_arcmap.arcmap_runner \
   --cookbook "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\316_Automation\mapCookbook.json" \
   --layerConfig "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\316_Automation\layerProperties.json" \
   --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador" \
   --template "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\32_MXD_Templates\arcgis_10_2\MapAction\01 Reference mapping\arcgis_10_2_ma000_reference_landscape_bottom_DEV.mxd" \
   --layerDirectory "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\312_Layer_files" \
   --product "Country Overview with Admin 1 Boundaries & P-Codes" \
   --country "El Salvador"
```

### Result

This ```Country Overview``` map was generated:

![alt text](Images/Result.png)

### Example 2

```C:\Python27\ArcGIS10.6\python.exe -m mapactionpy_arcmap.arcmap_runner \
   --cookbook "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\316_Automation\mapCookbook.json" \
   --layerConfig "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\316_Automation\layerProperties.json" \
   --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador" \
   --layerDirectory "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\312_Layer_files" \
   --product "Country Overview with Admin 1 Boundaries & P-Codes" \
   --country "El Salvador"
```

If an MXD is not supplied with the ```--template``` parameter as above, then the tool will decide the orientation of the map (landscape or portrait) and it will take a copy of the appropriate MXD from:

\<crash move folder>```\GIS\3_Mapping\32_MXD_Templates\arcgis_10_6\```

Using the ```mapnumber``` from the [mapCookbook.json](https://github.com/mapaction/default-crash-move-folder/blob/master/20YYiso3nn/GIS/3_Mapping/31_Resources/316_Automation/mapCookbook.json) file, the Automation Tool will create a copy of the MXD under the following directory:

\<crash move folder>```\GIS\3_Mapping\33_MXD_Maps\```\<map number>

For example:

```D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\33_MXD_Maps\MA001```

The MXD name will be \<map number>```_```\<product name>```.mxd```

... (but with any characters removed that upset Windows Explorer)

For example:

```MA001_country-overview-with-admin-1-boundaries-p-codes.mxd```

### Example 3

```
C:\Python27\ArcGIS10.6\python.exe -m mapactionpy_arcmap.arcmap_runner \
   --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador" \
   --product "Country Overview with Admin 1 Boundaries & P-Codes"
```

In this example, the following parameters were not provided:

    --cookbook
    --layerConfig
    --layerDirectory
    --country

The values for these parameters were inferred from the ```event_description.json``` and the ```cmf_description.json``` files.  
These files were provided at the root of the Crash Move Folder, i.e. the directory supplied by the ```--cmf``` parameter.

## Author

* **Steve Hurst** - [https://github.com/mapaction/mapactionpy_arcmap](https://github.com/mapaction/mapactionpy_arcmap)

