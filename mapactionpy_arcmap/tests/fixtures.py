# flake8: noqa
import json
from os import path

fixture_recipe_minimal = (
    '''{
      "mapnumber": "MA001",
      "category": "Reference",
      "product": "{e.country_name}: Overview Map",
      "summary": "Overview of {e.country_name} with topography displayed",
      "export": true,
      "template": "reference",
      "principal_map_frame": "Main map",
      "map_frames": [
         {
            "name": "Main map",
            "crs": "EPSG:3857",
            "layers": [
               {
                  "name": "mainmap-admn-ad1-py-s0-reference"
               }
            ]
         }
      ]
   }'''
)


_temp_recipe_processed_by_controller = (
    r'''{
      "mapnumber": "MA001",
      "category": "Reference",
      "product": "Atlantis: Overview Map",
      "summary": "Overview of Atlantis with topography displayed",
      "export": true,
      "template": "reference",
      "principal_map_frame": "Main map",
      "map_frames": [
         {
            "name": "Main map",
            "crs": "EPSG:3857",
            "extent": [
               30.76715745398743,
               31.029105187500107,
               36.2156944299999,
               36.930416107500065
            ],
            "layers": [
               {
                  "crs": "epsg:4326",
                  "data_source_path": "D:\\MapAction\\mapchef-test-env\\2020-08-05-Lebanon\\GIS/2_Active_Data\\211_elev\\aoi_elev_cst_ln_s0_gadm_pp.shp",
                  "name": "locationmap-elev-cst-ln-s0-locationmaps",
                  "schema_definition": "null-schema.yml",
                  "data_schema": true,
                  "data_name": "aoi_elev_cst_ln_s0_gadm_pp",
                  "definition_query": "\"NAME_0\" <> 'Lebanon'",
                  "label_classes": [],
                  "layer_file_path": "D:\\MapAction\\mapchef-test-env\\2020-08-05-Lebanon\\GIS\\3_Mapping\\31_Resources\\312_Layer_files\\locationmap-elev-cst-ln-s0-locationmaps.lyr",
                  "data_source_checksum": "2ee4edea9ec37087ed5b1cb3e55761af",
                  "layer_file_checksum": "a33da00ef5f5471d3d93a869b9843a87",
                  "extent": [
                     30.76715745398743,
                     31.029105187500107,
                     36.2156944299999,
                     36.930416107500065
                  ],
                  "add_to_legend": false,
                  "display": true,
                  "use_for_frame_extent": true,
                  "reg_exp": "^wrl_elev_cst_ln_(.*?)_(.*?)_([phm][phm])(.*?).shp$"
               }
            ]
         }
      ]
   }'''
)

_temp_recipe = json.loads(_temp_recipe_processed_by_controller)
_root_dir = path.abspath(path.dirname(__file__))
_shp_path = path.join(_root_dir, 'test_data', 'test_shapefile', 'aoi_elev_cst_ln_s0_gadm_pp.shp')
_lyr_path = path.join(_root_dir, 'test_data', 'test_shapefile', 'locationmap-elev-cst-ln-s0-locationmaps.lyr')
_temp_recipe['map_frames'][0]['layers'][0]['data_source_path'] = _shp_path
_temp_recipe['map_frames'][0]['layers'][0]['layer_file_path'] = _lyr_path
fixture_recipe_processed_by_controller = json.dumps(_temp_recipe)

fixture_datasource_dictionary_ma001 = r"""
{
"settlement_points": "D:\MapAction\2019-06-12-GBR\GIS\2_Active_Data\gbr_stle_stle_pt_s0_naturalearth_pp.shp"
"airports_points": "D:\MapAction\2019-06-12-GBR\GIS\2_Active_Data\232_tran\scr_tran_air_pt_s1_ourairports_pp.shp"
}
"""


fixture_layer_description_ma001 = r"""
-
   m: Main Map
   layer-group: None
   layer-name: Settlement - Places - pt
   source-folder: 229_stle
   regex: ^ XXX_stle_stl_pt_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: "SettleType" IN('national_capital', 'city')
   visable: Yes
-
   m: Main Map
   layer-group: Transport - Points
   layer-name: Transport - Airports - pt
   source-folder: 232_tran
   regex: ^ XXX_trans_air_pt_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Transport - Points
   layer-name: Transport - Seaports - pt
   source-folder: 232_tran
   regex: ^ XXX_trans_por_pt_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Lines
   layer-name: Elevation - Coastline - ln
   source-folder: 211_elev
   regex: ^ XXX_elev_cst_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: none
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Lines
   layer-name: Borders - Admin1 - ln
   source-folder: 202_admn
   regex: ^ XXX_admn_ad1_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Lines
   layer-name: Borders - Admin2 - ln
   source-folder: 202_admn
   regex: ^ XXX_admn_ad2_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Transport - Lines
   layer-name: Transport - Rail - ln
   source-folder: 232_tran
   regex: ^ XXX_tran_rrd_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Transport - Lines
   layer-name: Transport - Road - ln
   source-folder: 232_tran
   regex: ^ XXX_tran_rds_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: None
   layer-name: Cartography - Feather - pt
   source-folder: 207_carto
   regex: ^ (?!(XXX))_carto_fea_py_s0_mapaction_pp(_(.+)
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Physical
   layer-name: Physical - Waterbody - py
   source-folder: 221_phys
   regex: tbd
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Physical
   layer-name: Physical - River - ln
   source-folder: 221_phys
   regex: ^ XXX_phys_riv_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Polygons
   layer-name: Admin - Admin2 - py
   source-folder: 202_admn
   regex: ^ XXX_admn_ad2_py_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Polygons
   layer-name: Admin - Admin1 - py
   source-folder: 202_admn
   regex: ^ XXX_admn_ad1_py_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Polygons
   layer-name: Admin - AffectedCountry - py
   source-folder: 202_admn
   regex: ^ XXX_admn_ad0_py_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Admin - Polygons
   layer-name: Admin - SurroundingCountry - py
   source-folder: 202_admn
   regex: ^ (?!(XXX))_admn_ad0_py_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: ADM0_NAME <> '[reference country]'
   visable: Yes
-
   m: Main Map
   layer-group: Elevation
   layer-name: Physical - Sea - py
   source-folder: 221_phys
   regex: ^ XXX_phys_ocn_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Elevation
   layer-name: Elevation - DEM - ras
   source-folder: 211_elev
   regex: ^ XXX_elev_dem_ras_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Elevation
   layer-name: Elevation - Hillshade - ras
   source-folder: 211_elev
   regex: ^ XXX_elev_hsh_ras_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Elevation
   layer-name: Elevation - Curvature - ras
   source-folder: 211_elev
   regex: tbd
   query-definition: None
   visable: Yes
-
   m: Main Map
   layer-group: Legend
   layer-name: Legend - Road - ln
   source-folder: 232_tran
   regex: ^ XXX_tran_rds_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: No
-
   m: Main Map
   layer-group: Legend
   layer-name: Legend - WaterBody - py
   source-folder: 221_phys
   regex: tbd
   query-definition: None
   visable: No
-
   m: Main Map
   layer-group: Legend
   layer-name: Elevation - Elevation - ras
   source-folder: 211_elev
   regex: ^ XXX_elev_dem_ras_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: No
-
   m: Location Map
   layer-group: None
   layer-name: Location - Coastline - ln
   source-folder: 211_elev
   regex: ^ XXX_elev_cst_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Location Map
   layer-group: None
   layer-name: Location - Admin1 - ln
   source-folder: 202_admn
   regex: ^ XXX_admn_ad1_ln_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Location Map
   layer-group: None
   layer-name: Location - AffectedCountry - py
   source-folder: 202_admn
   regex: ^ XXX_admn_ad0_py_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: None
   visable: Yes
-
   m: Location Map
   layer-group: None
   layer-name: Location - SurroundingCountry - py
   source-folder: 202_admn
   regex: ^ (?!(XXX))_admn_ad0_py_(.*?)_(.*?)_([phm][phm])(_(.+))
   query-definition: "ADM0_NAME" <> '[reference country]'
   visable: Yes
"""
