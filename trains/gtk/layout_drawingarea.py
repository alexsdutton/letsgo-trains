import math
import random

import gi
from cairo import Context

from trains.drawing import DrawnPiece, hex_to_rgb
from trains.layout import Layout
from trains.track import TrackPiece
from .. import signals

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import GObject, Gdk


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

        signals.tick.connect(self.tick)

    def tick(self, sender, time, time_elapsed):
        alloc = self.drawing_area.get_allocation()
        self.drawing_area.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)

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
        self.draw_points_labels(self.layout, cr)
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

        self.piece_matrices[piece] = cr.get_matrix() * self.base_ctm

        relative_positions = drawn_piece.relative_positions()

        for anchor_name, anchor in piece.anchors.items():
            next_piece, next_anchor_name = anchor.next(piece)
            cr.save()

            if anchor_name in relative_positions:
                cr.translate(relative_positions[anchor_name].x, relative_positions[anchor_name].y)
                cr.rotate(relative_positions[anchor_name].angle)
            else:
                cr.rotate(math.pi)

            if next_piece and next_piece not in seen_pieces:
                if next_anchor_name != next_piece.anchor_names[0]:
                    next_drawn_piece = DrawnPiece.for_piece(next_piece)
                    next_position = next_drawn_piece.relative_positions()[next_anchor_name]
                    cr.rotate(-next_position.angle + math.pi)
                    cr.translate(-next_position.x, -next_position.y)
                self.draw_piece(next_piece, seen_pieces, cr)

            cr.set_source_rgb(1, .5, .5)
            cr.arc(0, 0, 1, 0, math.tau)
            cr.fill()

            cr.restore()

    def draw_points_labels(self, layout: Layout, cr: Context):
        for i, points in enumerate(layout.points):
            cr.save()
            cr.set_font_size(4)
            cr.translate(*self.piece_matrices[points].transform_point(4, -10 if points.direction == 'left' else 10))
            cr.rectangle(-4, -4, 8, 8)
            cr.set_source_rgb(1, 1, 1)
            cr.fill_preserve()
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1)
            cr.stroke()
            cr.move_to(-2, 2)
            cr.show_text(str(i))
            cr.restore()


    def transform_track_point(self, track_point):
        drawn_piece = DrawnPiece.for_piece(track_point.piece)
        px, py = drawn_piece.point_position(track_point.anchor_name, track_point.offset)
        return self.piece_matrices[track_point.piece].transform_point(px, py)

    def point_back(self, track_point, distance):
        error = distance
        px, py = self.transform_track_point(track_point)
        for i in range(2):
            track_point = track_point - error
            px2, py2 = self.transform_track_point(track_point)
            new_distance = math.sqrt((px-px2)**2 + (py-py2)**2)
            error = distance - new_distance
        return track_point, (px2, py2)

    def draw_trains(self, layout: Layout, cr: Context):
        for train in layout.trains:
            car_start = train.position

            annotation = train.meta.get('annotation')

            for i, car in enumerate(train.cars):
                front_bogey_offset, rear_bogey_offset = car.bogey_offsets
                bogey_spacing = rear_bogey_offset - front_bogey_offset
                front_bogey_position = car_start - front_bogey_offset
                front_bogey_xy = self.transform_track_point(front_bogey_position)
                rear_bogey_position, rear_bogey_xy = self.point_back(front_bogey_position, bogey_spacing)

                cr.save()
                cr.translate(front_bogey_xy[0], front_bogey_xy[1])
                cr.rotate(math.pi + math.atan2(front_bogey_xy[1] - rear_bogey_xy[1],
                                               front_bogey_xy[0] - rear_bogey_xy[0]))

                cr.set_source_rgb(*hex_to_rgb(train.meta.get('color', '#a0a0ff')))

                if i == 0 and annotation:
                    cr.move_to(0, -10)
                    cr.set_font_size(5)
                    cr.show_text(annotation)

                cr.set_line_width(4)
                cr.move_to(-front_bogey_offset, 0)
                cr.line_to(car.length - front_bogey_offset, 0)
                cr.stroke()

                cr.set_line_width(6)
                cr.move_to(1 - front_bogey_offset, 0)
                cr.line_to(car.length - front_bogey_offset - 1, 0)
                cr.stroke()

                if i == 0 and train.lights_on:
                    cr.set_source_rgba(1, 1, 0.2, 0.5)
                    for y in (-2.5, 2.5):
                        cr.move_to(-front_bogey_offset - 1, y)
                        cr.arc(-front_bogey_offset - 1, y, 10, 6/7 * math.pi, math.pi * 8/7)
                        cr.close_path()
                        cr.fill()

                cr.restore()
                car_start = rear_bogey_position - (car.length - rear_bogey_offset + 1)

