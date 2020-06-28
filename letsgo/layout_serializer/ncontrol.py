import functools
import xml.etree.ElementTree
from typing import Type

import math

from letsgo.layout_serializer import LayoutSerializer
from letsgo.pieces.curve import Curve, CurveDirection

from letsgo.track import Position

from letsgo.pieces import LeftPoints, Piece, RightPoints, Straight, piece_classes

from letsgo.layout import Layout


class NControlLayoutSerializer(LayoutSerializer):
    name = "nControl"
    file_extension = ".ncp"

    piece_mapping = {
        "TS_STRAIGHT": Straight,
        "TS_LEFTSWITCH": LeftPoints,
        "TS_RIGHTSWITCH": RightPoints,
        "TS_CURVE": Curve,
    }

    piece_params = {
        "TS_CURVE": {"direction": CurveDirection.right},
    }

    # anchor_name_mapping = {
    #     # nControl curves go the other way to ours
    #     'TS_CURVE': ('out', 'in')
    # }

    def serialize(self, fp, layout: Layout):
        pass
