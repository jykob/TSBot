from __future__ import annotations

import asyncio
import inspect
import itertools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Coroutine

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import bot


@dataclass(slots=True)
class TSCommand:
    commands: tuple[str, ...]
    handler: Callable[..., Coroutine[None, None, None]]

    help_text: str = field(repr=False)
    raw: bool = field(repr=False)
    hidden: bool = field(repr=False)

    checks: list[Callable[..., Coroutine[None, None, None]]] = field(default_factory=list, repr=False)

    @property
    def call_signature(self) -> tuple[inspect.Parameter, ...]:
        signature = inspect.signature(self.handler)

        return tuple(itertools.islice(signature.parameters.values(), 2, None))

    @property
    def usage(self) -> str:
        usage: list[str] = []

        for param in self.call_signature:
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

    async def run_checks(self, bot: bot.TSBot, ctx: dict[str, str], *args: str, **kwargs: str) -> None:
        done, pending = await asyncio.wait(
            [check(bot, ctx, *args, **kwargs) for check in self.checks],
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for pending_task in pending:
            pending_task.cancel()

        for done_task in done:
            if exception := done_task.exception():
                raise exception

    async def run(self, bot: bot.TSBot, ctx: dict[str, str], msg: str) -> None:
        args, kwargs = ((msg,), {}) if self.raw else utils.parse_args_kwargs(msg)

        if self.checks:
            await self.run_checks(bot, ctx, *args, **kwargs)

        await self.handler(bot, ctx, *args, **kwargs)
