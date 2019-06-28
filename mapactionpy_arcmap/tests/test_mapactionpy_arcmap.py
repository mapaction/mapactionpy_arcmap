from unittest import TestCase

import mapactionpy_arcmap


class TestArcMapRunner(TestCase):
    def test_alway_fail(self):
        self.assertTrue(False)

    def test_alway_pass(self):
        self.assertTrue(True)

    def test_zoom_to_layer(self):
        self.assertTrue(False, msg='zoom to layer for Main Map')
        self.assertTrue(False,
                        msg='zoom to layer plus margin for Location Map')

    def test_layer_in_dict_but_not_in_mxd(self):
        self.assertTrue(False)

    def test_datasource_does_not_exist(self):
        self.assertTrue(False)
