from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from tsbot import response

    T = TypeVar("T", bound="TSClientInfo")


@dataclass(slots=True)
class TSClientInfo:
    client_id: str = field(compare=False)
    database_id: str = field(compare=False)
    login_name: str = field(compare=False)
    nickname: str = field(compare=False)
    unique_identifier: str = field(compare=True)

    @classmethod
    def from_whoami(cls: type[T], resp: response.TSResponse) -> T:
        return cls(
            client_id=resp.first["client_id"],
            database_id=resp.first["client_database_id"],
            login_name=resp.first["client_login_name"],
            nickname=resp.first["client_nickname"],
            unique_identifier=resp.first["client_unique_identifier"],
        )
