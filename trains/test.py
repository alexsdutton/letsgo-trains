import math

from . import drawing, track

beginning = track.Join(None)

layout = 'SSCCCC' * 4

track_layout, end = [], beginning
for c in layout:
    piece = {'C': track.Curve, 'S': track.Straight}[c](end)
    track_layout.append(piece)
    end = piece.ends[0]

layout = yaml.loads("""

""")

import cairo

WIDTH, HEIGHT = 256, 256

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)

ctx.translate(100, 0)
ctx.scale(5, 5)

def collect_track_and_ends(anchors):
    tracks, ends = set(), set()
    remaining_ends = list(anchors)
    while remaining_ends:
        end = remaining_ends.pop()
        ends.add(end)
        if end.track:
            tracks.add(end.track)
            remaining_ends.extend(end.track.ends)
    return tracks, ends

tracks, ends = collect_track_and_ends([beginning])

for track in tracks:
    drawing.draw(track, ctx)

for end in ends:
    ctx.set_source_rgb(1, 1, 0)
    ctx.arc(end.location.position.real, end.location.position.imag, 3, 0, math.tau)
    ctx.fill()

#
# ends = [beginning]
# while ends:
#     end = ends.pop()
#     if end.track:
#         new_ends = end.track.ends
#         for new_end in new_ends:
#             print("M", end.location.position.real, end.location.position.imag)
#             ctx.move_to(end.location.position.real, end.location.position.imag)
#             ctx.line_to(new_end.location.position.real, new_end.location.position.imag)
#             ctx.set_source_rgb(*end.track.color)  # Solid color
#             ctx.set_line_width(1)
#             ctx.stroke()
#
#             ctx.set_source_rgb(1, 1, 0)
#             ctx.arc(new_end.location.position.real, new_end.location.position.imag, 3, 0, math.tau)
#             ctx.fill()
#         ends.extend(new_ends)
#

surface.write_to_png("example.png")  # Output to PNG