from __future__ import annotations

import asyncio
import time

import pytest

from tsbot import ratelimiter

# pyright: reportPrivateUsage=false, reportUnknownMemberType=false


@pytest.fixture
def default_rl():
    return ratelimiter.RateLimiter(max_calls=10, period=3)


def test_ratelimiter_call(default_rl: ratelimiter.RateLimiter):
    asyncio.run(default_rl.wait())

    assert default_rl._calls == 1


@pytest.mark.parametrize(
    ("number_of_calls"),
    (
        pytest.param(3, id="test_n_of_calls_3"),
        pytest.param(8, id="test_n_of_calls_8"),
    ),
)
def test_ratelimiter_multiple_calls(default_rl: ratelimiter.RateLimiter, number_of_calls: int):
    async def run_wrapper():
        for _ in range(number_of_calls):
            await default_rl.wait()

    asyncio.run(run_wrapper())

    assert default_rl._calls == number_of_calls


@pytest.mark.parametrize(
    ("rl", "number_of_calls"),
    (
        pytest.param(ratelimiter.RateLimiter(max_calls=5, period=1), 8, id="test_throttle"),
        pytest.param(ratelimiter.RateLimiter(max_calls=10, period=1), 10, id="test_throttle_2"),
    ),
)
def test_ratelimiter_throttle(rl: ratelimiter.RateLimiter, number_of_calls: int):
    async def run_wrapper():
        for _ in range(number_of_calls):
            await rl.wait()

    now = time.monotonic()
    asyncio.run(run_wrapper())
    elapsed = time.monotonic() - now

    assert pytest.approx(elapsed, abs=0.2) != 0
