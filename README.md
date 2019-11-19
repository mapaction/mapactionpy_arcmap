
# MapChef

Master branch [![Build Status](https://travis-ci.org/mapaction/mapactionpy_arcmap.svg?branch=master)](https://travis-ci.org/mapaction/mapactionpy_arcmap) [![Coverage Status](https://coveralls.io/repos/github/mapaction/mapactionpy_arcmap/badge.svg?branch=pep8-and-travis)](https://coveralls.io/github/mapaction/mapactionpy_arcmap?branch=master)

Adds geospatial data to an ArcMap MXD file based on a recipe from a cookbook configuration file and a product name.

### Prerequisites

* Python and ArcPy

    ```
    C:\Python27\ArcGIS10.6\python.exe
    ```
* ArcMap MapAction templates.
* Complete data scramble using Crash Move Folder Version xx.

## Packaging

```python setup.py bdist_wheel```

## Installing
1) Clone

    ```git clone https://github.com/mapaction/mapactionpy_arcmap/```
2) Change Directory at the command line
    ```cd mapactionpy_arcmap```
3) Run package ```python setup.py bdist_wheel```
4) Install
    ```
    python -m pip install pycountry
    python -m pip install jsonpickle
    python -m pip install mapactionpy_controller
    python -m pip install --user -e .
    ```
    To install for use non-development purposes:
    Clone the github repo then from the root of your local clone:
    ```
    python -m pip install .
    ```
5) If required, uninstall the ArcMap Esri Add-In.
6) Reinstall ArcMap Esri Add-In using file here:
	[https://drive.google.com/open?id=1kV1_6r8RzQ2fzA28AEQv9tpET-qZPIN-](https://drive.google.com/open?id=1kV1_6r8RzQ2fzA28AEQv9tpET-qZPIN-)
7) Restart ArcMap and ensure the 'Map Generation Tool' is available within the MapAction toolbar.
8) To run the 'Map Generation Tool' the following paths MUST exist:
    ```  
    <Crash Move Folder> \GIS\3_Mapping\31_Resources\312_Layer_files\
    ```
    This must contain the Layer files (```.lyr```) which correspond with the names quoted in the ```mapCookbook.json``` file.

9) Move the ```layerProperties.json``` and ```mapCookbook.json``` files from the Git repository to:
    ```
    <Crash Move Folder> \GIS\3_Mapping\31_Resources\31A_Automation\
    ```
    i.e.
    ```
    <Crash Move Folder> \GIS\3_Mapping\31_Resources\31A_Automation\layerProperties.json
    <Crash Move Folder> \GIS\3_Mapping\31_Resources\31A_Automation\mapCookbook.json
    ```

## Integration with MapAction Toolbar

In order to integrate this `MapActionPy_ArcMap` module with the MapAction Toolbar, the following steps need to be carried out:

:information_source: The "Automation" add-in is in development in the `automation` branch at: https://github.com/mapaction/mapaction-toolbox/tree/automation):

1) All layer `.lyr` files should be made available under the crash move folder at the following location:
`\GIS\3_Mapping\31_Resources\312_Layer_files`
2) Layer properties file [layerProperties.json](mapactionpy_arcmap/Config/layerProperties.json) copied to new directory under the crash move folder at the following location:
`\GIS\3_Mapping\31_Resources\31A_Automation`
3) Map cookbook file [mapCookbook.json](mapactionpy_arcmap/Config/mapCookbook.json) copied to directory under the crash move folder at the following location:
`\GIS\3_Mapping\31_Resources\31A_Automation`


## Configuration Files

### Cookbook File

The [mapCookbook.json](mapactionpy_arcmap/Config/mapCookbook.json) file is a static configuration file which contains "recipes" for each map product.

This example cookbook only contains a single product: ```Country Overview```.
```
{ 
   "recipes":[ 
      { 
         "mapnumber":"MA001",
         "category":"Reference",
         "product":"Country Overview with Admin 1 Boundaries & P-Codes",
         "export":"Yes",
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

The layer names in the "```layers```" array MUST correlate to layer files (```.lyr```) in the specified layer directory.

### layerConfig File

The Layer Config file ([layerProperties.json](mapactionpy_arcmap/Config/layerProperties.json)) is a static file which defines how to add a particular layer.

```
    {
      "MapFrame": "Main Map",
      "LayerName": "mainmap-s0-pt-settlements",
      "RegExp": "^[a-z]{3}_stle_stl_pt_(.*?)_(.*?)_([phm][phm])(.*?).shp$",
      "DefinitionQuery": "place IN ('national_capital', 'city', 'capital')",
      "Display": "Yes",
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
| 5 | Display         | Shows if set to 'Yes' | 
| 6 | LabelClasses    | Details for displaying labels | 
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

```
C:\Python27\ArcGIS10.6\python.exe -m mapactionpy_arcmap.arcmap_runner \
   --cookbook "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\31A_Automation\mapCookbook.json" \
   --layerConfig "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\31A_Automation\layerProperties.json" \
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

```
C:\Python27\ArcGIS10.6\python.exe -m mapactionpy_arcmap.arcmap_runner \
   --cookbook "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\31A_Automation\mapCookbook.json" \
   --layerConfig "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\31A_Automation\layerProperties.json" \
   --cmf "D:\MapAction\2019-06-25 - Automation - El Salvador" \
   --layerDirectory "D:\MapAction\2019-06-25 - Automation - El Salvador\GIS\3_Mapping\31_Resources\312_Layer_files" \
   --product "Country Overview with Admin 1 Boundaries & P-Codes" \
   --country "El Salvador"
```

If an MXD is not supplied with the ```--template``` parameter as above, then the tool will decide the orientation of the map (landscape or portrait) and it will take a copy of the appropriate MXD from:

\<crash move folder>```\GIS\3_Mapping\32_MXD_Templates\arcgis_10_6\```

Using the ```mapnumber``` from the [mapCookbook.json](mapactionpy_arcmap/Config/mapCookbook.json) file, the Automation Tool will create a copy of the MXD under the following directory:

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

todo:
[] enable installation via pypi.
