from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from tsbot.plugin import TSPlugin


@dataclass
class TSResponse:
    raw_data: str
    error: int
    msg: str


@dataclass
class TSEvent:
    event: str
    msg: str | None = None
    ctx: dict[str, Any] | None = None


@dataclass
class TSCommand:
    cmds: tuple[str]
    handler: Callable[..., None]
    plugin: TSPlugin

    def __name__(self):
        return self.handler.__name__

    def __call__(self, *args: tuple[str, ...], **kwargs: dict[str, str]):
        return self.handler(*args, **kwargs)


@dataclass
class TSEventHandler:
    event: str
    handler: Callable[..., None]
    plugin: TSPlugin

    def __name__(self):
        return self.handler.__name__

    def __call__(self, *args: tuple[str, ...], **kwargs: dict[str, str]):
        return self.handler(*args, **kwargs)
