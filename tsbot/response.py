from dataclasses import dataclass


@dataclass
class TSResponse:
    raw_data: str
    error: int
    msg: str


class TSResponseError(Exception):
    pass
