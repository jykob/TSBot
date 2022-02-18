from __future__ import annotations
from typing import TYPE_CHECKING, NamedTuple

from tsbot.extensions.extension import Extension

if TYPE_CHECKING:
    from tsbot.bot import TSBot


class CacheRecord(NamedTuple):
    timestamp: int
    value: list[dict[str, str]]


class Cache(Extension):
    def __init__(self, parent: TSBot) -> None:
        super().__init__(parent)

        self.cache: dict[int, CacheRecord] = {}
