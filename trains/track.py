from __future__ import annotations

import collections
import math
from numbers import Number
from typing import Dict, Tuple, TYPE_CHECKING

import cairo
import cmath
import uuid

if TYPE_CHECKING:
    from trains.pieces import Piece

from trains.registry_meta import WithRegistry


class Position(collections.namedtuple('Position', ('x', 'y', 'angle'))):
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

Bounds = collections.namedtuple('Bounds', ('x', 'y', 'width', 'height'))


class Anchor(dict):
    """A connection between two track pieces.

    An anchor is a dict of (piece: anchor_name) mappings. i.e. if a Points branch is connected to the right anchor of a
    crossover, the anchor is `{<Points …>: "branch", <Crossover …>: "right"}`.

    An anchor can only connect two pieces of track, and two anchors can be connected together by in-place addition, e.g.
    `anchor_1 += anchor_2`.
    """
    def __init__(self, *args, id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id or str(uuid.uuid4())

    def __setitem__(self, key, value):
        assert key in self or len(self) < 2
        super().__setitem__(key, value)

    def __iadd__(self, other):
        assert len(self) == 1 and len(other) == 1  # Neither anchor is already connected
        assert set(self) != set(other)  # The anchors aren't on the same piece of track

        # Unpack each anchor to find their pieces
        piece: Piece
        other_piece: Piece
        (piece,), (other_piece,) = self, other

        for track_piece, anchor_name in other.items():
            track_piece.anchors[anchor_name] = self
        self.update(other)

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

    def split(self, new_side: Piece):
        """Breaks an anchor in two if it is connected.

        The new_side piece gets a new anchor created, with new_side removed from the existing anchor. This means that
        `piece.anchors['out'] = piece.anchors['out'].split(piece)` will disconnect a piece from another through the
        out anchor. If it's not connected, this statement is a no-op.
        """
        if len(self) == 2:
            anchor_name = self.pop(new_side)

            # TODO: Make sure there's a placement on either side if the connected subset is broken

            return Anchor({new_side: anchor_name})
        elif len(self) == 1:
            return self
        else:
            raise AssertionError

