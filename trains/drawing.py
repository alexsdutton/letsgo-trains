import cmath
import enum
import math
import os

from cairosvg import svg2png
from lxml import builder, etree

from trains.track import Position

SVG = builder.ElementMaker(namespace='http://www.w3.org/2000/svg',
                           nsmap={None: 'http://www.w3.org/2000/svg'})

class HexColors(enum.Enum):
    dark_bluish_gray = '#5B6770'
    tan = '#aaaaaa'

class Colors(enum.Enum):
    pass


def hex_to_rgb(value):
    return (int(value[1:3], 16) / 255,
            int(value[3:5], 16) / 255,
            int(value[5:7], 16) / 255)

for hc in HexColors:
    setattr(Colors, hc.name, hex_to_rgb(hc.value))


class DrawnPieceMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        if cls.name:
            cls.registry[cls.name] = cls
        return cls


class DrawnPiece(metaclass=DrawnPieceMeta):
    registry = {}
    name = None

    @classmethod
    def for_piece(cls, piece):
        return cls.registry[piece.registry_type](piece)

    def __init__(self, piece):
        self.piece = piece

    def get_base_color(self):
        return Colors.dark_bluish_gray
        if self.piece.claimed_by:
            return [v/2 for v in hex_to_rgb(self.piece.claimed_by.meta.get('color',  '#a0a0ff'))]
        elif self.piece.reservations:
            return 1, 0.5, 0
        else:
            return Colors.dark_bluish_gray


class DrawnStraight(DrawnPiece):
    name = 'straight'

    def bounds(self):
        return dict(x=0, y=-4, width=self.piece.length, height=8)

    def as_svg(self):
        width = str(self.piece.length)
        return SVG.g(
            # base
            SVG.rect(x="0", y="-4", width=width, height="8", fill=HexColors.dark_bluish_gray.value),
            # top rail
            SVG.rect(x="0", y="-3", width=width, height="1", fill=HexColors.tan.value),
            # bottom rail
            SVG.rect(x="0", y="2", width=width, height="1", fill=HexColors.tan.value),
        )

    def draw(self, cr):
        cr.set_line_width(8)
        cr.move_to(0, 0)
        cr.line_to(self.piece.length, 0)
        cr.set_source_rgb(*self.get_base_color())
        cr.stroke()
        cr.set_line_width(1)
        cr.set_source_rgb(*Colors.tan)

        cr.move_to(0, -2.5)
        cr.line_to(self.piece.length, -2.5)
        cr.stroke()
        cr.move_to(0, 2.5)
        cr.line_to(self.piece.length, 2.5)
        cr.stroke()

    def relative_positions(self):
        return {
            'out': Position(self.piece.length, 0, 0),
        }

    def point_position(self, in_anchor, offset):
        if in_anchor == 'in':
            return offset, 0, 0
        elif in_anchor == 'out':
            return self.piece.length - offset, 0, math.pi


class DrawnCrossover(DrawnPiece):
    name = 'crossover'

    def bounds(self):
        return dict(x=0, y=-8, width=16, height=16)

    def as_svg(self):
        return SVG.g(
            # base
            SVG.rect(x="0", y="-4", width="16", height="8", fill=HexColors.dark_bluish_gray.value),
            # cross
            SVG.rect(x="4", y="-8", width="8", height="16", fill=HexColors.dark_bluish_gray.value),
            # top rail
            SVG.rect(x="0", y="-3", width="16", height="1", fill=HexColors.tan.value),
            # bottom rail
            SVG.rect(x="0", y="2", width="16", height="1", fill=HexColors.tan.value),
            # left rail
            SVG.rect(x="5", y="-8", width="1", height="16", fill=HexColors.tan.value),
            # right rail
            SVG.rect(x="10", y="-8", width="1", height="16", fill=HexColors.tan.value),
        )

    def draw(self, cr):
        cr.set_line_width(8)
        cr.set_source_rgb(*self.get_base_color())

        cr.move_to(0, 0)
        cr.line_to(self.piece.length, 0)
        cr.stroke()
        cr.move_to(self.piece.length / 2, - self.piece.length / 2)
        cr.line_to(self.piece.length / 2, self.piece.length / 2)
        cr.stroke()

        cr.set_line_width(1)
        cr.set_source_rgb(*Colors.tan)

        cr.move_to(0, -2.5)
        cr.line_to(self.piece.length, -2.5)
        cr.move_to(0, 2.5)
        cr.line_to(self.piece.length, 2.5)
        cr.move_to(5.5, -self.piece.length/2)
        cr.line_to(5.5, self.piece.length/2)
        cr.move_to(10.5, -self.piece.length/2)
        cr.line_to(10.5, self.piece.length/2)
        cr.stroke()

    def relative_positions(self):
        return {
            'out': Position(self.piece.length, 0, 0),
            'left': Position(self.piece.length / 2, -self.piece.length / 2, -math.pi / 2),
            'right': Position(self.piece.length / 2, self.piece.length / 2, math.pi / 2),
        }

    def point_position(self, in_anchor, offset):
        if in_anchor == 'in':
            return offset, 0, 0
        elif in_anchor == 'out':
            return self.piece.length - offset, 0, math.pi
        elif in_anchor == 'left':
            return self.piece.length / 2, self.piece.length / 2 - offset, - math.pi / 2
        elif in_anchor == 'right':
            return self.piece.length / 2, offset - self.piece.length / 2, math.pi / 2


class DrawnCurve(DrawnPiece):
    name = 'curve'

    def _get_end(self, offset, r):
        rotate = math.tau / self.piece.per_circle
        return offset + (cmath.rect(r, rotate) - r) * cmath.rect(1, -math.pi/2)

    def bounds(self):
        return dict(x=0, y=-4,
                    width=self._get_end(-4j, self.piece.radius + 4).real,
                    height=self._get_end(8j, self.piece.radius - 4).imag)

    def as_svg(self):
        radius, per_circle = self.piece.radius, self.piece.per_circle
        def get_end(offset, r):
            end = self._get_end(offset, r)
            return f'{end.real} {end.imag}'
        return SVG.g(
            # base
            SVG.path(
                d=f'M 0 0 A {radius} {radius} {360 / per_circle} 0 1 {get_end(0, radius)}',
                style=f'stroke: {HexColors.dark_bluish_gray.value}; stroke-width: 8; stroke-linecap: butt; fill: none',
            ),
            # top rail
            SVG.path(
                d=f'M 0 2.5 A {radius - 2.5} {radius - 2.5} {360 / per_circle} 0 1 {get_end(2.5j, radius - 2.5)}',
                style=f'stroke: {HexColors.tan.value}; stroke-width: 1; stroke-linecap: butt; fill: none',
            ),
            # bottom rail
            SVG.path(
                d=f'M 0 -2.5 A {radius + 2.5} {radius + 2.5} {360 / per_circle} 0 1 {get_end(-2.5j, radius + 2.5)}',
                style=f'stroke: {HexColors.tan.value}; stroke-width: 1; stroke-linecap: butt; fill: none',
            ),
        )

    def draw(self, cr):
        cr.set_line_width(8)
        cr.set_source_rgb(*self.get_base_color())

        if self.piece.direction == 'left':
            cy = - self.piece.radius
            angle1, angle2 = math.pi / 2 - math.tau / self.piece.per_circle, math.pi / 2
        else:
            cy = self.piece.radius
            angle1, angle2 = -math.pi / 2, math.tau / self.piece.per_circle - math.pi / 2

        cr.arc(0, cy, self.piece.radius, angle1, angle2)
        cr.stroke()

        cr.set_line_width(1)
        cr.set_source_rgb(*Colors.tan)
        cr.arc(0, cy, self.piece.radius-2.5, angle1, angle2)
        cr.stroke()
        cr.arc(0, cy, self.piece.radius+2.5, angle1, angle2)
        cr.stroke()

    def relative_positions(self):
        rotate = math.tau / self.piece.per_circle
        x = ((cmath.rect(self.piece.radius, rotate) - self.piece.radius) * cmath.rect(1, - math.pi/2))
        flip = -1 if self.piece.direction == 'left' else 1
        return {
            'out': Position(x.real, x.imag * flip, rotate * flip)
        }

    def point_position(self, in_anchor, offset):
        theta = offset / self.piece.radius
        if in_anchor == 'out':
            theta = math.tau / self.piece.per_circle - theta
        x = ((cmath.rect(self.piece.radius, theta) - self.piece.radius) * cmath.rect(1, - math.pi/2))
        flip = -1 if self.piece.direction == 'left' else 1
        return x.real, x.imag * flip, theta * flip


class Points(DrawnPiece):
    name = 'points'

    @property
    def flip(self):
        return -1 if self.piece.direction == 'left' else 1

    def draw(self, cr):
        if self.piece.state == 'out':
            self.draw_branch_rails(cr)
            self.draw_out_rails(cr)
        else:
            self.draw_out_rails(cr)
            self.draw_branch_rails(cr)

    def draw_branch_rails(self, cr):
        cr.move_to(0, 0)
        cr.curve_to(16, 0, 12, 3.4 * self.flip, 33, 13 * self.flip)

        cr.set_line_width(8)
        cr.set_source_rgb(*self.get_base_color())
        cr.stroke_preserve()

        cr.set_line_width(6)
        cr.set_source_rgb(*Colors.tan)
        cr.stroke_preserve()

        cr.set_line_width(4)
        cr.set_source_rgb(*self.get_base_color())
        cr.stroke()

    def draw_out_rails(self, cr):
        cr.move_to(0, 0)
        cr.line_to(32, 0)

        cr.set_line_width(8)
        cr.set_source_rgb(*self.get_base_color())
        cr.stroke_preserve()

        cr.set_line_width(6)
        cr.set_source_rgb(*Colors.tan)
        cr.stroke_preserve()

        cr.set_line_width(4)
        cr.set_source_rgb(*self.get_base_color())
        cr.stroke()

    def relative_positions(self):
        return {
            'out': Position(32, 0, 0),
            'branch': Position(self.piece.branch_point[0],
                               self.piece.branch_point[1] * self.flip,
                               math.tau / 16 * self.flip),
        }

    def point_position(self, in_anchor, offset):
        if in_anchor == 'in' and self.piece.state == 'out':
            return offset, 0, 0
        if in_anchor == 'in' and self.piece.state == 'branch':
            flip = -1 if self.piece.direction == 'left' else 1
            t = self.piece.intermediate_branch_t[max(0, min(int(offset / self.piece.branch_length * 100), 99))]
            x, y = self.piece.branch_bezier(t)
            # TODO: We return NaN for the angle because it's too much hassle to work out the actual angle, and our
            #       assumption is that no one will actually need to know the angle of the track on the branch. If we
            #       wanted to do this properly we would calculate the angle between branch_bezier(t-epsilon) and
            #       branch_bezier(t+epsilon).
            return x, y * flip, float('nan')
        if in_anchor == 'branch':
            flip = -1 if self.piece.direction == 'left' else 1
            t = self.piece.intermediate_branch_t[max(0, min(99 - int(offset / self.piece.branch_length * 100), 99))]
            x, y = self.piece.branch_bezier(t)
            # TODO: See above
            return x, y * flip, float('nan')
        if in_anchor == 'out':
            return 32 - offset, 0, math.pi

#
# border = 2
# max_width = max(drawn_piece().bounds()['width'] for drawn_piece in DrawnPiece.registry.values())
# max_height = max(drawn_piece().bounds()['height'] for drawn_piece in DrawnPiece.registry.values())
# max_dimension = max(max_height, max_width) + 2 * border
#
#
# for drawn_piece in DrawnPiece.registry.values():
#     dp = drawn_piece()
#     bounds = dp.bounds()
#     centre_x = bounds['x'] + bounds['width'] / 2
#     centre_y = bounds['y'] + bounds['height'] / 2
#
#     svg = SVG.svg(
#         drawn_piece().as_svg(),
#         viewBox=f'{centre_x - max_dimension / 2} {centre_y - max_dimension / 2} {max_dimension} {max_dimension}',
#     width='256', height='256')
#     svg_string = etree.tostring(svg)
#
#     with open(os.path.join(os.path.dirname(__file__), 'data', 'pieces', drawn_piece.name + ".svg"), 'wb') as f:
#         f.write(svg_string)
#
#     with open(os.path.join(os.path.dirname(__file__), 'data', 'pieces', drawn_piece.name + ".png"), 'wb') as f:
#         svg2png(svg_string, file_obj=f)
#     svg2png(svg_string, write_to=os.path.join(os.path.dirname(__file__), 'data', 'pieces', drawn_piece.name + ".png"))


#print(etree.tostring(curve()))