import logging
import os
import sys
import gi

gi.require_version('Gtk', '3.0')

from letsgo.gtk.utils import get_builder
from letsgo.gtk.window import LayoutWindow

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gio, GObject, GLib, Gdk

logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    APPLICATION_ID = "uk.dutton.letsgo-trains"

    WINDOW_STATE_TO_SAVE = (
        Gdk.WindowState.MAXIMIZED
        | Gdk.WindowState.LEFT_TILED
        | Gdk.WindowState.RIGHT_TILED
        | Gdk.WindowState.TOP_TILED
        | Gdk.WindowState.BOTTOM_TILED
    )

    def __init__(self):
        super().__init__(
            application_id=self.APPLICATION_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN
        )

        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.join(os.path.dirname(__file__), "..", "data"),
            Gio.SettingsSchemaSource.get_default(),
            False,
        )
        schema = Gio.SettingsSchemaSource.lookup(
            schema_source, self.APPLICATION_ID, False
        )
        self.settings = Gio.Settings.new_full(schema, None, None)

        # self.settings = Gio.Settings.new(self.APPLICATION_ID)

        self.builder = get_builder()

        self.window = LayoutWindow()

        self.load_from_settings()

    def load_from_settings(self):
        window_state = self.settings.get_int("window-state")
        if window_state & Gdk.WindowState.MAXIMIZED:
            self.window.maximize()

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        self.window.layout.start()

    def do_activate(self):
        Gtk.Application.do_activate(self)
        self.window.set_application(self)
        self.window.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        self.window.layout.stop()
        Gtk.Application.do_shutdown(self)

    def do_open(self, files, *args):
        self.window.load_from_filename(files[0].get_path())
        self.do_activate()

def main():
    app = Application()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
