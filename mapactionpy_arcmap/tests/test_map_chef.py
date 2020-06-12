import arcpy
import os
# import unittest
from unittest import TestCase
from mapactionpy_arcmap.map_chef import MapChef
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.map_cookbook import MapCookbook
from mapactionpy_controller.event import Event
from mapactionpy_controller.layer_properties import LayerProperties


class TestMapChef(TestCase):

    def setUp(self):
        self.parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.path_to_valid_cmf_des = os.path.join(
            self.parent_dir, 'tests', 'test_data', 'fixture_cmf_description_flat_test.json')
        self.cmf = CrashMoveFolder(self.path_to_valid_cmf_des)
        self.event = Event(os.path.join(self.parent_dir, 'tests', 'test_data',
                                        'event_description.json'))
        self.my_mxd_fname = os.path.join(self.parent_dir, 'tests', 'test_data',
                                         'output_arcgis_10_6_reference_landscape_bottom.mxd')
        self.layer_props = LayerProperties(self.cmf, '.lyr')
        self.cookBook = MapCookbook(self.cmf, self.layer_props)

    def test_map_chef_constructor(self):
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fname)

        mc = MapChef(
            my_mxd,
            self.cmf,
            self.event
        )
        self.assertIsInstance(mc, MapChef)

    def test_map_chef_cook(self):
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fname)
        productName = "Example Map"

        mc = MapChef(
            my_mxd,
            self.cmf,
            self.event
        )

        mc.cook(self.cookBook.products[productName])
        self.assertTrue(True)
