from __future__ import annotations

import asyncio

from typing_extensions import override

from tsbot import parsers
from tsbot.connection.connection_types import abc


class RawConnection(abc.Connection):
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int,
    ) -> None:
        self._username = username
        self._password = password
        self._address = address
        self._port = port

        self._writer: asyncio.StreamWriter | None = None
        self._reader: asyncio.StreamReader | None = None

    @override
    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self._address, self._port)

    @override
    async def validate_header(self) -> None:
        if (data := await self.readline()) and data != "TS3\n\r":
            raise ConnectionAbortedError("Invalid TeamSpeak server")
        await self.readline()

    @override
    async def authenticate(self) -> None:
        await self.write(f"login {self._username} {self._password}")

        data = await self.readline()
        if data is None:
            raise ConnectionAbortedError

        resp = parsers.parse_line(data.rstrip().removeprefix("error "))
        if resp["id"] != "0":
            raise ConnectionAbortedError(
                "".join((resp["msg"], f" ({extra})" if (extra := resp.get("extra_msg")) else ""))
            )

    @override
    def close(self) -> None:
        if self._writer:
            self._writer.close()

    @override
    async def wait_closed(self) -> None:
        if not self._writer:
            raise ConnectionError("Trying to wait on uninitialized connection")

        await self._writer.wait_closed()

    @override
    async def write(self, data: str) -> None:
        if not self._writer or self._writer.is_closing():
            raise BrokenPipeError("Trying to write on a closed connection")

        self._writer.write(f"{data}\n\r".encode())
        await self._writer.drain()

    @override
    async def readline(self) -> str | None:
        if not self._reader:
            raise ConnectionResetError("Reading on a closed connection")

        try:
            return (await self._reader.readuntil(b"\n\r")).decode()
        except Exception:
            return None
