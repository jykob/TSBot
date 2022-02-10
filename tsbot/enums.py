from enum import IntEnum


class TextMessageTargetMode(IntEnum):
    CLIENT = 1
    CHANNEL = 2
    SERVER = 3


class ReasonIdentifier(IntEnum):
    REASON_KICK_CHANNEL = (4,)
    REASON_KICK_SERVER = 5
