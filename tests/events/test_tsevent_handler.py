from tsbot import plugin
from tsbot.bot import TSBot
from tsbot.events import tsevent_handler


def handler(bot: TSBot, ctx: dict[str, str]):
    pass


class Plugin(plugin.TSPlugin):
    def handler(self, bot: TSBot, ctx: dict[str, str]):
        pass


def test_tsevent_handler_creation():
    event_handler = tsevent_handler.TSEventHandler("clientmove", handler)

    assert event_handler.event == "clientmove"
    assert event_handler.handler == handler


def test_tsevent_plugin_handler_creation():

    event_handler = tsevent_handler.TSEventHandler("clientmove", Plugin.handler)

    assert event_handler.event == "clientmove"
    assert event_handler.handler == Plugin.handler
