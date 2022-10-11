from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator, Type, TypeVar

from tsbot import utils

if TYPE_CHECKING:
    T = TypeVar("T", bound="TSResponse")


@dataclass(slots=True, frozen=True)
class TSResponse:
    data: list[dict[str, str]]
    error_id: int
    msg: str

    def __iter__(self) -> Generator[dict[str, str], None, None]:
        """Iterates through all the datapoints in data"""
        yield from self.data

    @property
    def first(self) -> dict[str, str]:
        """Returns the first datapoint from the response"""
        return self.data[0]

    @classmethod
    def from_server_response(cls: Type[T], raw_data: list[str]) -> T:
        error_id, msg = parse_error_line(raw_data.pop())
        data = utils.parse_data("".join(raw_data))
        return cls(data=data, error_id=error_id, msg=msg)


def parse_error_line(input_str: str) -> tuple[int, str]:
    data = utils.parse_line(input_str)
    return int(data["id"]), data["msg"]
