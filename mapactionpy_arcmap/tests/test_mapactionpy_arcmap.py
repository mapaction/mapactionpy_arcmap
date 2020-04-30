import os
import sys
# import unittest
from unittest import TestCase

from mapactionpy_controller.crash_move_folder import CrashMoveFolder
import mapactionpy_arcmap.arcmap_runner as arcmap_runner


class TestArcMapRunner(TestCase):

    def setUp(self):
        self.parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.path_to_valid_cmf_des = os.path.join(
            self.parent_dir, 'tests', 'test_data', 'fixture_cmf_description_flat_test.json')
        self.cmf = CrashMoveFolder(self.path_to_valid_cmf_des)

    def test_arcmap_runner_main(self):
        sys.argv[1:] = ['--eventConfigFile', os.path.join(self.cmf.path, 'event_description.json'),
                        '--template', os.path.join(self.cmf.map_templates,
                                                   'arcgis_10_6_reference_landscape_bottom.mxd'),
                        "--product", "Example Map"]

        arcmap_runner.main()
        self.assertTrue(True)

    def test_arcmap_runner_main_unknown_product(self):
        sys.argv[1:] = ['--eventConfigFile', os.path.join(self.cmf.path, 'event_description.json'),
                        '--template', os.path.join(self.cmf.map_templates,
                                                   'arcgis_10_6_reference_landscape_bottom.mxd'),
                        "--product", "This product does not exist"]
        try:
            arcmap_runner.main()
        except Exception as e:
            self.assertTrue("Could not find recipe for product: \"" +
                            sys.argv[6] + "\"" in str(e.message))
