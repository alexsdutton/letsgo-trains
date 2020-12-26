from unittest import TestCase

from letsgo.layout import Layout
from letsgo.routeing import Router
from letsgo.pieces import Straight, LeftPoints
from letsgo.train import Train, TrackPoint


class RouteingTestCase(TestCase):
    def test_branch(self):
        layout = Layout()
        straight, points, branch_straight, mainline_straight = (
            Straight(layout=layout),
            LeftPoints(layout=layout),
            Straight(layout=layout),
            Straight(layout=layout),
        )
        straight.anchors["out"] += points.anchors["in"]
        points.anchors["branch"] += branch_straight.anchors["in"]
        points.anchors["out"] += mainline_straight.anchors["in"]

        router = Router()
        choices = router.route(
            Train(layout=None, cars=[]),
            TrackPoint(straight, "in", 4),
            TrackPoint(branch_straight, "in", 10),
        )
        print(choices)

    def test_branch_with_converge(self):
        layout = Layout()
        straight, points_one, points_two, final_straight = (
            Straight(layout=layout),
            LeftPoints(layout=layout),
            LeftPoints(layout=layout),
            Straight(layout=layout),
        )
        straight.anchors["out"] += points_one.anchors["in"]
        points_one.anchors["branch"] += points_two.anchors["branch"]
        points_one.anchors["out"] += points_two.anchors["out"]
        points_two.anchors["in"] += final_straight.anchors["in"]

        router = Router()
        choices = router.route(
            Train(layout=None, cars=[]),
            TrackPoint(straight, "in", 4),
            TrackPoint(final_straight, "in", 10),
        )
        print(choices)
