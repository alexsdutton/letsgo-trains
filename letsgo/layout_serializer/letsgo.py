import codecs
import functools

import pkg_resources
import yaml

from letsgo.layout import Layout
from letsgo.layout_serializer import LayoutSerializer


class LetsGoLayoutSerializer(LayoutSerializer):
    name = "Let's Go!"
    file_extension = ".lgl"

    def serialize(self, fp, layout: Layout):
        doc = {
            "meta": layout.meta,
            "controllers": [],
            "sensors": [],
            "trains": [],
            "stations": [],
            "pieces": [],
        }

        for controller in layout.controllers.values():
            doc["controllers"].append(controller.to_yaml())
        for sensor in layout.sensors.values():
            doc["sensors"].append(sensor.to_yaml())
        for train in layout.trains.values():
            doc["trains"].append(train.to_yaml())
        for sensor in layout.sensors.values():
            doc["sensors"].append(sensor.to_yaml())
        for station in layout.stations.values():
            doc["station"].append(station.to_yaml())
        for piece in layout.pieces.values():
            doc["pieces"].append(piece.to_yaml())

        yaml.safe_dump(doc, codecs.getwriter("utf-8")(fp))  # type: ignore
