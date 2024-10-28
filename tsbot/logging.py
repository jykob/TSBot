from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any, TypedDict, cast

_logger = logging.getLogger(__package__)


class LoggerExtra(TypedDict):
    from_module: str


class TSBotLogger(logging.LoggerAdapter[logging.Logger]):
    _debug: bool = False

    def __init__(self, logger: logging.Logger, extra: LoggerExtra) -> None:
        super().__init__(logger, extra)

    @classmethod
    def set_debug(cls, value: bool):
        cls._debug = value

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        if self._debug:
            msg = f"[{cast(LoggerExtra,self.extra)['from_module']}] {msg}"

        return super().process(msg, kwargs)


def get_logger(name: str):
    return TSBotLogger(_logger, {"from_module": name.removeprefix(f"{__package__}.")})


def set_debug(value: bool):
    TSBotLogger.set_debug(value)
