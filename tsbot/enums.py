from __future__ import annotations

from enum import Enum


class TextMessageTargetMode(Enum):
    CLIENT = "1"
    CHANNEL = "2"
    SERVER = "3"
