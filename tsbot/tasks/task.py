from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsbot import bot


TTaskHandler = Callable[["bot.TSBot"], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSTask:
    handler: TTaskHandler
    name: str | None = None
    task: asyncio.Task[None] | None = None


def every(every_handler: TTaskHandler, seconds: float) -> TTaskHandler:
    @functools.wraps(every_handler)
    async def every_wrapper(bot: bot.TSBot) -> None:
        while True:
            try:
                await asyncio.sleep(seconds)
                await every_handler(bot)
            except asyncio.CancelledError:
                break

    return every_wrapper
