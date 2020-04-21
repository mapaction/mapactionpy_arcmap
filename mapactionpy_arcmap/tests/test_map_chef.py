import arcpy
import os
# import unittest
from unittest import TestCase

from mapactionpy_arcmap.map_chef import MapChef
from mapactionpy_controller.crash_move_folder import CrashMoveFolder


class TestMapChef(TestCase):

    def setUp(self):
        self.parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.path_to_valid_cmf_des = os.path.join(
            self.parent_dir, 'tests', 'test_data', 'fixture_cmf_description_flat_test.json')
        self.cmf = CrashMoveFolder(self.path_to_valid_cmf_des)

        self.my_mxd_fname = os.path.join(self.parent_dir, 'tests', 'test_data',
                                         'output_arcgis_10_6_reference_landscape_bottom.mxd')

    def test_map_chef_constructor(self):
        # def __init__(self,
        #              mxd,
        #              cookbookJsonFile,
        #              layerPropertiesJsonFile,
        #              crashMoveFolder,
        #              layerDirectory,
        #              versionNumber=1):
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fname)

        mc = MapChef(
            my_mxd,
            self.cmf.map_definitions,
            self.cmf.layer_properties,
            self.path_to_valid_cmf_des,
            self.cmf.layer_rendering,
            versionNumber=1
        )
        self.assertIsInstance(mc, MapChef)

    def test_map_chef_cook(self):
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fname)

        mc = MapChef(
            my_mxd,
            self.cmf.map_definitions,
            self.cmf.layer_properties,
            self.path_to_valid_cmf_des,
            self.cmf.layer_rendering,
            versionNumber=1
        )

        mc.cook("Example Map", "FICTION-LAND")
        # If it gets this far without throwing an exception that good enough for this test
        # At the commandline there is a more useful stacktrace if you don't explictly catch
        # the exception and fail the test here.
        self.assertTrue(True)
