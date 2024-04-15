from __future__ import annotations

# https://github.com/benediktschmitt/py-ts3/blob/v2/ts3/escape.py

ESCAPE_MAP = (
    ("\\", r"\\"),
    ("/", r"\/"),
    (" ", r"\s"),
    ("|", r"\p"),
    ("\a", r"\a"),
    ("\b", r"\b"),
    ("\f", r"\f"),
    ("\n", r"\n"),
    ("\r", r"\r"),
    ("\t", r"\t"),
    ("\v", r"\v"),
)


def escape(input_str: str) -> str:
    """Escapes characters that need escaping according to ESCAPE_MAP"""
    for char, replacement in ESCAPE_MAP:
        input_str = input_str.replace(char, replacement)
    return input_str


def unescape(input_str: str) -> str:
    """Undo escaping of characters according to ESCAPE_MAP"""
    for replacement, char in ESCAPE_MAP:
        input_str = input_str.replace(char, replacement)
    return input_str
