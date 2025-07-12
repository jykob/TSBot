from __future__ import annotations

import asyncio
from contextlib import suppress

from tsbot import TSBot, TSTask, plugin, query
from tsbot.exceptions import TSResponseError

AFK_CHANNEL_ID = "2"  # Channel ID of the AFK channel
MAX_IDLE_TIME = 30 * 60  # Clients idle for more than 30 minutes are moved to AFK channel
CHECK_PERIOD = 60  # Check every minute for AFK clients


class AFKPlugin(plugin.TSPlugin):
    CLIENT_LIST_QUERY = query("clientlist").option("times")

    _task: TSTask

    def __init__(self, check_period: int, afk_channel_id: str, max_idle_time: int) -> None:
        self.check_period = check_period
        self.afk_channel_id = afk_channel_id
        self.max_idle_time = max_idle_time

        self.move_query = query("clientmove").params(cid=self.afk_channel_id)

    def is_not_query(self, client: dict[str, str]) -> bool:
        return client["client_type"] != "1"

    def is_not_active(self, client: dict[str, str]) -> bool:
        return int(client["client_idle_time"]) > self.max_idle_time * 1000

    def not_in_afk_channel(self, client: dict[str, str]) -> bool:
        return client["cid"] != self.afk_channel_id

    def should_be_moved(self, client: dict[str, str]) -> bool:
        return all(
            check(client)
            for check in (self.is_not_query, self.not_in_afk_channel, self.is_not_active)
        )

    async def check_afk_clients(self, bot: TSBot):
        clients = await bot.send(self.CLIENT_LIST_QUERY)

        clients_to_be_moved = set(c["clid"] for c in clients if self.should_be_moved(c))
        if not clients_to_be_moved:
            return

        move_query = self.move_query.param_block({"clid": id} for id in clients_to_be_moved)

        with suppress(TSResponseError):
            await bot.send(move_query)

    @plugin.on("connect")
    async def start_task(self, bot: TSBot, ctx: None):
        """Start the checking task on connect."""
        self._task = bot.register_every_task(self.check_period, self.check_afk_clients)

    @plugin.on("disconnect")
    async def cancel_task(self, bot: TSBot, ctx: None):
        """Cleanup task on disconnect."""
        self._task.cancel()


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)

bot.load_plugin(
    AFKPlugin(
        check_period=CHECK_PERIOD,
        afk_channel_id=AFK_CHANNEL_ID,
        max_idle_time=MAX_IDLE_TIME,
    ),
)

asyncio.run(bot.run())
