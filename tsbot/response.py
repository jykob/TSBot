from __future__ import annotations

from tsbot.utils import parse_data, parse_line, unescape


class TSResponse:
    def __init__(self, data: list[dict[str, str]], error_id: int, msg: str) -> None:
        self.data = data
        self.error_id = error_id
        self.msg = msg

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(data={self.data!r}, error_id={self.error_id!r}, msg={self.msg!r})"

    @property
    def first(self):
        return self.data[0]

    @classmethod
    def from_server_response(cls, raw_data: list[str]):
        error_id, msg = parse_error_line(raw_data.pop())
        data = parse_data("".join(raw_data))
        return cls(data=data, error_id=error_id, msg=msg)


def parse_error_line(input_str: str) -> tuple[int, str]:
    data = parse_line(input_str)
    return int(data["id"]), data["msg"]
