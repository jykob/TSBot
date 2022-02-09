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


@dataclass
class TSEvent:
    event: str
    msg: str | None = None
    ctx: dict[str, Any] | None = None


T_CommandHandler = Callable[..., Coroutine[dict[str, Any], Any, None]]


@dataclass
class TSCommand:
    commands: tuple[str, ...]
    handler: T_CommandHandler
    plugin: TSPlugin | None = None


T_EventHandler = Callable[..., Coroutine[TSEvent, None, None]]


@dataclass
class TSEventHandler:
    event: str
    handler: T_EventHandler
    plugin: TSPlugin | None = None
