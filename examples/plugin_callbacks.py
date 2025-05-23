from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, plugin

"""
Example how to use callbacks to do side effects when the plugin is loaded or unloaded.

When the plugin is loaded, all the decorated event handlers and commands are registered.
If you want to manually register event handlers or commands, you can use the `on_load` callback.

When the plugin is unloaded, all the decorated event handlers and commands are removed automatically.
You need to manually remove dynamically registered event handlers and commands using the `on_unload` callback.
"""


class CallbackPlugin(plugin.TSPlugin):
    hello_command: plugin.TSCommand

    async def plugin_hello(self, bot: TSBot, ctx: TSCtx):
        await bot.respond(ctx, "This command will be unloaded!")

    def on_load(self, bot: TSBot):
        self.hello_command = bot.register_command("hello", self.plugin_hello)
        print("Plugin loaded")

    def on_unload(self, bot: TSBot):
        bot.remove_command(self.hello_command)
        print("Plugin unloaded")


callback_plugin = CallbackPlugin()

bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("load")
async def load_callback_plugin(bot: TSBot, ctx: TSCtx):
    bot.load_plugin(callback_plugin)


@bot.command("unload")
async def unload_callback_plugin(bot: TSBot, ctx: TSCtx):
    bot.unload_plugin(callback_plugin)


asyncio.run(bot.run())
