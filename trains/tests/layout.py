import unittest

from trains import track
from trains.layout import Layout


class LayoutTestCase(unittest.TestCase):
    def test_back_to_front_straights_in_in(self):
        layout = Layout()
        straight_1, straight_2 = track.Straight(), track.Straight()
        straight_1.anchors['in'] += straight_2.anchors['in']
        layout |= {straight_1, straight_2}
        serialized = layout.to_yaml()
        self.assertEqual(2, len(serialized))
        self.assertEqual(1, len(serialized[0]))
        self.assertEqual(1, len(serialized[1]))
        self.assertEqual(serialized[0][0]['anchors']['in'], serialized[1][0]['anchors']['in'])
        self.assertNotEqual(serialized[0][0]['anchors']['out'], serialized[1][0]['anchors']['out'])

    def test_back_to_front_straights_out_out(self):
        layout = Layout()
        straight_1, straight_2 = track.Straight(), track.Straight()
        straight_1.anchors['out'] += straight_2.anchors['out']
        layout |= {straight_1, straight_2}
        serialized = layout.to_yaml()
        self.assertEqual(2, len(serialized))
        self.assertEqual(1, len(serialized[0]))
        self.assertEqual(1, len(serialized[1]))
        self.assertNotEqual(serialized[0][0]['anchors']['in'], serialized[1][0]['anchors']['in'])
        self.assertEqual(serialized[0][0]['anchors']['out'], serialized[1][0]['anchors']['out'])

    def test_sequential_straights(self):
        layout = Layout()
        straights = [track.Straight() for _ in range(20)]
        for i in range(1, len(straights)):
            straights[i-1].anchors['out'] += straights[i].anchors['in']
        layout.update(straights)
        serialized = layout.to_yaml()
        self.assertEqual(1, len(serialized))

    def test_circle(self):
        layout = Layout()
        curves = [track.Curve() for _ in range(16)]
        for i in range(0, len(curves)):
            curves[i-1].anchors['out'] += curves[i].anchors['in']
        layout.update(curves)
        serialized = layout.to_yaml()
        self.assertEqual(1, len(serialized))
        self.assertEqual(serialized[0][0]['anchors']['in'], serialized[0][-1]['anchors']['out'])
