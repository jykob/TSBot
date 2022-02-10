from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tsbot.bot import TSBotBase


class Extension:
    def __init__(self, parent: TSBotBase) -> None:
        self.parent = parent
