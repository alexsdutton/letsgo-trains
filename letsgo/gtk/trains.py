import typing

from gi.repository import GObject, Gtk
from letsgo.layout import Layout

from letsgo.train import Train
from .. import signals


def get_train_controller(layout):
    for controller in layout.controllers.values():
        if Train in controller.controller_for:
            return controller


class TrainControls(Gtk.Grid):
    def __init__(self, train, popover):
        super().__init__()
        self.train = train
        self.popover = popover
        self.hub = None

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(30, 30)
        self.attach(self.drawing_area, 0, 0, 1, 3)
        self.label = Gtk.Label(train.meta.get("label", train.name or "Train"))
        signals.train_name_changed.connect(
            lambda sender, name: self.label.set_label(name or "Train"),
            sender=train,
            weak=False,
        )
        self.label.set_halign(Gtk.Align.START)
        self.attach(self.label, 1, 0, 1, 1)
        self.configure = Gtk.Button.new_from_icon_name(
            "gtk-properties", Gtk.IconSize.MENU
        )
        self.configure.connect("clicked", self.on_popover_show)
        self.attach(self.configure, 3, 0, 1, 2)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(box.get_style_context(), "linked")

        stop = Gtk.ToggleButton(label="\N{Back With Leftwards Arrow Above}")
        stop.connect("toggled", self.on_backwards_toggled)
        box.add(stop)
        stop = Gtk.Button(label="\N{Large Red Circle}")
        stop.connect("clicked", self.on_speed_button, lambda s: 0)
        box.add(stop)
        decrease_speed = Gtk.Button(label="\N{Heavy Minus Sign}")
        decrease_speed.connect("clicked", self.on_speed_button, lambda s: s - 0.1)
        box.add(decrease_speed)
        increase_speed = Gtk.Button(label="\N{Heavy Plus Sign}")
        increase_speed.connect("clicked", self.on_speed_button, lambda s: s + 0.1)
        box.add(increase_speed)

        self.attach(box, 1, 1, 1, 1)

        lights_button = Gtk.ToggleButton(label="\N{Electric Light Bulb}")
        lights_button.set_active(train.lights_on)
        lights_button.connect("toggled", self.on_lights_toggled)
        self.attach(lights_button, 2, 1, 1, 1)

        self.battery_level = Gtk.Label()
        self.attach(self.battery_level, 0, 2, 1, 2)

        signals.connected_changed.connect(self.on_connected_changed, sender=self.train)
        signals.battery_level_changed.connect(
            self.on_battery_level_changed, sender=self.train
        )

    def on_speed_button(self, widget, func):
        self.train.maximum_motor_speed = func(self.train.maximum_motor_speed)
        if self.hub and self.hub.train_motor:
            self.hub.train_motor.set_speed(int(self.train.motor_speed * 100))

    def on_lights_toggled(self, widget):
        self.train.lights_on = widget.get_active()

    def on_backwards_toggled(self, widget):
        pass

    def on_popover_show(self, widget):
        self.popover.set_relative_to(widget)
        self.popover.hub = self.train
        self.popover.show_all()
        self.popover.popup()

    def on_connected_changed(self, sender, connected):
        pass

    def on_battery_level_changed(self, sender, battery_level):
        self.battery_level.set_label(
            f"{battery_level}%" if battery_level is not None else ""
        )


class TrainPopover(Gtk.Popover):
    def __new__(cls, builder: Gtk.Builder):
        self = builder.get_object("train-popover")
        self.__class__ = cls
        return self

    def __init__(self, builder: Gtk.Builder):
        self._train: typing.Optional[Train] = None
        self.pair_button: Gtk.Button = builder.get_object("train-powered-up-pair")
        self.pair_status: Gtk.Label = builder.get_object("train-powered-up-status")
        self.name_entry: Gtk.Entry = builder.get_object("train-name-entry")
        self.pair_button.connect("clicked", self.on_pair_clicked)
        self.name_entry.connect("changed", self.on_name_changed)
        self.connect("closed", self.on_closed)

    @property
    def train(self):
        return self._train

    @train.setter
    def train(self, train):
        self._train = train
        if train:
            self.name_entry.set_text(train.name or "")
            self.pair_button.set_label("Unpair" if train.controller else "Pair")

    def on_pair_clicked(self, widget):
        train_controller = get_train_controller(self.train.layout)
        if self.train.controller:
            widget.set_label("Pair")
            self.train.controller = None
            self.train.controller_parameters = {}
        else:
            train_controller.pair_with.append(self.train)
            self.pair_status.set_label("Searching…")
            signals.controller_changed.connect(
                self.on_controller_changed, sender=self.train
            )
            GObject.timeout_add(10000, self.stop_pairing, self.train)

    def on_controller_changed(self, sender, controller):
        if controller:
            self.pair_status.set_label("Connected")
            self.pair_button.set_label("Disconnect")
        else:
            self.pair_status.set_label("")
            self.pair_button.set_label("Pair")

    def stop_pairing(self, train):
        signals.controller_changed.disconnect(
            self.on_controller_changed, sender=self.train
        )
        train_controller = get_train_controller(train.layout)
        try:
            train_controller.pair_with.remove(train)
        except ValueError:
            pass

        if self.pair_status.get_label() == "Searching…":
            self.pair_status.set_label("")

    def on_name_changed(self, widget):
        self.train.name = widget.get_text()

    def on_closed(self, widget):
        self.train = None


class TrainListBox(Gtk.ListBox):
    def __new__(cls, layout, builder):
        self = builder.get_object("train-listbox")
        self.__class__ = cls
        self.layout = layout
        self.builder = builder
        self._train_controls_by_train = {}
        self.popover = TrainPopover(self.builder)
        signals.train_added.connect(self.on_train_added, layout)
        signals.train_removed.connect(self.on_train_removed, layout)
        return self

    def on_layout_set(self, sender, layout):
        signals.train_added.disconnect(self.on_train_added)
        for train_controls in self.get_children():
            train_controls.destroy()
        signals.train_added.connect(self.on_train_added, layout)

    def on_train_added(self, sender, train):
        train_controls = TrainControls(train=train, popover=self.popover)
        self._train_controls_by_train[train] = train_controls
        self.add(train_controls)

    def on_train_removed(self, sender, train):
        train_controls = self._train_controls_by_train.pop(train)
        train_controls.destroy()
