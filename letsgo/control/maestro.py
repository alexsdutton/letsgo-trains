from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

import usb

from maestro import Maestro
from maestro.enums import ChannelMode
from .base import BinaryControl, Controllable, SensorController

if TYPE_CHECKING:
    from ..sensor import Sensor

__all__ = ["MaestroController"]


class MaestroChannelDefinition:
    def __init__(
        self,
        *,
        binary_control: BinaryControl = None,
        sensor: Sensor = None,
        normally_high: bool = True
    ):
        # One or the other
        assert (binary_control and not sensor) or (sensor and not binary_control)
        self.binary_control = binary_control
        self.sensor = sensor
        self.normally_high = normally_high

    @property
    def subject(self) -> Controllable:
        return self.binary_control or self.sensor  # type: ignore

    @property
    def mode(self) -> ChannelMode:
        if self.binary_control:
            return ChannelMode.Servo
        elif self.sensor:
            return ChannelMode.Input

    def to_yaml(self):
        if self.binary_control:
            return {"binary_control_id": self.binary_control.id}
        elif self.sensor:
            return {"sensor_id": self.sensor.id, "normally_high": self.normally_high}


class MaestroController(SensorController):
    label = "Maestro servo controller"

    def __init__(
        self,
        *,
        channels: Dict[int, MaestroChannelDefinition] = None,
        serial_number: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.maestro: Optional[Maestro] = None
        self.serial_number = serial_number
        self.channels = channels or {}
        self.pending_channel_definitions: List[
            Tuple[int, Optional[MaestroChannelDefinition]]
        ] = list(self.channels.items())
        self._running = threading.Event()
        self._thread = threading.Thread(target=self._process)

    @property
    def channel_count(self) -> Optional[int]:
        return self.maestro.channel_count if self.maestro else None

    def set_channel(self, index: int, channel: MaestroChannelDefinition):
        if not self.channel_count:
            raise ValueError("Cannot assign channels when not connected")
        if not (0 <= index < self.channel_count):
            raise ValueError("Channel index out of range")
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
            try:
                if not self.maestro:
                    if self.serial_number:
                        self.maestro = Maestro.get_by_serial_number(self.serial_number)
                    else:
                        self.maestro = Maestro.get_one()
                    if not self.maestro:
                        time.sleep(1)
                        continue
                    self.serial_number = self.maestro.serial_number
                    self.device_present = True

                    for index, channel_definition in self.channels.items():
                        self.maestro[index].mode = channel_definition.mode

                self.maestro.refresh_values()
                for i, channel_definition in self.channels.items():
                    channel = self.maestro[i]
                    if channel.mode != ChannelMode.Input:
                        continue
                    is_high = channel.value > 0.5
                    channel_definition.subject.activated = (
                        channel_definition.normally_high != is_high
                    )
                time.sleep(0.02)
            except usb.core.USBError as e:
                if e.errno == 19:  # No such device (it may have been disconnected)
                    self.maestro = None
                    self.device_present = False
                else:
                    raise

    def to_yaml(self) -> dict:
        return {
            **super().to_yaml(),
            "channels": {i: self.channels[i].to_yaml() for i in sorted(self.channels)},
            "serial_number": self.serial_number,
        }
