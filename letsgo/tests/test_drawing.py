from unittest import TestCase

import cairo
from letsgo.drawing_options import DrawingOptions

from letsgo.pieces import piece_classes


class DrawingTestCase(TestCase):
    def testDrawingDoesntChangeCTM(self):
        drawing_options = DrawingOptions(
            offset=(0, 0), scale=3, rail_color=(1, 0, 0), sleeper_color=(0, 1, 0)
        )
        for piece_cls in piece_classes.values():
            piece = piece_cls()
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
            ctx = cairo.Context(surface)
            piece.draw(ctx, drawing_options)
            self.assertEqual((1, 0), ctx.device_to_user(1, 0))
            self.assertEqual((1, 1), ctx.device_to_user_distance(1, 1))
