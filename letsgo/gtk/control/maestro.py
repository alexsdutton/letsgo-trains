import enum

from gi.repository import Gtk
from letsgo.control import MaestroController
from letsgo.gtk.control import GtkController


class _ChannelFields(enum.IntEnum):
    Index = 0
    ChannelDefinition = 1
    Subject = 2


class GtkMaestroController(GtkController, Gtk.Box):
    controller: MaestroController

    def __init__(self, controller: MaestroController):
        super().__init__(controller)

        self.model = Gtk.ListStore(
            int,  # index
            object,  # MaestroChannelDefinition
            object,  # subject
        )

        self.subject_model = Gtk.ListStore(int, str)

        self.view = Gtk.TreeView(model=self.model)
        self.view.append_column(
            Gtk.TreeViewColumn(
                "Channel",
                Gtk.CellRendererText(editable=False),
                text=_ChannelFields.Index,
            )
        )
        self.view.append_column(
            Gtk.TreeViewColumn(
                "Connect to", Gtk.CellRendererProgress(), value=_ChannelFields.Subject
            )
        )
        self.pack_start(self.view, True, True, 0)

    def on_presence_changed(self, sender, present):
        super().on_presence_changed(sender, present)
        print("OOO")

        if present:
            for index in range(self.controller.channel_count):
                channel_definition = self.controller.channels.get(index)
                self.model.append(
                    [
                        index,
                        channel_definition,
                        channel_definition.subject if channel_definition else None,
                    ]
                )
        else:
            self.model.clear()
