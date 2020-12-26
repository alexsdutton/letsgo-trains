from typing import Dict

import yaml
from letsgo.control import Controller

from letsgo.layout import Layout
from letsgo.layout_parser import LayoutParser
from letsgo.pieces import Piece, piece_classes
from letsgo.pieces.curve import CurveDirection
from letsgo.track import Anchor, Position


class LetsGoLayoutParser(LayoutParser):
    name = "Let's Go!"
    file_extension = ".lgl"

    def parse(self, fp, layout: Layout):
        doc = yaml.safe_load(fp)

        anchors_by_id: Dict[str, Anchor] = {}
        pieces_by_id: Dict[str, Piece] = {}

        for piece_data in doc.get("pieces", []):
            piece = Piece.from_yaml(layout, **piece_data)
            layout.add_piece(piece, announce=False)

        for controller_data in doc.get("controllers", ()):
            controller = Controller.from_yaml(layout, **controller_data)
            layout.add_controller(controller)

        # for station_object in yaml.get('stations', []):
        #     platforms = []
        #     for platform in station_object.get('platforms', ()):
        #         platform['position'] = TrackPoint(pieces_by_id[platform['position']['piece_id']],
        #                                           platform['position']['anchor_name'],
        #                                           platform['position'].get('offset', 0))
        #         platforms.append(Platform(**platform))
        #     station_object['platforms'] = platforms
        #     station = Station(**station_object)
        #     self.add_station(station, announce=False)
        #
        # for itinerary_object in yaml.get('itineraries', []):
        #     stops = []
        #     for stop in itinerary_object.get('stops', []):
        #         stop['station'] = self.stations[stop.pop('station_id')]
        #         stops.append(Stop(**stop))
        #     itinerary_object['stops'] = stops
        #     itinerary = Itinerary(**itinerary_object)
        #     self.add_itinerary(itinerary)

        # for train_object in yaml.get('trains', []):
        #     position = train_object.get('position')
        #     if position:
        #         train_object['position'] = TrackPoint(pieces_by_id[position['piece_id']],
        #                                               position['anchor_name'],
        #                                               position.get('offset', 0))
        #     if train_object.get('itinerary_id'):
        #         train_object['itinerary'] = self.itineraries[train_object.pop('itinerary_id')]
        #     train_object['cars'] = [Car(**car) for car in train_object['cars']]
        #     train = Train.from_yaml(layout=self, **train_object)
        #     self.add_train(train)
        #
        # for sensor_object in yaml.get('sensors', ()):
        #     position = sensor_object.get('position')
        #     if position:
        #         sensor_object['position'] = TrackPoint(pieces_by_id[position['piece_id']],
        #                                                position['anchor_name'],
        #                                                position.get('offset', 0))
        #     sensor = Sensor.from_yaml(layout=self, **sensor_object)
        #     self.add_sensor(sensor, announce=False)

        layout.changed()
