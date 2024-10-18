from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsbot import bot, tasks


logger = logging.getLogger(__name__)


class TasksHandler:
    def __init__(self) -> None:
        self._started = False
        self._tasks: set[asyncio.Task[None]] = set()
        self._starting_tasks: list[tasks.TSTask] = []

    def _start_task(self, bot: bot.TSBot, task: tasks.TSTask) -> None:
        task.task = asyncio.create_task(task.handler(bot), name=task.name)
        self._tasks.add(task.task)
        task.task.add_done_callback(self._tasks.remove)
        logger.debug("Started a task handler %r", task.handler.__name__)

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
