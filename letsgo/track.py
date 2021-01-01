from __future__ import annotations

import collections
import math
import uuid
import weakref
from typing import Dict, Optional, TYPE_CHECKING

import cairo

if TYPE_CHECKING:
    from letsgo.pieces import Piece


class Position:
    def __init__(self, x: float, y: float, angle: float):
        self.x = x
        self.y = y
        self.angle = angle

    def __iter__(self):
        return iter((self.x, self.y, self.angle))

    @classmethod
    def from_matrix(cls, matrix: cairo.Matrix):
        return cls(matrix.x0, matrix.y0, math.atan2(-matrix.xy, matrix.xx))

    def as_matrix(self) -> cairo.Matrix:
        return cairo.Matrix(
            xx=math.cos(self.angle),
            yx=-math.sin(self.angle),
            xy=math.sin(self.angle),
            yy=math.cos(self.angle),
            x0=self.x,
            y0=self.y,
        )

    def __add__(self, other: Position):
        return Position(
            self.x + math.cos(self.angle) * other.x - math.sin(self.angle) * other.y,
            self.y + math.sin(self.angle) * other.x + math.cos(self.angle) * other.y,
            (self.angle + other.angle) % math.tau,
        )

    def __radd__(self, other):
        # Adding anything to an unknown position results in an unknown position
        if other is None:
            return None
        else:
            return NotImplemented

    def __sub__(self, other: Position):
        angle = (self.angle - other.angle - math.pi) % math.tau
        return Position(
            self.x - math.cos(angle) * other.x + math.sin(angle) * other.y,
            self.y - math.sin(angle) * other.x - math.cos(angle) * other.y,
            angle,
        )

    def to_yaml(self):
        return {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
        }

    def angle_is_opposite(self, other: Position):
        r = (self.angle - other.angle - math.pi) % math.tau
        if r >= math.pi:
            r -= math.tau
        return abs(r) < 0.001


Bounds = collections.namedtuple("Bounds", ("x", "y", "width", "height"))


class Anchor(dict):
    """A connection between two track pieces.

    An anchor is a dict of (piece: anchor_name) mappings. i.e. if a Points branch is connected to the right anchor of a
    crossover, the anchor is `{<Points …>: "branch", <Crossover …>: "right"}`.

    An anchor can only connect two pieces of track, and two anchors can be connected together by in-place addition, e.g.
    `anchor_1 += anchor_2`.
    """

    def __init__(self, initial: Dict[Piece, str], id=None, **kwargs):
        super().__init__(initial)
        # self.layout = layout
        self.id = id or str(uuid.uuid4())
        self.position: Optional[Position] = None
        self.subsumes: weakref.WeakSet[Anchor] = weakref.WeakSet()
        # if self._position:
        #     signals.anchor_p

    def __setitem__(self, key: Piece, value: str):
        assert key in self or len(self) < 2
        super().__setitem__(key, value)

    def __iadd__(self, other):
        assert len(self) == 1 and len(other) == 1  # Neither anchor is already connected
        assert set(self) != set(other)  # The anchors aren't on the same piece of track

        # Unpack each anchor to find their pieces
        piece: Piece
        other_piece: Piece
        (piece,), (other_piece,) = self, other

        assert piece.layout == other_piece.layout

        for track_piece, anchor_name in other.items():
            track_piece.anchors[anchor_name] = self
        self.update(other)

        other.position = None
        other_piece.layout.anchor_positioned(other)

        if piece.placement_origin != other_piece.placement_origin:
            if other_piece.placement_origin:
                if piece.placement_origin:
                    piece.placement_origin._placement = None
                other_piece.placement_origin.update_connected_subset_positions()
            elif piece.placement_origin:
                piece.placement_origin.update_connected_subset_positions()

        return self

    def __hash__(self):
        # All anchors are unique
        return id(self)

    def next(self, piece):
        """Return the piece other than `piece` connected at this anchor"""
        for other_piece, anchor_name in self.items():
            if piece != other_piece:
                return other_piece, anchor_name
        else:
            return None, None

    def bounds(self):
        # An anchor is a point
        return Bounds(0, 0, 0, 0)

    def split(self) -> Optional[Anchor]:
        """Breaks an anchor in two if it is connected.

        The new_side piece gets a new anchor created, with new_side removed from the existing anchor. This means that
        `piece.anchors['out'] = piece.anchors['out'].split(piece)` will disconnect a piece from another through the
        out anchor. If it's not connected, this statement is a no-op.
        """
        if len(self) == 2:
            other_piece, other_anchor_name = self.popitem()
            (piece,) = self

            other_anchor = Anchor({other_piece: other_anchor_name})
            other_piece.anchors[other_anchor_name] = other_anchor

            piece.layout.anchors[other_anchor.id] = other_anchor

            updated_pieces = (
                other_piece.placement_origin.update_connected_subset_positions()
            )

            if piece not in updated_pieces:
                piece.placement = piece.position
            elif other_piece not in updated_pieces:
                other_piece.placement = other_piece.position
            if other_piece.position:
                other_anchor.position = (
                    other_piece.position
                    + other_piece.relative_positions()[other_anchor_name]
                )
            other_piece.layout.anchor_positioned(other_anchor)

            return other_anchor
        elif len(self) == 1:
            return None
        else:
            raise AssertionError
