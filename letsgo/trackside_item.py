from typing import Optional

from cairo import Context

from letsgo.drawing_options import DrawingOptions
from letsgo.track import Bounds, Position
from letsgo.utils.quadtree import WithBounds


class TracksideItem:
    position: Optional[Position]

    def draw(self, cr: Context, drawing_options: DrawingOptions):
        raise NotImplementedError

    def bounds(self) -> Bounds:
        raise NotImplementedError
