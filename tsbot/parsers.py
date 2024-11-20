from __future__ import annotations

import itertools
from typing import Literal, overload

from tsbot import encoders

KWARG_INDICATOR = "-"
QUOTES = ('"', "'")


def parse_data(input_str: str) -> tuple[dict[str, str], ...]:
    if not input_str:
        return tuple()

    return tuple(map(parse_line, input_str.split("|")))


def parse_line(input_str: str) -> dict[str, str]:
    if not input_str:
        return {}

    return dict(map(parse_value, input_str.split(" ")))


def parse_value(input_str: str) -> tuple[str, str]:
    key, _, value = input_str.partition("=")

    if not value:
        return key, ""

    if "|" in value:
        # Multiple values associated with the key. Making values comma separated
        return key, ",".join(map(encoders.unescape, value.split(f"|{key}=")))

    return key, encoders.unescape(value)


def _parse_quoted_arg(unparsed: str) -> tuple[str, str]:
    """
    Parses a quoted argument, returns it and unparsed part.

    If a quote doesn't have a whitespace behind it, that part is not considered a quote end.
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
    arg, unparsed = split_ensure_splits(unparsed, maxsplit=1)

    return arg, unparsed


def _parse_kwarg(unparsed: str) -> tuple[str, str, str]:
    """Parse an key-value argument"""
    key, unparsed = _parse_arg(unparsed[len(KWARG_INDICATOR) :])

    if unparsed.startswith(KWARG_INDICATOR):
        return key, "", unparsed

    if unparsed.startswith(QUOTES):
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

        elif unparsed.startswith(QUOTES):
            value, unparsed = _parse_quoted_arg(unparsed)
            args.append(value)

        else:
            value, unparsed = _parse_arg(unparsed)
            args.append(value)

    return tuple(args), kwargs


@overload
def split_ensure_splits(  # type: ignore[pyright incompatible overload return type]
    string: str, sep: str | None = None, maxsplit: Literal[1] = 1, fill: str = ""
) -> tuple[str, str]: ...


@overload
def split_ensure_splits(
    string: str, sep: str | None = None, maxsplit: int = -1, fill: str = ""
) -> tuple[str, ...]: ...


def split_ensure_splits(
    string: str,
    sep: str | None = None,
    maxsplit: int = -1,
    fill: str = "",
) -> tuple[str, ...]:
    """Splits a string at least maxsplit times, filling the rest with fill value"""

    return (
        *(result := string.split(sep, maxsplit)),
        *itertools.repeat(fill, maxsplit - len(result) + 1),
    )
