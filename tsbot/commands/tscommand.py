from __future__ import annotations

import asyncio
import inspect
import itertools
from typing import TYPE_CHECKING, Any

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import bot, plugin, typealiases


def add_check(func: typealiases.TCommandHandler) -> TSCommand:
    def check_decorator(command_handler: TSCommand) -> TSCommand:
        command_handler.add_check(func)
        return command_handler

    return check_decorator  # type: ignore


class TSCommand:
    def __init__(
        self,
        commands: tuple[str, ...],
        handler: typealiases.TCommandHandler | typealiases.TPluginCommandHandler,
        *,
        help_text: str | None = None,
        raw: bool = False,
        hidden: bool = False,
    ) -> None:
        self.commands = commands
        self.handler = handler

        self.help_text = help_text
        self.raw = raw
        self.hidden = hidden

        self.plugin_instance: plugin.TSPlugin | None = None
        self.checks: list[typealiases.TCommandHandler] = []

    def add_check(self, func: typealiases.TCommandHandler) -> None:
        self.checks.append(func)

    @property
    def call_signature(self) -> tuple[inspect.Parameter, ...]:
        signature = inspect.signature(self.handler)
        params_to_discard = 3 if self.plugin_instance else 2

        return tuple(itertools.islice(signature.parameters.values(), params_to_discard, None))

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

    async def run_checks(self, bot: bot.TSBot, ctx: typealiases.TCtx, *args: str, **kwargs: str) -> None:
        done, pending = await asyncio.wait(
            [check(bot, ctx, *args, **kwargs) for check in self.checks],
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for pending_task in pending:
            pending_task.cancel()

        for done_task in done:
            if exception := done_task.exception():
                raise exception

    async def run(self, bot: bot.TSBot, ctx: typealiases.TCtx, msg: str) -> None:
        kwargs: dict[str, str]
        args: tuple[str, ...]

        args, kwargs = ((msg,), {}) if self.raw else utils.parse_args_kwargs(msg)

        if self.checks:
            await self.run_checks(bot, ctx, *args, **kwargs)

        command_args = (bot, ctx) if not self.plugin_instance else (self.plugin_instance, bot, ctx)

        await self.handler(*command_args, *args, **kwargs)  # type: ignore

    def __call__(self, *args: Any, **kwargs: Any):
        return self.run(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(commands={self.commands!r}, handler={self.handler.__qualname__!r})"
