import os
import sys
import threading
import time

import pkg_resources

import gi
import yaml
from trains.pieces.points import BasePoints

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from trains.gtk.configure_dialog import ConfigureDialog
from trains.gtk.layout import LayoutListBox
from trains.gtk.layout_drawingarea import LayoutDrawer
from trains.gtk.trains import TrainListBox
from trains.layout import Layout
from trains.topham_hatt import TophamHatt
from trains.pieces import Piece

from gi.repository import Gtk, Gio, GObject, GLib, Gdk

from .. import signals, track


class Application(Gtk.Application):
    APPLICATION_ID = 'uk.dutton.trains'

    WINDOW_STATE_TO_SAVE = (
            Gdk.WindowState.MAXIMIZED |
            Gdk.WindowState.LEFT_TILED |
            Gdk.WindowState.RIGHT_TILED |
            Gdk.WindowState.TOP_TILED |
            Gdk.WindowState.BOTTOM_TILED
    )

    def __init__(self):
        super().__init__(application_id=self.APPLICATION_ID,
                                    flags=Gio.ApplicationFlags.FLAGS_NONE)

        schema_source = Gio.SettingsSchemaSource.new_from_directory(os.path.join(os.path.dirname(__file__), '..', 'data'),
                                                                    Gio.SettingsSchemaSource.get_default(), False)
        schema = Gio.SettingsSchemaSource.lookup(schema_source, 'apps.' + self.APPLICATION_ID, False)
        self.settings = Gio.Settings.new_full(schema, None, None)

        # self.settings = Gio.Settings.new(self.APPLICATION_ID)

        self.builder = Gtk.Builder()
        self.builder.add_from_string(pkg_resources.resource_string('trains', 'data/trains.glade').decode())
        self.window = self.builder.get_object('main-window')
        self.window.set_title('Trains!')
        self.window.connect('window-state-event', self.on_window_state_event)

        self.status_bar: Gtk.Statusbar = self.builder.get_object('status-bar')

        # lego_wireless.signals.hub_discovered.connect(self.hub_discovered)
        # lego_wireless.signals.hub_connected.connect(self.hub_connected)
        # lego_wireless.signals.hub_disconnected.connect(self.hub_disconnected)


        self.canvas = self.builder.get_object('canvas')


        self.layout_area = self.builder.get_object('layout')

        self.layout = Layout()
        signals.tick.connect(self.layout.tick)
        self.topham_hatt = TophamHatt(self.layout)
        signals.tick.connect(self.topham_hatt.tick)

        self.control_listbox = self.builder.get_object('control-listbox')
        self.train_listbox = TrainListBox(self.layout, self.builder)
        self.layout_listbox = LayoutListBox(self.layout, self.builder)
        self.configure_dialog = ConfigureDialog(self.layout, self.builder)
        self.builder.get_object('configure-button').connect('clicked', self.on_configure_clicked)
        self.builder.get_object('new-button').connect('clicked', self.on_new_clicked)

        self.layout_drawer = LayoutDrawer(self.layout_area, self.layout)

        signals.piece_added.connect(self.on_piece_added, sender=self.layout)

        self.layout.load_from_yaml(yaml.safe_load(pkg_resources.resource_string('trains', 'data/layouts/stations.yaml')))

        self.last_tick = time.time()
        GLib.timeout_add(30, self.send_tick)

        self.load_from_settings()


    def load_from_settings(self):
        window_state = self.settings.get_int('window-state')
        if window_state & Gdk.WindowState.MAXIMIZED:
            self.window.maximize()

    def on_new_clicked(self, widget):
        self.layout.clear()

    def on_configure_clicked(self, widget):
        if self.configure_dialog.get_visible():
            self.configure_dialog.hide()
        else:
            self.configure_dialog.show_all()

    def on_window_state_event(self, widget, event):
        self.settings.set_int('window-state', event.new_window_state & self.WINDOW_STATE_TO_SAVE)

    def send_tick(self):
        this_tick = time.time()
        signals.tick.send(self.layout, time=this_tick, time_elapsed=this_tick - self.last_tick)
        self.last_tick = this_tick
        return True

    def on_piece_added(self, sender, piece):
        if isinstance(piece, BasePoints):
            grid = Gtk.Grid()
            drawing_area = Gtk.DrawingArea()
            drawing_area.set_size_request(30, 30)
            grid.attach(drawing_area, 0, 0, 1, 2)
            label = Gtk.Label()
            label.set_text(piece.label.title())
            label.set_halign(Gtk.Align.START)
            grid.attach(label, 1, 0, 1, 1)
            switch = Gtk.Switch()
            switch.connect("notify::active", self.on_control_switch_activated, piece)
            switch.set_active(piece.state == 'branch')
            grid.attach(switch, 1, 1, 1, 1)
            configure = Gtk.Button.new_from_icon_name('preferences-other', Gtk.IconSize.MENU)
            grid.attach(configure, 2, 0, 1, 2)
            # self.control_listbox.add(grid)

    def on_control_switch_activated(self, switch, gparam, points):
        points.state = 'branch' if switch.get_active() else 'out'

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        self.layout.start()

    def do_activate(self):
        Gtk.Application.do_activate(self)
        self.window.set_application(self)
        self.window.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        self.layout.stop()
        Gtk.Application.do_shutdown(self)


def main():
    app = Application()
    app.run(sys.argv)

if __name__ == '__main__':
    main()
