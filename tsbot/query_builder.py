from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable, Protocol, TypeVar

from tsbot import utils

_T = TypeVar("_T", bound="TSQuery")


class Stringable(Protocol):
    def __str__(self) -> str: ...


def query(command: str) -> TSQuery:
    """
    Function to create :class:`TSQuery<tsbot.query_builder.TSQuery>` instances.

    :param command: Base query command.
    :return: The created :class:`TSQuery<tsbot.query_builder.TSQuery>` instance.
    """
    return TSQuery(command)


def _to_dict_values(kv: tuple[str, Stringable]) -> tuple[str, str]:
    return kv[0], str(kv[1])


def _format_value(kv: tuple[str, str]) -> str:
    return f"{kv[0]}={utils.escape(kv[1])}"


class TSQuery:
    """
    Class to represent query commands to the TeamSpeak server.
    """

    __slots__ = (
        "_command",
        "_cached_command",
        "_options",
        "_parameters",
        "_parameter_blocks",
    )

    def __init__(
        self,
        command: str,
        options: tuple[str, ...] | None = None,
        parameters: dict[str, str] | None = None,
        parameter_blocks: tuple[dict[str, str], ...] | None = None,
    ) -> None:
        """
        :param command: Base query command.
        :param options: Options attached to the query.
        :param parameters: Parameters attached to the query.
        :param parameter_blocks: Parameter blocks attached to the query.
        """
        if not command:
            raise ValueError("Command cannot be empty")

        self._command = command

        self._cached_command: str = ""

        self._options = options or tuple()
        self._parameters = parameters or {}
        self._parameter_blocks = parameter_blocks or tuple()

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self._command!r})"

    def option(self: _T, *args: Stringable) -> _T:
        """
        Add options to the command eg. ``-groups``.

        :param args: Tuple of options to be attached.
        :return: New :class:`TSQuery<tsbot.query_builder.TSQuery>` instance with added params
        """

        return type(self)(
            self._command,
            self._options + tuple(map(str, args)),
            self._parameters,
            self._parameter_blocks,
        )

    def params(self: _T, **kwargs: Stringable) -> _T:
        """
        Add parameters to the command eg. ``cldbid=12``.

        :param kwargs: Keyword to be attached.
        :return: New :class:`TSQuery<tsbot.query_builder.TSQuery>` instance with added parameters
        """

        return type(self)(
            self._command,
            self._options,
            self._parameters | dict(map(_to_dict_values, kwargs.items())),
            self._parameter_blocks,
        )

    def param_block(
        self: _T,
        blocks: Iterable[Mapping[str, Stringable]] | None = None,
        /,
        **kwargs: Stringable,
    ) -> _T:
        """
        Add parameter blocks eg. ``clid=1 | clid=2 | clid=3`` to the command.
        Takes in either an iterable of parameters in form of dict[str, Stringable]
        or **one** block at a time.

        :param blocks: Iterable of parameter blocks to be attached.
        :param kwargs: Parameters to be attached to single block.
        :return: New :class:`TSQuery<tsbot.query_builder.TSQuery>` instance with added parameter blocks
        """

        param_blocks = tuple(blocks) if blocks else (kwargs,)

        return type(self)(
            self._command,
            self._options,
            self._parameters,
            self._parameter_blocks
            + tuple(dict(map(_to_dict_values, block.items())) for block in param_blocks),
        )

    def compile(self) -> str:
        """
        Compiles the query into a raw command.

        :return: The compiled query command.
        """

        if self._cached_command:
            return self._cached_command

        compiled = self._command

        if self._parameters:
            compiled += f" {' '.join(map(_format_value, self._parameters.items()))}"

        if self._parameter_blocks:
            compiled += f" {'|'.join(' '.join(map(_format_value, parameters.items())) for parameters in self._parameter_blocks)}"

        if self._options:
            compiled += f" {' '.join(f'-{option}' for option in self._options)}"

        self._cached_command = compiled
        return compiled
