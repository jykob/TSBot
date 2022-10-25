from __future__ import annotations

import asyncio
import inspect
import itertools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Coroutine

from tsbot import exceptions, utils

if TYPE_CHECKING:
    from tsbot import bot, context


@dataclass(slots=True)
class TSCommand:
    commands: tuple[str, ...]
    handler: Callable[..., Coroutine[None, None, None]]

    help_text: str = field(repr=False, default="")
    raw: bool = field(repr=False, default=False)
    hidden: bool = field(repr=False, default=False)

    checks: list[Callable[..., Coroutine[None, None, None]]] = field(default_factory=list, repr=False)

    @property
    def call_signature(self) -> inspect.Signature:
        return inspect.signature(self.handler)

    @property
    def usage(self) -> str:
        usage: list[str] = []

        for param in itertools.islice(self.call_signature.parameters.values(), 2, None):
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                usage.append(f"[{param.name!r}, ...]")

            elif param.kind is inspect.Parameter.KEYWORD_ONLY:
                usage.append(
                    f"-{param.name} {'[!]' if param.default is param.empty else '[?]'}"
                    f"{f' ({param.default!r})' if param.default not in (param.empty, None) else ''}"
                )

            else:
                usage.append(
                    f"{param.name!r}"
                    f"""{f" ({param.default or '?'!r})" if param.default is not param.empty else ''}"""
                )

        return f"Usage: {' | '.join(self.commands)} {' '.join(usage)}"

    async def run_checks(self, bot: bot.TSBot, ctx: context.TSCtx, *args: str, **kwargs: str) -> None:
        done, pending = await asyncio.wait(
            [asyncio.create_task(check(bot, ctx, *args, **kwargs), name="Check-Task") for check in self.checks],
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for pending_task in pending:
            pending_task.cancel()

        for done_task in done:
            if exception := done_task.exception():
                raise exception

    async def run(self, bot: bot.TSBot, ctx: context.TSCtx, msg: str) -> None:
        args, kwargs = utils.parse_args_kwargs(msg) if not self.raw else ((msg,) if msg else (), {})

        if self.checks:
            await self.run_checks(bot, ctx, *args, **kwargs)

        try:
            binded_arguments = self.call_signature.bind(bot, ctx, *args, **kwargs)
        except TypeError as e:
            raise exceptions.TSInvalidParameterError(str(e)) from e
        else:
            await self.handler(*binded_arguments.args, **binded_arguments.kwargs)
