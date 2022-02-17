from __future__ import annotations

import logging
from types import TracebackType
from typing import AsyncGenerator

import asyncssh

logger = logging.getLogger(__name__)


class TSConnection:
    def __init__(self, username: str, password: str, address: str, port: int = 10022) -> None:
        self.username = username
        self.password = password
        self.address = address
        self.port = port

        self.writer: asyncssh.stream.SSHWriter[str]
        self.reader: asyncssh.stream.SSHReader[str]

    async def connect(self) -> None:
        connection = await asyncssh.connection.connect(
            self.address,
            port=self.port,
            username=self.username,
            password=self.password,
        )

        self.writer, self.reader, _ = await connection.open_session()  # type: ignore

    async def read_lines(self, number_of_lines: int = 1) -> AsyncGenerator[str, None]:
        try:
            lines_read: int = 0

            while not self.reader.at_eof():
                data = await self.reader.readuntil("\n\r")
                data = data.strip()

                if not data:
                    return

                lines_read += 1
                yield data

                if lines_read >= number_of_lines:
                    return

        except (ConnectionResetError, asyncssh.misc.ConnectionLost, asyncssh.misc.DisconnectError):
            pass

    async def read(self) -> AsyncGenerator[str, None]:
        try:
            while not self.reader.at_eof():
                data = await self.reader.readuntil("\n\r")
                data = data.strip()

                if not data:
                    break

                yield data

        except (ConnectionResetError, asyncssh.misc.ConnectionLost, asyncssh.misc.DisconnectError):
            pass

        logger.debug("Reading done")

    async def write(self, msg: str) -> None:
        self.writer.write(f"{msg}\n\r")
        await self.writer.drain()

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()

    async def __aenter__(self) -> None:
        await self.connect()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not hasattr(self, "writer") and self.writer.is_closing():
            return

        await self.close()
