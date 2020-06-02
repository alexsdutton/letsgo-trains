from gi.repository import GObject, Gtk

from trains.drawing import DrawnPiece
from trains.track import TrackPiece


class LayoutElement(Gtk.Grid):
    def __init__(self, piece, label):
        super().__init__()

        self.piece = piece
        self.drawn_piece = DrawnPiece.for_piece(piece)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(30, 30)
        self.attach(self.drawing_area, 0, 0, 1, 3)

        self.label = Gtk.Label(label)
        self.attach(self.label, 1, 0, 1, 1)


class LayoutListBox(Gtk.ListBox):
    def __new__(cls, layout, builder):
        self = builder.get_object('layout-listbox')
        self.__class__ = cls
        self.layout = layout
        self.builder = builder
        self.populate()
        return self

    def populate(self):
        for piece_cls in sorted(TrackPiece.registry.values(), key=lambda piece_cls: piece_cls.layout_priority):
            for option in piece_cls.get_layout_options():
                option = option.copy()
                label = option.pop('label')
                piece = piece_cls(layout=None, **option)
                layout_element = LayoutElement(piece, label)
                self.add(layout_element)
