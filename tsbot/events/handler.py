from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.events.tsevent import TSEvent
    from tsbot.events.tsevent_handler import TSEventHandler


logger = logging.getLogger(__name__)


class EventHanlder:
    def __init__(self, bot: TSBot) -> None:
        self.bot = bot

        self.event_handlers: defaultdict[str, list[TSEventHandler]] = defaultdict(list)
        self.event_queue: asyncio.Queue[TSEvent] = asyncio.Queue()

    def _handle_event(self, event: TSEvent, timeout: float | None = None):
        event_handlers = self.event_handlers.get(event.event, [])

        for event_handler in event_handlers:
            asyncio.create_task(
                asyncio.wait_for(event_handler.run(self.bot, event), timeout=timeout), name="EventHandler"
            )

    async def handle_events_task(self) -> None:
        """
        Task to run events put into the self._event_queue

        if task is cancelled, it will try to run all the events
        still in the queue with a timeout
        """
        try:
            while True:
                event = await self.event_queue.get()

                logger.debug("Got event: %s", event)
                self._handle_event(event)

                self.event_queue.task_done()

        except asyncio.CancelledError:
            while not self.event_queue.empty():
                event = await self.event_queue.get()
                self._handle_event(event, timeout=5.0)

                self.event_queue.task_done()

    def register_event_handler(self, event_handler: TSEventHandler) -> None:
        """Registers event handlers that will be called when given event happens"""
        self.event_handlers[event_handler.event].append(event_handler)

        logger.debug(f"Registered {event_handler.event!r} event to execute {event_handler.handler.__qualname__!r}")
