from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsbot import bot


TaskHandler = Callable[["bot.TSBot"], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSTask:
    handler: TaskHandler
    name: str | None = None
    task: asyncio.Task[None] | None = None


def every(every_handler: TaskHandler, seconds: float) -> TaskHandler:
    @functools.wraps(every_handler)
    async def every_wrapper(bot: bot.TSBot) -> None:
        while True:
            await asyncio.sleep(seconds)
            await every_handler(bot)

    return every_wrapper
