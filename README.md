# TSBot

Asynchronous framework to build **TeamSpeak 3 Server Query** bots

## Features

- INSERT FEATURES HERE
- Secure connection through SSH
- Query building

## Examples

```python
import asyncio

from tsbot import TSBot
from tsbot.query import query
from tsbot.extensions import events


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("hello")
async def hello_world(bot: TSBot, ctx: dict[str, str], *args: str, **kwargs: str):
    await bot.respond(ctx, "Hello World!")


@bot.on("cliententerview")
async def poke_on_enter(bot: TSBot, event: events.TSEvent):
    poke_query = query("clientpoke").params(clid=event.ctx["clid"], msg="Welcome to the server!")
    await bot.send(poke_query)


asyncio.run(bot.run())
```

**Check out [examples](https://github.com/0x4aK/TSBot/tree/master/examples) for more**

## Installation

**Python 3.8 or higher is required**

Installing with pip:

```shell
# Linux/macOS
python3 -m pip install tsbot

# Windows
py -3 -m pip install tsbot
```
