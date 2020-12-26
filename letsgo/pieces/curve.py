from __future__ import annotations

import enum

import cairo
import cmath
import math

from .base import FlippablePiece, Piece
from ..drawing_options import DrawingOptions
from ..track import Bounds, Position


class CurveDirection(enum.Enum):
    left = "left"
    right = "right"


class BaseCurve(FlippablePiece):
    anchor_names = ("in", "out")
    layout_priority = 20

    radius: float
    per_circle: float
    sleepers: int
    direction: CurveDirection

    def __init__(self, direction: CurveDirection = CurveDirection.left, **kwargs):
        self.direction = direction
        super().__init__(**kwargs)

    def traversals(self, anchor_from):
        return {
            "out"
            if anchor_from == "in"
            else "in": (math.tau * self.radius / self.per_circle, True)
        }

    def flip(self: BaseCurve) -> BaseCurve:
        self.direction = (
            CurveDirection.left
            if self.direction == CurveDirection.right
            else CurveDirection.right
        )
        self.placement_origin.update_connected_subset_positions()
        return self

    # Drawing

    def _get_end(self, offset, r):
        rotate = math.tau / self.per_circle
        return offset + (cmath.rect(r, rotate) - r) * cmath.rect(1, -math.pi / 2)

    def bounds(self):
        return Bounds(
            x=0,
            y=-4,
            width=self._get_end(-4j, self.radius + 4).real,
            height=self._get_end(8j, self.radius - 4).imag,
        )

    def draw(self, cr: cairo.Context, drawing_options: DrawingOptions):
        if self.direction == CurveDirection.left:
            cy = -self.radius
            angle1, angle2 = math.pi / 2 - math.tau / self.per_circle, math.pi / 2
        else:
            cy = self.radius
            angle1, angle2 = -math.pi / 2, math.tau / self.per_circle - math.pi / 2

        cr.save()

        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.move_to(0, cy)
        cr.arc(0, cy, self.radius + 5, angle1, angle2)
        cr.line_to(0, cy)
        cr.clip()

        for i in range(0, self.sleepers + 1):
            angle = (math.tau / self.per_circle) * (i / self.sleepers)
            if self.direction == CurveDirection.left:
                angle = -math.pi / 2 - angle
            else:
                angle = angle + math.pi / 2
            cr.move_to(
                -math.cos(angle) * (self.radius - 4),
                cy - math.sin(angle) * (self.radius - 4),
            )
            cr.line_to(
                -math.cos(angle) * (self.radius + 4),
                cy - math.sin(angle) * (self.radius + 4),
            )

        cr.set_line_width(2)
        cr.set_source_rgb(*drawing_options.sleeper_color)
        cr.stroke()

        cr.set_line_width(1)
        cr.set_source_rgb(*drawing_options.rail_color)
        cr.arc(0, cy, self.radius - 2.5, angle1, angle2)
        cr.stroke()
        cr.arc(0, cy, self.radius + 2.5, angle1, angle2)
        cr.stroke()

        cr.restore()

    def relative_positions(self):
        rotate = math.tau / self.per_circle
        x = (cmath.rect(self.radius, rotate) - self.radius) * cmath.rect(
            1, -math.pi / 2
        )
        flip = -1 if self.direction == CurveDirection.left else 1
        return {
            **super().relative_positions(),
            "out": Position(x.real, x.imag * flip, rotate * flip),
        }

    def point_position(self, in_anchor, offset):
        theta = offset / self.radius
        if in_anchor == "out":
            theta = math.tau / self.per_circle - theta
        x = (cmath.rect(self.radius, theta) - self.radius) * cmath.rect(1, -math.pi / 2)
        flip = -1 if self.direction == CurveDirection.left else 1
        return x.real, x.imag * flip, theta * flip

    # @classmethod
    # def cast_yaml_data(cls, layout, data):
    #     return {
    #         'direction': CurveDirection(data.pop('direction', 'left')),
    #         **super().cast_yaml_data(layout, data),
    #     }


# Standard radius curves


class Curve(BaseCurve):
    radius = 40
    per_circle = 16
    sleepers = 4
    label = "curve"


class HalfCurve(BaseCurve):
    radius = 40
    per_circle = 32
    sleepers = 2
    label = "half-curve"


# Other radius curves


class R24Curve(BaseCurve):
    radius = 24
    per_circle = 16
    sleepers = 2
    label = "R24 curve"


class R32Curve(BaseCurve):
    radius = 32
    per_circle = 16
    sleepers = 3
    label = "R32 curve"


class R56Curve(BaseCurve):
    radius = 56
    per_circle = 16
    sleepers = 5
    label = "R56 curve"


class R72Curve(BaseCurve):
    radius = 72
    per_circle = 32
    sleepers = 4
    label = "R72 curve"


class R88Curve(BaseCurve):
    radius = 88
    per_circle = 32
    sleepers = 4
    label = "R88 curve"


class R104Curve(BaseCurve):
    radius = 104
    per_circle = 32
    sleepers = 5
    label = "R104 curve"


class R120Curve(BaseCurve):
    radius = 120
    per_circle = 32
    sleepers = 6
    label = "R120 curve"
