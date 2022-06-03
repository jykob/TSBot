from __future__ import annotations

import asyncio
import time

import pytest

from tsbot import cache
from tsbot import response


class MockBot:
    pass


@pytest.fixture
def resp():
    return response.TSResponse(
        data=[
            {"clid": "378", "cid": "23", "client_database_id": "21", "client_type": "0"},
            {"clid": "377", "cid": "31", "client_database_id": "549", "client_type": "0"},
            {"clid": "375", "cid": "31", "client_database_id": "46", "client_type": "0"},
            {"clid": "371", "cid": "31", "client_database_id": "385", "client_type": "0"},
            {"clid": "333", "cid": "45", "client_database_id": "27", "client_type": "0"},
            {"clid": "3", "cid": "31", "client_database_id": "160", "client_type": "0"},
        ],
        error_id=0,
        msg="ok",
    )


@pytest.fixture
def timestamp():
    return 1000.0


@pytest.fixture
def resp_hash():
    return 1234567890


@pytest.fixture
def test_cache(timestamp: float, resp_hash: int, resp: response.TSResponse):
    test_cache = cache.Cache()
    test_cache.cache = {resp_hash: cache.CacheRecord(timestamp, resp)}

    return test_cache


def test_cache_add_record(resp: response.TSResponse):
    test_cache = cache.Cache()

    query_hash = hash("clientlist")
    test_cache.add_cache(query_hash, resp)

    assert test_cache.cache[query_hash].record == resp


def test_cache_get_record(
    monkeypatch: pytest.MonkeyPatch,
    test_cache: cache.Cache,
    timestamp: float,
    resp_hash: int,
    resp: response.TSResponse,
):
    monkeypatch.setattr(time, "monotonic", lambda: timestamp)

    cached_resp = test_cache.get_cache(resp_hash, max_age=1)

    assert cached_resp == resp


def test_cache_get_expired_record(
    monkeypatch: pytest.MonkeyPatch,
    test_cache: cache.Cache,
    timestamp: float,
    resp_hash: int,
):
    monkeypatch.setattr(time, "monotonic", lambda: timestamp + 5)

    cached_resp = test_cache.get_cache(resp_hash, max_age=1)

    assert cached_resp == None


def test_cache_get_no_response(resp: response.TSResponse, test_cache: cache.Cache):
    cached_resp = test_cache.get_cache(9876543210, max_age=1)

    assert cached_resp == None


def test_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    test_cache: cache.Cache,
    timestamp: float,
):
    times = [timestamp - 1000, timestamp + 1000]
    monkeypatch.setattr(time, "monotonic", lambda: times.pop(0))

    def assert_has_records():
        assert len(test_cache.cache) > 0

    def assert_has_no_records():
        assert len(test_cache.cache) == 0

    assert_has_records()

    test_cache.cleanup()
    assert_has_records()

    test_cache.cleanup()
    assert_has_no_records()


def test_cleanup_task(monkeypatch: pytest.MonkeyPatch):
    test_cache = cache.Cache(max_lifetime=0, cleanup_interval=0)

    has_called_cleanup: bool = False

    def set_has_called_cleanup():
        nonlocal has_called_cleanup
        has_called_cleanup = True

    monkeypatch.setattr(test_cache, "cleanup", set_has_called_cleanup)

    async def runner():
        task = asyncio.create_task(test_cache.cache_cleanup_task(MockBot()))  # type: ignore
        task.get_loop().call_later(0.1, task.cancel)
        await task

    asyncio.run(runner())

    assert has_called_cleanup
