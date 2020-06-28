"""
Sir Topham Hatt, teller of trains of where to go

This module implements automated train control
"""
import math
from numbers import Number

from trains.pieces.points import BasePoints

from trains.layout import Layout
from trains.track_point import EndOfTheLine


class TophamHatt:
    def __init__(
        self,
        layout: Layout,
        slow_speed: float = 0.1,
        stop_before_end_of_the_line: Number = 16,
        slow_down_distance: Number = 64,
    ):
        self.layout = layout
        self.slow_speed = slow_speed
        self.stop_before_end_of_the_line = stop_before_end_of_the_line
        self.slow_down_distance = slow_down_distance

    def tick(self, sender, time, time_elapsed):
        # print("Tick")
        for train in self.layout.trains.values():
            self.route_train(train)

    def route_train(self, train):

        position, distance = train.position, 0

        if train.speed == 0:
            # Unreserve pieces we might have previously claimed when moving
            position, _ = position.next_piece()
            while position.piece.claimed_by == train:
                position.piece.claimed_by = None
                position, _ = position.next_piece()

            position, distance = train.position, 0

        can_hide_behind_decision_point = False

        speed_limit = float("inf")

        # if train.meta.get('last_speed_limit') == 0:
        #     print("EE")

        seen_pieces = set()

        while position.piece not in seen_pieces:
            seen_pieces.add(position.piece)

            try:
                position, distance = position.next_piece(distance)
            except EndOfTheLine as e:
                speed_limit = min(
                    speed_limit,
                    math.sqrt(
                        max(
                            0,
                            (
                                distance
                                + e.remaining_distance
                                - self.stop_before_end_of_the_line
                            )
                            / self.slow_down_distance,
                        )
                    ),
                )

            if (distance - self.stop_before_end_of_the_line) < self.slow_down_distance:
                if position.piece.claimed_by == train:
                    pass
                elif position.piece.claimed_by:
                    speed_limit = min(
                        speed_limit,
                        math.sqrt(
                            max(
                                0,
                                (distance - self.stop_before_end_of_the_line)
                                / self.slow_down_distance,
                            )
                        ),
                    )
                elif train.speed:
                    position.piece.claimed_by = train

            traversals = position.piece.traversals(position.anchor_name)
            if len(position.piece.traversals(list(traversals)[0])) > 1:
                can_hide_behind_decision_point = True

            if (
                train not in position.piece.reservations
                or position.piece.reservations[train]["distance"] > distance
            ):
                position.piece.reservations[train] = {
                    "distance": distance,
                    "anchor_name": position.anchor_name,
                    "can_hide_behind_decision_point": can_hide_behind_decision_point,
                }

            # Only reserve as far as the next decision point
            if len(traversals) > 1:
                break

            # Check whether something the other way would have a choice to avoid us
            other_reservations = [
                reservation
                for other_train, reservation in position.piece.reservations.items()
                if other_train != train
                and reservation["anchor_name"] != position.anchor_name
            ]
            if can_hide_behind_decision_point and any(
                not reservation["can_hide_behind_decision_point"]
                for reservation in other_reservations
            ):
                speed_limit = min(
                    speed_limit,
                    math.sqrt(
                        max(
                            0,
                            (distance - self.stop_before_end_of_the_line)
                            / self.slow_down_distance,
                        )
                    ),
                )

        if speed_limit > 1:
            speed_limit = None

        train.speed_limits[self] = speed_limit
        train.meta["last_speed_limit"] = speed_limit
        # print(speed_limit)

        if isinstance(position.piece, BasePoints):

            train.meta[
                "annotation"
            ] = f"{can_hide_behind_decision_point} {train.motor_speed}"
            if speed_limit is not None:
                train.meta["annotation"] += f" {speed_limit:.1f}"

        # Unreserve pieces we've passed through
        rear_position, _ = train.rear_position.reversed().next_piece(
            use_branch_decisions=True
        )
        while rear_position.piece.claimed_by == train:
            rear_position.piece.claimed_by = None
            del rear_position.piece.reservations[train]
            rear_position, _ = rear_position.next_piece(use_branch_decisions=True)

        return

        target_stop = train.itinerary.stops[train.itinerary_index]
        target_station = target_stop.station
        platforms = target_station.available_platforms(train)
        # print(platforms)
