import typing

RGB = typing.Tuple[float, float, float]

class DrawingOptions:
    def __init__(self, *, offset: typing.Tuple[float, float], scale: float, rail_color: RGB, sleeper_color: RGB):
        self.offset = offset
        self.scale = scale
        self.rail_color = rail_color
        self.sleeper_color = sleeper_color
