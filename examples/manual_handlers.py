from __future__ import annotations

import asyncio

from tsbot import TSBot, events
from tsbot.query import query


async def hello_world(bot: TSBot, ctx: dict[str, str]):
    await bot.respond(ctx, "Hello World!")


async def print_name_on_enter(bot: TSBot, event: events.TSEvent):
    info_query = query("clientinfo").params(clid=event.ctx["clid"])
    resp = await bot.send(info_query)

    print(f"{resp.first['client_nickname']} has entered the server")


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)

bot.register_command("hello", hello_world)  # Register hello_world as a command
bot.register_event_handler("cliententerview", print_name_on_enter)  # Register print_name_on_enter as an event

asyncio.run(bot.run())
