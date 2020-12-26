from gi.repository import Gtk

from letsgo.control import Controller


class GtkController(Gtk.Box):
    entrypoint_group = "letsgo.gtk.controller"

    def __init__(self, controller: Controller):
        self.controller = controller
        super().__init__(orientation=Gtk.Orientation.VERTICAL, margin=5)

        self.pack_top_bar()

    def pack_top_bar(self):
        top_bar = Gtk.Box()
        top_bar.pack_start(Gtk.Label(label=self.controller.label), False, False, 0)
        remove_button = Gtk.Button(
            image=Gtk.Image.new_from_icon_name("edit-delete", Gtk.IconSize.BUTTON),
            # action_name='win.controller-remove::foo', # f'win.controller-remove::{self.controller.id}',
            tooltip_text="Remove controller",
        )

        # remove_button.set_text('Remove controller')
        # remove_button.set_image('edit-delete')
        remove_button.set_detailed_action_name(
            f"win.controller-remove::{self.controller.id}"
        )
        top_bar.pack_end(remove_button, False, False, 0)
        self.pack_start(top_bar, False, False, 0)
