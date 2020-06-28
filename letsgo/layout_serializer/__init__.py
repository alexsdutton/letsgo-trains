import logging
import os
from typing import Iterable, Optional, Type

import pkg_resources

from .base import LayoutSerializer
from .letsgo import LetsGoLayoutSerializer
from .ncontrol import NControlLayoutSerializer

__all__ = [
    "LayoutSerializer",
    "LetsGoLayoutSerializer",
    "NControlLayoutSerializer",
    "serializer_classes",
    "get_serializer_for_filename",
]

logger = logging.getLogger(__name__)


def _get_serializer_classes() -> Iterable[Type[LayoutSerializer]]:
    serializer_classes = []
    for ep in pkg_resources.iter_entry_points("letsgo.layout_serializer"):
        try:
            serializer_cls: Type[LayoutSerializer] = ep.load()
            assert issubclass(serializer_cls, LayoutSerializer)
        except Exception:
            logger.exception("Couldn't load entrypoint %s", ep)
            continue
        serializer_classes.append(serializer_cls)
    return serializer_classes


def get_serializer_for_filename(filename) -> Optional[LayoutSerializer]:
    _, ext = os.path.splitext(filename)
    for serializer_cls in serializer_classes:
        if serializer_cls.file_extension == ext:
            return serializer_cls()


serializer_classes = _get_serializer_classes()
