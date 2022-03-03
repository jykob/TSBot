from __future__ import annotations

import asyncio
import logging
from time import time
from typing import TYPE_CHECKING, NamedTuple

from tsbot import response
from tsbot.extensions import extension

if TYPE_CHECKING:
    from tsbot.bot import TSBot


logger = logging.getLogger(__name__)


class CacheRecord(NamedTuple):
    timestamp: float
    record: response.TSResponse


class Cache(extension.Extension):
    CACHE_CLEANUP_INTERVAL: int = 60 * 10
    CACHE_MAX_LIFETIME: int = 60 * 10

    def __init__(self, parent: TSBot) -> None:
        super().__init__(parent)

        self.cache: dict[int, CacheRecord] = {}

    def get_cache(self, cache_hash: int, max_age: int | float) -> response.TSResponse | None:
        cached_response = self.cache.get(cache_hash)

        if not cached_response:
            return None

        if cached_response.timestamp + max_age > time():
            return cached_response.record

    def add_cache(self, cache_hash: int, response: response.TSResponse) -> None:
        self.cache[cache_hash] = CacheRecord(time(), response)

    async def _clean_cache(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.CACHE_CLEANUP_INTERVAL)

                logger.debug("Running cache clean-up")

                delete_timestamp: float = time() - self.CACHE_MAX_LIFETIME

                for key, value in tuple(self.cache.items()):
                    if not value.timestamp < delete_timestamp:
                        continue

                    logger.debug("Deleting key %r", key)
                    del self.cache[key]

        except asyncio.CancelledError:
            pass

    async def run(self) -> None:
        self.parent.register_background_task(self._clean_cache, name="CacheClean")
