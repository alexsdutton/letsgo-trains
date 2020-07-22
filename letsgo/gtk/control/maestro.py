from gi.repository import Gtk
from letsgo.control import MaestroController
from letsgo.gtk.control import GtkController


class GtkMaestroController(GtkController, Gtk.Box):
    def __init__(self, controller: MaestroController):
        super().__init__(controller)

        l = Gtk.Label()
        l.set_text('MMM')
        self.pack_start(Gtk.Label('Maestro Servo Controller'), True, True, 0)
        self.pack_start(l, True, True, 0)

        self._connect_signals()

    def _connect_signals(self):
        self.connect('destroy-event', self._disconnect_signals)

    def _disconnect_signals(self, *args):
        pass