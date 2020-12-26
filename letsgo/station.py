import typing
import uuid
from typing import Optional

from .track_point import TrackPoint


class Platform:
    def __init__(
        self, position: TrackPoint, id: str = None, length: Optional[float] = None
    ):
        self.position = position
        self.id = id or str(uuid.uuid4())
        self.length = length


class Station:
    def __init__(self, id: str = None, name=None, platforms=()):
        self.name = name
        self.id = id or str(uuid.uuid4())
        self.platforms: typing.List[Platform] = []
        for platform in platforms:
            self.add_platform(platform)

    def add_platform(self, platform: Platform):
        self.platforms.append(platform)

    def available_platforms(self, train):
        for platform in self.platforms:
            if not platform.length or train.length <= platform.length:
                yield platform

    def to_yaml(self):
        raise NotImplementedError
