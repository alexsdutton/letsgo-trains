import math

import gi
import pkg_resources
import yaml
from cairo import Context

from trains.drawing import DrawnPiece
from trains.layout import Layout
from trains.track import Straight, Curve, TrackPiece

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, GLib, Gdk

class LayoutDrawer:
    def __init__(self, drawing_area, layout):
        self.drawing_area = drawing_area
        self.drawing_area.connect('draw', self.draw)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_MOTION_MASK)
        self.drawing_area.connect('button-press-event', self.mouse_press)
        self.drawing_area.connect('button-release-event', self.mouse_release)
        self.drawing_area.connect('motion-notify-event', self.mouse_motion)
        self.offset = 0, 0
        self.offset_orig = None
        self.mouse_down = None
        self.layout = layout

        GObject.timeout_add(50, self.move_trains)

    def move_trains(self):
        print("Moving trains")
        for train in self.layout.trains:
            train.position += 1

        ## This invalidates the screen, causing the expose event to fire.
        alloc = self.drawing_area.get_allocation()
        rect = Gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)
#        self.drawing_area.get_toplevel().invalidate_rect(rect, True)
        self.drawing_area.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)

        return True

    def mouse_press(self, widget, event):
        if event.button == Gdk.BUTTON_PRIMARY:
            self.offset_orig = self.offset
            self.mouse_down = event.x, event.y
    def mouse_release(self, widget, event):
        if event.button & Gdk.BUTTON_PRIMARY:
            self.offset_orig = None
            self.mouse_down = None
    def mouse_motion(self, widget, event):
        if self.mouse_down:
            self.offset = (self.offset_orig[0] + event.x - self.mouse_down[0],
                           self.offset_orig[1] + event.y - self.mouse_down[1])
            self.drawing_area.queue_draw()

    def draw(self, widget, cr):
        cr.set_line_width(9)
        cr.set_source_rgb(0.7, 0.2, 0.0)

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        #cr.identity_matrix()
        cr.translate(w / 2 + self.offset[0], h / 2 + self.offset[1])
        cr.scale(3, 3)
        self.base_ctm = cr.get_matrix()
        self.base_ctm.invert()
        #print(self.base_ctm)


        self.piece_matrices = {}

        self.draw_layout(self.layout, cr)
        self.draw_trains(self.layout, cr)

    def draw_layout(self, layout: Layout, cr: Context):
        seen_pieces = set()
        for piece in layout.placed_pieces:
            self.draw_piece(piece, seen_pieces, cr)

    def draw_piece(self, piece: TrackPiece, seen_pieces: set, cr: Context):
        seen_pieces.add(piece)

        drawn_piece = DrawnPiece.for_piece(piece)

        if piece.placement:
            cr.translate(piece.placement.x, piece.placement.y)
            cr.rotate(piece.placement.angle)

        drawn_piece.draw(cr)

        self.piece_matrices[piece] = cr.get_matrix()
        #print(cr.device_to_user(0, 0))

        relative_positions = drawn_piece.relative_positions()

        for anchor_name, anchor in piece.anchors.items():
            if anchor_name != piece.anchor_names[0]:
                cr.save()
                cr.translate(relative_positions[anchor_name].x, relative_positions[anchor_name].y)
                cr.rotate(relative_positions[anchor_name].angle)
                next_piece, next_anchor_name = anchor.next(piece)
                if next_piece and next_piece not in seen_pieces:
                    if next_anchor_name != next_piece.anchor_names[0]:
                        next_drawn_piece = DrawnPiece.for_piece(next_piece)
                        next_position = next_drawn_piece.relative_positions()[next_anchor_name]
                        cr.rotate(-next_position.angle + math.pi)
                        cr.translate(-next_position.x, -next_position.y)
                    self.draw_piece(next_piece, seen_pieces, cr)

                cr.set_source_rgb(1, 1, 0)
                cr.arc(0, 0, 1, 0, math.tau)
                cr.fill()

                cr.restore()

    def draw_trains(self, layout: Layout, cr: Context):
        print("Drawing trains")
        for train in layout.trains:
            cr.save()
            cr.set_matrix(self.piece_matrices[train.position.piece])

            #piece_x_y = 40, 40
            cr.set_source_rgb(0, 0, 1)
            cr.arc(0, 0, 5, 0, math.tau)
            print(cr.device_to_user(0, 0))
            cr.fill()
            cr.restore()