from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from tsbot import utils


@dataclass(slots=True, frozen=True)
class TSResponse:
    data: list[dict[str, str]]
    error_id: int
    msg: str

    def __iter__(self) -> Iterator[dict[str, str]]:
        """Iterates through all the datapoints in data"""
        yield from self.data

    @property
    def first(self) -> dict[str, str]:
        """Returns the first datapoint from the response"""
        return self.data[0]

    @classmethod
    def from_server_response(cls, raw_data: list[str]):
        error_id, msg = parse_error_line(raw_data.pop())
        data = utils.parse_data("".join(raw_data))
        return cls(data=data, error_id=error_id, msg=msg)


def parse_error_line(input_str: str) -> tuple[int, str]:
    data = utils.parse_line(input_str)
    return int(data["id"]), data["msg"]
