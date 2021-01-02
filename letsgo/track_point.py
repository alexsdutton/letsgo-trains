import enum
from typing import Optional

from letsgo.pieces import Piece

from . import track
from .track import Position

_sentinel = object()


class EndOfTheLine(Exception):
    def __init__(self, piece, final_anchor_name, remaining_distance):
        self.piece, self.final_anchor_name, self.remaining_distance = (
            piece,
            final_anchor_name,
            remaining_distance,
        )


class TrackPoint:
    """A single point on a track layout"""

    def __init__(
        self,
        piece: Piece,
        in_anchor: str,
        out_anchor: str = None,
        offset: float = 0,
        branch_decisions=None,
        train=None,
    ):
        self.piece = piece
        self.in_anchor = in_anchor
        self.out_anchor = out_anchor or piece.available_traversal(in_anchor)[0]
        self.offset = offset
        self.branch_decisions = branch_decisions or {}
        """Intended to be used for backtracking

        This is so we know which way we came through points when there were multiple
        options."""
        self.train = train

    def to_yaml(self):
        return {
            "piece_id": self.piece.id,
            "in_anchor": self.in_anchor,
            "out_anchor": self.out_anchor,
            "offset": self.offset,
        }

    @property
    def position(self) -> Optional[Position]:
        if self.piece.position:
            return self.piece.position + self.piece.point_position(
                in_anchor=self.in_anchor, out_anchor=self.out_anchor, offset=self.offset
            )

    def next_piece(self, distance=0, use_branch_decisions=False):
        anchor_distance = self.piece.traversals(self.in_anchor)[self.out_anchor][0]
        next_piece, next_in_anchor = self.piece.anchors[self.out_anchor].next(
            self.piece
        )
        return (
            TrackPoint(
                piece=next_piece,
                in_anchor=next_in_anchor,
                offset=0,
                train=self.train,
                branch_decisions=self.branch_decisions,
            ),
            anchor_distance + distance,
        )

    def _get_traversal(self, piece, anchor_name, use_branch_decisions):
        if use_branch_decisions and (piece, anchor_name) in self.branch_decisions:
            return self.branch_decisions[(piece, anchor_name)]
        else:
            out_anchor_name, anchor_distance = piece.available_traversal(anchor_name)
            self.branch_decisions[(piece, out_anchor_name)] = (
                anchor_name,
                anchor_distance,
            )
            return out_anchor_name, anchor_distance

    def _add(self, piece, in_anchor, out_anchor, offset, use_branch_decisions=False):
        out_anchor_name, anchor_distance = self._get_traversal(
            piece, in_anchor, use_branch_decisions
        )
        while offset > anchor_distance:
            next_piece, in_anchor = piece.anchors[out_anchor_name].next(piece)
            offset -= anchor_distance
            if not next_piece:
                raise EndOfTheLine(piece, out_anchor_name, offset)
            else:
                piece = next_piece
                out_anchor_name, anchor_distance = self._get_traversal(
                    piece, in_anchor, use_branch_decisions
                )
        return piece, in_anchor, None, offset

    def copy(self, train=_sentinel):
        return type(self)(
            piece=self.piece,
            in_anchor=self.in_anchor,
            out_anchor=self.out_anchor,
            offset=self.offset,
            branch_decisions=self.branch_decisions,
            train=self.train if train == _sentinel else train,
        )

    def reversed(self):
        anchor_name, anchor_distance = self._get_traversal(
            self.piece, self.in_anchor, True
        )
        return TrackPoint(
            piece=self.piece,
            anchor_name=anchor_name,
            offset=anchor_distance,
            train=self.train,
            branch_decisions=self.branch_decisions.copy(),
        )

    def __add__(self, distance):
        return TrackPoint(
            *self._add(
                self.piece, self.in_anchor, self.out_anchor, self.offset + distance
            ),
            branch_decisions=self.branch_decisions.copy(),
        )

    def __iadd__(self, distance):
        self.piece, self.in_anchor, self.out_anchor, self.offset = self._add(
            self.piece, self.in_anchor, self.out_anchor, self.offset + distance
        )
        return self

    def _sub(self, piece, in_anchor, offset):
        in_anchor, anchor_distance = self._get_traversal(piece, in_anchor, True)
        piece, in_anchor, out_anchor, offset = self._add(
            piece, in_anchor, anchor_distance + offset, True
        )
        anchor_name, anchor_distance = self._get_traversal(piece, in_anchor, True)
        return piece, in_anchor, None, anchor_distance - offset

    def __sub__(self, distance):
        return TrackPoint(
            *self._sub(self.piece, self.in_anchor, distance - self.offset),
            branch_decisions=self.branch_decisions.copy(),
            train=self.train,
        )

    def __isub__(self, distance):
        self.piece, self.in_anchor, self.out_anchor, self.offset = self._sub(
            self.piece, self.in_anchor, distance - self.offset
        )
        return self

    def __str__(self):
        return (
            f"TrackPoint({self.piece} {self.in_anchor} {self.out_anchor} {self.offset})"
        )

    def distance_to(self, other, maximum_distance=1000):
        distance = 0
        position = self.copy()
        while (
            not (
                position.piece == other.piece
                and position.anchor_name == other.anchor_name
            )
            and distance < maximum_distance
        ):
            position, distance = position.next_piece(distance)
        distance += other.offset - position.offset
        if distance < maximum_distance:
            return distance
