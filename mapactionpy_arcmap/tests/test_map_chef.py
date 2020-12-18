import arcpy
import os
# import unittest
from unittest import TestCase, skip
from mapactionpy_arcmap.map_chef import MapChef
from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.map_cookbook import MapCookbook
from mapactionpy_controller.event import Event
from mapactionpy_controller.layer_properties import LayerProperties
from mapactionpy_controller.map_recipe import MapRecipe

import fixtures


class TestMapChef(TestCase):

    def setUp(self):
        try:
            import arcpy  # noqa: F401
        except ImportError:
            self.skipTest()

        self.parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.path_to_valid_cmf_des = os.path.join(
            self.parent_dir, 'tests', 'test_data', 'fixture_cmf_description_flat_test.json')
        self.cmf = CrashMoveFolder(self.path_to_valid_cmf_des)
        self.event = Event(os.path.join(self.parent_dir, 'tests', 'test_data',
                                        'event_description.json'))
        self.my_mxd_fpath = os.path.join(self.parent_dir, 'tests', 'test_data',
                                         'output_arcgis_10_6_reference_landscape_bottom.mxd')
        self.layer_props = LayerProperties(self.cmf, '.lyr')
        self.cookBook = MapCookbook(self.cmf, self.layer_props)

    def test_map_chef_constructor(self):
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fpath)

        mc = MapChef(
            my_mxd,
            self.cmf,
            self.event
        )
        self.assertIsInstance(mc, MapChef)

    def test_map_chef_cook(self):
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fpath)

        mc = MapChef(
            my_mxd,
            self.cmf,
            self.event
        )

        test_recipe = MapRecipe(fixtures.fixture_recipe_processed_by_controller, self.layer_props)
        mc.cook(test_recipe)
        self.assertTrue(True)

    def test_apply_frame_crs_and_extent(self):
        """
        Because the test can't assume what starting extent the mxd is, the test applies to different
        extents as checks that the mxd changes.
        """
        recipe = MapRecipe(fixtures.fixture_recipe_minimal, self.layer_props)
        recipe_frame = recipe.get_frame(recipe.principal_map_frame)
        my_mxd = arcpy.mapping.MapDocument(self.my_mxd_fpath)
        arc_frame = arcpy.mapping.ListDataFrames(my_mxd, recipe.principal_map_frame).pop()

        mc = MapChef(
            my_mxd,
            self.cmf,
            self.event
        )

        # Approximations of Lebanon in WGS1984 and Web Mercator
        # Case 1 - approx Lebanon in WGS1984
        # Case 2 - Lebanon in Web Mercator
        # Case 3 - Very tall and narrow, the height will dominate the extent
        # Case 4 - Very flat and wide, the width will dominate the extent
        sample_extents = [
            ('epsg:4326', 35, 33, 36, 34),
            ('epsg:3857', 3907702.338605, 3902606.144123, 4076844.286459, 4122112.913080),
            ('epsg:4326', 1, -70, 2, 70),
            ('epsg:4326', -170, -2, 170, -1)
        ]

        for extent_def in sample_extents:
            crs, x_min, y_min, x_max, y_max = extent_def

            recipe_frame.crs = crs
            recipe_frame.extent = (x_min, y_min, x_max, y_max)

            mc.apply_frame_crs_and_extent(arc_frame, recipe_frame)

            # Either the height will approx match but the width probably won't
            # OR the width with approx match but the height probably won't
            target_height = y_max - y_min
            target_width = x_max - x_min
            actual_height = arc_frame.extent.YMax - arc_frame.extent.YMin
            actual_width = arc_frame.extent.XMax - arc_frame.extent.XMin

            print('target_height, target_width, actual_height, actual_width = ')
            print(target_height, target_width, actual_height, actual_width)

            # Aim for with 1% tolerance for one  or the two dimensions
            tolerance = 0.01

            passable_height = (
                (target_height*(1+tolerance)) > actual_height and (target_height*(1-tolerance)) < actual_height
            )

            passable_width = (
                (target_width*(1+tolerance)) > actual_width and (target_width*(1-tolerance)) < actual_width
            )

            print('passable_height = {}'.format(passable_height))
            print('passable_width = {}'.format(passable_width))

            self.assertTrue(any((passable_height, passable_width)))

    @skip('Not ready yet')
    def test_add_layer(self):
        self.fail()

    @skip('Not ready yet')
    def test_apply_label_classes(self):
        self.fail()

    @skip('Not ready yet')
    def test_apply_definition_query(self):
        # Load a test shapefile

        # feature count without DQ
        # https://desktop.arcgis.com/en/arcmap/10.6/tools/data-management-toolbox/get-count.htm
        # feature count with DQ

        self.fail()
