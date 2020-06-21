import unittest
import unittest.mock

from trains.track import Position

from trains.pieces import Curve, Straight

from trains.gtk.layout_drawingarea import LayoutDrawer
from trains.layout import Layout


class LayoutDrawerTestCase(unittest.TestCase):
    def test_anchor_position_bookkeeping(self):
        layout = Layout()
        drawing_area = unittest.mock.Mock()
        layout_drawer = LayoutDrawer(drawing_area, layout)

        piece_1 = Straight(layout=layout, placement=Position(0, 0, 0))
        layout.add_piece(piece_1)

        piece_2 = Straight(layout=layout)
        layout.add_piece(piece_2)

        piece_3 = Straight(layout=layout)
        layout.add_piece(piece_3)

        # Connect them explicitly not out->in, out->in, and check how many are positioned in the layout as we go
        self.assertEqual(2, len(layout_drawer.anchors_qtree))
        piece_1.anchors['out'] += piece_2.anchors['in']
        self.assertEqual(3, len(layout_drawer.anchors_qtree))
        piece_3.anchors['in'] += piece_2.anchors['out']
        # for anchor, bbox in layout_drawer.anchors_qtree._bounds.items():
        #     print(f'  {bbox} - {anchor}')
        self.assertEqual(4, len(layout_drawer.anchors_qtree))

        layout.remove_piece(piece_2)
        self.assertEqual(4, len(layout_drawer.anchors_qtree))
        layout.remove_piece(piece_1)
        self.assertEqual(2, len(layout_drawer.anchors_qtree))
        layout.remove_piece(piece_3)
        self.assertEqual(0, len(layout_drawer.anchors_qtree))
