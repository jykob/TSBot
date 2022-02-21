from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tsbot.bot import TSBot
    from tsbot.extensions import extension

logger = logging.getLogger(__name__)


class BotInfo(extension.Extension):
    def __init__(self, parent: TSBot) -> None:
        super().__init__(parent)

        self.clid: str
        self.database_id: str
        self.login_name: str
        self.nickname: str
        self.unique_identifier: str

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(clid={self.clid}, nickname={self.nickname}, database_id={self.database_id}, unique_identifier={self.unique_identifier})"

    async def run(self):
        await self.update()

    async def update(self):
        response = await self.parent.send_raw("whoami")

        self.clid = response.first["client_id"]
        self.database_id = response.first["client_database_id"]
        self.login_name = response.first["client_login_name"]
        self.nickname = response.first["client_nickname"]
        self.unique_identifier = response.first["client_unique_identifier"]
