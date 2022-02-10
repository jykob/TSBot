import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from tsbot.plugin import TSPlugin

logger = logging.getLogger(__name__)


@dataclass
class TSEvent:
    event: str
    msg: str | None = None
    ctx: dict[str, Any] | None = None


T_EventHandler = Callable[..., Coroutine[TSEvent, None, None]]


@dataclass
class TSEventHandler:
    event: str
    handler: T_EventHandler
    plugin: TSPlugin | None = None


class EventHanlder:
    def __init__(self) -> None:
        self.event_handlers: defaultdict[str, list[TSEventHandler]] = defaultdict(list)

        self.event_queue: asyncio.Queue[TSEvent] = asyncio.Queue()

    def _handle_event(self, event: TSEvent, timeout: int | float | None = None):
        async def _run_event_handler(handler: T_EventHandler) -> None:
            try:
                await asyncio.wait_for(handler(event), timeout=timeout)
            except asyncio.TimeoutError:
                pass
            except Exception:
                logger.exception("Exception happend in event handler")
                raise

        event_handlers = self.event_handlers.get(event.event)

        if not event_handlers:
            return

        for event_handlers in event_handlers:
            asyncio.create_task(_run_event_handler(event_handlers.handler))

    async def handle_events_task(self) -> None:
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
        """
        Registers event handlers that will be called when given event happens
        """
        self.event_handlers[event_handler.event].append(event_handler)
        logger.debug(
            f"Registered {event_handler.event!r} event to execute {event_handler.handler.__name__}"
            f"""{f" from '{event_handler.plugin}'" if event_handler.plugin else ''}"""
        )
