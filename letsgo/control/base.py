import threading

from letsgo.registry_meta import WithRegistry

__all__ = ["Controller"]


class Controller(WithRegistry):
    entrypoint_name = "letsgo.controller"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_present = threading.Event()
