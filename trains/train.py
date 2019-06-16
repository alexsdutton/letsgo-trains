import enum
import uuid
from numbers import Number
from typing import Optional, List

from trains.routeing import Itinerary
from trains.track_point import TrackPoint
from trains.train_controller import TrainController
from . import signals, track


class SpeedLimits(dict):
    def __init__(self, train, limit_changed_callback):
        self.train = train
        self._limit_changed_callback = limit_changed_callback

    @property
    def limit(self):
        return min(self.values(), default=float('inf'))

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
    def __init__(self, length: Number, bogey_offsets: List[Number], nose='vestibule', tail='vestibule'):
        self.length = length
        self.bogey_offsets = bogey_offsets


class Train:
    def __init__(self,
                 cars: List[Car],
                 position: Optional[TrackPoint]=None,
                 meta: Optional[dict]=None,
                 id: str=None,
                 name: str=None,
                 itinerary: Optional[Itinerary] = None,
                 itinerary_index: Optional[int] = None,
                 controller: TrainController=None):
        self.cars = cars
        self.position = position.copy(train=self)
        self.length = sum(car.length for car in cars) + 2 * (len(cars) - 1)
        self.rear_position = position.copy(train=self) - self.length
        self.meta = meta or {}
        self._name = name
        self.id = id or str(uuid.uuid4())
        self._motor_speed = 0
        self._maximum_motor_speed = 0
        self._lights_on = False
        self._speed_limits = SpeedLimits(self, self._update_motor_speed)
        self.itinerary = itinerary
        self.itinerary_index = itinerary_index

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
            signals.train_motor_speed_changed.send(self, motor_speed=self._motor_speed)

    def stop(self):
        self.maximum_motor_speed = 0

    speed_mapping = {
        0.1: 12,
        0.2: 15.7,
        0.3: 19.3,
        0.4: 25.1,
    }

    @property
    def lights_on(self):
        return self._lights_on

    @lights_on.setter
    def lights_on(self, value):
        if value != self._lights_on:
            self._lights_on = value
            signals.train_lights_on_changed.send(self, lights_on=value)

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
        return self.motor_speed * 64  # studs per second

    def tick(self, time, time_elapsed):
        self.move(self.speed * time_elapsed)

    def move(self, distance):
        self.position += distance
        self.rear_position += distance
        print(self, "Moving", distance, self.speed)
