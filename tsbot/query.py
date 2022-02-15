from __future__ import annotations

from typing import TypeVar

from tsbot.utils import escape

T_TSQuery = TypeVar("T_TSQuery", bound="TSQuery")
T_Stringable = str | int | float | bytes


class TSQuery:
    def __init__(self, command: str) -> None:
        if not command:
            raise ValueError("command cannot be empty")

        self.command = command
        self._options: list[str] = []
        self._parameters: dict[str, str] = {}
        self._parameter_blocks: list[dict[str, str]] = []

    def option(self: T_TSQuery, *args: T_Stringable) -> T_TSQuery:
        """
        Add options to the command
        """
        self._options.extend(str(arg) for arg in args)
        return self

    def params(self: T_TSQuery, **kwargs: T_Stringable) -> T_TSQuery:
        self._parameters.update({k: str(v) for k, v in kwargs.items()})
        return self

    def param_block(self: T_TSQuery, **kwargs: T_Stringable) -> T_TSQuery:
        self._parameter_blocks.append({k: str(v) for k, v in kwargs.items()})
        return self

    def compile(self) -> str:
        """
        Compile query into command understood by the server
        """
        compiled = self.command

        if self._parameters:
            compiled += f" {' '.join(f'{k}={escape(v)}' for k, v in self._parameters.items())}"

        if self._parameter_blocks:
            compiled_blocks: list[str] = []

            for parameters in self._parameter_blocks:
                compiled_blocks.append(" ".join(f"{k}={escape(v)}" for k, v in parameters.items()))

            compiled += f" {'|'.join(compiled_blocks)}"

        if self._options:
            compiled += f" {' '.join(f'-{option}' for option in self._options)}"

        return compiled
