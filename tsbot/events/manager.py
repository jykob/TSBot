from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from tsbot import logging

if TYPE_CHECKING:
    from tsbot import bot, events

logger = logging.get_logger(__name__)


class EventManager:
    def __init__(self) -> None:
        self._event_handlers: defaultdict[str, list[events.TSEventHandler]] = defaultdict(list)
        self._event_queue: asyncio.Queue[events.TSEvent] = asyncio.Queue()
        self._running = False

    def __enter__(self) -> None:
        self._running = True

    def __exit__(self, *exc: Any) -> None:
        self._running = False

    def add_event(self, event: events.TSEvent) -> None:
        if not self._running:
            logger.warning("Event %r emitted during closing and is ignored", event.event)
        else:
            self._event_queue.put_nowait(event)

    def handle_event(self, bot: bot.TSBot, event: events.TSEvent) -> None:
        logger.debug("Got event: %r", event)
        handlers = self._event_handlers.get(event.event)

        if not handlers:
            self._event_queue.task_done()
            return

        tasks = [asyncio.create_task(h.run(bot, event), name="EventHandler") for h in handlers]
        watcher = asyncio.create_task(asyncio.wait(tasks), name="EventWatcher")
        watcher.add_done_callback(lambda _: self._event_queue.task_done())

    async def run_till_empty(self, bot: bot.TSBot) -> None:
        while not self._event_queue.empty():
            self.handle_event(bot, self._event_queue.get_nowait())

        await self._event_queue.join()

    async def handle_events_task(self, bot: bot.TSBot) -> None:
        """Task to run events put into the event queue."""

        with self:
            while True:
                self.handle_event(bot, await self._event_queue.get())

    def register_event_handler(self, event_handler: events.TSEventHandler) -> None:
        """Registers event handlers that will be called when given event happens."""

        self._event_handlers[event_handler.event].append(event_handler)

        logger.debug(
            "Registered %r event to execute handler %r",
            event_handler.event,
            getattr(event_handler.handler, "__name__", event_handler.handler),
        )

    def remove_event_handler(self, event_handler: events.TSEventHandler) -> None:
        self._event_handlers[event_handler.event].remove(event_handler)

        if not self._event_handlers[event_handler.event]:
            del self._event_handlers[event_handler.event]
