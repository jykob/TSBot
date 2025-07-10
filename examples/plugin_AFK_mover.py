from __future__ import annotations

import asyncio
from contextlib import suppress

from tsbot import TSBot, TSTask, plugin, query
from tsbot.exceptions import TSResponseError

AFK_CHANNEL_ID = "2"
MAX_IDLE_TIME = 30 * 60  # 30 minutes


def is_not_active(client: dict[str, str]) -> bool:
    return int(client["client_idle_time"]) > MAX_IDLE_TIME * 1000


def not_in_afk_channel(client: dict[str, str]) -> bool:
    return client["cid"] != AFK_CHANNEL_ID


def is_not_query(client: dict[str, str]) -> bool:
    return client["client_type"] != "1"


class AFKPlugin(plugin.TSPlugin):
    CHECK_PERIOD = 5 * 60  # 5 minutes
    CLIENT_LIST_QUERY = query("clientlist").option("times")
    MOVE_QUERY = query("clientmove").params(cid=AFK_CHANNEL_ID)

    _task: TSTask

    def should_be_moved(self, client: dict[str, str]) -> bool:
        return all(check(client) for check in (is_not_active, not_in_afk_channel, is_not_query))

    async def check_afk_clients(self, bot: TSBot):
        clients = await bot.send(self.CLIENT_LIST_QUERY)

        clients_to_be_moved = set(c["clid"] for c in clients if self.should_be_moved(c))
        if not clients_to_be_moved:
            return

        move_query = self.MOVE_QUERY.param_block({"clid": id} for id in clients_to_be_moved)

        with suppress(TSResponseError):
            await bot.send(move_query)

    @plugin.on("connect")
    async def start_task(self, bot: TSBot, ctx: None):
        """Start the checking task on connect."""
        self._task = bot.register_every_task(self.CHECK_PERIOD, self.check_afk_clients)

    @plugin.on("disconnect")
    async def cancel_task(self, bot: TSBot, ctx: None):
        """Cleanup task on disconnect."""
        self._task.cancel()


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)
bot.load_plugin(AFKPlugin())

asyncio.run(bot.run())
