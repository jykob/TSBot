from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsbot import bot, events


logger = logging.getLogger(__name__)


class EventHanlder:
    def __init__(self) -> None:
        self.event_handlers: defaultdict[str, list[events.TSEventHandler]] = defaultdict(list)
        self.event_queue: asyncio.Queue[events.TSEvent] = asyncio.Queue()

    async def start_event_handlers(self, bot: bot.TSBot, event: events.TSEvent):
        event_handlers = self.event_handlers.get(event.event, [])

        for event_handler in event_handlers:
            asyncio.create_task(event_handler.run(bot, event), name="EventHandler")

    def handle_event(self, bot: bot.TSBot, event: events.TSEvent):
        logger.debug("Got event: %s", event)
        task = asyncio.create_task(self.start_event_handlers(bot, event), name="EventStarter")
        task.add_done_callback(lambda _: self.event_queue.task_done())

    def run_till_empty(self, bot: bot.TSBot):
        while not self.event_queue.empty():
            event = self.event_queue.get_nowait()
            self.handle_event(bot, event)

    async def handle_events_task(self, bot: bot.TSBot) -> None:
        """
        Task to run events put into the self._event_queue

        if task is cancelled, it will try to run all the events
        still in the queue until empty
        """

        try:
            while True:
                event = await self.event_queue.get()
                self.handle_event(bot, event)

        except asyncio.CancelledError:
            logger.debug("Cancelling event handling")
            self.run_till_empty(bot)

    def register_event_handler(self, event_handler: events.TSEventHandler) -> None:
        """Registers event handlers that will be called when given event happens"""
        self.event_handlers[event_handler.event].append(event_handler)

        logger.debug(f"Registered {event_handler.event!r} event to execute {event_handler.handler.__qualname__!r}")
