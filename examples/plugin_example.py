from __future__ import annotations

import asyncio

from tsbot import TSBot, plugin, query
from tsbot.events import TSEvent


class TestPlugin(plugin.TSPlugin):
    def __init__(self) -> None:
        self.message = "Hello from plugin"
        self.move_message = "{username} has moved"

    @plugin.command("plugin-hello")
    async def plugin_hello(self, bot: TSBot, ctx: dict[str, str]):
        await bot.respond(ctx, message=self.message)

    @plugin.on("clientmove")
    async def plugin_move(self, bot: TSBot, event: TSEvent):
        info_query = query("clientinfo").params(clid=event.ctx["clid"])
        resp = await bot.send(info_query)

        print(self.move_message.format(username=resp.first["client_nickname"]))


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)

bot.load_plugin(TestPlugin())


asyncio.run(bot.run())
