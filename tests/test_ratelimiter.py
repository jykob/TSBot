# pyright: reportPrivateUsage=false

import asyncio
import time

import pytest

from tsbot import ratelimiter


def test_ratelimiter_call():
    rl = ratelimiter.RateLimiter(max_calls=10, period=3)

    asyncio.run(rl.wait())

    assert rl._calls == 1


@pytest.mark.parametrize(
    ("rl", "number_of_calls"),
    (
        pytest.param(ratelimiter.RateLimiter(max_calls=10, period=3), 3, id="test_n_of_calls_3"),
        pytest.param(ratelimiter.RateLimiter(max_calls=10, period=3), 8, id="test_n_of_calls_8"),
    ),
)
def test_ratelimiter_multiple_calls(rl: ratelimiter.RateLimiter, number_of_calls: int):
    async def run_wrapper():
        for _ in range(number_of_calls):
            await rl.wait()

    asyncio.run(run_wrapper())

    assert rl._calls == number_of_calls


@pytest.mark.parametrize(
    ("rl", "number_of_calls"),
    (
        pytest.param(ratelimiter.RateLimiter(max_calls=4, period=2), 8, id="test_throttle"),
        pytest.param(ratelimiter.RateLimiter(max_calls=5, period=2), 10, id="test_throttle_2"),
    ),
)
def test_ratelimiter_throttle(rl: ratelimiter.RateLimiter, number_of_calls: int):
    async def run_wrapper():
        for _ in range(number_of_calls):
            await rl.wait()

    now = time.monotonic()
    asyncio.run(run_wrapper())
    elapsed = time.monotonic() - now

    time_should_have_elapsed = rl._period

    assert elapsed > time_should_have_elapsed
