import os

import cairo
import click
import math

from letsgo.drawing import Colors

from letsgo.drawing_options import DrawingOptions
from letsgo.layout import Layout
from letsgo.pieces.base import Piece

from ..pieces import piece_classes


@click.command()
@click.argument("output_directory")
def track_library(output_directory):
    drawing_options = DrawingOptions(
        offset=(0, 0),
        scale=20,
        rail_color=Colors.dark_bluish_gray.rgb,
        sleeper_color=Colors.tan.rgb,
    )

    for name, cls in sorted(
        piece_classes.items(), key=lambda name_cls: name_cls[1].layout_priority
    ):
        print(name)
        piece: Piece = cls(layout=Layout())
        image = piece.get_icon_surface(drawing_options)
        image.write_to_png(os.path.join(output_directory, f"{name}.png"))


if __name__ == "__main__":
    track_library()
