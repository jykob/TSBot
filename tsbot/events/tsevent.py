from __future__ import annotations

from typing import NamedTuple, TypeVar

from tsbot import context, utils

T = TypeVar("T", bound="TSEvent")


class TSEvent(NamedTuple):
    event: str
    ctx: context.TSCtx

    @classmethod
    def from_server_response(cls: type[T], raw_data: str) -> T:
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, _, data = raw_data.partition(" ")
        return cls(event=event.removeprefix("notify"), ctx=context.TSCtx(utils.parse_line(data)))
