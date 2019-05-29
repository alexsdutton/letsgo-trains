from trains import track
from trains.train import Train, TrackPoint, Car


class Layout:
    def __init__(self, pieces: set, trains: list):
        self.pieces = pieces
        self.trains = trains

    @classmethod
    def from_yaml(cls, yaml):
        pieces = set()
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

                    pieces.add(piece)

        trains = []
        for train_object in yaml.get('trains', []):
            position = train_object.get('position')
            if position:
                train_object['position'] = TrackPoint(pieces_by_id[position['piece_id']],
                                                      position['anchor_name'],
                                                      position.get('offset', 0))
            train_object['cars'] = [Car(**car) for car in train_object['cars']]
            train = Train(**train_object)
            trains.append(train)

        return cls(pieces, trains)

    @property
    def placed_pieces(self):
        for piece in self.pieces:
            if piece.placement:
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




    # def to_yaml(self):
    #     remaining_pieces = self.pieces.copy()
    #     runs, anchor_ids, anchor_id_index = [], {}, 0
    #     while remaining_pieces:
    #         run = []
    #         piece = remaining_pieces.pop()
    #         item = {'piece': piece.name}
    #         run.append(item)
    #         in_anchor_name = piece.anchor_names[0]
    #         out_anchor_name = piece.anchor_names[-1]
    #         # Special-case first piece in run being at end, so look in the other direction
    #         if len(piece.anchors[out_anchor_name]) == 1 and len(piece.anchors[in_anchor_name]) == 2:
    #             in_anchor_name, out_anchor_name = out_anchor_name, in_anchor_name
    #             item['reverse'] = True
    #         if len(piece.anchors[in_anchor_name]) > 1:
    #             anchor_ids[id(piece.anchors[in_anchor_name])] = f'anchor-{anchor_id_index}'
    #             anchor_id_index += 1
    #             item['anchors'] = {}
    #             item['anchors'][in_anchor_name] = anchor_ids[id(piece.anchors[in_anchor_name])]
    #
    #         while True:
    #             next_piece, next_in_anchor_name = piece.anchors[out_anchor_name].other(piece)
    #             if not next_piece:
    #                 break
    #             item = {'piece': next_piece.name}
    #             if next_in_anchor_name == next_piece.anchor_names[-1]:
    #                 item['reverse'] = True
    #             elif next_in_anchor_name != next_piece.anchor_names[0]:
    #                 break
    #
    #             run.append(item)
    #
    #
    #         runs.append(run)
    #
    #     return {'runs': runs}



if __name__ == '__main__':
    import pkg_resources
    import yaml

    data = yaml.safe_load(pkg_resources.resource_stream('trains', 'data/layouts/simple.yaml'))
    layout = Layout.from_yaml(data)
    for piece in layout.pieces:
        print(piece, piece.anchors)

    print(yaml.dump(layout.to_yaml()))

# piece_1 = track.Straight()
# piece_2 = track.Curve()
# piece_1.anchors['out'] += piece_2.anchors['out']
# piece_3 = track.Points()
# piece_3.anchors['branch'] += piece_2.anchors['in']
