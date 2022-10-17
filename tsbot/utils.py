from __future__ import annotations


KWARG_INDICATOR = "-"


def parse_data(input_str: str) -> list[dict[str, str]]:
    if not input_str:
        return []

    return [parse_line(item) for item in input_str.split("|")]


def parse_line(input_str: str) -> dict[str, str]:
    if not input_str:
        return {}

    return {k: v for k, v in (parse_value(item) for item in input_str.split(" "))}


def parse_value(input_str: str) -> tuple[str, str]:
    key, _, value = input_str.partition("=")

    if "|" in value:
        # Multiple values associated with the key. Making values comma separated
        return key, ",".join(v for v in value.split(f"|{key}="))

    return key, unescape(value) if value else value


def _parse_quoted_arg(unparsed: str) -> tuple[str, str]:
    """
    Parses a quoted argument, returns it and unparsed part.

    If a qoute doesn't have a whitespace behind it, that part is not considered a quote end.
    If a valid quote is not found, parse as normal argument.
    """
    quote, unparsed_len = unparsed[0], len(unparsed)

    if (quote_end := unparsed.find(quote, 1)) < 0:
        return _parse_arg(unparsed)

    while quote_end + 1 < unparsed_len and not unparsed[quote_end + 1].isspace():
        if (quote_end := unparsed.find(quote, quote_end + 1)) < 0:
            return _parse_arg(unparsed)

    return unparsed[1:quote_end], unparsed[quote_end + 1 :].lstrip()


def _parse_arg(unparsed: str) -> tuple[str, str]:
    """Parse an argument out of unparsed message, return it and unparsed part."""
    arg, unparsed = d if len(d := unparsed.split(maxsplit=1)) > 1 else (d[0] if d else "", "")

    return arg, unparsed


def _parse_kwarg(unparsed: str) -> tuple[str, str, str]:
    """Parse an key-value argument"""
    key, unparsed = _parse_arg(unparsed[len(KWARG_INDICATOR) :])

    if unparsed.startswith(KWARG_INDICATOR):
        return key, "", unparsed

    if unparsed.startswith(('"', "'")):
        return key, *_parse_quoted_arg(unparsed)

    return key, *_parse_arg(unparsed)


def parse_args_kwargs(msg: str) -> tuple[tuple[str, ...], dict[str, str]]:
    """Parses a message in to arguments and keyword arguments"""

    args: list[str] = []
    kwargs: dict[str, str] = {}

    unparsed = msg.strip()

    while unparsed:
        if unparsed.startswith(KWARG_INDICATOR):
            key, value, unparsed = _parse_kwarg(unparsed)
            kwargs[key] = value

        elif unparsed.startswith(('"', "'")):
            value, unparsed = _parse_quoted_arg(unparsed)
            args.append(value)

        else:
            value, unparsed = _parse_arg(unparsed)
            args.append(value)

    return tuple(args), kwargs


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
    for replacement, char in reversed(ESCAPE_MAP):
        input_str = input_str.replace(char, replacement)
    return input_str
