from __future__ import annotations


from typing import TYPE_CHECKING, Any, Callable, Coroutine, ParamSpec
from tsbot.extensions.command_handler import TSCommand
from tsbot.extensions.event_handler import TSEventHandler


if TYPE_CHECKING:
    from tsbot.bot import TSBotBase


P = ParamSpec("P")


class TSPlugin:
    __plugins__: list[TSPlugin] = []
    __events__: list[TSEventHandler] = []
    __commands__: list[TSCommand] = []

    bot: TSBotBase

    def __new__(cls, *args: Any, **kwargs: Any):
        new_instance = super().__new__(cls, *args, **kwargs)
        cls.__plugins__.append(new_instance)

        return new_instance

    @classmethod
    def on(cls, event_type: str):
        """Decorator to register coroutines on events"""

        def event_decorator(func: Callable[P, TSEventHandler]) -> TSEventHandler:
            handler = TSEventHandler(event_type, func)
            cls.__events__.append(handler)
            return func

        return event_decorator

    @classmethod
    def command(cls, *commands: str):
        """Decorator to register coroutines on commands"""
        print("COMMAND CREATED")

        def command_decorator(func: Callable[P, TSCommand]) -> Callable[..., Coroutine[None, None, None]]:
            handler = TSCommand(commands, func)
            cls.__commands__.append(handler)
            return func

        return command_decorator
