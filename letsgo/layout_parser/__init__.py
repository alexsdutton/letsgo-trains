import logging
import os
from typing import Iterable, Optional, Type

import pkg_resources

from .base import LayoutParser
from .letsgo import LetsGoLayoutParser
from .ncontrol import NControlLayoutParser

__all__ = [
    "LayoutParser",
    "LetsGoLayoutParser",
    "NControlLayoutParser",
    "parser_classes",
    "get_parser_for_filename",
]

logger = logging.getLogger(__name__)


def _get_parser_classes() -> Iterable[Type[LayoutParser]]:
    parser_classes = []
    for ep in pkg_resources.iter_entry_points("letsgo.layout_parser"):
        try:
            parser_cls: Type[LayoutParser] = ep.load()
            assert issubclass(parser_cls, LayoutParser)
        except Exception:
            logger.exception("Couldn't load entrypoint %s", ep)
            continue
        parser_classes.append(parser_cls)
    return parser_classes


def get_parser_for_filename(filename) -> Optional[LayoutParser]:
    _, ext = os.path.splitext(filename)
    for parser_cls in parser_classes:
        if parser_cls.file_extension == ext:
            return parser_cls()
    return None


parser_classes = _get_parser_classes()
