from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any, TypedDict, cast

# TODO: Python 3.10 compat. Remove when 3.10 EOL
if TYPE_CHECKING:
    _LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    _LoggerAdapter = logging.LoggerAdapter


_logger = logging.getLogger(__package__ or "tsbot")


class LoggerExtra(TypedDict):
    from_module: str


class TSBotLogger(_LoggerAdapter):
    _debug: bool = False

    def __init__(self, logger: logging.Logger, extra: LoggerExtra) -> None:
        super().__init__(logger, extra)

    @classmethod
    def set_debug(cls, value: bool) -> None:
        cls._debug = value

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        if self._debug:
            msg = f"[{cast(LoggerExtra,self.extra)['from_module']}] {msg}"

        return super().process(msg, kwargs)


def get_logger(name: str) -> TSBotLogger:
    return TSBotLogger(_logger, {"from_module": name.removeprefix(f"{__package__}.")})


def set_debug(value: bool) -> None:
    TSBotLogger.set_debug(value)
