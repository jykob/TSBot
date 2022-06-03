# pyright: reportUnknownArgumentType=false
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


def test_cache_add_record(resp: response.TSResponse):
    c = cache.Cache()

    query_hash = hash("clientlist")

    c.add_cache(query_hash, resp)

    assert c.cache[query_hash].record == resp


def test_cache_get_record(monkeypatch: pytest.MonkeyPatch, resp: response.TSResponse):
    c = cache.Cache()

    timestamp = 1000.0
    resp_hash = 1234567890
    c.cache = {resp_hash: cache.CacheRecord(timestamp, resp)}

    monkeypatch.setattr(time, "monotonic", lambda: timestamp)

    cached_resp = c.get_cache(resp_hash, max_age=1)

    assert cached_resp == resp


def test_cache_get_expired_record(monkeypatch: pytest.MonkeyPatch, resp: response.TSResponse):
    c = cache.Cache()

    timestamp = 1000.0
    resp_hash = 1234567890
    c.cache = {resp_hash: cache.CacheRecord(timestamp, resp)}

    monkeypatch.setattr(time, "monotonic", lambda: timestamp + 5)

    cached_resp = c.get_cache(resp_hash, max_age=1)

    assert cached_resp == None


def test_cache_get_no_response(resp: response.TSResponse):
    c = cache.Cache()

    timestamp = 1000.0
    resp_hash = 1234567890
    c.cache = {resp_hash: cache.CacheRecord(timestamp, resp)}

    cached_resp = c.get_cache(9876543210, max_age=1)

    assert cached_resp == None


def test_cleanup_task(resp: response.TSResponse):
    c = cache.Cache(max_lifetime=2, cleanup_interval=0)

    resp_hash = 1234567890
    c.add_cache(resp_hash, resp)

    def assert_has_records():
        assert len(c.cache) > 0

    def assert_has_no_records():
        assert len(c.cache) == 0

    async def run_task(c: cache.Cache):
        task = asyncio.create_task(c.cache_cleanup_task(MockBot()))  # type:ignore
        task.get_loop().call_later(1, assert_has_records)  # test that there are still records in cache after 1 sec
        task.get_loop().call_later(3, task.cancel)  # cancel the task after 3 seconds
        await task

    asyncio.run(run_task(c))
    assert_has_no_records()
