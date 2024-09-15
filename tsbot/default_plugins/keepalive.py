from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from tsbot import plugin

if TYPE_CHECKING:
    from tsbot import bot, context, tasks


logger = logging.getLogger(__name__)


class KeepAlive(plugin.TSPlugin):
    KEEP_ALIVE_INTERVAL: float = 4 * 60  # 4 minutes
    KEEP_ALIVE_COMMAND: str = "version"

    def __init__(self) -> None:
        self.keep_alive_task: tasks.TSTask | None = None
        self.command_sent_event = asyncio.Event()

    @plugin.on("connect")
    async def init_keep_alive(self, bot: bot.TSBot, ctx: None) -> None:
        self.keep_alive_task = bot.register_task(self._keep_alive_task, name="KeepAlive-Task")

    @plugin.on("disconnect")
    async def kill_keep_alive(self, bot: bot.TSBot, ctx: None) -> None:
        if self.keep_alive_task:
            bot.remove_task(self.keep_alive_task)

    @plugin.on("send")
    async def on_command_sent(self, bot: bot.TSBot, ctx: context.TSCtx) -> None:
        self.command_sent_event.set()

    async def _keep_alive_task(self, bot: bot.TSBot) -> None:
        """
        Task to keep connection alive with the TeamSpeak server

        Normally TeamSpeak server cuts the connection to the query client
        after 5 minutes of inactivity. If the bot doesn't send any commands
        to the server, this task sends a command to keep connection alive.
        """
        logger.debug("Keep-alive task started")

        while True:
            self.command_sent_event.clear()
            try:
                await asyncio.wait_for(
                    asyncio.shield(self.command_sent_event.wait()),
                    timeout=self.KEEP_ALIVE_INTERVAL,
                )
            except asyncio.TimeoutError:
                logger.debug("Sending keep-alive")
                await bot.send_raw(self.KEEP_ALIVE_COMMAND)

            except asyncio.CancelledError:
                logger.debug("Keep-alive task cancelled")
                break
