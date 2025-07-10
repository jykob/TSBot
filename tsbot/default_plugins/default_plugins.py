from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from tsbot.default_plugins.help import Help
from tsbot.default_plugins.keepalive import KeepAlive

if TYPE_CHECKING:
    from tsbot.plugin import TSPlugin


class _DefaultPlugins(NamedTuple):
    help: Help
    keepalive: KeepAlive

    def remove(self, *plugins: TSPlugin) -> tuple[TSPlugin, ...]:
        return tuple(filter(lambda p: p not in plugins, self))


DEFAULT_PLUGINS = _DefaultPlugins(help=Help(), keepalive=KeepAlive())
