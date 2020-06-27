from __future__ import annotations

import functools
import threading
import time
from typing import Dict, Union

import pyqtree
from trains.utils.quadtree import ResizingIndex

from trains.pieces.curve import CurveDirection
from trains.pieces.points import BasePoints

from trains.track import Anchor, Position

from trains import track
from trains.control import Controller
from trains.pieces import piece_classes, Piece
from trains.routeing import Stop, Itinerary
from trains.sensor import Sensor
from trains.station import Station, Platform
from trains.train import Train, TrackPoint, Car

from . import signals


def _changes_layout(func):
    """Decorator to record that a layout has changed, unless told not to.

    Call with announce=False if you are making lots of changes in batch, and then remember to call
    layout.changed() at the end.
    """
    @functools.wraps(func)
    def f(self: Layout, *args, announce: bool = True, **kwargs):
        result = func(self, *args, **kwargs)
        if announce:
            self.changed()
        return result
    return f


class Layout:
    def __init__(self):
        self.pieces: Dict[str, Piece] = {}
        self.trains: Dict[str, Train] = {}
        self.stations: Dict[str, Station] = {}
        self.itineraries: Dict[str, Itinerary] = {}
        self.controllers: Dict[str, Controller] = {}
        self.sensors: Dict[str, Sensor] = {}

        self.anchors: Dict[str, Anchor] = {}

        self.pieces_qtree = ResizingIndex(bbox=(-80, -80, 80, 80))
        self.anchors_qtree = ResizingIndex(bbox=(-80, -80, 80, 80))

        self.running = threading.Event()
        self._epoch = 0
        self.meta = {}

        self.sensor_magnets_last_seen = {}

    @property
    def collections(self):
        return {
            Piece: self.pieces,
            Train: self.trains,
            Station: self.stations,
            Itinerary: self.itineraries,
            Controller: self.controllers,
            Sensor: self.sensors,
        }

    @_changes_layout
    def add_piece(self, piece):
        self.pieces[piece.id] = piece
        for anchor in piece.anchors.values():
            if anchor.id in self.anchors and anchor != self.anchors[anchor.id]:
                self.anchors[anchor.id] += anchor
            else:
                self.anchors[anchor.id] = anchor

        self.piece_positioned(piece)
        signals.piece_added.send(self, piece=piece)

    @_changes_layout
    def remove_piece(self, piece: Piece):
        # Disconnect from any other pieces
        for anchor_name in piece.anchor_names:
            piece.anchors[anchor_name].split()
            self.anchors_qtree.remove_item(piece.anchors[anchor_name])
            del self.anchors[piece.anchors[anchor_name].id]
        del self.pieces[piece.id]
        self.pieces_qtree.remove_item(piece)
        signals.piece_removed.send(self, piece=piece)

    def add_train(self, train):
        self.trains[train.id] = train
        signals.train_added.send(self, train=train)

    def remove_train(self, train):
        del self.trains[train.id]
        signals.train_removed.send(self, train=train)

    @_changes_layout
    def add_station(self, station):
        self.stations[station.id] = station
        signals.station_added.send(self, station=station)

    @_changes_layout
    def remove_station(self, station):
        del self.stations[station.id]
        signals.station_removed.send(self, station=station)

    def add_itinerary(self, itinerary):
        self.itineraries[itinerary.id] = itinerary
        signals.itinerary_added.send(self, itinerary=itinerary)

    def remove_itinerary(self, itinerary):
        del self.itineraries[itinerary.id]
        signals.itinerary_removed.send(self, itinerary=itinerary)

    def add_controller(self, controller):
        self.controllers[controller.id] = controller
        signals.controller_added.send(self, controller=controller)

    def remove_controller(self, controller):
        del self.controllers[controller.id]
        signals.controller_removed.send(self, controller=controller)

    @_changes_layout
    def add_sensor(self, sensor):
        self.sensors[sensor.id] = sensor
        signals.sensor_added.send(self, sensor=sensor)
        signals.sensor_activity.connect(self.on_sensor_activity, sender=sensor)

    @_changes_layout
    def remove_sensor(self, sensor):
        del self.sensors[sensor.id]
        signals.sensor_removed.send(self, sensor=sensor)
        signals.sensor_activity.disconnect(self.on_sensor_activity, sender=sensor)

    def piece_positioned(self, piece):
        if piece.position:
            self.pieces_qtree.insert_item(piece, piece.position)
        else:
            self.pieces_qtree.remove_item(piece)
        for anchor in piece.anchors.values():
            self.anchor_positioned(anchor)
        self.changed()

    def anchor_positioned(self, anchor):
        if anchor.position:
            self.anchors_qtree.insert_item(anchor, anchor.position)
        else:
            self.anchors_qtree.remove_item(anchor)
        while anchor.subsumes:
            self.anchors_qtree.remove_item(anchor.subsumes.pop())

    def tick(self, sender, time, time_elapsed):
        for train in self.trains.values():
            train.tick(time, time_elapsed)

    def start(self):
        if self.running.is_set():
            raise AssertionError
        self.running.set()
        for controller in self.controllers.values():
            controller.start()

    def stop(self):
        return
        if not self.running.is_set():
            raise AssertionError
        self.running.clear()
        for controller in self.controllers.values():
            controller.stop()

    @property
    def epoch(self):
        """This changes whenever the layout changes.

        This property can be used to detect changes for e.g. reactive re-rendering.
        """
        return self._epoch

    def changed(self, cleared=False):
        self._epoch += 1
        signals.layout_changed.send(self, cleared=cleared)

    def on_sensor_activity(self, sender: Sensor, activated, when):
        last_train_seen, last_magnet_index_seen, last_time_seen = \
            self.sensor_magnets_last_seen.get(sender, (None, None, None))

        if not activated:
            return

        maximum_distance = 1000

        train_seen, train_seen_offset, magnet_index_seen = None, None, None

        for train in self.trains.values():
            car_offset = 0

            if train.speed == 0:
                continue

            for i, car in enumerate(train.cars):
                # No magnet in this car to expect
                if car.magnet_offset is None:
                    continue
                # Discount any magnets we've seen in the last two seconds
                if train == last_train_seen and i == last_magnet_index_seen and when < last_time_seen + 2:
                    continue

                train_offset = car_offset + car.magnet_offset
                expected_magnet_position = train.position - train_offset

                distance_forward = expected_magnet_position.distance_to(sender.position, maximum_distance)
                if distance_forward:
                    train_seen, train_seen_offset, magnet_index_seen = train, train_offset, i
                    maximum_distance = min(distance_forward, maximum_distance)
                distance_backward = sender.position.distance_to(expected_magnet_position, maximum_distance)
                if distance_backward:
                    train_seen, train_seen_offset, magnet_index_seen = train, train_offset, i
                    maximum_distance = min(distance_backward, maximum_distance)

                # The 1 is the gap between cars
                car_offset += car.length + 1

        if train_seen:
            self.sensor_magnets_last_seen[sender] = train_seen, magnet_index_seen, when
            branch_decisions = train_seen.position.branch_decisions
            train_seen.position = sender.position + train_seen_offset
            train_seen.position.branch_decisions = branch_decisions
            signals.train_spotted.send(train_seen, sensor=sender, position=train_seen.position, when=when)

    @property
    def placed_pieces(self):
        for piece in self.pieces.values():
            if piece.placement:
                yield piece

    @property
    def points(self):
        for piece in self.pieces.values():
            if isinstance(piece, BasePoints):
                yield piece

    def clear(self):
        # Could do `while self.trains: self.remove_train(self.trains.popvalue())` or some such, but never mind
        for train in list(self.trains.values()):
            self.remove_train(train)
        for station in list(self.stations.values()):
            self.remove_station(station, announce=False)
        for sensor in list(self.sensors.values()):
            self.remove_sensor(sensor, announce=False)
        for controller in list(self.controllers.values()):
            self.remove_controller(controller)
        for piece in list(self.pieces.values()):
            self.remove_piece(piece, announce=True)
        self.changed(cleared=True)

if __name__ == '__main__':
    import pkg_resources
    import yaml

    data = yaml.safe_load(pkg_resources.resource_stream('trains', 'data/layouts/simple.yaml'))
    layout = Layout()
    layout.load_from_yaml(data)
    for piece in layout.pieces.values():
        print(piece, piece.anchors)

    print(yaml.dump(layout.to_yaml()))

# piece_1 = track.Straight()
# piece_2 = track.Curve()
# piece_1.anchors['out'] += piece_2.anchors['out']
# piece_3 = track.Points()
# piece_3.anchors['branch'] += piece_2.anchors['in']
