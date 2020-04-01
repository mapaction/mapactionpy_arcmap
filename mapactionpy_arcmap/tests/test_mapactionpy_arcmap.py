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
        sys.argv[1:] = ['--cookbook', self.cmf.map_definitions,
                        '--layerConfig', self.cmf.layer_properties,
                        '--template', os.path.join(self.cmf.mxd_templates,
                                                   'arcgis_10_6_reference_landscape_bottom.mxd'),
                        '--cmf', self.cmf.path,
                        '--layerDirectory', self.cmf.layer_rendering,
                        '--product', 'Example Map',
                        '--country', 'FICTION-LAND',
                        '--orientation', 'landscape']

        arcmap_runner.main()
        self.assertTrue(True)

        try:
            arcmap_runner.main()
            self.assertTrue(True)
        except Exception as e:
            self.fail(e.message)
