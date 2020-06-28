import math

from letsgo.track import Bounds, Position

from .base import Piece


class BaseCrossover(Piece):
    anchor_names = ("in", "left", "right", "out")

    length: float
    label: str

    def traversals(self, anchor_from):
        return {
            self.anchor_names[3 - self.anchor_names.index(anchor_from)]: (
                self.length,
                True,
            )
        }

    layout_priority = 40

    # Drawing

    def bounds(self):
        return Bounds(x=0, y=-self.length / 2, width=self.length, height=self.length)

    def draw(self, cr, drawing_options):
        cr.set_line_width(8)
        cr.set_source_rgb(*drawing_options.sleeper_color)

        cr.move_to(0, 0)
        cr.line_to(self.length, 0)
        cr.stroke()
        cr.move_to(self.length / 2, -self.length / 2)
        cr.line_to(self.length / 2, self.length / 2)
        cr.stroke()

        cr.set_line_width(1)
        cr.set_source_rgb(*drawing_options.rail_color)

        cr.move_to(0, -2.5)
        cr.line_to(self.length, -2.5)
        cr.move_to(0, 2.5)
        cr.line_to(self.length, 2.5)
        cr.move_to(self.length / 2 - 2.5, -self.length / 2)
        cr.line_to(self.length / 2 - 2.5, self.length / 2)
        cr.move_to(self.length / 2 + 2.5, -self.length / 2)
        cr.line_to(self.length / 2 + 2.5, self.length / 2)
        cr.stroke()

    def relative_positions(self):
        return {
            **super().relative_positions(),
            "out": Position(self.length, 0, 0),
            "left": Position(self.length / 2, -self.length / 2, -math.pi / 2),
            "right": Position(self.length / 2, self.length / 2, math.pi / 2),
        }

    def point_position(self, in_anchor, offset):
        if in_anchor == "in":
            return offset, 0, 0
        elif in_anchor == "out":
            return self.length - offset, 0, math.pi
        elif in_anchor == "left":
            return self.length / 2, self.length / 2 - offset, -math.pi / 2
        elif in_anchor == "right":
            return self.length / 2, offset - self.length / 2, math.pi / 2


class Crossover(BaseCrossover):
    length = 16
    label = "crossover"


class ShortCrossover(BaseCrossover):
    length = 8
    label = "crossover (short)"
