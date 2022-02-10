from __future__ import annotations

from typing import TypeVar, Union

from tsbot.utils import escape


T_TSQuery = TypeVar("T_TSQuery", bound="TSQuery")
T_Stringable = Union[str, int, float, bytes]


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

        if self._parameter_blocks:  # TODO: REFACTOR
            to_add: list[str] = []

            for parameters in self._parameter_blocks:
                to_add.append(" ".join(f"{k}={escape(v)}" for k, v in parameters.items()))

            compiled += f" {'|'.join(to_add)}"

        if self._options:
            compiled += f" {' '.join(f'-{option}' for option in self._options)}"

        return compiled


if __name__ == "__main__":

    # TODO: Move to tests/

    # EXCEPT: permget permid=21174
    query = TSQuery("permget").params(permid=21174).option("ignoreerrors")
    print(f"{query.compile()!r}")

    # EXCEPT: clientkick reasonmsg=ASDFTE reasonid=4 clid=5|clid=6|clid=7 -ignoreerrors
    query = (
        TSQuery("clientkick")
        .params(reasonmsg="ASDFTE", reasonid="4")
        .param_block(clid=5)
        .param_block(clid=6)
        .param_block(clid=7)
        .option("ignoreerrors")
    )

    print(f"{query.compile()!r}")

    # EXCEPT: clientaddperm cldbid=16 permid=17276 permvalue=50 permskip=1|permid=21415 permvalue=20 permskip=0 -ignoreerrors
    query = (
        TSQuery("clientaddperm")
        .params(cldbid="16")
        .param_block(permid=17276, permvalue="50", permskip=True)
        .param_block(permid="21415", permvalue="20", permskip=1)
        .option("ignoreerrors")
    )

    print(f"{query.compile()!r}")
