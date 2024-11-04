from __future__ import annotations

import asyncio
from unittest import mock

import pytest

from tsbot import ratelimiter

# pyright: reportPrivateUsage=false


@pytest.fixture
def default_rl():
    return ratelimiter.RateLimiter(max_calls=10, period=3)


@pytest.mark.asyncio
async def test_ratelimiter_call(default_rl: ratelimiter.RateLimiter):
    await default_rl.wait()
    assert default_rl._calls == 1


@pytest.mark.parametrize(
    ("number_of_calls"),
    (
        pytest.param(3, id="test_n_of_calls_3"),
        pytest.param(8, id="test_n_of_calls_8"),
    ),
)
@pytest.mark.asyncio
async def test_ratelimiter_multiple_calls(
    default_rl: ratelimiter.RateLimiter, number_of_calls: int
):
    for _ in range(number_of_calls):
        await default_rl.wait()

    assert default_rl._calls == number_of_calls


@pytest.mark.parametrize(
    ("rl", "number_of_calls"),
    (
        pytest.param(ratelimiter.RateLimiter(max_calls=5, period=1), 8, id="test_throttle"),
        pytest.param(ratelimiter.RateLimiter(max_calls=10, period=1), 10, id="test_throttle_2"),
    ),
)
@pytest.mark.asyncio
async def test_ratelimiter_throttle(
    monkeypatch: pytest.MonkeyPatch, rl: ratelimiter.RateLimiter, number_of_calls: int
):
    mock_sleep = mock.AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    for _ in range(number_of_calls):
        await rl.wait()

    mock_sleep.assert_awaited()
