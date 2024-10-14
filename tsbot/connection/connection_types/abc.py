from abc import ABC, abstractmethod


class Connection(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """
        Establishes connection to the TeamSpeak server.

        Once awaited, the connection should be ready to write and receive data.
        """

    @abstractmethod
    async def validate_header(self) -> None:
        """
        Validate the header given by the server.

        This method shall consume the whole header to make
        sure normal communication with the server can be started.
        Will raise `ConnectionAbortedError` if invalid header found.
        """

    @abstractmethod
    async def authenticate(self) -> None:
        """
        Authenticate the connection.

        This method is called after the header is validated.
        Normal communication with the server allowed.
        """

    @abstractmethod
    def close(self) -> None:
        """Closes the connection to the server."""

    @abstractmethod
    async def wait_closed(self) -> None:
        """Awaits until the connection is closed."""

    @abstractmethod
    async def write(self, data: str) -> None:
        """Write data to the server."""

    @abstractmethod
    async def readline(self) -> str | None:
        """Reads a single line."""

    @abstractmethod
    async def readuntil(self, separator: str) -> str | None:
        """Reads until given separator."""
