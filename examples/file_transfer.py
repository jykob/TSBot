from __future__ import annotations

import asyncio
import io
import itertools
import os
import socket

from tsbot import TSBot, TSCtx, query
from tsbot.exceptions import TSException

"""
Example to handle file upload/download.

This code uses synchronous code to handle reading/writing data from/to files
and sending/receiving data from the server.
This is done inside another thread via asyncio.to_thread().
Running upload/download on another thread allows the bot to continue
running while the synchronous operations are running.
"""


_ft_id_gen = itertools.count()


async def get_default_channel_id(bot: TSBot):
    for channel in await bot.send(query("channellist").option("flags")):
        if channel["channel_flag_default"] == "1":
            return int(channel["cid"])

    raise TSException("Failed to find default channel")


async def upload(
    bot: TSBot,
    file: io.BufferedReader,
    path: str,
    *,
    cid: int | None = None,
    cpw: str = "",
    overwrite: bool = False,
) -> int:
    """
    Uploads a file to the TeamSpeak server.
    If no channel id (cid) provided, will use the default channel.

    :return: Number of bytes uploaded.
    """

    def _upload(file: io.BufferedReader, key: str, addr: tuple[str, int]) -> int:
        with socket.create_connection(addr) as s:
            s.sendall(key.encode())
            return s.sendfile(file)

    size = os.fstat(file.fileno()).st_size
    cid = cid if cid is not None else (await get_default_channel_id(bot))

    init_query = query("ftinitupload").params(
        clientftfid=next(_ft_id_gen),
        name=path,
        size=size,
        cid=cid,
        cpw=cpw,
        resume=0,
        overwrite=overwrite,
    )

    resp = await bot.send(init_query)

    if resp.first.get("status") == "2050":
        raise TSException("File already exists")

    ftkey = resp.first["ftkey"]
    address = (resp.first.get("ip", "127.0.0.1"), int(resp.first["port"]))

    return await asyncio.to_thread(_upload, file, ftkey, address)


async def download(
    bot: TSBot,
    file: io.BufferedWriter,
    path: str,
    *,
    cid: int | None = None,
    cpw: str = "",
) -> int:
    """
    Downloads a file from the TeamSpeak server.
    If no channel id (cid) provided, will use the default channel.

    :return: Number of bytes downloaded.
    """

    def _download(file: io.BufferedWriter, key: str, addr: tuple[str, int]) -> int:
        download_buffer, total = bytearray(io.DEFAULT_BUFFER_SIZE), 0

        with socket.create_connection(addr) as s:
            s.sendall(key.encode())
            while read := s.recv_into(download_buffer):
                file.write(download_buffer[:read])
                total += read

        return total

    cid = cid if cid is not None else (await get_default_channel_id(bot))

    init_query = query("ftinitdownload").params(
        clientftfid=next(_ft_id_gen),
        name=path,
        cid=cid,
        cpw=cpw,
        seekpos=0,
    )

    resp = await bot.send(init_query)

    if resp.first.get("status") == "2051":
        raise TSException("File not found")

    ftkey = resp.first["ftkey"]
    address = (resp.first.get("ip", "127.0.0.1"), int(resp.first["port"]))

    return await asyncio.to_thread(_download, file, ftkey, address)


bot = TSBot(
    username="USERNAME",
    password="PASSWORD",
    address="ADDRESS",
)


@bot.command("upload")
async def send_file(bot: TSBot, ctx: TSCtx, filename: str):
    with open(filename, "rb") as f:
        total = await upload(bot, f, f"/{filename}", overwrite=True)

    await bot.respond(ctx, f"Uploaded {total} bytes to the server")


@bot.command("download")
async def download_file(bot: TSBot, ctx: TSCtx, filename: str):
    with open(filename, "wb") as f:
        total = await download(bot, f, f"/{filename}")

    await bot.respond(ctx, f"Downloaded {total} bytes from the server")


asyncio.run(bot.run())
