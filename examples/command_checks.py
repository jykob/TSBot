from __future__ import annotations

import asyncio

from tsbot import TSBot, commands
from tsbot.exceptions import TSPermissionError


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


def allow_only_uids(*uid: str):
    """Checks for UIDs. If uid not in given list, raise TSPermissionError"""

    async def check_uid(bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str) -> None:
        if ctx.get("invokeruid") not in uid:
            raise TSPermissionError("User not allowed to run this command")

    return check_uid


@commands.add_check(allow_only_uids("v8t+Jw6+qNDl1KHuDfS7zVjKSws="))
@bot.command("eval")
async def eval_(bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str) -> None:
    try:
        response = eval(ctx["invoker_removed"])
    except Exception as e:
        response = f"{e.__class__.__name__}: {e}"

    await bot.respond(ctx, response)


asyncio.run(bot.run())
