from __future__ import annotations
from dataclasses import dataclass, field

from tsbot import utils


@dataclass(slots=True, frozen=True)
class TSEvent:
    event: str
    msg: str | None = None
    ctx: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_server_response(cls, raw_data: str):
        event, data = raw_data.split(" ", maxsplit=1)
        return cls(event=event.removeprefix("notify"), msg=None, ctx=utils.parse_line(data))
