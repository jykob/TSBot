from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx

bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
    # Default calls per period is 10/3
    ratelimited=True,
    ratelimit_calls=10,
    ratelimit_period=3,
)


@bot.command("spam")
async def spam_chat(bot: TSBot, ctx: TSCtx):
    """
    Spams chat to test ratelimiting.

    When going over the allowed amount of calls during the period,
    the bot will automatically throttle the amount of calls
    """

    for _ in range(20):
        await bot.respond(ctx, "SPAM")


asyncio.run(bot.run())
