from __future__ import annotations

from tsbot import utils


class TSEvent:
    __slots__ = "event", "msg", "ctx"

    def __init__(self, event: str, msg: str | None = None, ctx: dict[str, str] | None = None) -> None:
        self.event = event
        self.msg = msg
        self.ctx = ctx or {}

    @classmethod
    def from_server_response(cls, raw_data: str):
        """
        Creates a TSEvent instance from server notify

        Will remove the 'notify' from the beginning of the 'event'
        """
        event, data = raw_data.split(" ", maxsplit=1)
        return cls(event=event.removeprefix("notify"), msg=None, ctx=utils.parse_line(data))

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(event={self.event!r}, msg={self.msg!r}, ctx={self.ctx!r})"
