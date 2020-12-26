import threading

from letsgo.registry_meta import WithRegistry

__all__ = ["Controller"]


class Controller(WithRegistry):
    entrypoint_group = "letsgo.controller"
    label: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_present = threading.Event()

    def start(self):
        raise NotImplemented

    def stop(self):
        raise NotImplemented


class SensorController(Controller):
    def register_sensor(self, sensor, *, index: int, **params):
        raise NotImplemented


class TrainController(Controller):
    def register_train(self, train, mac_address):
        raise NotImplemented
