# MapChef

Adds geospatial data to an ArcMap MXD file as separate layers based on a supplied recipe configuration file.

### Prerequisites

Python and ArcPy

```
C:\Python27\ArcGIS10.6\python.exe
```

## Execution

```
C:\Python27\ArcGIS10.6\python.exe main.py \
   --recipeFile "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\recipe.json" \
   --layerConfig "C:\Users\steve\Source\Repos\MapChef\MapChef\Config\layerProperties.json" \
   --cmf "D:\MapAction\2018-11-16-SierraCobre" \
   --template "D:\MapAction\2018-11-16-SierraCobre\GIS\3_Mapping\33_MXD_Maps\MA001_scb_country_overview_DEV.mxd" 
```

## Authors

* **Steve Hurst** - *Initial work* - [poc](https://github.com/mapaction/mapactionpy_arcmap/poc)

