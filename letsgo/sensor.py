import time

from letsgo import signals
from letsgo.control.base import Controllable, SensorController
from letsgo.registry_meta import WithRegistry
from letsgo.track_point import TrackPoint


class Sensor(Controllable, WithRegistry):
    entrypoint_group = "letsgo.sensor"

    def __init__(self, position: TrackPoint, single_direction: bool = False, **kwargs):
        self.position = position
        self.single_direction = single_direction
        self._activated = False
        super().__init__(**kwargs)

    def to_yaml(self) -> dict:
        return {
            **super().to_yaml(),
            "position": self.position.to_yaml(),
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
    pass
