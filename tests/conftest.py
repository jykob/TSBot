from __future__ import annotations

from unittest import mock

import pytest


class MockBot(mock.Mock):
    uid: str = "1"
    clid: str = "1"
    cldbid: str = "1"


@pytest.fixture
def mock_bot():
    return MockBot()
