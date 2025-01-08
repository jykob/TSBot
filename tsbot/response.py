from __future__ import annotations

from collections.abc import Generator, Sequence
from dataclasses import dataclass
from typing import overload

from typing_extensions import Self

from tsbot import parsers


@dataclass(slots=True, frozen=True)
class TSResponse:
    """
    Class to represent the response to a query from a Teamspeak server.
    """

    data: tuple[dict[str, str], ...]  #: The response data.
    error_id: int  #: Id of the error if any.
    msg: str  #: Message of the error if any.

    def __iter__(self) -> Generator[dict[str, str], None, None]:
        yield from self.data

    def __getitem__(self, key: str) -> str:
        """Get the value of a key from the first response dict"""
        return self.first[key]

    @property
    def first(self) -> dict[str, str]:
        """The first dict from the response data"""
        return self.data[0]

    @property
    def last(self) -> dict[str, str]:
        """The last dict from the response data"""
        return self.data[-1]

    @overload
    def get(self, key: str, /) -> str | None: ...

    @overload
    def get(self, key: str, default: str, /) -> str: ...

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get the value of a key from the first response dict"""
        return self.first.get(key, default)

    @classmethod
    def from_server_response(cls, raw_data: Sequence[str]) -> Self:
        response_info = parsers.parse_line(raw_data[-1].removeprefix("error "))
        data = parsers.parse_data("".join(raw_data[:-1]))

        error_id = int(response_info.pop("id"))
        msg = response_info.pop("msg")

        if response_info:
            data += (response_info,)

        return cls(data=data, error_id=error_id, msg=msg)
