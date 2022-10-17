from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator, TypeVar

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

    @property
    def last(self) -> dict[str, str]:
        """Returns the last datapoint from the response"""
        return self.data[-1]

    @classmethod
    def from_server_response(cls: type[T], raw_data: list[str]) -> T:
        response_info = utils.parse_line(raw_data.pop().removeprefix("error "))
        data = utils.parse_data("".join(raw_data))

        error_id = int(response_info.pop("id"))
        msg = response_info.pop("msg")

        if response_info:
            data.append(response_info)

        return cls(data=data, error_id=error_id, msg=msg)
