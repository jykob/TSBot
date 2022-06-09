import asyncio

import pytest

from tsbot import bot, response

whoami_data = {
    "virtualserver_status": "online",
    "virtualserver_id": "1",
    "virtualserver_unique_identifier": "aQmTwGbjuNsfxVsemkmPDmt7KHE=",
    "virtualserver_port": "9987",
    "client_id": "4",
    "client_channel_id": "10",
    "client_nickname": "TestUser",
    "client_database_id": "4",
    "client_login_name": "TestUser",
    "client_unique_identifier": "249keib7GhnT2UtpZ511fyKRzas=",
    "client_origin_server_id": "1",
}


@pytest.mark.usefixtures("whoami_data")
class MockBot(bot.TSBot):
    async def send_raw(self, command: str, *, max_cache_age: int | float = 0):
        if command == "whoami":
            return response.TSResponse([whoami_data], error_id=0, msg="ok")

        raise NotImplementedError


def test_ts_bot_info_creation():
    ts_info = bot.TSBotInfo()

    assert not hasattr(ts_info, "clid")
    assert not hasattr(ts_info, "database_id")
    assert not hasattr(ts_info, "login_name")
    assert not hasattr(ts_info, "nickname")
    assert not hasattr(ts_info, "unique_identifier")


def test_ts_bot_info_update():
    ts_info = bot.TSBotInfo()

    asyncio.run(ts_info.update(MockBot("", "", "")))

    assert whoami_data["client_id"] == ts_info.client_id
    assert whoami_data["client_database_id"] == ts_info.database_id
    assert whoami_data["client_login_name"] == ts_info.login_name
    assert whoami_data["client_nickname"] == ts_info.nickname
    assert whoami_data["client_unique_identifier"] == ts_info.unique_identifier
