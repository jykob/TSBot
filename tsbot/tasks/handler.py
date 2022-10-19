from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tsbot import tasks, bot


class TasksHandler:
    def __init__(self) -> None:
        self._started = False
        self._to_be_started: list[tasks.TSTask] = []
        self._tasks: list[tasks.TSTask] = []

    def _start_task(self, bot: bot.TSBot, task: tasks.TSTask) -> None:
        task.task = asyncio.create_task(task.handler(bot), name=task.name)
        task.task.add_done_callback(lambda _: self.remove_task(task))

        self._tasks.append(task)

    def register_task(self, bot: bot.TSBot, task: tasks.TSTask) -> None:
        if not self._started:
            self._to_be_started.append(task)
        else:
            self._start_task(bot, task)

        logger.debug(f"Registered a task: {task.handler.__qualname__!r}")

    def remove_task(self, task: tasks.TSTask) -> None:
        if task.task and not task.task.done():
            task.task.cancel()

        self._tasks = [t for t in self._tasks if t != task]

    def start(self, bot: bot.TSBot):

        while self._to_be_started:
            self._start_task(bot, self._to_be_started.pop())

        self._started = True
        logger.debug("Task handler started")

    async def close(self):
        for task in self._tasks:
            if task.task:
                task.task.cancel()

        # Sleep until all the tasks are removed from tasks list
        while self._tasks:
            await asyncio.sleep(0)
