from __future__ import annotations

import asyncio
import logging
from time import time
from typing import NamedTuple

from tsbot.response import TSResponse


logger = logging.getLogger(__name__)


class CacheRecord(NamedTuple):
    timestamp: float
    record: TSResponse


class Cache:
    CACHE_CLEANUP_INTERVAL: int = 60 * 5
    CACHE_MAX_LIFETIME: int = 60 * 10

    def __init__(self) -> None:
        self.cache: dict[int, CacheRecord] = {}

    def get_cache(self, cache_hash: int, max_age: int | float) -> TSResponse | None:
        cached_response = self.cache.get(cache_hash)

        if not cached_response:
            return None

        if cached_response.timestamp + max_age > time():
            return cached_response.record

    def add_cache(self, cache_hash: int, response: TSResponse) -> None:
        self.cache[cache_hash] = CacheRecord(time(), response)

    async def cache_cleanup_task(self) -> None:
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
