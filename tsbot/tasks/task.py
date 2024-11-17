from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typing_extensions import TypeVarTuple, Unpack

if TYPE_CHECKING:
    from tsbot import bot

_Ts = TypeVarTuple("_Ts")


TaskHandler = Callable[["bot.TSBot", Unpack[_Ts]], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSTask:
    handler: TaskHandler[Unpack[tuple[Any, ...]]]
    args: tuple[Any, ...] = ()
    name: str | None = None
    task: asyncio.Task[None] | None = None


def every(every_handler: TaskHandler[Unpack[_Ts]], seconds: float) -> TaskHandler[Unpack[_Ts]]:
    @functools.wraps(every_handler)
    async def every_wrapper(bot: bot.TSBot, *args: Unpack[_Ts]) -> None:
        while True:
            await asyncio.sleep(seconds)
            await every_handler(bot, *args)

    return every_wrapper
