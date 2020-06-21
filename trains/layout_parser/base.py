import typing


class LayoutParser:
    name: str
    file_extension: str


class LayoutFileParseException(Exception):
    pass