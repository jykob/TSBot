from __future__ import annotations


def parse_data(input_str: str) -> list[dict[str, str]]:
    if not input_str:
        return []

    return [parse_line(item) for item in input_str.split("|")]


def parse_line(input_str: str) -> dict[str, str]:
    if not input_str:
        return {}

    return {k: v for k, v in (parse_value(item) for item in input_str.split(" "))}


def parse_value(input_str: str) -> tuple[str, str]:
    key, value = input_str.split("=", maxsplit=1)
    return key, unescape(value)


# https://github.com/benediktschmitt/py-ts3/blob/v2/ts3/escape.py

ESCAPE_MAP = [
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
]


def escape(input_str: str) -> str:
    """
    Escapes characters that need escaping according to ESCAPE_MAP
    """
    for char, replacement in ESCAPE_MAP:
        input_str = input_str.replace(char, replacement)
    return input_str


def unescape(input_str: str) -> str:
    """
    Undo escaping of characters according to ESCAPE_MAP
    """
    for replacement, char in reversed(ESCAPE_MAP):
        input_str = input_str.replace(char, replacement)
    return input_str
