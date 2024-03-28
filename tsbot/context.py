from __future__ import annotations

from collections.abc import Mapping
from typing import NewType

TSCtx = NewType("TSCtx", Mapping[str, str])
