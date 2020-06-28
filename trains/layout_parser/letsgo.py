import yaml
from trains.control import Controller

from trains.layout import Layout
from trains.layout_parser import LayoutParser
from trains.pieces import Piece, piece_classes
from trains.pieces.curve import CurveDirection
from trains.track import Position


class LetsGoLayoutParser(LayoutParser):
    name = "Let's Go!"
    file_extension = ".lgl"

    def parse(self, fp, layout: Layout):
        doc = yaml.safe_load(fp)

        anchors_by_id, pieces_by_id = {}, {}
        for piece_data in doc.get("pieces", []):
            piece = Piece.from_yaml(layout, **piece_data)
            layout.add_piece(piece, announce=False)

        for controller_data in doc.get("controllers", ()):
            controller = Controller.from_yaml(layout=self, **controller_data)
            self.add_controller(controller)

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
