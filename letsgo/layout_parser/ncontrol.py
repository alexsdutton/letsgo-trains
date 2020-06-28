import functools
import xml.etree.ElementTree
from typing import Type

import math
from letsgo.pieces.curve import Curve, CurveDirection

from letsgo.track import Position

from letsgo.pieces import LeftPoints, Piece, RightPoints, Straight, piece_classes

from letsgo.layout import Layout

from letsgo.layout_parser.base import LayoutFileParseException, LayoutParser


class NControlLayoutParser(LayoutParser):
    name = "nControl"
    file_extension = ".ncp"

    piece_mapping = {
        "TS_STRAIGHT": Straight,
        "TS_LEFTSWITCH": LeftPoints,
        "TS_RIGHTSWITCH": RightPoints,
        "TS_CURVE": Curve,
    }

    piece_params = {
        "TS_CURVE": {"direction": CurveDirection.right},
    }

    # anchor_name_mapping = {
    #     # nControl curves go the other way to ours
    #     'TS_CURVE': ('out', 'in')
    # }

    def parse(self, fp, layout: Layout):
        doc = xml.etree.ElementTree.parse(fp)
        root = doc.getroot()
        if (
            root.tag != "data"
            or root.attrib.get("type") != "nControl"
            or root.attrib.get("version") != "1"
        ):
            raise LayoutFileParseException("Unexpected root element in nControl file")

        nodes = {
            i: {
                "x": float(node.find("coordinates").attrib["x"]) / 8,
                "y": float(node.find("coordinates").attrib["y"]) / 8,
                "anchor": None,
            }
            for i, node in enumerate(root.findall("node"))
        }

        for segment in root.findall("segment"):
            segment_data = {elem.tag: elem.attrib["value"] for elem in segment}
            piece_cls = self.piece_mapping[segment_data["type"]]
            node_count = int(segment_data["nodes"])
            assert len(piece_cls.anchor_names) == node_count
            node_ids = [int(segment_data[f"node{i}"]) for i in range(1, node_count + 1)]
            # if segment_data['type'] in self.anchor_name_mapping:
            #     node_ids = [
            #         node_ids[piece_cls.anchor_names.index(anchor_name)]
            #         for anchor_name in self.anchor_name_mapping[segment_data['type']]
            #     ]
            piece_nodes = [nodes[node_id] for node_id in node_ids]
            placement = Position(
                piece_nodes[0]["x"],
                piece_nodes[0]["y"],
                float(segment_data["angle"]) / 360 * math.tau,
            )
            piece = piece_cls(
                layout=layout,
                id=segment.find("index").attrib["value"],
                placement=placement,
                **self.piece_params.get(segment_data["type"], {}),
            )
            layout.add_piece(piece, announce=False)

            for node, anchor_name in zip(piece_nodes, piece.anchor_names):
                if node["anchor"]:
                    node["anchor"] += piece.anchors[anchor_name]
                else:
                    node["anchor"] = piece.anchors[anchor_name]

        layout.changed()
