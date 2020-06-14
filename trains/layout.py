from __future__ import annotations

import functools
import threading
import time
from typing import Union

import pyqtree
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
        self.pieces = set()
        self.trains = {}
        self.stations = {}
        self.itineraries = {}
        self.controllers = {}
        self.sensors = {}
        self.by_id = {}
        self.running = threading.Event()
        self._epoch = 0

        self.sensor_magnets_last_seen = {}

    @_changes_layout
    def add_piece(self, piece):
        self.pieces.add(piece)
        signals.piece_added.send(self, piece=piece)

    @_changes_layout
    def remove_piece(self, piece: Piece):
        # Disconnect from any other pieces
        for anchor_name in piece.anchors:
            piece.anchors[anchor_name] = piece.anchors[anchor_name].split(piece)
        self.pieces.remove(piece)
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

    def load_from_yaml(self, yaml):
        anchors_by_id, pieces_by_id = {}, {}
        for run in yaml['runs']:
            previous_anchor = None
            for track_object in run:
                piece_kwargs = {k: v for k, v in track_object.items() if k not in ('type', 'anchors', 'count')}
                if piece_kwargs.get('placement'):
                    piece_kwargs['placement'] = Position(**piece_kwargs['placement'])
                n = track_object.get('count', 1)
                for i in range(0, n):
                    piece = piece_classes[track_object['type']](layout=self, **piece_kwargs)
                    pieces_by_id[piece.id] = piece
                    in_anchor = piece.anchors[piece.anchor_names[0]]
                    out_anchor = piece.anchors[piece.anchor_names[-1]]
                    if track_object.get('reverse'):
                        in_anchor, out_anchor = out_anchor, in_anchor
                    if previous_anchor:
                        previous_anchor += in_anchor
                    previous_anchor = out_anchor

                    for anchor_name, anchor_id in track_object.get('anchors', {}).items():
                        if i == 0 and anchor_name == piece.anchor_names[0] or \
                                i == n - 1 and anchor_name == piece.anchor_names[-1] or \
                                n == 1:
                            if anchor_id in anchors_by_id:
                                piece.anchors[anchor_name] += anchors_by_id[anchor_id]
                            else:
                                anchors_by_id[anchor_id] = piece.anchors[anchor_name]
                            anchors_by_id[anchor_id].id = anchor_id

                    self.add_piece(piece, announce=False)

        for station_object in yaml.get('stations', []):
            platforms = []
            for platform in station_object.get('platforms', ()):
                platform['position'] = TrackPoint(pieces_by_id[platform['position']['piece_id']],
                                                  platform['position']['anchor_name'],
                                                  platform['position'].get('offset', 0))
                platforms.append(Platform(**platform))
            station_object['platforms'] = platforms
            station = Station(**station_object)
            self.add_station(station, announce=False)

        for itinerary_object in yaml.get('itineraries', []):
            stops = []
            for stop in itinerary_object.get('stops', []):
                stop['station'] = self.stations[stop.pop('station_id')]
                stops.append(Stop(**stop))
            itinerary_object['stops'] = stops
            itinerary = Itinerary(**itinerary_object)
            self.add_itinerary(itinerary)

        for controller_object in yaml.get('controllers', ()):
            controller = Controller.from_yaml(layout=self, **controller_object)
            self.add_controller(controller)

        for train_object in yaml.get('trains', []):
            position = train_object.get('position')
            if position:
                train_object['position'] = TrackPoint(pieces_by_id[position['piece_id']],
                                                      position['anchor_name'],
                                                      position.get('offset', 0))
            if train_object.get('itinerary_id'):
                train_object['itinerary'] = self.itineraries[train_object.pop('itinerary_id')]
            train_object['cars'] = [Car(**car) for car in train_object['cars']]
            train = Train.from_yaml(layout=self, **train_object)
            self.add_train(train)

        for sensor_object in yaml.get('sensors', ()):
            position = sensor_object.get('position')
            if position:
                sensor_object['position'] = TrackPoint(pieces_by_id[position['piece_id']],
                                                      position['anchor_name'],
                                                      position.get('offset', 0))
            sensor = Sensor.from_yaml(layout=self, **sensor_object)
            self.add_sensor(sensor, announce=False)

        self.changed()

    def serialize(self):
        return {
            'trains': [train.serialize() for train in self.trains.values()],
            'controllers': [controller.serialize() for controller in self.controllers.values()],
            'sensors': [sensor.serialize() for sensor in self.sensors.values()],
            'runs': self.serialize_runs(),
        }

    @property
    def placed_pieces(self):
        for piece in self.pieces:
            if piece.placement:
                yield piece

    @property
    def points(self):
        for piece in self.pieces:
            if isinstance(piece, BasePoints):
                yield piece

    def serialize_runs(self):
        remaining_pieces = set(self.pieces)

        runs = []
        piece, run = remaining_pieces.pop(), []

        while True:
            out_anchor_name = piece.anchor_names[-1]
            piece_item = {'piece': piece.registry_type, 'anchors': {}}
            if not run:
                piece_item['anchors'][piece.anchor_names[0]] = piece.anchors[piece.anchor_names[0]].id
            run.append(piece_item)
            next_piece, next_in_anchor = piece.anchors[piece.anchor_names[-1]].next(piece)

            for anchor_name in piece.anchor_names[1:-1]:
                piece_item['anchors'][anchor_name] = piece.anchors[anchor_name].id

            if not next_piece or next_piece not in remaining_pieces or next_in_anchor != next_piece.anchor_names[0]:
                piece_item['anchors'][piece.anchor_names[-1]] = piece.anchors[piece.anchor_names[-1]].id
                runs.append(run)
                run = []
                try:
                    piece = remaining_pieces.pop()
                except KeyError:
                    break
            else:
                remaining_pieces.remove(next_piece)
                piece = next_piece

        run_ins, run_outs = {}, {}

        for run in runs:
            for piece_item in run:
                if not piece_item['anchors']:
                    del piece_item['anchors']
            run_ins[run[0]['anchors']['in']] = run
            run_outs[run[-1]['anchors']['out']] = run

        for anchor_id in set(run_ins) & set(run_outs):
            if run_ins[anchor_id] != run_outs[anchor_id]:
                run_outs[anchor_id] += run_ins[anchor_id]
                runs.remove(run_ins[anchor_id])

        return runs

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
        for piece in list(self.pieces):
            self.remove_piece(piece, announce=True)
        self.changed(cleared=True)

if __name__ == '__main__':
    import pkg_resources
    import yaml

    data = yaml.safe_load(pkg_resources.resource_stream('trains', 'data/layouts/simple.yaml'))
    layout = Layout()
    layout.load_from_yaml(data)
    for piece in layout.pieces:
        print(piece, piece.anchors)

    print(yaml.dump(layout.to_yaml()))

# piece_1 = track.Straight()
# piece_2 = track.Curve()
# piece_1.anchors['out'] += piece_2.anchors['out']
# piece_3 = track.Points()
# piece_3.anchors['branch'] += piece_2.anchors['in']
