# TSBot &nbsp; [![PyPI - Version](https://img.shields.io/pypi/v/tsbot)](https://pypi.org/project/tsbot/)

Asynchronous Python framework to build **TeamSpeak 3 Server Query** bots

## ✅ Features

- Modern Python `async` and `await` syntax
- Secure connection through SSH
- Ease of use query building
- Built-in and configurable ratelimiter if no access to `query_ip_allowlist.txt`

## ✏️ Examples

```python
from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, query


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("hello")
async def hello_world(bot: TSBot, ctx: TSCtx):
    await bot.respond(ctx, f"Hello {ctx['invokername']}!")


@bot.on("cliententerview")
async def poke_on_enter(bot: TSBot, ctx: TSCtx):
    poke_query = query("clientpoke").params(clid=ctx["clid"], msg="Welcome to the server!")
    await bot.send(poke_query)


asyncio.run(bot.run())
```

**Check out [📁examples](https://github.com/jykob/TSBot/blob/main/examples) for more**

## 📦 Installation

**Python 3.10 or higher is required**

Installing with pip:

```shell
# Linux/macOS
python3 -m pip install tsbot

# Windows
py -3 -m pip install tsbot
```
