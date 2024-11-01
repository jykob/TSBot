from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

from tsbot import logging

if TYPE_CHECKING:
    from tsbot import bot, tasks


logger = logging.get_logger(__name__)


class TasksHandler:
    def __init__(self) -> None:
        self._started = False
        self._tasks: set[asyncio.Task[None]] = set()
        self._starting_tasks: list[tasks.TSTask] = []

    def _start_task(self, bot: bot.TSBot, task: tasks.TSTask) -> None:
        task.task = asyncio.create_task(task.handler(bot), name=task.name)
        self._tasks.add(task.task)
        task.task.add_done_callback(self._task_callback)
        logger.debug("Started a task handler %r", getattr(task.handler, "__name__", task.handler))

    def _task_callback(self, task: asyncio.Task[None]) -> None:
        self._tasks.remove(task)

        with contextlib.suppress(asyncio.CancelledError):
            if e := task.exception():
                logger.exception("Task finished with an exception: %r", e, exc_info=e)

    def register_task(self, bot: bot.TSBot, task: tasks.TSTask) -> None:
        self._start_task(bot, task) if self._started else self._starting_tasks.append(task)

    def remove_task(self, task: tasks.TSTask) -> None:
        if task.task and not task.task.done():
            task.task.cancel()

    def start(self, bot: bot.TSBot) -> None:
        while self._starting_tasks:
            self._start_task(bot, self._starting_tasks.pop())

        self._started = True
        logger.debug("Task handler started")

    async def close(self) -> None:
        self._started = False
        self._starting_tasks.clear()

        for task in self._tasks:
            task.cancel()

        # Sleep until all the tasks are removed from tasks list
        while self._tasks:
            await asyncio.sleep(0)
