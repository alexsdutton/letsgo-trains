import collections
from numbers import Number

from trains.train import TrackPoint, Train


class Route:
    pass

class Router:
    """Routes trains"""

    def route(self, train: Train, from_trackpoint: TrackPoint, to_trackpoint: TrackPoint):
        routes = collections.defaultdict(set)
        track_points = [(0, from_trackpoint, ())]
        while track_points:
            distance, track_point, choices = track_points.pop(0)  # type: Number, TrackPoint, tuple
            traversals = track_point.piece.traversals(track_point.anchor_name)
            for anchor_to, (anchor_distance, _) in traversals.items():
                anchor_distance -= track_point.offset
                next_piece, next_anchor = track_point.piece.anchors[anchor_to].next(track_point.piece)
                anchor_choices = choices
                if len(traversals) > 1:
                    anchor_choices += ((track_point.piece, anchor_to),)
                if next_piece == to_trackpoint.piece and next_anchor == to_trackpoint.anchor_name:
                    for choice_piece, choice_anchor in anchor_choices:
                        routes[choice_piece].add(choice_anchor)
                elif next_piece:
                    track_points.append((distance + anchor_distance,
                                         TrackPoint(next_piece, next_anchor, 0),
                                         anchor_choices))

            track_points.sort()
        return routes
