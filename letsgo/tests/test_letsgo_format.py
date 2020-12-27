import importlib.resources
import io
import unittest
from unittest import TestCase

import pkg_resources
import yaml

from letsgo.control import Controller
from letsgo.layout import Layout
from letsgo.layout_parser import LetsGoLayoutParser
from letsgo.layout_serializer import LetsGoLayoutSerializer
from letsgo.pieces import Piece


class LetsGoSerializerTestCase(TestCase):
    pass


class LetsGoParserTestCase(TestCase):
    def test_parsing(self):
        for fn in pkg_resources.resource_listdir("letsgo.tests", "data"):
            if not fn.endswith(".lgl"):
                continue
            layout_string = pkg_resources.resource_string("letsgo.tests", "data/" + fn)
            with self.subTest(fn=fn):
                layout = Layout()
                parser = LetsGoLayoutParser()

                reader = io.BytesIO(layout_string)
                writer = io.BytesIO()

                parser.parse(reader, layout)

                for controller in layout.controllers.values():
                    self.assertIsInstance(controller, Controller)
                for piece in layout.pieces.values():
                    self.assertIsInstance(piece, Piece)

                serializer = LetsGoLayoutSerializer()
                serializer.serialize(writer, layout)

                original = yaml.safe_load(layout_string)
                roundtripped = yaml.safe_load(writer.getvalue())

                # Check round-tripping works
                self.assertDictEqual(original, roundtripped)
