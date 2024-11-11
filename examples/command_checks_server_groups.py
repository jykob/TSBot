from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, query
from tsbot.exceptions import TSPermissionError

bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


ALLOWED_SERVER_GROUPS = ("Server Admin",)


async def check_server_groups(bot: TSBot, ctx: TSCtx, *args: str, **kwargs: str):
    """Check if client has allowed server group. If not, raise permission error"""

    client_query = query("clientgetdbidfromuid").params(cluid=ctx["invokeruid"])
    client = (await bot.send(client_query)).first

    server_group_query = query("servergroupsbyclientid").params(cldbid=client["cldbid"])
    groups = (await bot.send(server_group_query)).data

    # Switch 'g == sg["name"]' to 'g in sg["name"]' if you don't want to match strictly
    if not any(g == sg["name"] for g in ALLOWED_SERVER_GROUPS for sg in groups):
        raise TSPermissionError(f"Client not in {', '.join(ALLOWED_SERVER_GROUPS)}")


@bot.command("eval", raw=True, checks=[check_server_groups])
async def eval_(bot: TSBot, ctx: TSCtx, eval_str: str) -> None:
    try:
        response = eval(eval_str)
    except Exception as e:
        response = f"{e.__class__.__name__}: {e}"

    await bot.respond(ctx, response)


asyncio.run(bot.run())
