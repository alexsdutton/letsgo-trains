import cairo
import cmath
import math

from letsgo.drawing_options import DrawingOptions
from .base import Piece
from letsgo.track import Bounds, Position


def _bezier(xy1, xy2, xy3, t):
    (x1, y1), (x2, y2), (x3, y3) = xy1, xy2, xy3
    return (
        3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3 * x3,
        3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3 * y3,
    )


def _distance(xy1, xy2):
    (x1, y1), (x2, y2) = xy1, xy2
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


class BasePoints(Piece):
    anchor_names = ("in", "out", "branch")
    layout_priority = 30

    def __init__(self, state: str = "out", **kwargs):
        self.state = state

        branch_point = cmath.rect(40, math.tau * 5 / 16) + 48 - 24j
        self.branch_point = branch_point.real, branch_point.imag * self.flip

        # Bezier curve control points for the branch
        self.control_points = [
            (16, 0),
            (
                self.branch_point[0] - math.sin(math.tau * 5 / 16) * 16,
                self.branch_point[1] + (math.cos(math.tau * 5 / 16) * 16) * self.flip,
            ),
        ]

        intermediate_branch_point_count = 1000
        intermediate_branch_lengths = []
        branch_length = 0
        for i in range(1, intermediate_branch_point_count + 1):
            branch_length += _distance(
                self.branch_bezier(i / intermediate_branch_point_count),
                self.branch_bezier((i + 1) / intermediate_branch_point_count),
            )
            intermediate_branch_lengths.append(branch_length)

        self.branch_length = branch_length

        self.intermediate_branch_t = [0.0]
        for i in range(1, intermediate_branch_point_count):
            t = i / intermediate_branch_point_count
            x, y = intermediate_branch_lengths[i - 1 : i + 1]
            if (
                intermediate_branch_lengths[i - 1]
                < self.branch_length * len(self.intermediate_branch_t) / 100
                <= intermediate_branch_lengths[i]
            ):
                self.intermediate_branch_t.append(t)

        super().__init__(**kwargs)

    def branch_bezier(self, t):
        return _bezier(*self.control_points, self.branch_point, t)

    def traversals(self, anchor_from):
        traversals = {}
        if anchor_from == "in":
            return {
                "out": (32, self.state == "out"),
                "branch": (self.branch_length, self.state == "branch"),
            }
        elif anchor_from == "out":
            return {"in": (32, True)}
        elif anchor_from == "branch":
            return {"in": (self.branch_length, True)}

    # Drawing

    @property
    def flip(self):
        return -1 if self.direction == "left" else 1

    def bounds(self):
        width = self.branch_point[0] + 4 * math.sin(math.pi / 8)
        height = abs(self.branch_point[1]) + 4 * math.cos(math.pi / 8) + 4
        return Bounds(
            x=0,
            y=4 - height if self.direction == "left" else -4,
            width=width,
            height=height,
        )

    def draw(self, cr: cairo.Context, drawing_options: DrawingOptions):
        cr.set_source_rgb(*drawing_options.sleeper_color)
        cr.set_line_width(2)

        # Main sleepers
        cr.save()
        cr.move_to(0, 0)
        cr.line_to(25, 4 * self.flip)
        cr.line_to(32, 4 * self.flip)
        cr.line_to(32, -4 * self.flip)
        cr.line_to(0, -4 * self.flip)
        cr.close_path()
        cr.clip()

        for i in range(0, 36, 4):
            cr.move_to(i, -4)
            cr.line_to(i, 4)
        cr.stroke()
        cr.restore()

        # Branch sleepers
        cr.save()
        cr.move_to(0, 0)
        cr.line_to(25, 4 * self.flip)
        cr.line_to(32, 4 * self.flip)
        cr.line_to(40, 4 * self.flip)
        cr.line_to(40, 32 * self.flip)
        cr.line_to(0, 32 * self.flip)
        cr.close_path()
        cr.clip()
        # cr.stroke()

        for i in range(0, 10):
            x, y, theta = self.point_position(
                "in", i / 9 * self.branch_length, out_anchor="branch"
            )
            theta += -math.pi / 2
            x_off, y_off = math.cos(theta) * 4, math.sin(theta) * 4
            cr.move_to(x + x_off, y + y_off)
            cr.line_to(x - x_off, y - y_off)

        cr.stroke()

        cr.restore()

        if self.state == "out":
            rail_draw_order = ("branch", "out")
        else:
            rail_draw_order = ("out", "branch")

        cr.save()

        mask = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            math.ceil(40 * drawing_options.scale),
            math.ceil(80 * drawing_options.scale),
        )
        mask_cr = cairo.Context(mask)
        mask_cr.scale(drawing_options.scale, drawing_options.scale)
        mask_cr.translate(0, 40)
        mask_cr.set_source_rgb(0, 1, 0)

        # mask_cr.rectangle(0, 0, 100, 100)

        i = 0
        mask.write_to_png(f"/home/alex/mask-{i:03d}.png")

        for anchor_name in rail_draw_order:
            self.draw_rails_path(mask_cr, anchor_name)

            mask_cr.set_operator(cairo.OPERATOR_CLEAR)
            mask_cr.set_line_width(8)
            mask_cr.stroke_preserve()

            mask_cr.set_operator(cairo.OPERATOR_SOURCE)
            mask_cr.set_line_width(6)
            mask_cr.stroke_preserve()

            mask_cr.set_operator(cairo.OPERATOR_CLEAR)
            mask_cr.set_line_width(4)
            mask_cr.stroke()

        cr.set_source_rgb(*drawing_options.rail_color)

        cr.scale(1 / drawing_options.scale, 1 / drawing_options.scale)
        cr.mask_surface(mask, 0, -40 * drawing_options.scale)

        cr.restore()

    def draw_rails_path(self, cr: cairo.Context, anchor_name: str):
        """Creates a path for the rails from anchor 'in' to the given anchor name"""
        cr.move_to(0, 0)
        if anchor_name == "out":
            # For some reason line_to doesn't play nice with cairo.OPERATOR_CLEAR
            # cr.line_to(32, 0)
            cr.curve_to(1, 0, 31, 0, 32, 0)
        elif anchor_name == "branch":
            cr.curve_to(
                *self.control_points[0], *self.control_points[1], *self.branch_point
            )
        else:
            raise AssertionError

    def relative_positions(self):
        return {
            **super().relative_positions(),
            "out": Position(32, 0, 0),
            "branch": Position(*self.branch_point, math.tau / 16 * self.flip),
        }

    def point_position(self, in_anchor, offset, out_anchor=None):
        out_anchor = out_anchor or self.state

        if in_anchor == "in" and out_anchor == "out":
            return offset, 0, 0
        if in_anchor == "in" and out_anchor == "branch":
            t = self.intermediate_branch_t[
                max(0, min(int(offset / self.branch_length * 100), 99))
            ]
            x, y = self.branch_bezier(t)

            x1, y1 = self.branch_bezier(t - 1e-6)
            x2, y2 = self.branch_bezier(t + 1e-6)
            theta = math.atan2(y2 - y1, x2 - x1)

            return x, y, theta
        if in_anchor == "branch":
            t = self.intermediate_branch_t[
                max(0, min(99 - int(offset / self.branch_length * 100), 99))
            ]
            x, y = self.branch_bezier(t)

            x1, y1 = self.branch_bezier(t - 1e-6)
            x2, y2 = self.branch_bezier(t + 1e-6)
            theta = math.atan2(y2 - y1, x2 - x1)

            return x, y, theta
        if in_anchor == "out":
            return 32 - offset, 0, math.pi


class LeftPoints(BasePoints):
    direction = "left"
    label = "points (left)"


class RightPoints(BasePoints):
    direction = "right"
    label = "points (right)"
