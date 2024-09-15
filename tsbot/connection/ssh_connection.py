import asyncssh

from tsbot import connection


class SSHConnection(connection.ConnectionABC):
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        port: int,
    ) -> None:
        self.username = username
        self.password = password
        self.address = address
        self.port = port

        self._connection: asyncssh.SSHClientConnection | None = None
        self._writer: asyncssh.SSHWriter[str] | None = None
        self._reader: asyncssh.SSHReader[str] | None = None

    async def connect(self) -> None:
        self._connection = await asyncssh.connect(
            host=self.address,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=None,
            preferred_auth="password",
        )

        self._writer, self._reader, _ = await self._connection.open_session()  # type: ignore

    async def validate_header(self) -> None:
        if (data := await self.readline()) and data != "TS3\n\r":
            raise ConnectionAbortedError("Invalid TeamSpeak server")
        await self.readline()

    async def authenticate(self) -> None:
        """Teamspeak SSH query clients are already authenticated on connect"""

    def close(self) -> None:
        if self._writer:
            self._writer.close()

        if self._connection:
            self._connection.close()

    async def wait_closed(self) -> None:
        if not self._writer or not self._connection:
            raise ConnectionError("Trying to wait on uninitialized connection")

        await self._writer.wait_closed()
        await self._connection.wait_closed()

    async def write(self, data: str) -> None:
        if not self._writer or self._writer.is_closing():
            raise BrokenPipeError("Trying to write on a closed connection")

        self._writer.write(f"{data}\n\r")
        await self._writer.drain()

    async def readline(self) -> str | None:
        return await self.readuntil("\n\r")

    async def readuntil(self, separator: str = "\n\r") -> str | None:
        if not self._reader:
            raise ConnectionResetError("Reading on a closed connection")

        try:
            return await self._reader.readuntil(separator)
        except Exception:
            return None
