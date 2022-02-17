from __future__ import annotations

import asyncio

from tsbot import plugin, TSBot


class TestPlugin(plugin.TSPlugin):
    def __init__(self) -> None:
        self.message = "Hello from plugin"

    @plugin.command("plugin-hello")
    async def plugin_hello(self, bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str):
        await bot.respond(ctx, message=self.message)


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)

bot.load_plugin(TestPlugin())


asyncio.run(bot.run())
