from __future__ import annotations

from typing import Any, NamedTuple

from typing_extensions import Self

from tsbot import context, parsers


class TSEvent(NamedTuple):
    event: str
    ctx: Any

    @classmethod
    def from_server_notification(cls, raw_data: str) -> Self:
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, _, data = raw_data.partition(" ")
        return cls(
            event=event.removeprefix("notify"),
            ctx=context.TSCtx(parsers.parse_line(data)),
        )
