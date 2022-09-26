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

    def handle_event(self, bot: bot.TSBot, event: events.TSEvent):
        logger.debug("Got event: %s", event)

        if handlers := self.event_handlers.get(event.event):
            tasks = [asyncio.create_task(h.run(bot, event), name="EventHandler") for h in handlers]

            task = asyncio.create_task(asyncio.wait(tasks), name="EventWatcher")
            task.add_done_callback(lambda _: self.event_queue.task_done())

        else:
            self.event_queue.task_done()

    def run_till_empty(self, bot: bot.TSBot):
        while not self.event_queue.empty():
            self.handle_event(bot, self.event_queue.get_nowait())

    async def handle_events_task(self, bot: bot.TSBot) -> None:
        """
        Task to run events put into the self.event_queue

        if task is cancelled, it will try to run all the events
        still in the queue until empty
        """

        try:
            while True:
                self.handle_event(bot, await self.event_queue.get())

        except asyncio.CancelledError:
            logger.debug("Cancelling event handling")
            self.run_till_empty(bot)

    def register_event_handler(self, event_handler: events.TSEventHandler) -> None:
        """Registers event handlers that will be called when given event happens"""
        self.event_handlers[event_handler.event].append(event_handler)

        logger.debug(f"Registered {event_handler.event!r} event to execute {event_handler.handler.__qualname__!r}")
