import asyncio

from tsbot import TSBot, TSCtx, plugin
from tsbot.exceptions import TSCommandError


class ExceptionHandler(plugin.TSPlugin):
    @plugin.on("command_error")
    async def catch_command_error(self, bot: TSBot, ctx: TSCtx):
        await bot.respond(ctx, f"COMMAND_ERROR - {ctx['exception']!r}")

    @plugin.on("permission_error")
    async def catch_permission_error(self, bot: TSBot, ctx: TSCtx):
        await bot.respond(ctx, f"PERMISSION_ERROR - {ctx['exception']!r}")

    @plugin.on("parameter_error")
    async def catch_parameter_error(self, bot: TSBot, ctx: TSCtx):
        await bot.respond(ctx, f"PARAMETER_ERROR - {ctx['exception']!r}")


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("error", help_text="Raises exception to test handling")
def raise_ts_exception(bot: TSBot, ctx: TSCtx):
    raise TSCommandError("Exception raised")


bot.load_plugin(ExceptionHandler())

asyncio.run(bot.run())
