from __future__ import annotations

from typing import Iterable, Mapping, TypeVar

from tsbot import utils

_T = TypeVar("_T", bound="TSQuery")
ParameterTypes = str | int | bytes | float


def query(command: str) -> TSQuery:
    """Function to create :class:`TSQuery<tsbot.query_builder.TSQuery>` instances"""
    return TSQuery(command)


class TSQuery:
    __slots__ = (
        "command",
        "_cached_command",
        "_options",
        "_parameters",
        "_parameter_blocks",
    )

    def __init__(
        self,
        command: str,
        options: tuple[str, ...] | None = None,
        parameters: Mapping[str, str] | None = None,
        parameter_blocks: tuple[dict[str, str], ...] | None = None,
    ) -> None:
        if not command:
            raise ValueError("Command cannot be empty")

        self.command = command

        self._cached_command: str = ""

        self._options = options or tuple()
        self._parameters = parameters or {}
        self._parameter_blocks = parameter_blocks or tuple()

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.command!r})"

    def option(self: _T, *args: ParameterTypes) -> _T:
        """Add options to the command eg. ``-groups``"""

        return type(self)(
            self.command,
            (
                *self._options,
                *map(str, args),
            ),
            self._parameters,
            self._parameter_blocks,
        )

    def params(self: _T, **kwargs: ParameterTypes) -> _T:
        """Add parameters to the command eg. ``cldbid=12``"""

        return type(self)(
            self.command,
            self._options,
            {**self._parameters, **{k: str(v) for k, v in kwargs.items()}},
            self._parameter_blocks,
        )

    def param_block(
        self: _T,
        block: Iterable[dict[str, ParameterTypes]] | None = None,
        /,
        **kwargs: ParameterTypes,
    ) -> _T:
        """Add parameter blocks eg. ``clid=1 | clid=2 | clid=3`` to the command"""

        param_blocks = tuple(block) if block else (kwargs,)

        return type(self)(
            self.command,
            self._options,
            self._parameters,
            (
                *self._parameter_blocks,
                *({k: str(v) for k, v in block.items()} for block in param_blocks),
            ),
        )

    def compile(self) -> str:
        """Compiles the query into a raw command"""

        if self._cached_command:
            return self._cached_command

        compiled = self.command

        if self._parameters:
            compiled += (
                f" {' '.join(f'{k}={utils.escape(v)}' for k, v in self._parameters.items())}"
            )

        if self._parameter_blocks:
            compiled_blocks: list[str] = []

            for parameters in self._parameter_blocks:
                compiled_blocks.append(
                    " ".join(f"{k}={utils.escape(v)}" for k, v in parameters.items())
                )

            compiled += f" {'|'.join(compiled_blocks)}"

        if self._options:
            compiled += f" {' '.join(f'-{option}' for option in self._options)}"

        self._cached_command = compiled
        return compiled
