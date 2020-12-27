from __future__ import annotations

import threading
import time
from typing import Dict, List, TYPE_CHECKING, Tuple

from maestro import Maestro
from maestro.enums import ChannelMode

from .base import BinaryControl, Controllable, SensorController

if TYPE_CHECKING:
    from ..sensor import Sensor

__all__ = ["MaestroController"]


class MaestroChannelDefinition:
    def __init__(self, *, binary_control: BinaryControl = None, sensor: Sensor = None):
        # One or the other
        assert (binary_control and not sensor) or (sensor and not binary_control)
        self.binary_control = binary_control
        self.sensor = sensor

    @property
    def subject(self) -> Controllable:
        return self.binary_control or self.sensor

    def to_yaml(self):
        if self.binary_control:
            return {"binary_control_id": self.binary_control.id}
        elif self.sensor:
            return {"sensor_id": self.sensor.id}


class MaestroController(SensorController):
    label = "Maestro servo controller"

    def __init__(self, *, channels: Dict[int, MaestroChannelDefinition], **kwargs):
        super().__init__(**kwargs)
        self.maestro = None
        self.channels = channels
        self.pending_channel_definitions: List[
            Tuple[int, MaestroChannelDefinition]
        ] = list(self.channels.items())
        self._running = threading.Event()
        self._thread = threading.Thread(target=self._process)

    def set_channel(self, index: int, channel: MaestroChannelDefinition):
        if channel:
            self.channels[index] = channel
            self.pending_channel_definitions.append((index, channel))
            channel.subject.set_controller(self, index=index)
        elif index in self.channels:
            self.channels[index].subject.set_controller(None)
            self.pending_channel_definitions.append((index, None))
            del self.channels[index]

    def start(self):
        self._running.set()
        self._thread.start()

    def stop(self):
        self._running.clear()
        self._thread.join()

    def _process(self):
        while self._running.is_set():
            if not self.maestro:
                self.maestro = Maestro.get_one()
                if not self.maestro:
                    time.sleep(1)
                    continue
                self.device_present.set()
            self.maestro.refresh_values()
            for i, (sensor, params) in self.channels.items():
                channel = self.maestro[i]
                if channel.mode != ChannelMode.Input:
                    continue
                is_high = channel.value > 0.5
                sensor.activated = params.get("normally_high", True) != is_high
            time.sleep(0.02)

    def to_yaml(self) -> dict:
        return {
            **super().to_yaml(),
            "channels": {i: self.channels[i].to_yaml() for i in sorted(self.channels)},
        }
