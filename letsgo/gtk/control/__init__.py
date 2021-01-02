from typing import Dict, Type

from pkg_resources import iter_entry_points

from .base import GtkController

from .maestro import GtkMaestroController
from .powered_up import GtkPoweredUpController

gtk_controller_classes: Dict[str, Type[GtkController]] = {
    ep.name: ep.load() for ep in iter_entry_points("letsgo.gtk.controller")
}
