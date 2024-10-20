from __future__ import annotations

import asyncio

import pytest

from tsbot import bot, tasks


class MockBot(bot.TSBot):
    def __init__(self) -> None: ...


@pytest.fixture
def mock_bot():
    return MockBot()


@pytest.fixture
def tasks_handler():
    return tasks.TasksHandler()


@pytest.fixture
def running_tasks_handler(tasks_handler: tasks.TasksHandler, mock_bot: bot.TSBot):
    tasks_handler.start(mock_bot)
    return tasks_handler


@pytest.fixture
def tstask():
    async def task(bot: bot.TSBot):
        while True:
            await asyncio.sleep(0)

    return tasks.TSTask(task)


@pytest.mark.asyncio
async def test_registered_task_has_remove_callback(
    running_tasks_handler: tasks.TasksHandler, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    running_tasks_handler.register_task(mock_bot, tstask)
    assert tstask.task and tstask.task._callbacks


def test_register_task_on_not_started_handler(
    tasks_handler: tasks.TasksHandler, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    tasks_handler.register_task(mock_bot, tstask)
    assert tstask.task is None


@pytest.mark.asyncio
async def test_removing_task_cancels_task(
    running_tasks_handler: tasks.TasksHandler, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    running_tasks_handler.register_task(mock_bot, tstask)
    running_tasks_handler.remove_task(tstask)

    assert tstask.task
    assert tstask.task.cancelling() or tstask.task.cancelled()


@pytest.mark.asyncio
async def test_register_task_on_not_started_handler_start(
    tasks_handler: tasks.TasksHandler, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    tasks_handler.register_task(mock_bot, tstask)
    assert tstask.task is None

    tasks_handler.start(mock_bot)
    assert tstask.task


@pytest.mark.asyncio
async def test_close_finishes_all_tasks(
    running_tasks_handler: tasks.TasksHandler, tstask: tasks.TSTask, mock_bot: bot.TSBot
):
    running_tasks_handler.register_task(mock_bot, tstask)
    await running_tasks_handler.close()
    assert running_tasks_handler.empty
