import unittest
from unittest import TestCase


class TestArcMapRunner(TestCase):
    def test_alway_pass(self):
        self.assertTrue(True)

    @unittest.SkipTest
    def test_zoom_to_layer(self):
        self.assertTrue(False, msg='zoom to layer for Main Map')
        self.assertTrue(False,
                        msg='zoom to layer plus margin for Location Map')

    @unittest.SkipTest
    def test_layer_in_dict_but_not_in_mxd(self):
        self.assertTrue(False)

    @unittest.SkipTest
    def test_datasource_does_not_exist(self):
        self.assertTrue(False)
