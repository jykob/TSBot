from __future__ import annotations

import warnings
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


def check_for_deprecated_event(event_type: str) -> None:
    if event_type == "ready":
        warnings.warn(
            "'ready' event is deprecated. Use 'connect' instead",
            DeprecationWarning,
            stacklevel=3,
        )
