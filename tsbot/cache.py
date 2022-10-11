from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, NamedTuple

from tsbot import response

if TYPE_CHECKING:
    from tsbot import bot


logger = logging.getLogger(__name__)


class CacheRecord(NamedTuple):
    timestamp: float
    record: response.TSResponse


class Cache:
    def __init__(self, cleanup_interval: float = 60 * 5, max_lifetime: float = 60 * 10) -> None:
        self.cleanup_interval = cleanup_interval
        self.max_lifetime = max_lifetime

        self.cache: dict[int, CacheRecord] = {}

    def get_cache(self, cache_hash: int, max_age: int | float) -> response.TSResponse | None:
        cached_response = self.cache.get(cache_hash)

        if not cached_response:
            return None

        if cached_response.timestamp + max_age < time.monotonic():
            return None

        return cached_response.record

    def add_cache(self, cache_hash: int, response: response.TSResponse) -> None:
        self.cache[cache_hash] = CacheRecord(time.monotonic(), response)

    def cleanup(self) -> None:
        logger.debug("Running cache clean-up")

        delete_timestamp: float = time.monotonic() - self.max_lifetime

        for key, value in tuple(self.cache.items()):
            if not value.timestamp < delete_timestamp:
                continue

            logger.debug("Deleting key %r", key)
            del self.cache[key]

    async def cache_cleanup_task(self, bot: bot.TSBot) -> None:
        logger.debug("Clean-up task started")

        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                logger.debug("Clean-up task cancelled")
                break
            else:
                self.cleanup()

        logger.debug("Clean-up task done")
