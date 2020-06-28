import threading

import lego_wireless
from letsgo.train import Train

from .base import Controller
from .. import signals


class PoweredUpController(Controller):
    registry_type = "powered_up"
    controller_for = {Train}

    def __init__(self, adapter_name="hci0", **kwargs):
        super().__init__(**kwargs)
        self.hub_manager = lego_wireless.HubManager(adapter_name)
        self.hub_manager_thread = threading.Thread(target=self.hub_manager.run)

        lego_wireless.signals.hub_discovered.connect(self.hub_discovered)
        lego_wireless.signals.hub_connected.connect(self.hub_connected)
        lego_wireless.signals.hub_disconnected.connect(self.hub_disconnected)

        self.trains = {}
        self.train_hubs = {}
        self.pair_with = []

    def start(self):
        try:
            if self.hub_manager.is_adapter_powered:
                self.device_present.set()
                self.hub_manager.start_discovery()
                self.hub_manager_thread.start()
                for device in self.hub_manager.devices():
                    pass
                    # self.hub_manager.device_discovered(device)
        except:
            pass

    def stop(self):
        self.hub_manager.stop()

    def register_train(self, train, mac_address):
        self.trains[mac_address.lower()] = train
        train.connected = False

    def start_discovery(self, train):
        self.pair_with.append(train)

    def stop_discovery(self, train):
        self.pair_with.remove(train)

    def hub_discovered(self, sender, hub):
        train = None
        if hub.mac_address.lower() in self.trains:
            train = self.trains[hub.mac_address.lower()]
        elif self.pair_with:
            train = self.pair_with.pop(0)
            train.controller = self
            train.controller_parameters = {"mac_address": hub.mac_address.lower()}
        if train:
            self.trains[hub.mac_address.lower()] = train
            self.train_hubs[train] = hub
            hub.connect()

    def hub_connected(self, sender, hub):
        self.trains[hub.mac_address.lower()].connected = True
        lego_wireless.signals.hub_battery_level.connect(
            self.on_hub_battery_level, sender=hub
        )

    def hub_disconnected(self, sender, hub):
        lego_wireless.signals.hub_battery_level.disconnect(
            self.on_hub_battery_level, sender=hub
        )
        self.trains[hub.mac_address.lower()].connected = False

    def on_hub_battery_level(self, sender, battery_level):
        self.trains[sender.mac_address.lower()].battery_level = battery_level

    def set_train_lights(self, train: Train, value: bool):
        hub = self.train_hubs.get(train)
        if hub and hub.led_light:
            hub.led_light.set_brightness(100 if value else 0)
            return True

    def set_train_motor_speed(self, train: Train, value: float):
        hub = self.train_hubs.get(train)
        if hub and hub.train_motor:
            hub.train_motor.set_speed(int(value * 100))
            return True
