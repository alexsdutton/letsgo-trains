import logging
import os
import sys
import time
from typing import Dict, Type

import pkg_resources

import gi
import yaml

from letsgo.layout_parser import LayoutParser, get_parser_for_filename, parser_classes
from letsgo.layout_serializer import get_serializer_for_filename, serializer_classes
from letsgo.pieces.points import BasePoints

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from letsgo.gtk.configure_dialog import ConfigureDialog
from letsgo.gtk.layout import LayoutListBox
from letsgo.gtk.layout_drawingarea import LayoutDrawer
from letsgo.gtk.trains import TrainListBox
from letsgo.layout import Layout
from letsgo.topham_hatt import TophamHatt

from gi.repository import Gtk, Gio, GObject, GLib, Gdk

from .. import signals

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
            application_id=self.APPLICATION_ID, flags=Gio.ApplicationFlags.FLAGS_NONE
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

        self.builder = Gtk.Builder()
        self.builder.add_from_string(
            pkg_resources.resource_string("letsgo", "data/letsgo.glade").decode()
        )
        self.window = self.builder.get_object("main-window")
        self.window.set_title("Trains!")
        self.window.connect("window-state-event", self.on_window_state_event)

        self.status_bar: Gtk.Statusbar = self.builder.get_object("status-bar")

        # lego_wireless.signals.hub_discovered.connect(self.hub_discovered)
        # lego_wireless.signals.hub_connected.connect(self.hub_connected)
        # lego_wireless.signals.hub_disconnected.connect(self.hub_disconnected)

        self.canvas = self.builder.get_object("canvas")

        self.layout_area = self.builder.get_object("layout")

        self.layout = Layout()

        self.current_filename = None
        self.saved_epoch = self.layout.epoch

        signals.tick.connect(self.layout.tick)
        self.topham_hatt = TophamHatt(self.layout)
        signals.tick.connect(self.topham_hatt.tick)

        self.control_listbox = self.builder.get_object("control-listbox")
        self.train_listbox = TrainListBox(self.layout, self.builder)
        self.layout_listbox = LayoutListBox(self.layout, self.builder)
        self.configure_dialog = ConfigureDialog(self.layout, self.builder)
        self.builder.get_object("new-button").connect("clicked", self.on_new_clicked)
        self.builder.get_object("open-button").connect("clicked", self.on_open_clicked)
        self.builder.get_object("save-button").connect("clicked", self.on_save_clicked)

        self.menu = Gio.Menu()
        self.menu.append('Layout details', 'win.layout-details')
        self.menu.append('Save _as…', 'win.save-as')
        self.menu.append('About', 'app.about')

        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', lambda action, parameter: self.builder.get_object('about-dialog').run())
        self.builder.get_object('about-dialog').connect('delete-event', self.hide_about_dialog)
        self.builder.get_object('about-dialog').connect('response', self.hide_about_dialog)
        self.add_action(about_action)

        layout_details_action = Gio.SimpleAction.new('layout-details', None)
        self.window.add_action(layout_details_action)
        layout_details_action.connect(
            "activate", self.on_configure_clicked
        )


        save_as_action = Gio.SimpleAction.new('save-as', None)
        self.window.add_action(save_as_action)

        save_as_action.connect(
            "activate", self.on_save_as_clicked
        )

        self.builder.get_object('menu-button').set_menu_model(self.menu)



        self.window.connect("delete-event", self.on_delete_event)

        self.layout_drawer = LayoutDrawer(self.layout_area, self.layout)

        signals.piece_added.connect(self.on_piece_added, sender=self.layout)

        # self.layout.load_from_yaml(yaml.safe_load(pkg_resources.resource_string('letsgo', 'data/layouts/simple.yaml')))

        self.last_tick = time.time()
        GLib.timeout_add(30, self.send_tick)

        self.load_from_settings()

    def load_from_settings(self):
        window_state = self.settings.get_int("window-state")
        if window_state & Gdk.WindowState.MAXIMIZED:
            self.window.maximize()

    def on_new_clicked(self, widget):
        self.layout.clear()

    def on_open_clicked(self, widget):
        file_chooser = Gtk.FileChooserNative.new(
            "Open layout", self.window, Gtk.FileChooserAction.OPEN, "_Open", "_Cancel",
        )

        supported_file_filter = Gtk.FileFilter()
        supported_file_filter.set_name("All supported files")
        file_chooser.add_filter(supported_file_filter)

        for parser_cls in parser_classes:
            file_filter = Gtk.FileFilter()
            file_filter.set_name(
                f"{parser_cls.name} layout ({parser_cls.file_extension})"
            )
            supported_file_filter.add_pattern("*" + parser_cls.file_extension)
            file_filter.add_pattern("*" + parser_cls.file_extension)
            file_chooser.add_filter(file_filter)

        file_filter = Gtk.FileFilter()
        file_filter.set_name("All files")
        file_filter.add_pattern("*")
        file_chooser.add_filter(file_filter)

        if file_chooser.run() == Gtk.ResponseType.ACCEPT:
            filename = file_chooser.get_filename()
            parser = get_parser_for_filename(filename)
            if parser:
                self.layout.clear()
                with open(filename, "rb") as f:
                    parser.parse(f, self.layout)
                self.current_filename = filename
                self.saved_epoch = self.layout.epoch
            else:
                logger.warning("No parser for file %s", filename)

    def on_configure_clicked(self, action, parameter):
        if not self.configure_dialog.get_visible():
            self.configure_dialog.show()

    def on_window_state_event(self, widget, event):
        self.settings.set_int(
            "window-state", event.new_window_state & self.WINDOW_STATE_TO_SAVE
        )

    def send_tick(self):
        this_tick = time.time()
        signals.tick.send(
            self.layout, time=this_tick, time_elapsed=this_tick - self.last_tick
        )
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
            switch.set_active(piece.state == "branch")
            grid.attach(switch, 1, 1, 1, 1)
            configure = Gtk.Button.new_from_icon_name(
                "preferences-other", Gtk.IconSize.MENU
            )
            grid.attach(configure, 2, 0, 1, 2)
            # self.control_listbox.add(grid)

    def on_control_switch_activated(self, switch, gparam, points):
        points.state = "branch" if switch.get_active() else "out"

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

    def on_delete_event(self, widget: Gtk.Window, event: Gdk.Event) -> bool:
        """Should be called before the current layout is abandoned, either by closing or opening a new layout.

        :return: True if the current action should be cancelled, otherwise False, in line with signal propagation"""
        if self.layout.epoch == self.saved_epoch:
            return False

        if self.current_filename:
            layout_name = f' "{os.path.basename(self.current_filename)}"'
        else:
            layout_name = ""

        dialog = Gtk.MessageDialog(
            parent=self.window, modal=True, destroy_with_parent=True,
        )

        dialog.set_markup(
            f'<span weight="bold" size="larger">Save changes to layout{layout_name} before closing?</span>'
        )
        dialog.format_secondary_text(
            "If you don't save, changes will be permanently lost."
        )

        close_without_saving_button = dialog.add_button(
            "Close _without Saving", Gtk.ResponseType.NO
        )
        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button(
            "_Save" if self.current_filename else "_Save As…", Gtk.ResponseType.YES
        )

        close_without_saving_button.get_style_context().add_class(
            Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION
        )

        dialog.set_default_response(Gtk.ResponseType.YES)

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            return self.on_save_clicked()

        return response == Gtk.ResponseType.CANCEL

    def on_save_clicked(self, *args, **kwargs):
        if not self.current_filename:
            return self.on_save_as_clicked()

        serializer = get_serializer_for_filename(self.current_filename)
        if not serializer:
            return self.on_save_as_clicked()

        with open(self.current_filename, "wb") as fp:
            serializer.serialize(fp, self.layout)
            self.saved_epoch = self.layout.epoch

        return False

    def on_save_as_clicked(self, *args, **kwargs):
        file_chooser = Gtk.FileChooserNative.new(
            "Save layout", self.window, Gtk.FileChooserAction.SAVE, "_Save", "_Cancel",
        )

        file_chooser.set_do_overwrite_confirmation(True)
        if self.current_filename:
            file_chooser.set_filename(self.current_filename)
        else:
            file_chooser.set_current_name("layout.lgl")

        for serializer_cls in serializer_classes:
            file_filter = Gtk.FileFilter()
            file_filter.set_name(
                f"{serializer_cls.name} layout ({serializer_cls.file_extension})"
            )
            file_filter.add_pattern("*" + serializer_cls.file_extension)
            file_chooser.add_filter(file_filter)

        if file_chooser.run() == Gtk.ResponseType.ACCEPT:
            filename = file_chooser.get_filename()
            serializer = get_serializer_for_filename(filename)
            if serializer:
                with open(filename, "wb") as fp:
                    serializer.serialize(fp, self.layout)
                self.current_filename = filename
                self.saved_epoch = self.layout.epoch
            else:
                logger.warning("No parser for file %s", filename)

            return False
        else:
            return True

    def hide_about_dialog(self, dialog, *args):
        dialog.hide()
        return True


def main():
    app = Application()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
