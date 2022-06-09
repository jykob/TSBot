from __future__ import annotations

from tsbot import plugin
from tsbot.bot import TSBot
from tsbot.events import tsevent_handler, TSEvent


async def handler(bot: TSBot, event: TSEvent):
    pass


class Plugin(plugin.TSPlugin):
    async def handler(self, bot: TSBot, event: TSEvent):
        pass


def test_tsevent_handler_creation():
    event_handler = tsevent_handler.TSEventHandler("clientmove", handler)

    assert event_handler.event == "clientmove"
    assert event_handler.handler == handler


def test_tsevent_plugin_handler_creation():
    event_handler = tsevent_handler.TSEventHandler("clientmove", Plugin.handler)

    assert event_handler.event == "clientmove"
    assert event_handler.handler == Plugin.handler
