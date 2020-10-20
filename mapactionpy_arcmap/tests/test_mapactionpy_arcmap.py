import os
import six
import sys
from itertools import repeat
# from unittest import TestCase
import unittest

from mapactionpy_controller.crash_move_folder import CrashMoveFolder
from mapactionpy_controller.event import Event
import mapactionpy_arcmap.arcmap_runner as arcmap_runner


# works differently for python 2.7 and python 3.x
if six.PY2:
    import mock  # noqa: F401
else:
    from unittest import mock  # noqa: F401


class TestArcMapRunner(unittest.TestCase):

    def setUp(self):
        self.parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.path_to_valid_cmf_des = os.path.join(
            self.parent_dir, 'tests', 'test_data', 'fixture_cmf_description_flat_test.json')
        self.cmf = CrashMoveFolder(self.path_to_valid_cmf_des)
        self.event = Event(os.path.join(self.cmf.path, 'event_description.json'))
        self.arcmap_runner = arcmap_runner.ArcMapRunner(self.event)

        # 1) insert map
        self.df1 = mock.Mock(name='data_frame1')
        self.df1.name = 'data_frame1'
        self.df1.elementHeight = 19
        self.df1.elementWidth = 17
        # 2) main map
        self.df2 = mock.Mock(name='data_frame2')
        self.df2.name = 'data_frame2'
        self.df2.elementHeight = 100
        self.df2.elementWidth = 200
        # 3) main map (same size different asspect ratio)
        self.df3 = mock.Mock(name='data_frame3')
        self.df3.name = 'data_frame3'
        self.df3.elementHeight = 50
        self.df3.elementWidth = 400
        # 4) main map - identical to df3
        self.df4 = mock.Mock(name='data_frame4')
        self.df4.name = 'data_frame4'
        self.df4.elementHeight = 50
        self.df4.elementWidth = 400
        # 5) main map - widest, but not the largest area
        self.df5 = mock.Mock(name='data_frame5')
        self.df5.name = 'data_frame5'
        self.df5.elementHeight = 10
        self.df5.elementWidth = 500
        # 6) inset map - identical to df1 in every way including the name
        self.df6 = mock.Mock(name='data_frame6')
        self.df6.name = 'data_frame1'
        self.df6.elementHeight = 19
        self.df6.elementWidth = 17

    @unittest.skip('Not ready yet')
    def test_arcmap_runner_main(self):
        sys.argv[1:] = ['--eventConfigFile', os.path.join(self.cmf.path, 'event_description.json'),
                        '--template', os.path.join(self.cmf.map_templates,
                                                   'arcgis_10_6_reference_landscape_bottom.mxd'),
                        "--product", "Example Map"]

        arcmap_runner.main()
        self.assertTrue(True)

    @unittest.skip('Not ready yet')
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

    def test_get_largest_map_frame(self):

        # Case 1)
        # Main map and inset map
        result1 = self.arcmap_runner._get_largest_map_frame([self.df1, self.df2])
        self.assertIs(result1, self.df2)
        self.assertIsNot(result1, self.df1)

        # Case 2)
        # Two large maps and the inset map
        result2 = self.arcmap_runner._get_largest_map_frame([self.df1, self.df2, self.df3, self.df5])
        self.assertIs(result2, self.df3)
        self.assertIsNot(result2, self.df1)
        self.assertIsNot(result2, self.df2)
        self.assertIsNot(result2, self.df5)

        # Case 3)
        # Three large maps, two of which are identical in size plus the inset map
        result3 = self.arcmap_runner._get_largest_map_frame([self.df1, self.df2, self.df3, self.df4])
        self.assertIs(result3, self.df4)
        self.assertIsNot(result3, self.df1)
        self.assertIsNot(result3, self.df2)
        self.assertIsNot(result3, self.df3)
        self.assertIsNot(result3, self.df5)

        # Case 4
        with self.assertRaises(ValueError):
            self.arcmap_runner._get_largest_map_frame([self.df1, self.df6])

    @mock.patch('mapactionpy_arcmap.arcmap_runner.arcpy.mapping.MapDocument')
    @mock.patch('mapactionpy_arcmap.arcmap_runner.arcpy.mapping.ListDataFrames')
    def test_get_aspect_ratios_of_templates(self, mock_ListDataFrames, mock_MapDocument):
        mock_MapDocument.return_value = None
        df_lists = [
            [self.df1], [self.df2], [self.df3], [self.df4], [self.df5], [self.df6]
        ]
        mock_ListDataFrames.side_effect = df_lists
        tmpl_paths = repeat('/the/path', len(df_lists))

        expected_result = [
            ('/the/path', float(self.df1.elementWidth)/self.df1.elementHeight),
            ('/the/path', float(self.df2.elementWidth)/self.df2.elementHeight),
            ('/the/path', float(self.df3.elementWidth)/self.df3.elementHeight),
            ('/the/path', float(self.df4.elementWidth)/self.df4.elementHeight),
            ('/the/path', float(self.df5.elementWidth)/self.df5.elementHeight),
            ('/the/path', float(self.df6.elementWidth)/self.df6.elementHeight)
        ]

        actual_result = self.arcmap_runner.get_aspect_ratios_of_templates(tmpl_paths)

        self.assertEqual(actual_result, expected_result)
