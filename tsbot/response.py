from __future__ import annotations

from collections.abc import Generator, Sequence
from dataclasses import dataclass

from typing_extensions import Self

from tsbot import parsers


@dataclass(slots=True, frozen=True)
class TSResponse:
    """
    Class to represent the response to a query from a Teamspeak server.
    """

    data: tuple[dict[str, str], ...]
    error_id: int
    msg: str

    def __iter__(self) -> Generator[dict[str, str], None, None]:
        yield from self.data

    @property
    def first(self) -> dict[str, str]:
        """First datapoint from the response"""
        return self.data[0]

    @property
    def last(self) -> dict[str, str]:
        """Last datapoint from the response"""
        return self.data[-1]

    @classmethod
    def from_server_response(cls, raw_data: Sequence[str]) -> Self:
        response_info = parsers.parse_line(raw_data[-1].removeprefix("error "))
        data = parsers.parse_data("".join(raw_data[:-1]))

        error_id = int(response_info.pop("id"))
        msg = response_info.pop("msg")

        if response_info:
            data += (response_info,)

        return cls(data=data, error_id=error_id, msg=msg)
