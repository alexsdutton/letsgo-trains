import sys

import usb.core
import usb.util

from maestro import Maestro
from maestro.enums import USCParameter

dev = usb.core.find(idVendor=0x1ffb, idProduct=0x008a)

maestro = Maestro.for_device(dev)
# print(maestro)

while True:
    maestro.refresh_values()
    print(maestro[1].value)

# print(maestro.get_raw_parameter(USCParameter.ChannelModes0To3))