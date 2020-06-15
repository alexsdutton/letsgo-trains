import cairo
import math

from .base import Piece
from ..drawing_options import DrawingOptions
from ..track import Bounds, Position


class BaseStraight(Piece):
    anchor_names = ('in', 'out')
    layout_priority = 10

    label: str
    length: float

    def traversals(self, anchor_from):
        return {'out' if anchor_from == 'in' else 'in': (self.length, True)}

    # Drawing

    def bounds(self):
        return Bounds(x=0, y=-4, width=self.length, height=8)

    def draw(self, cr: cairo.Context, drawing_options: DrawingOptions):
        cr.set_source_rgb(*drawing_options.sleeper_color)

        # The half-sleepers at either end
        cr.set_line_width(1)
        cr.move_to(0.5, -4)
        cr.line_to(0.5, 4)
        cr.move_to(self.length - 0.5, -4)
        cr.line_to(self.length - 0.5, 4)
        cr.stroke()

        # The sleepers in between
        cr.set_line_width(2)
        for x in range(4, int(self.length), 4):
            cr.move_to(x, -4)
            cr.line_to(x, 4)
        cr.stroke()

        cr.set_source_rgb(*drawing_options.rail_color)
        cr.set_line_width(1)
        cr.move_to(0, -2.5)
        cr.line_to(self.length, -2.5)
        cr.move_to(0, 2.5)
        cr.line_to(self.length, 2.5)
        cr.stroke()

    def relative_positions(self):
        return {
            **super().relative_positions(),
            'out': Position(self.length, 0, 0),
        }

    def point_position(self, in_anchor, offset):
        if in_anchor == 'in':
            return offset, 0, 0
        elif in_anchor == 'out':
            return self.length - offset, 0, math.pi


class Straight(BaseStraight):
    label = 'straight'
    length = 16


class HalfStraight(BaseStraight):
    label = 'half-straight'
    length = 8


class QuarterStraight(BaseStraight):
    label = 'quarter-straight'
    length = 4
