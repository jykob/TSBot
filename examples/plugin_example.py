from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, TSEvent, plugin, query


class TestPlugin(plugin.TSPlugin):
    def __init__(self) -> None:
        self.message = "Hello from plugin"
        self.move_message = "{username} has moved"

    @plugin.command("pluginhello")
    async def plugin_hello(self, bot: TSBot, ctx: TSCtx):
        await bot.respond(ctx, message=self.message)

    @plugin.on("clientmoved")
    async def plugin_move(self, bot: TSBot, event: TSEvent):
        info_query = query("clientinfo").params(clid=event.ctx["clid"])
        resp = await bot.send(info_query, max_cache_age=5)

        print(self.move_message.format(username=resp.first["client_nickname"]))


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)

bot.load_plugin(TestPlugin())

asyncio.run(bot.run())
