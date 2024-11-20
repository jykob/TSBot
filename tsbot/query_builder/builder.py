from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Final, Protocol

from typing_extensions import Self

from tsbot import encoders

if TYPE_CHECKING:
    from tsbot.query_builder import commands


class Stringable(Protocol):
    def __str__(self) -> str: ...


def _format_value(key: str, value: Stringable) -> str:
    return f"{key}={int(value) if isinstance(value, bool) else encoders.escape(str(value))}"


def _format_parameters(params: Mapping[str, Stringable]) -> str:
    return " ".join(itertools.starmap(_format_value, params.items()))


class TSQuery:
    """
    Class to represent query commands to the TeamSpeak server.
    """

    __slots__ = (
        "_command",
        "_cached_query",
        "_options",
        "_parameters",
        "_parameter_blocks",
    )

    def __init__(
        self,
        command: commands.Commands,
        options: tuple[Stringable, ...] | None = None,
        parameters: dict[str, Stringable] | None = None,
        parameter_blocks: tuple[dict[str, Stringable], ...] | None = None,
    ) -> None:
        """
        :param command: Base query command.
        :param options: Options attached to the query.
        :param parameters: Parameters attached to the query.
        :param parameter_blocks: Parameter blocks attached to the query.
        """
        self._command: Final = command
        self._cached_query: str | None = None

        self._options: Final = options or ()
        self._parameters: Final = parameters or {}
        self._parameter_blocks: Final = parameter_blocks or ()

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self._command!r})"

    def option(self, *args: Stringable) -> Self:
        """
        Add options to the command eg. ``-groups``.

        :param args: Tuple of options to be attached.
        :return: New :class:`TSQuery<tsbot.query_builder.TSQuery>` instance with added params
        """

        return type(self)(
            self._command,
            self._options + args,
            self._parameters,
            self._parameter_blocks,
        )

    def params(self, **kwargs: Stringable) -> Self:
        """
        Add parameters to the command eg. ``cldbid=12``.

        :param kwargs: Keyword to be attached.
        :return: New :class:`TSQuery<tsbot.query_builder.TSQuery>` instance with added parameters
        """

        return type(self)(
            self._command,
            self._options,
            self._parameters | kwargs,
            self._parameter_blocks,
        )

    def param_block(
        self, blocks: Iterable[Mapping[str, Stringable]] | None = None, /, **kwargs: Stringable
    ) -> Self:
        """
        Add parameter blocks eg. ``clid=1 | clid=2 | clid=3`` to the command.
        Takes in either an iterable of parameters in form of dict[str, Stringable]
        or **one** block at a time.

        :param blocks: Iterable of parameter blocks to be attached.
        :param kwargs: Parameters to be attached to single block.
        :return: New :class:`TSQuery<tsbot.query_builder.TSQuery>` instance with added parameter blocks
        """

        param_blocks: tuple[dict[str, Stringable], ...] = (
            tuple(map(dict, blocks)) if blocks else (kwargs,)
        )

        return type(self)(
            self._command,
            self._options,
            self._parameters,
            self._parameter_blocks + param_blocks,
        )

    def compile(self) -> str:
        """
        Compiles the query into a raw command.

        :return: The compiled query command.
        """

        if self._cached_query:
            return self._cached_query

        compiled: str = self._command

        if self._parameters:
            compiled += f" {_format_parameters(self._parameters)}"

        if self._parameter_blocks:
            compiled += f" {'|'.join(map(_format_parameters, self._parameter_blocks))}"

        if self._options:
            compiled += f" {' '.join(f'-{option}' for option in self._options)}"

        self._cached_query = compiled
        return compiled


query = TSQuery
