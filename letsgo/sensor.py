from __future__ import annotations

import math
import time
from typing import Dict, Type, TYPE_CHECKING

from cairo import Context
from pkg_resources import iter_entry_points

from letsgo import signals
from letsgo.control.base import Controllable, SensorController
from letsgo.drawing_options import DrawingOptions
from letsgo.pieces import Piece
from letsgo.registry_meta import WithRegistry
from letsgo.track import Bounds, Position
from letsgo.track_point import TrackPoint
from letsgo.trackside_item import TracksideItem

if TYPE_CHECKING:
    from letsgo.layout import Layout

# Colors, red and green
SENSOR_NORMAL = (1, 0, 0)
SENSOR_ACTIVATED = (0, 1, 0)


class Sensor(Controllable, TracksideItem, WithRegistry):
    entrypoint_group = "letsgo.sensor"
    label: str

    def __init__(
        self, track_point: TrackPoint, single_direction: bool = False, **kwargs
    ):
        self.track_point = track_point
        self.single_direction = single_direction
        self._activated = False

        self._position = None
        signals.piece_positioned.connect(
            self.on_piece_positioned, self.track_point.piece
        )
        signals.piece_removed.connect(
            self.on_piece_removed, self.track_point.piece.layout
        )
        if track_point.position:
            self.on_piece_positioned(track_point.piece)

        super().__init__(**kwargs)

    def on_piece_positioned(self, sender: Piece):
        if self.track_point.position:
            position = self.track_point.position + Position(0, 5, 0)
        else:
            position = None
        if position != self._position:
            self._position = position
            signals.sensor_positioned.send(self)

    def on_piece_removed(self, sender: Layout, piece: Piece):
        if piece == self.track_point.piece:
            self.layout.remove_sensor(self)

    @property
    def position(self):
        return self._position

    def draw(self, cr: Context, drawing_options: DrawingOptions):

        cr.set_source_rgb(*drawing_options.rail_color)
        cr.rectangle(-1, -1, 2, 2)
        cr.fill()

        cr.set_source_rgb(*(SENSOR_ACTIVATED if self.activated else SENSOR_NORMAL))
        cr.arc(0, 0, 0.8, 0, math.tau)
        cr.fill()

    def bounds(self) -> Bounds:
        return Bounds(-1, -1, 2, 2)

    def to_yaml(self) -> dict:
        return {
            **super().to_yaml(),
            "track_point": self.track_point.to_yaml(),
            "single_direction": self.single_direction,
        }

    @property
    def activated(self):
        return self._activated

    @activated.setter
    def activated(self, value):
        if value != self._activated:
            self._activated = value
            signals.sensor_activity.send(
                self, activated=self._activated, when=time.time()
            )


class HallEffectSensor(Sensor):
    label = "Hall-effect sensor"


class BeamSensor(Sensor):
    label = "Beam sensor"


sensor_classes: Dict[str, Type[Sensor]] = {
    ep.name: ep.load() for ep in iter_entry_points("letsgo.sensor")
}
