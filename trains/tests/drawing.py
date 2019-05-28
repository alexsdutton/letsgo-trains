from unittest import TestCase

import cairo

from trains.drawing import DrawnPiece
from trains.track import TrackPiece


class DrawingTestCase(TestCase):
    def testDrawingDoesntChangeCTM(self):
        for piece in TrackPiece.registry.values():
            drawn_piece = DrawnPiece.for_piece(piece())
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
            ctx = cairo.Context(surface)
            drawn_piece.draw(ctx)
            self.assertEqual((1, 0), ctx.device_to_user(1, 0))
            self.assertEqual((1, 1), ctx.device_to_user_distance(1, 1))
