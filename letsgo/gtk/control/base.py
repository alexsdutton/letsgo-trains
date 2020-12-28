from gi.repository import Gtk

from letsgo import signals
from letsgo.control import Controller


class GtkController(Gtk.Box):
    entrypoint_group = "letsgo.gtk.controller"

    presence_text = {True: "✅", False: "❎"}

    def __init__(self, controller: Controller):
        self.controller = controller
        super().__init__(orientation=Gtk.Orientation.VERTICAL, margin=5)

        self.pack_top_bar()

        self._connect_signals()

    def pack_top_bar(self):
        top_bar = Gtk.Box()
        top_bar.pack_start(Gtk.Label(label=self.controller.label), False, False, 0)
        remove_button = Gtk.Button(
            image=Gtk.Image.new_from_icon_name("edit-delete", Gtk.IconSize.BUTTON),
            tooltip_text="Remove controller",
        )

        remove_button.set_detailed_action_name(
            f"win.controller-remove::{self.controller.id}"
        )

        self.device_present_indicator = Gtk.Label(
            label=self.presence_text[self.controller.device_present]
        )

        top_bar.pack_end(remove_button, False, False, 0)
        top_bar.pack_end(self.device_present_indicator, False, False, 5)
        self.pack_start(top_bar, False, False, 0)

    def on_presence_changed(self, sender, present):
        self.device_present_indicator.set_text(self.presence_text[present])

    def _connect_signals(self):
        self.connect("destroy-event", self._disconnect_signals)
        signals.controller_presence_changed.connect(
            self.on_presence_changed, self.controller
        )

    def _disconnect_signals(self, *args):
        signals.controller_presence_changed.disconnect(
            self.on_presence_changed, self.controller
        )
