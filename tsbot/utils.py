from __future__ import annotations

import warnings


def check_for_deprecated_event(event_type: str) -> None:
    if event_type == "ready":
        warnings.warn(
            "'ready' event is deprecated. Use 'connect' instead",
            DeprecationWarning,
            stacklevel=3,
        )
