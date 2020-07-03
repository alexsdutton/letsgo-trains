from typing import Dict, Type
from pkg_resources import iter_entry_points

from .base import Piece, FlippablePiece
from .straight import Straight, HalfStraight, QuarterStraight
from .curve import (
    Curve,
    HalfCurve,
    R24Curve,
    R32Curve,
    R56Curve,
    R72Curve,
    R88Curve,
    R104Curve,
    R120Curve,
)
from .points import LeftPoints, RightPoints
from .crossover import Crossover, ShortCrossover

piece_classes: Dict[str, Type[Piece]] = {
    ep.name: ep.load() for ep in iter_entry_points("letsgo.piece")
}
