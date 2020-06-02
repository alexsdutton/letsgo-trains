import unittest

from trains.track_point import EndOfTheLine
from ..train import TrackPoint
from .. import track


class TrackPointTestCase(unittest.TestCase):
    def test_forward_within_piece(self):
        piece = track.Straight(layout=None)
        track_point = TrackPoint(piece, 'in', 3)
        track_point += 5
        self.assertEqual(piece, track_point.piece)
        self.assertEqual('in', track_point.anchor_name)
        self.assertEqual(8, track_point.offset)

    def test_backward_within_piece(self):
        piece = track.Straight(layout=None)
        track_point = TrackPoint(piece, 'in', 3)
        track_point -= 2
        self.assertEqual(piece, track_point.piece)
        self.assertEqual('in', track_point.anchor_name)
        self.assertEqual(1, track_point.offset)

    def test_forward_across_one_piece_with_nowhere_to_go(self):
        piece = track.Straight(layout=None)
        track_point = TrackPoint(piece, 'in', 3)
        with self.assertRaises(EndOfTheLine) as cm:
            track_point += 20
        self.assertEqual(7, cm.exception.remaining_distance)
        self.assertEqual(piece, cm.exception.piece)
        self.assertEqual('out', cm.exception.final_anchor_name)

    def test_forward_across_one_piece(self):
        piece, next_piece = track.Straight(layout=None), track.Curve(layout=None)
        piece.anchors['out'] += next_piece.anchors['in']
        track_point = TrackPoint(piece, 'in', 3)
        track_point += 20
        self.assertEqual(next_piece, track_point.piece)
        self.assertEqual('in', track_point.anchor_name)
        self.assertEqual(7, track_point.offset)


    def test_backward_across_one_piece(self):
        pass