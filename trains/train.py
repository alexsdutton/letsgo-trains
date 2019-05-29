import uuid
from numbers import Number
from typing import Optional, List

from trains.train_controller import TrainController
from . import track


class EndOfTheLine(Exception):
    def __init__(self, piece, final_anchor_name, remaining_distance):
        self.piece, self.final_anchor_name, self.remaining_distance = piece, final_anchor_name, remaining_distance


class TrackPoint:
    """A single point on a track layout"""
    def __init__(self, piece: track.TrackPiece, anchor_name, offset=0):
        self.piece, self.anchor_name, self.offset = piece, anchor_name, offset

    def _add(self, piece, anchor_name, offset):
        out_anchor_name, anchor_distance = piece.available_traversal(anchor_name)
        while offset > anchor_distance:
            next_piece, anchor_name = piece.anchors[out_anchor_name].next(piece)
            offset -= anchor_distance
            if not next_piece:
                raise EndOfTheLine(piece, out_anchor_name, offset)
            else:
                piece = next_piece
                out_anchor_name, anchor_distance = piece.available_traversal(anchor_name)
        return piece, anchor_name, offset

    def __add__(self, distance):
        return TrackPoint(*self._add(self.piece, self.anchor_name, self.offset + distance))

    def __iadd__(self, distance):
        self.piece, self.anchor_name, self.offset = self._add(self.piece, self.anchor_name, self.offset + distance)
        return self

    def _sub(self, piece, anchor_name, offset):
        anchor_name, anchor_distance = piece.available_traversal(anchor_name)
        piece, anchor_name, offset = self._add(piece, anchor_name, anchor_distance + offset)
        anchor_name, anchor_distance = piece.available_traversal(anchor_name)
        return piece, anchor_name, anchor_distance - offset

    def __sub__(self, distance):
        return TrackPoint(*self._sub(self.piece, self.anchor_name, distance - self.offset))

    def __isub__(self, distance):
        self.piece, self.anchor_name, self.offset = self._sub(self.piece, self.anchor_name, distance - self.offset)
        return self

    def __str__(self):
        return f'TrackPoint({self.piece} {self.anchor_name} {self.offset})'


class Car:
    def __init__(self, length: Number, bogey_offsets: List[Number], nose='vestibule', tail='vestibule'):
        self.length = length
        self.bogey_offsets = bogey_offsets


class Train:
    def __init__(self,
                 cars: List[Car],
                 position: Optional[TrackPoint]=None,
                 meta: Optional[dict]=None,
                 id: str=None,
                 controller: TrainController=None):
        self.cars = cars
        self.position = position
        self.length = sum(car.length for car in cars) + 2 * (len(cars) - 1)
        self.rear_position = self.position - self.length
        self.rear_position -= 0
        self.meta = meta or {}
        self.id = id or str(uuid.uuid4())

    def move(self, distance):
        self.position += distance
        self.rear_position += distance