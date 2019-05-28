import collections
import cmath
import math
import uuid
from numbers import Number
from typing import Dict, Tuple


Position = collections.namedtuple('Position', ('x', 'y', 'angle'))


class Anchor(dict):
    def __init__(self, *args, id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id or str(uuid.uuid4())

    def __setitem__(self, key, value):
        assert key in self or len(self) < 2
        super().__setitem__(key, value)

    def __iadd__(self, other):
        # Neither anchor is already connected
        assert len(self) == 1 and len(other) == 1

        assert set(self) != set(other)
        for track_piece, anchor_name in other.items():
            track_piece.anchors[anchor_name] = self
        self.update(other)
        return self

    def next(self, piece):
        """Return the piece other than `piece` connected at this anchor"""
        for other_piece, anchor_name in self.items():
            if piece != other_piece:
                return other_piece, anchor_name
        else:
            return None, None


class TrackPieceMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        if cls.name:
            cls.registry[cls.name] = cls
        return cls


class TrackPiece(metaclass=TrackPieceMeta):
    registry = {}
    name = None
    anchor_names = ()
    placement = None

    def __init__(self, placement: dict=None, id: str=None):
        self.anchors = {anchor_name: Anchor({self: anchor_name})
                        for anchor_name in self.anchor_names}
        if placement:
            self.placement = Position(**placement)
        self.id = id or str(uuid.uuid4())

    def traversals(self, anchor_from: str) -> Dict[str, Tuple[Number, bool]]:
        return {}

    def available_traversal(self, anchor_name):
        for anchor_name, (distance, available) in self.traversals(anchor_name).items():
            if available:
                return anchor_name, distance


class Straight(TrackPiece):
    anchor_names = ('in', 'out')
    name = 'straight'
    label = 'straight'

    def __init__(self, length: int=16, **kwargs):
        self.length = length
        super().__init__(**kwargs)

    def traversals(self, anchor_from):
        return {'out' if anchor_from == 'in' else 'in': (self.length, True)}


class Curve(TrackPiece):
    anchor_names = ('in', 'out')
    name = 'curve'
    label = 'curve'
    ldraw_id = '53400'

    def __init__(self, radius: int=40, per_circle: int=16, direction: str='left', **kwargs):
        self.radius = radius
        self.per_circle = per_circle
        self.direction = direction
        super().__init__(**kwargs)

    def traversals(self, anchor_from):
        return {'out' if anchor_from == 'in' else 'in': (math.tau * self.radius / self.per_circle, True)}


class Points(TrackPiece):
    anchor_names = ('in', 'branch', 'out')
    name = 'points'
    label = 'points'

    def __init__(self, direction: str='left', state: str='out', **kwargs):
        self.direction = direction
        self.state = state
        super().__init__(**kwargs)

    def traversals(self, anchor_from):
        traversals = {}
        if anchor_from == 'in':
            return {
                'out': (32, self.state == 'out'),
                'branch': (35, self.state == 'branch'),
            }
        elif anchor_from == 'out':
            return {'in': (32, True)}
        elif anchor_from == 'branch':
            return {'in': (35, True)}


class Crossover(TrackPiece):
    anchor_names = ('in', 'left', 'right', 'out')
    name = 'crossover'
    label = 'crossover'


    def __init__(self, length: int=16, **kwargs):
        self.length = length
        super().__init__(**kwargs)

    def traversals(self, anchor_from):
        return {self.anchor_names[3 - self.anchor_names.index(anchor_from)]: (self.length, True)}





#
#     asymmetrical = False
#
#     def __init__(self, start):
#         assert isinstance(start, Join)
#         self.start = start
#         self.start.attach(self)
#
#     @property
#     def location(self):
#         return self._location
#
#     @location.setter
#     def location(self, location):
#         self._location = location
#         for end in self.ends:
#             end.location = location + end.owner_offset
#
#     @cached_property
#     def ends(self):
#         return [
#             Join(self, join_location)
#             for join_location in self.join_locations()
#         ]
#
# #    def rotate(self, n=1):
#
#
#
# class Straight(Track):
#     length = 16
#     color = 1, 0, 0
#
#     def join_locations(self):
#         return [
#             Location(cmath.rect(self.length, 0), 0),
#         ]
#
#
# class Curve(Track):
#     asymmetrical = True
#     radius = 40
#     color = 0, 1, 0
#
#     @property
#     def length(self):
#         self.radius * math.tau / 16
#
#     @property
#     def centre(self):
#         rotate = math.tau / 16
#         return self.location + ((cmath.rect(self.radius, rotate) - self.radius) * cmath.rect(1, - math.pi / 2))
#
#     def join_locations(self):
#         rotate = math.tau / 16
#         return [
#             Location(
#                 ((cmath.rect(self.radius, rotate) - self.radius) * cmath.rect(1, - math.pi/2 )),
#                 rotate,
#             )
#         ]
#
#
# class Points(Track):
#     def join_locations(self):
#         return [
#             Location(cmath.rect(16, 0), 0),
#             Location(16 - 8j, 0)
#         ]
