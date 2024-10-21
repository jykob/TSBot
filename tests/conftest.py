from __future__ import annotations

from unittest import mock

import pytest

from tsbot import bot


class MockBot(mock.Mock, bot.TSBot): ...


@pytest.fixture
def mock_bot():
    return MockBot()
