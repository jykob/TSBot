from __future__ import annotations

from typing import Literal

BUILTIN_NO_CTX_EVENTS = Literal[
    "run",
    "connect",
    "disconnect",
    "reconnect",
    "close",
]

BUILTIN_EVENTS = Literal[
    "send",
    "command_error",
    "permission_error",
    "parameter_error",
]

TS_EVENTS = Literal[
    "textmessage",
    "cliententerview",
    "clientleftview",
    "serveredited",
    "channeledited",
    "channeldescriptionchanged",
    "clientmoved",
    "channelcreated",
    "channeldeleted",
    "channelmoved",
    "channelpasswordchanged",
    "tokenused",
]
