from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx
from tsbot.exceptions import TSPermissionError

bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


ALLOWED_UIDS = ("v8t+Jw6+qNDl1KHuDfS7zVjKSws=",)


async def check_uid(bot: TSBot, ctx: TSCtx, *args: str, **kwargs: str) -> None:
    """Checks for UIDs. If uid not in given list, raise `TSPermissionError`."""
    if ctx.get("invokeruid") not in ALLOWED_UIDS:
        raise TSPermissionError("User not allowed to run this command")


@bot.command("eval", raw=True, checks=[check_uid])
async def eval_(bot: TSBot, ctx: TSCtx, eval_str: str) -> None:
    try:
        response = eval(eval_str)
    except Exception as e:
        response = f"{e.__class__.__name__}: {e}"

    await bot.respond(ctx, response)


asyncio.run(bot.run())
