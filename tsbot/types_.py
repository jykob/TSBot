from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from tsbot.plugin import TSPlugin


@dataclass
class TSResponse:
    raw_data: str
    error: int
    msg: str


class TSResponseError(Exception):
    pass


T_CommandHandler = Callable[..., Coroutine[dict[str, Any], Any, None]]


@dataclass
class TSCommand:
    commands: tuple[str, ...]
    handler: T_CommandHandler
    plugin: TSPlugin | None = None
