from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tsbot import exceptions, parsers

if TYPE_CHECKING:
    from tsbot import bot, context


RawCommandHandler = Callable[["bot.TSBot", "context.TSCtx", str], Coroutine[None, None, None]]
CommandHandler = Callable[..., Coroutine[None, None, None]]

# TODO: Use after 'typing_extensions' releases support for Python 3.10 'Concatenate[...]'
# CommandHandler = Callable[Concatenate["bot.TSBot", "context.TSCtx", ...], Coroutine[None, None, None]]


@dataclass(slots=True)
class TSCommand:
    commands: tuple[str, ...]
    handler: CommandHandler
    call_signature: inspect.Signature = field(repr=False, init=False)

    help_text: str = field(repr=False, default="")
    raw: bool = field(repr=False, default=False)
    hidden: bool = field(repr=False, default=False)

    checks: tuple[CommandHandler, ...] = field(default=(), repr=False)

    def __post_init__(self) -> None:
        self.call_signature = inspect.signature(self.handler)

    async def run_checks(
        self, bot: bot.TSBot, ctx: context.TSCtx, *args: str, **kwargs: str
    ) -> None:
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(check(bot, ctx, *args, **kwargs), name="CommandCheck-Task")
                for check in self.checks
            ],
            return_when=asyncio.FIRST_EXCEPTION,
        )

        for pending_task in pending:
            pending_task.cancel()

        for done_task in done:
            if exception := done_task.exception():
                raise exception

    async def run(self, bot: bot.TSBot, ctx: context.TSCtx, msg: str) -> None:
        if self.raw:
            args: tuple[str, ...] = (msg,) if msg else ()
            kwargs: dict[str, str] = {}
        else:
            args, kwargs = parsers.parse_args_kwargs(msg)

        if self.checks:
            await self.run_checks(bot, ctx, *args, **kwargs)

        try:
            bound_arguments = self.call_signature.bind(bot, ctx, *args, **kwargs)
        except TypeError as e:
            raise exceptions.TSInvalidParameterError(str(e).capitalize()) from e
        else:
            await self.handler(*bound_arguments.args, **bound_arguments.kwargs)
