from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tsbot.bot import TSBot


class Extension:
    def __init__(self, parent: TSBot) -> None:
        self.parent = parent

    async def run(self):
        ...
