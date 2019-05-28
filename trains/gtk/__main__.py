import os
import sys
import threading

import pkg_resources

import gi
import yaml

from trains.drawing import DrawnPiece
from trains.gtk.layout_drawingarea import LayoutDrawer
from trains.layout import Layout
from trains.track import TrackPiece

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, GLib, Gdk


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.myap")

        self.builder = Gtk.Builder()
        self.builder.add_from_string(pkg_resources.resource_string('trains', 'data/trains.glade').decode())
        self.window = self.builder.get_object('main-window')

        self.status_bar: Gtk.Statusbar = self.builder.get_object('status-bar')

        # self.hub_manager = lego_wireless.HubManager('hci0')
        # self.hub_manager_thread = threading.Thread(target=self.hub_manager.run)
        #
        # lego_wireless.signals.hub_connected.connect(self.hub_connected)
        # lego_wireless.signals.hub_disconnected.connect(self.hub_disconnected)

        self.canvas = self.builder.get_object('canvas')

        self.layout_target_entries = [
            Gtk.TargetEntry('LAYOUT', Gtk.TargetFlags.SAME_APP, 0)
        ]

        self.layout = Layout.from_yaml(yaml.safe_load(pkg_resources.resource_string('trains', 'data/layouts/other.yaml')))

        self.layout_palette = self.builder.get_object('layout-palette')
        self.layout_palette.add(self.get_track_piece_toolgroup())
        self.layout_area = self.builder.get_object('layout')
        self.layout_drawer = LayoutDrawer(self.layout_area, self.layout)

    def get_track_piece_toolgroup(self):
        toolitemgroup = Gtk.ToolItemGroup(label='Track')
        toolitemgroup.add(self.get_track_piece_toolitem('straight'))
        toolitemgroup.add(self.get_track_piece_toolitem('curve'))
        toolitemgroup.add(self.get_track_piece_toolitem('crossover'))
        toolitemgroup.add(self.get_track_piece_toolitem('points'))
        return toolitemgroup

    def get_track_piece_toolitem(self, name):
        tool = Gtk.ToggleToolButton.new()
        tp = TrackPiece.registry[name]()

        image = Gtk.Image.new_from_file(os.path.join(os.path.dirname(__file__), 'data', 'pieces', tp.name + '.png'))
        tool.set_label(tp.label)
        tool.get_child().set_always_show_image(True)
        tool.get_child().set_image(image)


        return tool

    def run(self, *args, **kwargs):
        # self.hub_manager_thread.start()
        super().run(*args, **kwargs)

    # def hub_connected(self, sender, hub):
    #     hub_status_context = self.status_bar.get_context_id('hub')
    #     self.status_bar.push(hub_status_context, 'Hub connected')
    #     self.train_box.pack_end(TrainEntry(hub), False, False, 0)
    #
    # def hub_disconnected(self, sender, hub):
    #     hub_status_context = self.status_bar.get_context_id('hub')
    #     self.status_bar.push(hub_status_context, 'Hub disconnected')

    def do_activate(self):
        Gtk.Application.do_activate(self)
        print(self.window)
        self.window.set_application(self)
        self.window.show_all()
        print('here')

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_shutdown(self):
        # self.hub_manager.stop()
        # self.hub_manager_thread.join()
        Gtk.Application.do_shutdown(self)


if __name__ == '__main__':
    app = Application()
    app.run(sys.argv)