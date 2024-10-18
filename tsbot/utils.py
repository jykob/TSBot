from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def toggle(obj: object, attr: str, enter: Any, exit: Any) -> Generator[None, None, None]:
    setattr(obj, attr, enter)
    try:
        yield
    finally:
        setattr(obj, attr, exit)
