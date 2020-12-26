import uuid
from typing import List

from letsgo.control import Controller
from letsgo.registry_meta import WithRegistry
from letsgo.routeing import Itinerary
from letsgo.speed_estimation import SpeedEstimation
from letsgo.track_point import TrackPoint
from . import signals


class TrainNotOnTrack(Exception):
    pass


class SpeedLimits(dict):
    def __init__(self, train, limit_changed_callback):
        self.train = train
        self._limit_changed_callback = limit_changed_callback

    @property
    def limit(self):
        return min(self.values(), default=float("inf"))

    def __setitem__(self, key, value):
        if value is None or value > 1:
            if key in self:
                del self[key]
        else:
            super().__setitem__(key, value)
            self._limit_changed_callback()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._limit_changed_callback()


class Car:
    def __init__(
        self,
        length: float,
        bogey_offsets: List[float],
        nose="vestibule",
        tail="vestibule",
        magnet_offset: float = None,
    ):
        self.length = length
        self.bogey_offsets = bogey_offsets
        self.nose, self.tail = nose, tail
        self.magnet_offset = magnet_offset

    def serialize(self):
        return {
            "length": self.length,
            "bogey_offsets": self.bogey_offsets,
            "nose": self.nose,
            "tail": self.tail,
        }


class Train(WithRegistry):
    def __init__(
        self,
        cars: List[Car],
        position: TrackPoint = None,
        meta: dict = None,
        id: str = None,
        name: str = None,
        itinerary: Itinerary = None,
        itinerary_index: int = None,
        controller: Controller = None,
        controller_parameters: dict = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cars = cars
        self.length = sum(car.length for car in cars) + 2 * (len(cars) - 1)
        self.position = position
        self.meta = meta or {}
        self._name = name
        self.id = id or str(uuid.uuid4())
        self._motor_speed = 0
        self._maximum_motor_speed = 0
        self._lights_on = False
        self._speed_limits = SpeedLimits(self, self._update_motor_speed)
        self._multiplier = 110
        self.itinerary = itinerary
        self.itinerary_index = itinerary_index

        self._connected = None
        self._battery_level = None

        self._controller = controller
        self.controller_parameters = controller_parameters or {}
        if self.controller:
            self.controller.register_train(self, **self.controller_parameters)

        self.last_spotted_at_position = None
        self.last_spotted_time = None

        self._speed_estimation = SpeedEstimation(self)

    def serialize(self):
        data = {
            **super().serialize(),
            "position": self.position.serialize(),
            "cars": [car.serialize() for car in self.cars],
        }
        if self.controller:
            data.update(
                {
                    "controller_id": self.controller.id,
                    "controller_parameters": self.controller_parameters,
                }
            )
        return data

    @property
    def speed_limits(self):
        return self._speed_limits

    @property
    def maximum_motor_speed(self):
        return self._maximum_motor_speed

    @maximum_motor_speed.setter
    def maximum_motor_speed(self, value):
        value = max(0, min(value, 1))
        if value != self._maximum_motor_speed:
            self._maximum_motor_speed = value
            self._update_motor_speed()

    @property
    def motor_speed(self):
        return self._motor_speed

    def _update_motor_speed(self):
        new_motor_speed = min(self.speed_limits.limit, self.maximum_motor_speed)
        if new_motor_speed != self._motor_speed:
            self._motor_speed = new_motor_speed
            if self.controller:
                self.controller.set_train_motor_speed(self, new_motor_speed)
            signals.train_motor_speed_changed.send(self, motor_speed=self._motor_speed)

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, value):
        if value != self._controller:
            self._controller = value
            signals.controller_changed.send(self, controller=self._controller)

    def stop(self):
        self.maximum_motor_speed = 0

    @property
    def lights_on(self):
        return self._lights_on

    @lights_on.setter
    def lights_on(self, value):
        if value != self._lights_on:
            self._lights_on = value
            if self.controller:
                self.controller.set_train_lights(self, value)
            signals.train_lights_on_changed.send(self, lights_on=value)

    @property
    def battery_level(self):
        return self._battery_level

    @battery_level.setter
    def battery_level(self, value):
        if value != self._connected:
            self._battery_level = value
            signals.battery_level_changed.send(self, battery_level=value)

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        if value != self._connected:
            self._connected = value
            signals.connected_changed.send(self, connected=value)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value != self._name:
            self._name = value
            signals.train_name_changed.send(self, name=value)

    @property
    def speed(self):
        return self._speed_estimation.predict()  # studs per second

    def tick(self, time, time_elapsed):
        self.move(self.speed * time_elapsed)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if value:
            self._position = value.copy(train=self)
            self.rear_position = value.copy(train=self) - self.length
        else:
            self._position, self.rear_position = None, None

    def move(self, distance):
        if not self.position:
            raise TrainNotOnTrack
        self.position += distance
        self.rear_position += distance
        # print(self, "Moving", distance, self.speed)
