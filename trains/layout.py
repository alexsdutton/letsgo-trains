from trains import track
from trains.routeing import Stop, Itinerary
from trains.station import Station, Platform
from trains.train import Train, TrackPoint, Car

from . import signals


class Layout:
    def __init__(self):
        self.pieces = set()
        self.trains = []
        self.stations = {}
        self.itineraries = {}

    def add_piece(self, piece):
        self.pieces.add(piece)
        signals.piece_added.send(self, piece=piece)

    def remove_piece(self, piece):
        self.pieces.remove(piece)
        signals.piece_removed.send(self, piece=piece)

    def add_train(self, train):
        self.trains.append(train)
        signals.train_added.send(self, train=train)

    def remove_train(self, train):
        self.trains.remove(train)
        signals.train_removed.send(self, train=train)

    def add_station(self, station):
        self.stations[station.id] = station
        signals.station_added.send(self, station=station)

    def remove_station(self, station):
        del self.stations[station.id]
        signals.station_removed.send(self, station=station)

    def add_itinerary(self, itinerary):
        self.itineraries[itinerary.id] = itinerary
        signals.itinerary_added.send(self, itinerary=itinerary)

    def remove_itinerary(self, itinerary):
        del self.itineraries[itinerary.id]
        signals.itinerary_removed.send(self, itinerary=itinerary)

    def tick(self, sender, time, time_elapsed):
        for train in self.trains:
            train.tick(time, time_elapsed)

    def load_from_yaml(self, yaml):
        anchors_by_id, pieces_by_id = {}, {}
        for run in yaml['runs']:
            previous_anchor = None
            for track_object in run:
                piece_kwargs = {k: v for k, v in track_object.items() if k not in ('piece', 'anchors', 'count')}
                n = track_object.get('count', 1)
                for i in range(0, n):
                    piece = track.TrackPiece.registry[track_object['piece']](**piece_kwargs)
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

                    self.add_piece(piece)

        for station_object in yaml.get('stations', []):
            platforms = []
            for platform in station_object.get('platforms', ()):
                platform['position'] = TrackPoint(pieces_by_id[platform['position']['piece_id']],
                                                  platform['position']['anchor_name'],
                                                  platform['position'].get('offset', 0))
                platforms.append(Platform(**platform))
            station_object['platforms'] = platforms
            station = Station(**station_object)
            self.add_station(station)

        for itinerary_object in yaml.get('itineraries', []):
            stops = []
            for stop in itinerary_object.get('stops', []):
                stop['station'] = self.stations[stop.pop('station_id')]
                stops.append(Stop(**stop))
            itinerary_object['stops'] = stops
            itinerary = Itinerary(**itinerary_object)
            self.add_itinerary(itinerary)

        for train_object in yaml.get('trains', []):
            position = train_object.get('position')
            if position:
                train_object['position'] = TrackPoint(pieces_by_id[position['piece_id']],
                                                      position['anchor_name'],
                                                      position.get('offset', 0))
            if train_object.get('itinerary_id'):
                train_object['itinerary'] = self.itineraries[train_object.pop('itinerary_id')]
            train_object['cars'] = [Car(**car) for car in train_object['cars']]
            train = Train(**train_object)
            self.add_train(train)

    @property
    def placed_pieces(self):
        for piece in self.pieces:
            if piece.placement:
                yield piece

    @property
    def points(self):
        for piece in self.pieces:
            if isinstance(piece, track.Points):
                yield piece

    def to_yaml(self):
        remaining_pieces = set(self)

        runs = []
        piece, run = remaining_pieces.pop(), []

        while True:
            out_anchor_name = piece.anchor_names[-1]
            piece_item = {'piece': piece.name, 'anchors': {}}
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
