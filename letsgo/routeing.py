import collections
import typing
import uuid
from typing import Any, Optional, List, Sequence, Tuple

from letsgo.station import Station
from letsgo.track_point import TrackPoint


class Stop:
    def __init__(
        self,
        station: Station,
        dwell: Optional[float] = None,
        dwell_min: Optional[float] = None,
        dwell_max: Optional[float] = None,
        no_stopping: bool = False,
    ):
        self.station = station
        self.dwell_min = dwell or dwell_min
        self.dwell_max = dwell or dwell_max
        self.no_stopping = no_stopping


class Itinerary:
    """A list of stations to travel through"""

    def __init__(self, id: str = None, stops: Sequence[Stop] = (), repeat: bool = True):
        self.id = id or str(uuid.uuid4())
        self.stops = stops
        self.repeat = repeat


class Route:
    pass


class Router:
    """Routes trains"""

    @typing.no_type_check
    def route(self, train, from_trackpoint: TrackPoint, to_trackpoint: TrackPoint):
        routes = collections.defaultdict(set)
        track_points: List[Tuple[float, TrackPoint, Tuple[Any, ...]]] = [
            (0.0, from_trackpoint, ())
        ]
        while track_points:
            distance, track_point, choices = track_points.pop(
                0
            )  # type: float, TrackPoint, Tuple[Any, ...]
            traversals = track_point.piece.traversals(track_point.anchor_name)
            for anchor_to, (anchor_distance, _) in traversals.items():
                anchor_distance -= track_point.offset
                next_piece, next_anchor = track_point.piece.anchors[anchor_to].next(
                    track_point.piece
                )
                anchor_choices = choices
                if len(traversals) > 1:
                    anchor_choices += ((track_point.piece, anchor_to),)
                if (
                    next_piece == to_trackpoint.piece
                    and next_anchor == to_trackpoint.anchor_name
                ):
                    for choice_piece, choice_anchor in anchor_choices:
                        routes[choice_piece].add(choice_anchor)
                elif next_piece:
                    track_points.append(
                        (
                            distance + anchor_distance,
                            TrackPoint(next_piece, next_anchor, 0),
                            anchor_choices,
                        )
                    )

            track_points.sort()
        return routes
