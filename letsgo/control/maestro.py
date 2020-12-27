import threading
import time

from maestro import Maestro
from maestro.enums import ChannelMode

from .base import SensorController

__all__ = ["MaestroController"]


class MaestroController(SensorController):
    label = "Maestro servo controller"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.maestro = None
        self.channels = {}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._process)

    def register_sensor(self, sensor, *, index: int, **params):
        self.channels[index] = sensor, params

    def start(self):
        self._stop.clear()
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join()

    def _process(self):
        while not self._stop.is_set():
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
