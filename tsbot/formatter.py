from __future__ import annotations

from typing import Sequence

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from tsbot import typealiases


def url(url_link: str, url_text: typealiases.Stringable | None = None) -> str:
    return f"[URL={url_link}]{url_text}[/URL]" if url_text else f"[URL]{url_link}[/URL]"


def img(image_url: str) -> str:
    return f"[IMG]{image_url}[/IMG]"


def size(font_size: int, string: typealiases.Stringable) -> str:
    return f"[SIZE={font_size}]{string}[/SIZE]"


def bold(string: typealiases.Stringable) -> str:
    return f"[B]{string}[/B]"


def color(color_code: str, string: typealiases.Stringable) -> str:
    return f"[COLOR={color_code}]{string}[/COLOR]"


def italic(string: typealiases.Stringable) -> str:
    return f"[I]{string}[/I]"


def underline(string: typealiases.Stringable) -> str:
    return f"[U]{string}[/U]"


def center(string: typealiases.Stringable) -> str:
    return f"[CENTER]{string}[/CENTER]"


def numeric_list(*list_members: tuple[typealiases.Stringable]) -> str:
    items = "\n".join(f"[*]{item}" for item in list_members)
    return f"""[LIST=1]\n{items}\n[/LIST]"""


def upper_list(*list_members: tuple[typealiases.Stringable]) -> str:
    items = "\n".join(f"[*]{item}" for item in list_members)
    return f"""[LIST=A]\n{items}\n[/LIST]"""


def lower_list(*list_members: tuple[typealiases.Stringable]) -> str:
    items = "\n".join(f"[*]{item}" for item in list_members)
    return f"""[LIST=a]\n{items}\n[/LIST]"""
