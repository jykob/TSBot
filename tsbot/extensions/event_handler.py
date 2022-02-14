from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Callable, Coroutine, TypeAlias


from tsbot.extensions.extension import Extension
from tsbot.utils import parse_line


if TYPE_CHECKING:
    from tsbot.bot import TSBotBase
    from tsbot.plugin import TSPlugin


logger = logging.getLogger(__name__)


class TSEvent:
    __slots__ = ["event", "msg", "ctx"]

    def __init__(self, event: str, msg: str | None = None, ctx: dict[str, str] | None = None) -> None:
        self.event = event
        self.msg = msg
        self.ctx: dict[str, str] = ctx if ctx else {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(event={self.event!r}, msg={self.msg!r}, ctx={self.ctx!r})"

    @classmethod
    def from_server_response(cls, raw_data: str):
        event, data = raw_data.split(" ", maxsplit=1)
        return cls(event=event.removeprefix("notify"), msg=None, ctx=parse_line(data))


T_EventHandler: TypeAlias = Callable[..., Coroutine[TSEvent, None, None]]


class TSEventHandler:
    def __init__(self, event: str, handler: T_EventHandler, plugin_instance: TSPlugin | None = None) -> None:
        self.event = event
        self.handler = handler
        self.plugin_instance = plugin_instance

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(event={self.event!r}, "
            f"handler={self.handler.__name__!r}, "
            f"plugin={None if not self.plugin_instance else self.plugin_instance.__class__.__name__!r})"
        )

    async def run(self, event: TSEvent) -> None:
        if self.plugin_instance:
            await self.handler(self.plugin_instance, event)
        else:
            await self.handler(event)


class EventHanlder(Extension):
    def __init__(self, parent: TSBotBase) -> None:
        super().__init__(parent)
        self.event_handlers: defaultdict[str, list[TSEventHandler]] = defaultdict(list)

        self.event_queue: asyncio.Queue[TSEvent] = asyncio.Queue()

    async def _run_event_handler(
        self,
        event: TSEvent,
        handler: T_EventHandler,
        timeout: float | None = None,
    ) -> None:
        try:
            await asyncio.wait_for(handler(event), timeout=timeout)
        except asyncio.TimeoutError:
            pass  # TODO: Add warning from warning module. tell that coro ran out of time
        except Exception as e:
            logger.exception(f"{e.__class__.__name__} happend in event handler")
            self.parent.emit(TSEvent(event="exception", msg=f"Error: {str(e)}", ctx=event.ctx))
            # raise TSEventException(e) from None  # TODO: Send only current stackframe (_run_event_handler)

    def _handle_event(self, event: TSEvent, timeout: float | None = None):
        event_handlers = self.event_handlers.get(event.event, [])

        for event_handler in event_handlers:
            asyncio.create_task(self._run_event_handler(event, event_handler.run, timeout))

    async def _handle_events_task(self) -> None:
        """
        Task to run events put into the self._event_queue

        if task is cancelled, it will try to run all the events
        still in the queue with a timeout
        """
        try:
            while True:
                event = await self.event_queue.get()

                logger.debug(f"Got event: {event}")
                self._handle_event(event)

                self.event_queue.task_done()

        except asyncio.CancelledError:
            while not self.event_queue.empty():
                event = await self.event_queue.get()

                self._handle_event(event, timeout=1.0)

                self.event_queue.task_done()

    def register_event_handler(self, event_handler: TSEventHandler) -> None:
        """Registers event handlers that will be called when given event happens"""

        self.event_handlers[event_handler.event].append(event_handler)

        logger.debug(
            f"Registered {event_handler.event!r} event to execute {event_handler.handler.__name__!r}"
            f"""{f" from {event_handler.plugin_instance.__class__.__name__!r}" if event_handler.plugin_instance else ''}"""
        )

    async def run(self):
        self.parent.register_background_task(self._handle_events_task, name="HandleEvent-Task")
