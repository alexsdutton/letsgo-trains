"""
Calculates expected stud-per-second speeds for trains based on a number of factors
"""
import time

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from letsgo.track_point import TrackPoint
from . import signals


class SpeedEstimation:
    def __init__(self, train, data=None):
        self.train = train
        self.data = data or []
        self.last_position = None
        self.last_time = None
        self.current_profile = []
        self.last_profile_update = None
        self.regression = None

        signals.battery_level_changed.connect(self.on_state_changed, sender=train)
        signals.train_motor_speed_changed.connect(self.on_state_changed, sender=train)
        signals.train_lights_on_changed.connect(self.on_state_changed, sender=train)

        signals.train_spotted.connect(self.on_train_spotted, sender=train)

    def on_state_changed(self, sender, **kwargs):
        self.update_profile(time.time())

    def update_profile(self, when):
        if self.last_profile_update:
            self.current_profile.append(
                {
                    "duration": when - self.last_profile_update,
                    "motor_speed": self.train.motor_speed,
                    "battery_level": self.train.battery_level or 0,
                    "battery_level_available": int(
                        self.train.battery_level is not None
                    ),
                    "lights_on": int(self.train.lights_on),
                }
            )
        self.last_profile_update = when

    def on_train_spotted(self, sender, sensor, position, when):
        if self.last_position:
            self.update_profile(when)
            distance = self._get_distance_travelled(self.last_position, position)
            duration = sum(state["duration"] for state in self.current_profile)
            self.data.append(
                {
                    "distance": distance,
                    "profile": self.current_profile,
                    "duration": duration,
                    "motor_speed": sum(
                        state["motor_speed"] * state["duration"]
                        for state in self.current_profile
                    )
                    / duration,
                    "battery_level": sum(
                        state["battery_level"] * state["duration"]
                        for state in self.current_profile
                    )
                    / duration,
                    "battery_level_available": sum(
                        state["battery_level_available"] * state["duration"]
                        for state in self.current_profile
                    )
                    / duration,
                    "lights_on": sum(
                        state["lights_on"] * state["duration"]
                        for state in self.current_profile
                    )
                    / duration,
                    "speed": distance / duration,
                }
            )
            self.update_model()

        self.last_time, self.last_position, self.last_profile_update = (
            when,
            position,
            when,
        )

        self.current_profile = []
        self.update_profile(when)

    def get_constant_speed_profiles(self):
        return [
            [
                d["speed"],
                d["motor_speed"],
                d["battery_level"],
                d["battery_level_available"],
                d["lights_on"],
            ]
            for d in self.data
            if len(set(state["motor_speed"] for state in d["profile"])) == 1
        ]

    def update_model(self):
        constant_speed_profiles = self.get_constant_speed_profiles()
        # We know trains can't go anywhere if their motor isn't running
        constant_speed_profiles.extend(
            [
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 1],
                [0, 0, 100, 1, 0],
                [0, 0, 50, 1, 0],
                [0, 0, 100, 1, 1],
                [0, 0, 50, 1, 1],
            ]
        )
        constant_speed_profiles = np.array(constant_speed_profiles)
        X = constant_speed_profiles[:, 1:]
        X = PolynomialFeatures(3).fit_transform(X)
        y = constant_speed_profiles[:, 0]
        self.regression = LinearRegression().fit(X, y)

    def predict(self, **kwargs):
        X = [
            kwargs.get("motor_speed", self.train.motor_speed),
            kwargs.get("battery_level", self.train.battery_level or 0),
            kwargs.get(
                "battery_level_available", int(self.train.battery_level is not None)
            ),
            float(kwargs.get("lights_on", int(self.train.lights_on))),
        ]

        if X[0] == 0:
            return 0

        if not self.regression:
            # This is a hard-coded prediction
            return X[0] * 60

        X = PolynomialFeatures(3).fit_transform(np.array([X]))

        # Make sure we don't predict it going backwards
        return max(0, self.regression.predict(X))

    def _get_distance_travelled(self, last_position: TrackPoint, position: TrackPoint):
        # Calculate the distance travelled by this train since it was last spotted, by tracing its path backwards
        # to where it was last spotted
        p = position.reversed()
        p, distance = p.next_piece(-p.offset, True)
        c = 0
        while last_position.piece != p.piece:
            p, distance = p.next_piece(distance, True)
            c += 1
            if c > 1000:
                print()
        p = p.reversed()
        distance += p.offset - last_position.offset
        return distance

    #
    # def spotted_at(self, position: TrackPoint):
    #     self.motor_speed_profile.append((time.time(), self.motor_speed))
    #
    #     if self.last_spotted_at_position:
    #         # Calculate the distance travelled by this train since it was last spotted, by tracing its path backwards
    #         # to where it was last spotted
    #         p = position.reversed()
    #         p, distance = p.next_piece(-p.offset, True)
    #         while self.last_spotted_at_position.piece != p.piece:
    #             p, distance = p.next_piece(distance, True)
    #         p = p.reversed()
    #         distance += p.offset - self.last_spotted_at_position.offset
    #
    #         # Now integrate the speed profile
    #         last_t, last_motor_speed = self.motor_speed_profile[0]
    #         integrated_speed = 0
    #         profile = []
    #         for t, motor_speed in self.motor_speed_profile[1:]:
    #             integrated_speed += (t - last_t) * last_motor_speed
    #             profile.append((t- last_t, last_motor_speed))
    #             last_t, last_motor_speed = t, motor_speed
    #
    #         self._multiplier = distance / integrated_speed
    #         print(distance, integrated_speed, self._multiplier)
    #         self._speed_estimation.add_profile(profile, distance)
    #
    #     self.position = position
    #     self.last_spotted_at_position = position
    #     self.motor_speed_profile[:-1] = []
