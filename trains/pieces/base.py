from __future__ import annotations

import uuid
from numbers import Number
from typing import Dict, Tuple, TYPE_CHECKING

import typing

import cairo
import math

if TYPE_CHECKING:
    from cairo import Context
    from trains.layout import Layout
    from trains.drawing_options import DrawingOptions

from trains.track import Anchor, Bounds, Position


class Piece:
    anchor_names = ()
    layout_priority = float('inf')

    def __init__(self, layout: Layout = None, placement: Position = None, id: str = None):
        self.anchors = {anchor_name: Anchor({self: anchor_name})
                        for anchor_name in self.anchor_names}
        self._placement = placement
        self.claimed_by = None
        self.reservations = {}

        self.id = id or str(uuid.uuid4())
        self.layout = layout
        if self.layout:
            if self.layout.by_id.get(self.id) not in (None, self):
                raise AssertionError("Can't reuse an ID for a new object")
            self.layout.by_id[self.id] = self

    @property
    def placement(self) -> Position:
        return self._placement

    @placement.setter
    def placement(self, value: Position):
        if value != self._placement:
            self._placement = value
            self.layout.changed()

    def traversals(self, anchor_from: str) -> Dict[str, Tuple[Number, bool]]:
        raise NotImplementedError

    def available_traversal(self, anchor_name):
        for anchor_name, (distance, available) in self.traversals(anchor_name).items():
            if available:
                return anchor_name, distance

    def bounds(self) -> Bounds:
        raise NotImplementedError

    def draw(self, cr: Context, drawing_options: DrawingOptions):
        raise NotImplementedError

    @classmethod
    def get_icon_surface(cls, drawing_options: DrawingOptions):
        self = cls()

        bounds = self.bounds()

        image = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                   math.ceil(drawing_options.scale * bounds.width + 10),
                                   math.ceil(drawing_options.scale * bounds.height + 10))
        cr = cairo.Context(image)
        cr.translate(5, 5)
        cr.scale(drawing_options.scale, drawing_options.scale)
        cr.translate(-bounds.x, -bounds.y)
        self.draw(cr, drawing_options)

        return image
