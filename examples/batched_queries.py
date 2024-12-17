from __future__ import annotations

import asyncio

from tsbot import TSBot, TSCtx, query

"""
Example to send multiple queries to the server at once

Some queries have no real reason to wait for a response from the server.
Sending a bunch of these queries can cause massive slowdowns.
Each query has to be sent one-by-one due to limitations of the Server Query interface.
This means each query has to wait for a response from the server before another query can be sent.

In cases of high latency and/or high amount of queries, you can use `bot.send_batched()` methods.
These methods allow you to send multiple queries at once, while discarding the responses.
"""


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("poke", help_text="pokes all clients with a message")
async def poke_all_clients(bot: TSBot, ctx: TSCtx, message: str) -> None:
    clients_list = await bot.send(query("clientlist"))
    poke_query = query("clientpoke").params(msg=message)

    await bot.send_batched(
        poke_query.params(clid=client["clid"])
        for client in clients_list
        if client["client_type"] == "0"
    )


asyncio.run(bot.run())
