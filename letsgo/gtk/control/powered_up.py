import enum

from gi.repository import Gtk

from lego_wireless.enums import ColorNo, color_names
from lego_wireless.hub import Hub

from letsgo.control import HubConfig, PoweredUpController
from letsgo.gtk.control import GtkController


class _HubFields(enum.IntEnum):
    HubConfig = 0
    Name = 1
    BatteryLevel = 2
    Active = 3
    Connected = 4
    Train = 5
    Color = 6


class GtkPoweredUpController(GtkController, Gtk.Box):
    def __init__(self, controller: PoweredUpController):
        super().__init__(controller)
        controller.hub_discovered.connect(self.on_hub_discovered)
        # controller.hub_connected.connect(self.on_hub_connected)

        # self.hub_controls = Gtk.Box(
        #     orientation=Gtk.Orientation.VERTICAL,
        #     margin=5,
        # )
        # self.pack_start(self.hub_controls, False, False, 0)

        self.model = Gtk.ListStore(
            object,  # HubConfig
            str,  # Name
            int,  # BatteryLevel
            bool,  # Active
            bool,  # Connected
            object,  # Train
            str,  # Color
        )

        self.color_model = Gtk.ListStore(int, str)
        for color, name in color_names.items():
            self.color_model.append([color, name])

        self.view = Gtk.TreeView(model=self.model)
        self.view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(editable=True), text=_HubFields.Name)
        )
        self.view.append_column(
            Gtk.TreeViewColumn("Battery", Gtk.CellRendererProgress(), value=_HubFields.BatteryLevel)
        )
        active_cell_renderer = Gtk.CellRendererToggle(radio=False)
        # active_cell_renderer.set_property('editable', True)
        self.view.append_column(
            Gtk.TreeViewColumn("Active", active_cell_renderer, active=_HubFields.Active)
        )
        active_cell_renderer.connect('toggled', self.on_active_toggled)

        self.view.append_column(
            Gtk.TreeViewColumn("Connected", Gtk.CellRendererToggle(radio=False), active=_HubFields.Connected)
        )
        self.pack_start(self.view, True, True, 0)

        color_cell_renderer = Gtk.CellRendererCombo(editable=True, model=self.color_model, text_column=1, has_entry=False)
        self.view.append_column(
            Gtk.TreeViewColumn("Color", color_cell_renderer, text=_HubFields.Color)
        )
        color_cell_renderer.connect('changed', self.on_color_changed)

        for hub_config in self.controller.hubs.values():
            self.on_hub_discovered(self.controller, hub=hub_config.hub, hub_config=hub_config)

        self.pack_start(self.view, True, True, 0)

        self._connect_signals()

    def _connect_signals(self):
        self.connect('destroy-event', self._disconnect_signals)

    def _disconnect_signals(self, *args):
        pass

    def on_hub_discovered(self, sender, hub: Hub, hub_config: HubConfig):
        self.model.append([
            hub_config, hub.name, hub.battery_level, hub_config.active, hub_config.connected, hub_config.train, color_names.get(hub_config.color, '')
        ])
        hub_config.updated.connect(self.on_hub_config_updated)
        # hub.connect()

    def on_active_toggled(self, widget, path):
        print(widget.get_active())
        self.model[path][int(_HubFields.Active)] = not self.model[path][_HubFields.Active]
        self.model[path][_HubFields.HubConfig].active = self.model[path][_HubFields.Active]

    def on_color_changed(self, widget, path, new_iter):
        self.model[path][int(_HubFields.Color)] = color_names[self.color_model[new_iter][0]]
        self.model[path][_HubFields.HubConfig].color = ColorNo(self.color_model[new_iter][0])

    def on_hub_config_updated(self, sender: HubConfig):
        for row in self.model:
            if row[_HubFields.HubConfig] == sender:
                row[_HubFields.BatteryLevel] = sender.battery_level
                row[_HubFields.Connected] = sender.connected
                row[_HubFields.Active] = sender.active
                row[_HubFields.Color] = color_names.get(sender.color, '')
                print(dict(zip(_HubFields, row)))
        pass

class GtkPoweredUpHubControls(Gtk.Frame):
    def __init__(self, controller, hub):
        super().__init__(border_width=5)
        self.controller, self.hub = controller, hub
        self.hub = hub
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.hub_name_entry = Gtk.Entry()
        self.train_combo = Gtk.ComboBoxText()
        self.grid.attach(Gtk.Label('MAC address:'), 0, 0, 1, 1)
        self.grid.attach(Gtk.Label(hub.mac_address), 1, 0, 1, 1)
        self.grid.attach(Gtk.Label('Name:'), 0, 1, 1, 1)
        self.grid.attach(self.hub_name_entry, 1, 1, 1, 1)
        self.grid.attach(Gtk.Label('Train:'), 0, 2, 1, 1)
        self.grid.attach(self.train_combo, 1, 2, 1, 1)

        self.button = Gtk.Button()
        self.button.connect('clicked', self.on_button_clicked)
        self.grid.attach(self.button, 1, 3, 1, 1)

    def on_button_clicked(self, *args, **kwargs):
        print("Button")
        self.hub.name = 'Blue Shunter'
