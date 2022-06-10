from __future__ import annotations

import asyncio

from tsbot import TSBot, events, query


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("hello")
async def hello_world(bot: TSBot, ctx: dict[str, str]):
    await bot.respond(ctx, f"Hello {ctx['invokername']}!")


@bot.on("cliententerview")
async def poke_on_enter(bot: TSBot, event: events.TSEvent):
    poke_query = query("clientpoke").params(clid=event.ctx["clid"], msg="Welcome to the server!")
    await bot.send(poke_query)


asyncio.run(bot.run())
