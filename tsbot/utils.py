from __future__ import annotations

import itertools
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


def pop_traceback(exception: Exception, amount: int = 1) -> Exception:
    tb, count = exception.__traceback__, itertools.count()

    while tb and next(count) < amount:
        tb = tb.tb_next

    return exception.with_traceback(tb)
