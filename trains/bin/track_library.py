import cairo
import click
import math

from trains.drawing import Colors

from trains.drawing_options import DrawingOptions
from trains.pieces.base import Piece

from ..pieces import piece_classes


click.command()
def track_library():
    drawing_options = DrawingOptions(
        offset=(0, 0),
        scale=20,
        rail_color=Colors.dark_bluish_gray,
        sleeper_color=Colors.tan,
    )

    for name, cls in sorted(piece_classes.items(), key=lambda name_cls: name_cls[1].layout_priority):
        print(name)
        piece: Piece = cls()
        bounds = piece.bounds()

        image = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                   math.ceil(drawing_options.scale * bounds['width'] + 10),
                                   math.ceil(drawing_options.scale * bounds['height'] + 10))
        cr = cairo.Context(image)
        cr.translate(5, 5)
        cr.scale(drawing_options.scale, drawing_options.scale)
        cr.translate(-bounds['x'], -bounds['y'])
        piece.draw(cr, drawing_options)

        image.write_to_png(f'docs/_static/pieces/{name}.png')

if __name__ == '__main__':
    track_library()