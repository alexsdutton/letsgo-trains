from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple, TYPE_CHECKING


import cairo
import math
from letsgo.registry_meta import WithRegistry

if TYPE_CHECKING:
    from letsgo.train import Train

from letsgo import signals

if TYPE_CHECKING:
    from cairo import Context
    from letsgo.layout import Layout
    from letsgo.drawing_options import DrawingOptions

from letsgo.track import Anchor, Bounds, Position


class Piece(WithRegistry):
    """Base class for all track pieces.

    Each non-abstract subclass should be registered with a ``letsgo.piece`` entry point.
    """

    entrypoint_group = "letsgo.piece"

    anchor_names: Tuple[str, ...]
    layout_priority = float("inf")

    def __init__(
        self, placement: Position = None, anchors: Dict[str, str] = None, **kwargs
    ):
        super().__init__(**kwargs)
        anchors = anchors or {}

        self.anchors: Dict[str, Anchor] = {
            anchor_name: Anchor({self: anchor_name}, id=anchors.get(anchor_name))
            for anchor_name in self.anchor_names
        }

        # Instance variables related to piece placement and position
        self._placement = placement
        """An explicit placement of this piece"""
        self._placement_origin = self if placement else None
        """The piece controlling the placement of this connected subset of the network"""
        self._position: Optional[Position] = None
        self.position = placement

        self.claimed_by = None
        self.reservations: Dict[Train, Dict] = {}

    @property
    def placement(self) -> Optional[Position]:
        return self._placement

    @placement.setter
    def placement(self, value: Optional[Position]):
        assert self.layout

        if value == self._placement:
            return

        self._placement = value
        self.update_connected_subset_positions()
        self.layout.changed()

    @property
    def position(self) -> Optional[Position]:
        """The inferred position of this piece"""
        return self._position

    @position.setter
    def position(self, value: Optional[Position]):
        old_value = self._position
        self._position = value
        relative_positions = self.relative_positions()
        for anchor_name, anchor in self.anchors.items():
            anchor.position = self.position + relative_positions[anchor_name]

        if value != old_value and self.layout:
            self.layout.piece_positioned(self)

    @property
    def placement_origin(self) -> Optional[Piece]:
        return self._placement_origin

    def update_connected_subset_positions(self):
        connected_subset_pieces = set()
        changed = False
        for piece, position in self.traverse_connected_subset(self._placement):
            if piece.position != position:
                piece.position = position
                changed = True
            piece._placement_origin = self
            if piece != self:
                piece._placement = None
            connected_subset_pieces.add(piece)
        if changed and self.layout:
            self.layout.changed()
        return connected_subset_pieces

    def traverse_connected_subset(
        self, starting_position: Position = None
    ) -> Iterable[Tuple[Piece, Optional[Position]]]:
        seen_pieces = {self}
        stack = [(self, starting_position)]
        while stack:
            piece, position = stack.pop()
            yield piece, position
            relative_positions = piece.relative_positions()
            for anchor_name, relative_position in relative_positions.items():
                next_piece, next_anchor_name = piece.anchors[anchor_name].next(piece)
                if next_piece and next_piece not in seen_pieces:
                    if next_anchor_name != next_piece.anchor_names[0]:
                        relative_position -= next_piece.relative_positions()[
                            next_anchor_name
                        ]
                    next_position = position + relative_position
                    stack.append((next_piece, next_position))
                    seen_pieces.add(next_piece)

    def relative_positions(self) -> Dict[str, Position]:
        """Returns a mapping from anchor name to that anchor's relative position.

        The base implementation provides a relative position for the first anchor,
        which should always be backwards out from the piece position (i.e. x=0, y=0,
        theta=pi).

        Subclasses should override and extend this method to provide relative positions
        for other anchors. e.g., for a hypothetical 90° 40R curve piece:

        >>> def relative_positions(self):
        >>>     return {
        >>>         **super().relative_positions(),
        >>>         'out': Position(40, -40, math.pi / 2),
        >>>     }

        This method is used when calculating positions for connected pieces, starting
        from the placement origin (i.e. the piece in a connected subset which has
        `self.placement` set).
        """
        return {self.anchor_names[0]: Position(0, 0, math.pi)}

    def traversals(self, anchor_from: str) -> Dict[str, Tuple[float, bool]]:
        raise NotImplementedError

    def available_traversal(self, anchor_name):
        for anchor_name, (distance, available) in self.traversals(anchor_name).items():
            if available:
                return anchor_name, distance

    def bounds(self) -> Bounds:
        raise NotImplementedError

    def draw(self, cr: Context, drawing_options: DrawingOptions):
        raise NotImplementedError

    def point_position(
        self, in_anchor: str, offset: float, out_anchor: str = None
    ) -> Position:
        raise NotImplementedError

    @classmethod
    def get_icon_surface(cls, drawing_options: DrawingOptions):
        self = cls(layout=None)

        bounds = self.bounds()

        image = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            math.ceil(drawing_options.scale * bounds.width + 10),
            math.ceil(drawing_options.scale * bounds.height + 10),
        )
        cr = cairo.Context(image)
        cr.translate(5, 5)
        cr.scale(drawing_options.scale, drawing_options.scale)
        cr.translate(-bounds.x, -bounds.y)
        self.draw(cr, drawing_options)

        return image

    # @classmethod
    # def from_yaml(self, layout, data) -> Piece:
    #     anchors = data.pop('anchors')
    #     piece = super().from_yaml(layout, data)

    # @classmethod
    # def cast_yaml_data(cls, layout, data):
    #     return {
    #         'placement': Position(**data.pop('placement')) if 'placement' in data else None,
    #         **super().cast_yaml_data(layout, data),
    #     }

    def to_yaml(self) -> dict:
        data = {
            **super().to_yaml(),
            "anchors": {
                anchor_name: anchor.id
                for anchor_name, anchor in self.anchors.items()
                if len(anchor) == 2
            },
        }
        if self.placement:
            data["placement"] = self.placement.to_yaml()
        return data


class FlippablePiece(Piece):
    def flip(self: Piece) -> Piece:
        raise NotImplementedError
