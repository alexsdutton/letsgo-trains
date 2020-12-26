import pkg_resources

from gi.repository import Gtk


def get_builder():
    builder = Gtk.Builder()
    builder.add_from_string(
        pkg_resources.resource_string("letsgo", "data/letsgo.glade").decode()
    )
    return builder
