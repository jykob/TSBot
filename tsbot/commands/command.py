from __future__ import annotations

import asyncio
import functools
import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

from tsbot import exceptions, parsers

if TYPE_CHECKING:
    from tsbot import bot, context


TCommandHandler = Callable[..., Coroutine[None, None, None]]


class CheckKwargs(TypedDict):
    bot: bot.TSBot
    ctx: context.TSCtx
    args: tuple[str, ...]
    kwargs: dict[str, str]


def _create_check_task(check: TCommandHandler, kwargs: CheckKwargs) -> asyncio.Task[None]:
    return asyncio.create_task(check(**kwargs), name="Check-Task")


@dataclass(slots=True)
class TSCommand:
    commands: tuple[str, ...]
    handler: TCommandHandler
    call_signature: inspect.Signature = field(repr=False, init=False)

    help_text: str = field(repr=False, default="")
    raw: bool = field(repr=False, default=False)
    hidden: bool = field(repr=False, default=False)

    checks: list[TCommandHandler] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.call_signature = inspect.signature(self.handler)

    async def run_checks(
        self, bot: bot.TSBot, ctx: context.TSCtx, *args: str, **kwargs: str
    ) -> None:
        check_kwargs = CheckKwargs(bot=bot, ctx=ctx, args=args, kwargs=kwargs)
        create_check_task = functools.partial(_create_check_task, kwargs=check_kwargs)
        check_tasks = list(map(create_check_task, self.checks))

        done, pending = await asyncio.wait(check_tasks, return_when=asyncio.FIRST_EXCEPTION)

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
