from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, query
from tsbot.exceptions import TSPermissionError

ALLOWED_SERVER_GROUPS = ("Server Admin",)

GET_DATABASE_ID_QUERY = query("clientgetdbidfromuid")
SERVER_GROUPS_BY_ID_QUERY = query("servergroupsbyclientid")


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


async def check_server_groups(bot: TSBot, ctx: TSCtx, *args: str, **kwargs: str):
    """Check if client has allowed server group. If not, raise permission error"""

    ids = await bot.send(GET_DATABASE_ID_QUERY.params(cluid=ctx["invokeruid"]))
    groups = await bot.send(SERVER_GROUPS_BY_ID_QUERY.params(cldbid=ids.first["cldbid"]))

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
