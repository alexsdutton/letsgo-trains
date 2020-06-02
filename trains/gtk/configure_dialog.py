from gi.repository import GObject, Gtk

class ConfigureDialog(Gtk.Dialog):
    def __new__(cls, layout, builder):
        self = builder.get_object('configure-dialog')
        self.__class__ = cls
        self.layout = layout
        self.builder = builder
        self.builder.get_object('close-configure-dialog-button').connect('clicked', self.on_close_clicked)
        return self

    def on_close_clicked(self, widget):
        self.hide()
