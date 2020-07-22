from typing import Dict, Type

from pkg_resources import iter_entry_points

from .base import *
from .maestro import *
from .powered_up import *


controller_classes: Dict[str, Type[Controller]] = {
    ep.name: ep.load() for ep in iter_entry_points("letsgo.controller")
}
