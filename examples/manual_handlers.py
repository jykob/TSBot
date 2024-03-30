from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, query


async def hello_world(bot: TSBot, ctx: TSCtx):
    await bot.respond(ctx, "Hello World!")


async def print_name_on_enter(bot: TSBot, ctx: TSCtx):
    info_query = query("clientinfo").params(clid=ctx["clid"])
    resp = await bot.send(info_query)

    print(f"{resp.first['client_nickname']} has entered the server")


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)

# Register hello_world as a command
bot.register_command("hello", hello_world)

# Register print_name_on_enter as an event
bot.register_event_handler("cliententerview", print_name_on_enter)

asyncio.run(bot.run())
