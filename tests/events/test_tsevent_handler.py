from __future__ import annotations

from tsbot import plugin, events, TSBot


async def handler(bot: TSBot, event: events.TSEvent):
    pass


class Plugin(plugin.TSPlugin):
    async def handler(self, bot: TSBot, event: events.TSEvent):
        pass


def test_tsevent_handler_creation():
    event_handler = events.TSEventHandler("clientmove", handler)

    assert event_handler.event == "clientmove"
    assert event_handler.handler == handler


def test_tsevent_plugin_handler_creation():
    event_handler = events.TSEventHandler("clientmove", Plugin.handler)

    assert event_handler.event == "clientmove"
    assert event_handler.handler == Plugin.handler
