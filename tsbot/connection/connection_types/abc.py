from __future__ import annotations

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

        Will raise `ConnectionAbortedError` if cannot authenticate connection.
        """

    @abstractmethod
    def close(self) -> None:
        """Closes the connection to the server."""

    @abstractmethod
    async def wait_closed(self) -> None:
        """Awaits until the connection is closed."""

    @abstractmethod
    async def write(self, data: str) -> None:
        """
        Write data to the server.

        This method must terminate data with line ending.
        """

    @abstractmethod
    async def readline(self) -> str | None:
        """
        Reads a single line determined by line ending sequence.

        Will include line ending sequence in return str
        """
