from __future__ import annotations

from typing import Any

import pytest

from tsbot import response


@pytest.mark.parametrize(
    ("input_list", "excepted_values"),
    (
        pytest.param(["error id=0 msg=ok"], {"data": [], "error_id": 0, "msg": "ok"}, id="test_acknowledgement"),
        pytest.param(
            ["version=3.13.3 build=1608128225 platform=Windows", "error id=0 msg=ok"],
            {"data": [{"version": "3.13.3", "build": "1608128225", "platform": "Windows"}], "error_id": 0, "msg": "ok"},
            id="test_simple",
        ),
        pytest.param(
            ["error id=2568 msg=insufficient\\sclient\\spermissions failed_permid=4"],
            {"data": [], "error_id": 2568, "msg": "insufficient client permissions"},
            id="test_error",
        ),
        pytest.param(
            ["ip=0.0.0.0|ip=::", "error id=0 msg=ok"],
            {"data": [{"ip": "0.0.0.0"}, {"ip": "::"}], "error_id": 0, "msg": "ok"},
            id="test_multiple_results",
        ),
    ),
)
def test_from_server_response(input_list: list[str], excepted_values: dict[str, Any]):
    resp = response.TSResponse.from_server_response(input_list)

    assert resp.data == excepted_values["data"]
    assert resp.error_id == excepted_values["error_id"]
    assert resp.msg == excepted_values["msg"]


def test_first_property():
    resp = response.TSResponse([{"version": "3.13.3", "build": "1608128225", "platform": "Windows"}], 0, "ok")
    assert resp.first == {"version": "3.13.3", "build": "1608128225", "platform": "Windows"}

    resp = response.TSResponse([{"ip": "0.0.0.0"}, {"ip": "::"}], 0, "ok")
    assert resp.first == {"ip": "0.0.0.0"}


def test_first_property_empty():
    resp = response.TSResponse([], 0, "ok")

    with pytest.raises(IndexError):
        resp.first


@pytest.mark.parametrize(
    ("input_str", "excepted"),
    (
        pytest.param("error id=0 msg=ok", (0, "ok"), id="test_error_line"),
        pytest.param(
            "error id=256 msg=command\\snot\\sfound",
            (256, "command not found"),
            id="test_error_line_with_error_1",
        ),
        pytest.param(
            "error id=1539 msg=parameter\\snot\\sfound",
            (1539, "parameter not found"),
            id="test_error_line_with_error_2",
        ),
        pytest.param(
            "error id=2568 msg=insufficient\\sclient\\spermissions failed_permid=4",
            (2568, "insufficient client permissions"),
            id="test_error_line_with_error_3",
        ),
    ),
)
def test_parse_error_line(input_str: str, excepted: tuple[int, str]) -> None:
    assert response.parse_error_line(input_str) == excepted


def test_iter_response():
    resp = response.TSResponse(
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

    for client in resp:
        assert isinstance(client, dict)


def test_response_repr():
    resp = response.TSResponse([{"ip": "0.0.0.0"}, {"ip": "::"}], 0, "ok")
    assert repr(resp)
