from collections.abc import Mapping
from typing import NewType


TSCtx = NewType("TSCtx", Mapping[str, str])
