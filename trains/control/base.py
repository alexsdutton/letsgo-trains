import threading

from trains.registry_meta import WithRegistry

__all__ = ["Controller"]


class Controller(WithRegistry):
    entrypoint_name = "trains.controller"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_present = threading.Event()
