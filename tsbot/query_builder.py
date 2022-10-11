from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from tsbot import utils

if TYPE_CHECKING:
    T = TypeVar("T", bound="TSQuery")

    ParameterTypes = str | int | bytes | float


def query(command: str) -> TSQuery:
    """Function to create :class:`TSQuery<tsbot.query_builder.TSQuery>` instances"""
    return TSQuery(command)


class TSQuery:
    __slots__ = (
        "command",
        "_cached_command",
        "_dirty",
        "_options",
        "_parameters",
        "_parameter_blocks",
    )

    def __init__(self, command: str) -> None:
        if not command:
            raise ValueError("Command cannot be empty")

        self.command = command

        self._cached_command: str = ""
        self._dirty = True

        self._options: list[str] = []
        self._parameters: dict[str, str] = {}
        self._parameter_blocks: list[dict[str, str]] = []

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.command!r})"

    def option(self: T, *args: ParameterTypes) -> T:
        """Add options to the command eg. ``-groups``"""
        self._dirty = True

        self._options.extend(map(str, args))
        return self

    def params(self: T, **kwargs: ParameterTypes) -> T:
        """Add parameters to the command eg. ``cldbid=12``"""
        self._dirty = True

        self._parameters.update({k: str(v) for k, v in kwargs.items()})
        return self

    def param_block(self: T, **kwargs: ParameterTypes) -> T:
        """Add parameter blocks eg. ``clid=1 | clid=2 | clid=3`` to the command"""
        self._dirty = True

        self._parameter_blocks.append({k: str(v) for k, v in kwargs.items()})
        return self

    def compile(self) -> str:
        """Compiles the query into a raw command"""

        if not self._dirty:
            return self._cached_command

        compiled = self.command

        if self._parameters:
            compiled += f" {' '.join(f'{k}={utils.escape(v)}' for k, v in self._parameters.items())}"

        if self._parameter_blocks:
            compiled_blocks: list[str] = []

            for parameters in self._parameter_blocks:
                compiled_blocks.append(" ".join(f"{k}={utils.escape(v)}" for k, v in parameters.items()))

            compiled += f" {'|'.join(compiled_blocks)}"

        if self._options:
            compiled += f" {' '.join(f'-{option}' for option in self._options)}"

        self._cached_command, self._dirty = compiled, False
        return compiled
