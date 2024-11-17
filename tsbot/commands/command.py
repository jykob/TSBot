from __future__ import annotations

import asyncio
import inspect
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from tsbot import exceptions, parsers

if TYPE_CHECKING:
    from tsbot import bot, context


class RawCommandHandler(Protocol):
    def __call__(
        self, bot: bot.TSBot, ctx: context.TSCtx, arg: str, /
    ) -> Coroutine[None, None, None]: ...


class CommandHandler(Protocol):
    def __call__(
        self, bot: bot.TSBot, ctx: context.TSCtx, /, *args: Any, **kwargs: Any
    ) -> Coroutine[None, None, None]: ...


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
