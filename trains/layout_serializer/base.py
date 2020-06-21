import typing

from trains.layout import Layout


class LayoutSerializer:
    name: str
    file_extension: str

    def serialize(self, fp, layout: Layout):
        raise NotImplementedError


class LayoutFileSerializeException(Exception):
    pass