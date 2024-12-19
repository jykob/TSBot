from __future__ import annotations

from typing import Any

import pytest

from tsbot import response


@pytest.mark.parametrize(
    ("input_list", "expected_values"),
    (
        pytest.param(
            ["error id=0 msg=ok"],
            {"data": (), "error_id": 0, "msg": "ok"},
            id="test_acknowledgement",
        ),
        pytest.param(
            ["version=3.13.3 build=1608128225 platform=Windows", "error id=0 msg=ok"],
            {
                "data": ({"version": "3.13.3", "build": "1608128225", "platform": "Windows"},),
                "error_id": 0,
                "msg": "ok",
            },
            id="test_simple",
        ),
        pytest.param(
            ["error id=256 msg=command\\snot\\sfound"],
            {"data": (), "error_id": 256, "msg": "command not found"},
            id="test_error",
        ),
        pytest.param(
            ["ip=0.0.0.0|ip=::", "error id=0 msg=ok"],
            {"data": ({"ip": "0.0.0.0"}, {"ip": "::"}), "error_id": 0, "msg": "ok"},
            id="test_multiple_results",
        ),
    ),
)
def test_from_server_response(input_list: list[str], expected_values: dict[str, Any]):
    resp = response.TSResponse.from_server_response(input_list)

    assert resp.data == expected_values["data"]
    assert resp.error_id == expected_values["error_id"]


@pytest.mark.parametrize(
    ("resp",),
    (
        pytest.param(
            response.TSResponse(
                ({"version": "3.13.3", "build": "1608128225", "platform": "Windows"},), 0, "ok"
            ),
            id="test_one_datapoint",
        ),
        pytest.param(
            response.TSResponse(({"ip": "0.0.0.0"}, {"ip": "::"}), 0, "ok"),
            id="test_two_datapoint",
        ),
    ),
)
def test_first_property(resp: response.TSResponse):
    assert resp.first == resp.data[0]


def test_first_property_empty_raises():
    resp = response.TSResponse(tuple(), 0, "ok")

    with pytest.raises(IndexError):
        resp.first


def test_response_iter():
    resp = response.TSResponse(
        data=(
            {"clid": "378", "cid": "23", "client_database_id": "21", "client_type": "0"},
            {"clid": "377", "cid": "31", "client_database_id": "549", "client_type": "0"},
            {"clid": "375", "cid": "31", "client_database_id": "46", "client_type": "0"},
            {"clid": "371", "cid": "31", "client_database_id": "385", "client_type": "0"},
            {"clid": "333", "cid": "45", "client_database_id": "27", "client_type": "0"},
            {"clid": "3", "cid": "31", "client_database_id": "160", "client_type": "0"},
        ),
        error_id=0,
        msg="ok",
    )

    for index, client in enumerate(resp):
        assert client is resp.data[index]


def test_response_getitem():
    resp = response.TSResponse(
        data=(
            {"clid": "378", "cid": "23", "client_database_id": "21", "client_type": "0"},
            {"clid": "377", "cid": "31", "client_database_id": "549", "client_type": "0"},
            {"clid": "375", "cid": "31", "client_database_id": "46", "client_type": "0"},
            {"clid": "371", "cid": "31", "client_database_id": "385", "client_type": "0"},
            {"clid": "333", "cid": "45", "client_database_id": "27", "client_type": "0"},
            {"clid": "3", "cid": "31", "client_database_id": "160", "client_type": "0"},
        ),
        error_id=0,
        msg="ok",
    )

    for key in resp.data[0]:
        assert resp[key] is resp.data[0][key]
