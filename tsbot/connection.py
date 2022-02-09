from __future__ import annotations

import logging
import asyncssh


logger = logging.getLogger(__name__)


class TSConnection:
    def __init__(self) -> None:
        self.writer: asyncssh.stream.SSHWriter[str]
        self.reader: asyncssh.stream.SSHReader[str]

    async def connect(self, username: str, password: str, address: str, port: int = 10022):
        connection = await asyncssh.connection.connect(address, port=port, username=username, password=password)

        self.writer, self.reader, _ = await connection.open_session()  # type: ignore

    async def read_lines(self, number_of_lines: int = 1):
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
            logger.warning("Connection closed")

    async def read(self):
        try:
            while not self.reader.at_eof():
                data = await self.reader.readuntil("\n\r")
                data = data.strip()

                if not data:
                    break

                yield data

        except (ConnectionResetError, asyncssh.misc.ConnectionLost, asyncssh.misc.DisconnectError):
            logger.warning("Connection closed")

        finally:
            await self.close()

        logger.debug("Reading done")

    async def write(self, msg: str):
        self.writer.write(f"{msg}\n\r")
        await self.writer.drain()

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()
