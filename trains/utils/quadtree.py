import math
import typing

import pyqtree

from trains.track import Bounds, Position


class WithBounds(typing.Protocol):
    def bounds(self) -> Bounds:
        ...


class ResizingIndex:
    """A pyqtree.Index-compatible class that works with item bounds and resizes automatically."""

    def __init__(self, *args, **kwargs):
        self._index = pyqtree.Index(*args, **kwargs)
        self._bbox = (
            self._index.center[0] - self._index.width / 2,
            self._index.center[1] - self._index.height / 2,
            self._index.center[0] + self._index.width / 2,
            self._index.center[1] + self._index.height / 2,
        )
        self._bounds = {}

    def insert(self, *args, **kwargs):
        return self._index.insert(*args, **kwargs)

    def remove(self, *args, **kwargs):
        return self._index.remove(*args, **kwargs)

    def intersect(self, *args, **kwargs):
        return self._index.intersect(*args, **kwargs)

    def insert_item(self, item: WithBounds, position: Position):
        bounds = item.bounds()
        corners = [
            (bounds.x, bounds.y),
            (bounds.x + bounds.width, bounds.y),
            (bounds.x, bounds.y + bounds.height),
            (bounds.x + bounds.width, bounds.y + bounds.height),
        ]
        corners = [
            (
                (math.cos(position.angle) * x + math.sin(position.angle) * y),
                (math.sin(position.angle) * x + math.cos(position.angle) * y),
            )
            for x, y in corners
        ]
        bbox = (
            position.x + min(x for x, y in corners),
            position.y + min(y for x, y in corners),
            position.x + max(x for x, y in corners),
            position.y + max(y for x, y in corners),
        )

        previous_bbox = self._bounds.get(item)

        if bbox == previous_bbox:
            return

        if previous_bbox:
            self._index.remove(item, previous_bbox)
        self._bounds[item] = bbox

        if (
            bbox[0] <= self._bbox[0]
            or bbox[1] <= self._bbox[1]
            or bbox[2] >= self._bbox[2]
            or bbox[3] >= self._bbox[3]
        ):
            # If it falls outside the quadtree bounds, increase the size of the quadtree to fits
            minx, miny, maxx, maxy = -80, -80, 80, 80
            for item_minx, item_miny, item_maxx, item_maxy in self._bounds.values():
                minx, miny = min(minx, item_minx), min(miny, item_miny)
                maxx, maxy = max(maxx, item_maxx), max(maxy, item_maxy)
            minx, maxx = minx - (maxx - minx) * 0.2, maxx + (maxx - minx) * 0.2
            miny, maxy = miny - (maxy - miny) * 0.2, maxy + (maxy - miny) * 0.2
            self._index = pyqtree.Index(bbox=(minx, miny, maxx, maxy),)
            self._bbox = (minx, miny, maxx, maxy)
            for item, item_bbox in self._bounds.items():
                self._index.insert(item, item_bbox)
        else:
            self._index.insert(item, bbox)

    def remove_item(self, item):
        previous_bbox = self._bounds.pop(item, None)
        if previous_bbox:
            self._index.remove(item, previous_bbox)
        # else:
        #     print('oh no')

    def __len__(self):
        return len(self._bounds)
