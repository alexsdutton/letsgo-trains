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
    red = '#ffaaaa'

class Colors(enum.Enum):
    pass


def hex_to_rgb(value):
    return (int(value[1:3], 16) / 255,
            int(value[3:5], 16) / 255,
            int(value[5:7], 16) / 255)

for hc in HexColors:
    setattr(Colors, hc.name, hex_to_rgb(hc.value))
