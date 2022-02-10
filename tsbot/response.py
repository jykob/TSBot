from typing import Any


class TSResponse:
    def __init__(self, data: dict[str, Any], error: int, msg: str) -> None:
        self.data = data
        self.error = error
        self.msg = msg

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(data={self.data!r}, error={self.error!r}, msg={self.msg!r})"

    @classmethod
    def from_server_response(cls, raw_data: list[str]):
        error, msg = parse_response_error(raw_data.pop())
        data = {}  # TODO: parse response
        return cls(data=data, error=error, msg=msg)


class TSResponseError(Exception):
    pass


def parse_response_error(input_str: str) -> tuple[int, str]:
    _, error_id, msg = input_str.split(" ")

    return int(error_id.split("=")[-1]), msg.split("=")[-1]
