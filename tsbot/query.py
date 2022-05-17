from __future__ import annotations

from typing import TypeVar

from tsbot.utils import escape

TTSQuery = TypeVar("TTSQuery", bound="TSQuery")
TStringable = str | int | float | bytes


class TSQuery:
    def __init__(self, command: str) -> None:
        if not command:
            raise ValueError("command cannot be empty")

        self.command = command
        self._options: list[str] = []
        self._parameters: dict[str, str] = {}
        self._parameter_blocks: list[dict[str, str]] = []

    def option(self: TTSQuery, *args: TStringable) -> TTSQuery:
        """
        Add options to the command
        """
        self._options.extend(str(arg) for arg in args)
        return self

    def params(self: TTSQuery, **kwargs: TStringable) -> TTSQuery:
        self._parameters.update({k: str(v) for k, v in kwargs.items()})
        return self

    def param_block(self: TTSQuery, **kwargs: TStringable) -> TTSQuery:
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


def query(command: str) -> TSQuery:
    return TSQuery(command)
