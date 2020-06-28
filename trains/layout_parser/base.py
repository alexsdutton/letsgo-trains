from trains.layout import Layout


class LayoutParser:
    name: str
    file_extension: str

    def parse(self, fp, layout: Layout):
        raise NotImplementedError


class LayoutFileParseException(Exception):
    pass
