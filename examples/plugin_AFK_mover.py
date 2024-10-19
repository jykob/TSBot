import asyncio
from contextlib import suppress

from tsbot import TSBot, TSTask, plugin, query
from tsbot.exceptions import TSException, TSResponseError


class AFKPlugin(plugin.TSPlugin):
    CHECK_PERIOD = 60 * 5  # 5 minutes

    def __init__(self) -> None:
        self.afk_channel_id = "0"
        self.client_query = query("clientlist").option("away")
        self._task: TSTask | None = None

    @plugin.on("connect")
    async def get_afk_channel(self, bot: TSBot, ctx: None):
        channel_list = await bot.send(query("channellist"))

        for channel in channel_list:
            if "AFK" in channel["channel_name"]:
                self.afk_channel_id = channel["cid"]
                break
        else:
            raise TSException("No AFK channel found")

        self._task = bot.register_every_task(self.CHECK_PERIOD, self.check_afk_clients)

    @plugin.on("disconnect")
    async def cancel_task(self, bot: TSBot, ctx: None):
        """Cleanup task on disconnect"""
        if self._task:
            self._task = bot.remove_task(self._task)

    async def check_afk_clients(self, bot: TSBot):
        clients = await bot.send(self.client_query)
        clients_to_be_moved = tuple(
            c["clid"]
            for c in clients
            if c["client_away"] != "0" and c["cid"] != self.afk_channel_id
        )

        if not clients_to_be_moved:
            return

        move_query = (
            query("clientmove")
            .params(cid=self.afk_channel_id)
            .param_block({"clid": id} for id in clients_to_be_moved)
        )

        with suppress(TSResponseError):
            await bot.send(move_query)


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)
bot.load_plugin(AFKPlugin())

asyncio.run(bot.run())
