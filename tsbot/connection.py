from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

import asyncssh

logger = logging.getLogger(__name__)


class TSConnection:
    def __init__(self, username: str, password: str, address: str, port: int = 10022) -> None:
        self.username = username
        self.password = password
        self.address = address
        self.port = port

        self._connection: asyncssh.connection.SSHClientConnection | None = None
        self._writer: asyncssh.stream.SSHWriter[str] | None = None
        self._reader: asyncssh.stream.SSHReader[str] | None = None

    async def connect(self) -> None:
        self._connection = await asyncssh.connection.connect(
            self.address,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=None,
        )

        self._writer, self._reader, _ = await self._connection.open_session()  # type: ignore
        logger.info("Connected")

    async def close(self) -> None:
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

        if self._connection:
            self._connection.close()
            await self._connection.wait_closed()

        logger.info("Connection closed")

    async def read_lines(self, number_of_lines: int = 1) -> AsyncIterator[str]:
        lines_read = 0

        while lines_read < number_of_lines and (data := await self._read()):
            lines_read += 1
            yield data.strip()

    async def read(self) -> AsyncIterator[str]:
        while data := await self._read():
            yield data.strip()

        logger.debug("Reading done")

    async def _read(self) -> str | None:
        if not self._reader:
            raise ConnectionResetError("Trying to read on a closed connection")

        try:
            data = await self._reader.readuntil("\n\r")

        except asyncio.IncompleteReadError:
            return None

        else:
            return data

    async def write(self, msg: str) -> None:
        if not self._writer or self._writer.is_closing():
            raise BrokenPipeError("Trying to write on a closed connection")

        self._writer.write(f"{msg}\n\r")

        try:
            await self._writer.drain()
        except Exception as e:
            logger.warning("%s: %s", e.__class__.__qualname__, e)
