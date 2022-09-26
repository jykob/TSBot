from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tsbot import utils

if TYPE_CHECKING:
    from tsbot import typealiases


@dataclass(slots=True, frozen=True, eq=False)
class TSEvent:
    event: str
    ctx: typealiases.TCtx = field(default_factory=dict)

    @classmethod
    def from_server_response(cls, raw_data: str):
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, data = raw_data.split(" ", maxsplit=1)
        return cls(event=event.removeprefix("notify"), ctx=utils.parse_line(data))
