import logging
import threading
import typing
from typing import Dict

import blinker

import lego_wireless
import lego_wireless.signals
from lego_wireless.enums import ColorNo
from lego_wireless.hub import Hub
from letsgo.train import Train
from .base import TrainController

logger = logging.getLogger(__name__)


class HubConfig:
    def __init__(
        self,
        *,
        hub: Hub = None,
        active: bool = False,
        color: ColorNo = None,
        train: Train = None,
        battery_level: int = None,
    ):
        self._hub = None
        self._active = active
        self._color = color
        self._train = train
        self._connected = hub and hub.connected
        self._battery_level = battery_level

        self.updated = blinker.Signal()
        self.hub = hub

    @property
    def hub(self):
        return self._hub

    @hub.setter
    def hub(self, hub: Hub):
        if hub == self._hub:
            return
        if self._hub:
            lego_wireless.signals.hub_connected.connect(self.on_hub_connected)
            lego_wireless.signals.hub_disconnected.connect(self.on_hub_disconnected)
            if self._hub.connected:
                self._hub.async_disconnect()
        self._hub = hub
        if self._hub:
            lego_wireless.signals.hub_connected.connect(
                self.on_hub_connected, sender=self._hub
            )
            lego_wireless.signals.hub_disconnected.connect(
                self.on_hub_disconnected, sender=self._hub
            )
            if self._active and not hub.connected:
                hub.async_connect()
        self.updated.send(self)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        if active == self._active:
            return
        if active and self._hub and not self._hub.connected:
            self._hub.async_connect()
        elif not active and self._hub and self._hub.connected:
            self._hub.async_disconnect()
        self._active = active
        self.updated.send(self)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color: ColorNo):
        if color == self._color:
            return
        self._color = color
        if (
            color is not None
            and self._hub
            and self._hub.connected
            and self._hub.rgb_light
        ):
            self._hub.rgb_light.set_rgb_color_no(color)
        self.updated.send()

    @property
    def connected(self):
        return self._connected

    @property
    def battery_level(self):
        return self._battery_level

    @property
    def train(self):
        return self._train

    @train.setter
    def train(self, train):
        self._train = train

    def on_hub_connected(self, hub):
        lego_wireless.signals.hub_battery_level.connect(
            self.on_hub_battery_level, sender=hub
        )
        if self.color is not None and hub.rgb_light:
            print("Resetting color")
            hub.rgb_light.set_rgb_color_no(self.color)
        self._connected = True
        self.updated.send(self)

    def on_hub_disconnected(self, hub):
        lego_wireless.signals.hub_battery_level.disconnect(self.on_hub_battery_level)
        self._connected = False
        self.updated.send(self)

    def on_hub_battery_level(self, sender, battery_level):
        self._battery_level = battery_level
        self.updated.send(self)


class PoweredUpController(TrainController):
    label = "Powered UP"

    def __init__(
        self, adapter_name="hci0", hubs: Dict[str, HubConfig] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.hub_manager = lego_wireless.HubManager(adapter_name)
        self.hub_manager_thread = threading.Thread(target=self.hub_manager.run)

        self.hub_discovered = blinker.Signal()
        self.hub_connected = blinker.Signal()
        self.hub_disconnected = blinker.Signal()

        lego_wireless.signals.hub_discovered.connect(self.on_hub_discovered)
        # lego_wireless.signals.hub_connected.connect(self.on_hub_connected)
        # lego_wireless.signals.hub_disconnected.connect(self.on_hub_disconnected)

        self.hubs: Dict[str, HubConfig] = hubs or {}
        self.pairings: Dict[Hub, Train] = {}

        self.discovered_mac_addresses: typing.Set[str] = set()

        # self.trains = {}
        # self.train_hubs = {}
        # self.pair_with = []

    def start(self):
        try:
            if self.hub_manager.is_adapter_powered:
                logger.info("Starting Powered UP controller")
                self.device_present.set()
                self.hub_manager.start_discovery()
                self.hub_manager_thread.start()
                for device in self.hub_manager.devices():
                    pass
            else:
                logger.warning(
                    "Attempted to start Powered UP controller, but Bluetooth adapter not powered"
                )
                # self.hub_manager.device_discovered(device)
        except:
            pass

    def stop(self):
        logger.info("Stopping Powered Up controller")
        self.hub_manager.stop()

    def register_train(self, train, mac_address):
        self.trains[mac_address.lower()] = train
        train.connected = False

    def on_hub_discovered(self, sender, hub):
        logger.info("Powered UP hub discovered: %r", hub)
        mac_address = hub.mac_address.lower()
        if mac_address not in self.hubs:
            self.hubs[mac_address] = HubConfig(hub=hub)
        else:
            self.hubs[mac_address].hub = hub
        if mac_address not in self.discovered_mac_addresses:
            self.discovered_mac_addresses.add(mac_address)
            self.hub_discovered.send(hub=hub, hub_config=self.hubs[mac_address])

    #
    # def on_hub_connected(self, sender, hub):
    #     mac_address = hub.mac_address.lower()
    #     lego_wireless.signals.hub_battery_level.connect(
    #         self.on_hub_battery_level, sender=hub
    #     )
    #     self.hub_connected.send(hub=hub)

    # def on_hub_disconnected(self, sender, hub):
    #     pass
    #
    # def on_hub_battery_level(self, sender, battery_level):
    #     pass  # self.trains[sender.mac_address.lower()].battery_level = battery_level

    # def set_train_lights(self, train: Train, value: bool):
    #     hub = self.train_hubs.get(train)
    #     if hub and hub.led_light:
    #         hub.led_light.set_brightness(100 if value else 0)
    #         return True

    # def set_train_motor_speed(self, train: Train, value: float):
    #     hub = self.train_hubs.get(train)
    #     if hub and hub.train_motor:
    #         hub.train_motor.set_speed(int(value * 100))
    #         return True

    def to_yaml(self) -> dict:
        return {
            **super().to_yaml(),
            "hubs": {
                mac_address: {
                    "active": hub_config.active,
                    "color": hub_config.color.name if hub_config.color else None,
                }
                for mac_address, hub_config in self.hubs.items()
            },
        }
