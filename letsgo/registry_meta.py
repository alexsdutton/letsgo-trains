from __future__ import annotations

import enum
import functools
import importlib
import inspect
import uuid
from typing import TYPE_CHECKING, get_type_hints

import pkg_resources
import typing

if TYPE_CHECKING:
    from letsgo.layout import Layout


class WithRegistryMeta(type):
    entrypoint_group: str

    @property
    def entrypoint_name(cls) -> str:
        try:
            return cls._entrypoint_name
        except AttributeError:
            for ep in pkg_resources.iter_entry_points(cls.entrypoint_group):
                if ep.load() in cls.__mro__:
                    cls._entrypoint_name: str = ep.name
                    return cls._entrypoint_name
        raise AttributeError(
            f"Entrypoint not found for class {cls} in group {cls.entrypoint_group}"
        )


def cast_to_type_hint(layout: Layout, obj, type_hint):
    from letsgo.layout import Layout
    from letsgo.track import Position
    from letsgo.track import Anchor
    from letsgo.track_point import TrackPoint

    if not type_hint:
        return obj

    if (
        getattr(type_hint, "__origin__", None) == typing.Union
        and len(type_hint.__args__) == 2
        and type_hint.__args__[1] is type(None)
    ):
        if obj is None:
            return None
        type_hint = type_hint.__args__[0]

    if isinstance(type_hint, type) and isinstance(obj, type_hint):
        return obj

    if getattr(type_hint, "__origin__", None) in (typing.Dict, dict):
        key_type_hint, value_type_hint = type_hint.__args__
        assert isinstance(obj, dict)
        for key, value in obj.items():
            key = cast_to_type_hint(layout, key, key_type_hint)
            if isinstance(key, str) and key.endswith("_id"):
                obj[key[:-3]] = layout.collections[type_hint][value]
                del obj[key]
            else:
                obj[key] = cast_to_type_hint(layout, value, value_type_hint)
    elif getattr(type_hint, "__origin__", None) == (typing.List, list):
        raise NotImplementedError
    elif getattr(type_hint, "__origin__", None) == (typing.Tuple, tuple):
        raise NotImplementedError
    elif isinstance(type_hint, type) and isinstance(obj, dict):
        cls = type_hint

        type_hints = {}
        for supercls in reversed(cls.__mro__):
            mod = importlib.import_module(supercls.__module__)
            mod_globals = {
                # 'typing': typing,
                # **typing.__dict__,
                **mod.__dict__,
                "Layout": Layout,
                "Position": Position,
                "Anchor": Anchor,
                "TrackPoint": TrackPoint,
            }

            type_hints.update(
                get_type_hints(supercls.__init__, mod_globals)  # type: ignore
            )

        for key, value in list(obj.items()):
            if isinstance(key, str) and key.endswith("_id") and key[:-3] in type_hints:
                obj[key[:-3]] = layout.collections[type_hints[key[:-3]]][value]
                del obj[key]
            elif key in type_hints:
                obj[key] = cast_to_type_hint(layout, value, type_hints[key])

        constructor = getattr(type_hint, "from_yaml", type_hint)
        argspec = inspect.getfullargspec(constructor)
        if "layout" in argspec.args:
            constructor = functools.partial(constructor, layout)
        elif "layout" in argspec.kwonlyargs:
            constructor = functools.partial(constructor, layout=layout)

        if isinstance(obj, dict):
            print(constructor, obj)
            obj = constructor(**obj)
        else:
            obj = constructor(obj)
    elif issubclass(type_hint, enum.Enum):
        # Enums are by name, not value
        obj = type_hint[obj]
    elif isinstance(type_hint, type):
        obj = type_hint(obj)

    return obj


class WithRegistry(metaclass=WithRegistryMeta):
    def __init__(self, *, id: str = None, layout: Layout):
        self.id = id or str(uuid.uuid4())
        self.layout = layout

    def to_yaml(self) -> dict:
        data = {
            "id": self.id,
            "type": type(self).entrypoint_name,
        }
        return data

    @classmethod
    def cast_yaml_data(cls, layout, /, **obj):

        from letsgo.layout import Layout
        from letsgo.track import Position
        from letsgo.track import Anchor
        from letsgo.track_point import TrackPoint

        type_hints = {}
        for supercls in reversed(cls.__mro__[:-1]):  # ignore <class 'object'>
            mod_globals = {
                # 'typing': typing,
                # **typing.__dict__,
                **supercls.__init__.__globals__,
                "Layout": Layout,
                "Position": Position,
                "Anchor": Anchor,
                "TrackPoint": TrackPoint,
            }

            type_hints.update(get_type_hints(supercls.__init__, mod_globals))

        for key, value in list(obj.items()):
            if isinstance(key, str) and key.endswith("_id") and key[:-3] in type_hints:
                obj[key[:-3]] = layout.collections[type_hints[key[:-3]]][value]
                del obj[key]
            elif key in type_hints:
                obj[key] = cast_to_type_hint(layout, value, type_hints[key])

        return obj

    @classmethod
    def from_yaml(cls, layout, /, **data):
        entrypoint_name = data.pop("type")
        try:
            actual_cls = next(
                pkg_resources.iter_entry_points(cls.entrypoint_group, entrypoint_name)
            ).load()
        except StopIteration as e:
            raise ValueError(
                f"Couldn't find entrypoint {entrypoint_name} in group {cls.entrypoint_group}"
            ) from e
        return actual_cls(layout=layout, **actual_cls.cast_yaml_data(layout, **data))
