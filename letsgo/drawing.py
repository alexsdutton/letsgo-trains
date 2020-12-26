import cmath
import enum
import math
import os
from typing import Tuple

from cairosvg import svg2png
from lxml import builder, etree

from letsgo.track import Position

SVG = builder.ElementMaker(
    namespace="http://www.w3.org/2000/svg", nsmap={None: "http://www.w3.org/2000/svg"}
)


def hex_to_rgb(value) -> Tuple[float, float, float]:
    return (
        int(value[1:3], 16) / 255,
        int(value[3:5], 16) / 255,
        int(value[5:7], 16) / 255,
    )


class Colors(enum.Enum):
    dark_bluish_gray = "#5B6770"
    tan = "#aaaaaa"
    red = "#ffaaaa"

    @property
    def rgb(self) -> Tuple[float, float, float]:
        return hex_to_rgb(self.value)
