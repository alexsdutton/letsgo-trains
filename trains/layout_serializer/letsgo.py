from trains.layout import Layout

from trains.layout_serializer import LayoutSerializer


class LetsGoLayoutSerializer(LayoutSerializer):
    name = "Let's Go!"
    file_extension = '.lgl'

    def serialize(self, fp, layout: Layout):
        pass