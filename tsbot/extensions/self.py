from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tsbot.extensions.extension import Extension


if TYPE_CHECKING:
    from tsbot.bot import TSBot

logger = logging.getLogger(__name__)


class Self(Extension):
    def __init__(self, parent: TSBot) -> None:
        super().__init__(parent)

        self.clid: str
        self.nickname: str
        self.database_id: str
        self.unique_identifier: str

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(clid={self.clid}, nickname={self.nickname}, database_id={self.database_id}, unique_identifier={self.unique_identifier})"

    async def run(self):
        await self.update()

    async def update(self):
        response = await self.parent.send_raw("whoami")

        self.clid = response.first["client_id"]
        self.nickname = response.first["client_nickname"]
        self.database_id = response.first["client_database_id"]
        self.unique_identifier = response.first["client_unique_identifier"]