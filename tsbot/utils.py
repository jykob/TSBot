from __future__ import annotations


def remove_prefix(prefix: str, target: str) -> str:
    if target.startswith(prefix):
        return target[len(prefix) :]

    return target


def parse_data(input_str: str) -> list[dict[str, str]]:
    if not input_str:
        return []

    return [parse_line(item) for item in input_str.split("|")]


def parse_line(input_str: str) -> dict[str, str]:
    if not input_str:
        return {}

    return {k: v for k, v in (parse_value(item) for item in input_str.split(" "))}


def parse_value(input_str: str) -> tuple[str, str]:
    key_value = input_str.split("=", maxsplit=1)

    if len(key_value) == 1:
        # Key doesn't have value associated with it. Making value empty str
        return key_value[0], ""

    key, value = key_value

    if "|" in value:
        # Multiple values associated with the key. Making values comma separated
        return key, ",".join(v for v in value.split(f"|{key}="))

    return key, unescape(value)


def parse_args_kwargs(msg: str) -> tuple[tuple[str, ...], dict[str, str]]:
    """Parses message in to given command, its arguments and keyword arguments"""
    msg_list = msg.split()

    args: list[str] = []
    kwargs: dict[str, str] = {}

    while msg_list:
        item = msg_list.pop(0)

        if item.startswith("-"):
            key = remove_prefix("-", item)
            value = ""
            if len(msg_list) and not msg_list[0].startswith("-"):
                value = msg_list.pop(0)

            kwargs[key] = value
        else:
            args.append(item)

    return tuple(args), kwargs


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
