import unittest

from letsgo.gtk.__main__ import Application


class GtkTestCase(unittest.TestCase):
    def test_app(self):
        app = Application()
