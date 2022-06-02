from __future__ import annotations

import logging
from typing import AsyncGenerator

import asyncssh

logger = logging.getLogger(__name__)


class TSConnection:
    def __init__(self, username: str, password: str, address: str, port: int = 10022) -> None:
        self.username = username
        self.password = password
        self.address = address
        self.port = port

        self.connection: asyncssh.connection.SSHClientConnection
        self.writer: asyncssh.stream.SSHWriter[str]
        self.reader: asyncssh.stream.SSHReader[str]

    async def connect(self) -> None:
        self.connection = await asyncssh.connection.connect(
            self.address,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=None,
        )

        self.writer, self.reader, _ = await self.connection.open_session()  # type: ignore
        logger.info("Connected")

    async def close(self) -> None:
        if hasattr(self, "writer"):
            self.writer.close()
            await self.writer.wait_closed()

        if hasattr(self, "connection"):
            self.connection.close()
            await self.connection.wait_closed()

        logger.info("Connection closed")

    async def read_lines(self, number_of_lines: int = 1) -> AsyncGenerator[str, None]:
        try:
            lines_read: int = 0

            while not (self.reader.at_eof() or lines_read >= number_of_lines):
                data = await self.reader.readuntil("\n\r")

                if not data:
                    return

                lines_read += 1
                yield data.strip()

        except ConnectionError as e:
            logger.warning(e)

        except Exception as e:
            logger.warning(e)

    async def read(self) -> AsyncGenerator[str, None]:
        try:
            while not self.reader.at_eof():
                data = await self.reader.readuntil("\n\r")

                if not data:
                    break

                yield data.strip()

        except ConnectionError as e:
            logger.warning(e)

        except Exception as e:
            logger.warning(e)

        logger.debug("Reading done")

    async def write(self, msg: str) -> None:
        if self.writer.is_closing():
            return

        self.writer.write(f"{msg}\n\r")

        try:
            await self.writer.drain()
        except ConnectionError as e:
            logger.warning(e)
