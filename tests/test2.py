import asyncio

from tsbot import TSBot
from tsbot import events
from tsbot.query import query


bot = TSBot(
    username="HontBot",
    password="YRn6hLZ0",
    address="localhost",
)


@bot.command("hello")
async def hello_world(bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str):
    await bot.respond(ctx, "Hello World!")


@bot.on("cliententerview")
async def poke_on_enter(bot: TSBot, event: events.TSEvent):
    poke_query = query("clientpoke").params(clid=event.ctx["clid"], msg="Welcome to the server!")
    await bot.send(poke_query)


asyncio.run(bot.run())
