from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, TypeVar

from tsbot import utils

if TYPE_CHECKING:
    T = TypeVar("T", bound="TSEvent")


class TSEvent(NamedTuple):
    event: str
    ctx: dict[str, str]

    @classmethod
    def from_server_response(cls: type[T], raw_data: str) -> T:
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, _, data = raw_data.partition(" ")
        return cls(event=event.removeprefix("notify"), ctx=utils.parse_line(data))
