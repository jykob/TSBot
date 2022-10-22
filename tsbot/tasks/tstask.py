from __future__ import annotations

import asyncio
import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Coroutine

if TYPE_CHECKING:
    from tsbot import bot


TTaskH = Callable[["bot.TSBot"], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSTask:
    handler: TTaskH
    name: str | None = None
    task: asyncio.Task[None] | None = None


def every(every_handler: TTaskH, seconds: int) -> TTaskH:
    @functools.wraps(every_handler)
    async def every_wrapper(bot: bot.TSBot) -> None:
        while True:
            try:
                await asyncio.sleep(seconds)
                await every_handler(bot)
            except asyncio.CancelledError:
                break

    return every_wrapper
