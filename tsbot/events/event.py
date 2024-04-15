from __future__ import annotations

from typing import Any, NamedTuple, TypeVar

from tsbot import context, parsers

_T = TypeVar("_T", bound="TSEvent")


class TSEvent(NamedTuple):
    event: str
    ctx: Any

    @classmethod
    def from_server_notification(cls: type[_T], raw_data: str) -> _T:
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, _, data = raw_data.partition(" ")
        return cls(
            event=event.removeprefix("notify"),
            ctx=context.TSCtx(parsers.parse_line(data)),
        )
