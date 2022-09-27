from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import typealiases


class TSEvent(NamedTuple):
    event: str
    ctx: typealiases.TCtx

    @classmethod
    def from_server_response(cls, raw_data: str):
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, data = raw_data.split(" ", maxsplit=1)
        return cls(event=event.removeprefix("notify"), ctx=utils.parse_line(data))
