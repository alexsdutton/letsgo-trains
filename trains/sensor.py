import time

from trains import signals
from trains.control import Controller
from trains.registry_meta import WithRegistry
from trains.track import Position


class Sensor(WithRegistry):
    def __init__(self,
                 position: Position,
                 controller: Controller,
                 controller_parameters: dict={},
                 single_direction: bool=False,
                 **kwargs):
        self.position = position
        self.controller = controller
        self.controller_parameters = controller_parameters
        self.controller.register_sensor(self, **controller_parameters)
        self.single_direction = single_direction
        self._activated = False
        super().__init__(**kwargs)

    def serialize(self):
        data = {
            **super().serialize(),
            'single_direction': self.single_direction,
        }
        if self.controller:
            data.update({
                'controller_id': self.controller.id,
                'controller_parameters': self.controller_parameters,
            })
        return data

    @property
    def activated(self):
        return self._activated

    @activated.setter
    def activated(self, value):
        if value != self._activated:
            self._activated = value
            signals.sensor_activity.send(self,
                                         activated=self._activated,
                                         when=time.time())


class HallEffectSensor(Sensor):
    registry_type = 'hall'

