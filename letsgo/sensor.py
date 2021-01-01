import time
from typing import Dict, Type

from pkg_resources import iter_entry_points

from letsgo import signals
from letsgo.control.base import Controllable, SensorController
from letsgo.registry_meta import WithRegistry
from letsgo.track_point import TrackPoint


class Sensor(Controllable, WithRegistry):
    entrypoint_group = "letsgo.sensor"
    label: str

    def __init__(
        self, track_point: TrackPoint, single_direction: bool = False, **kwargs
    ):
        self.track_point = track_point
        self.single_direction = single_direction
        self._activated = False
        super().__init__(**kwargs)

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
