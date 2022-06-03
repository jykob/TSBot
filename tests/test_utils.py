from __future__ import annotations

import pytest

from tsbot import utils


@pytest.mark.parametrize(
    ("prefix", "target_str", "excepted"),
    (
        pytest.param("!", "!hello user", "hello user", id="test_remove"),
        pytest.param("notify", "notifycliententerview", "cliententerview", id="test_remove_notify"),
        pytest.param("!", "hello user", "hello user", id="test_no_match"),
    ),
)
def test_remove_prefix(prefix: str, target_str: str, excepted: tuple[str, str]) -> None:
    assert utils.remove_prefix(prefix, target_str) == excepted


@pytest.mark.parametrize(
    ("input_str", "excepted"),
    (
        pytest.param("", [], id="test_empty"),
        pytest.param("ip=0.0.0.0|ip=::", [{"ip": "0.0.0.0"}, {"ip": "::"}], id="test_simple"),
        pytest.param(
            "clid=14 client_nickname=Sven|clid=17 client_nickname=SvenBot",
            [{"clid": "14", "client_nickname": "Sven"}, {"clid": "17", "client_nickname": "SvenBot"}],
            id="test_multiple_data_simple",
        ),
        pytest.param(
            "cgid=1 name=Channel\\sAdmin type=0 iconid=100 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=50 n_member_removep=50|cgid=2 name=Operator type=0 iconid=200 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=30 n_member_removep=30|cgid=3 name=Voice type=0 iconid=600 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=25 n_member_removep=25|cgid=4 name=Guest type=0 iconid=0 savedb=0 sortid=0 namemode=0 n_modifyp=75 n_member_addp=0 n_member_removep=0|cgid=5 name=Channel\\sAdmin type=1 iconid=100 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=50 n_member_removep=50|cgid=6 name=Operator type=1 iconid=200 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=30 n_member_removep=30|cgid=7 name=Voice type=1 iconid=600 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=25 n_member_removep=25|cgid=8 name=Guest type=1 iconid=0 savedb=0 sortid=0 namemode=0 n_modifyp=75 n_member_addp=0 n_member_removep=0",
            [
                {
                    "cgid": "1",
                    "name": "Channel Admin",
                    "type": "0",
                    "iconid": "100",
                    "savedb": "1",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "50",
                    "n_member_removep": "50",
                },
                {
                    "cgid": "2",
                    "name": "Operator",
                    "type": "0",
                    "iconid": "200",
                    "savedb": "1",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "30",
                    "n_member_removep": "30",
                },
                {
                    "cgid": "3",
                    "name": "Voice",
                    "type": "0",
                    "iconid": "600",
                    "savedb": "1",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "25",
                    "n_member_removep": "25",
                },
                {
                    "cgid": "4",
                    "name": "Guest",
                    "type": "0",
                    "iconid": "0",
                    "savedb": "0",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "0",
                    "n_member_removep": "0",
                },
                {
                    "cgid": "5",
                    "name": "Channel Admin",
                    "type": "1",
                    "iconid": "100",
                    "savedb": "1",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "50",
                    "n_member_removep": "50",
                },
                {
                    "cgid": "6",
                    "name": "Operator",
                    "type": "1",
                    "iconid": "200",
                    "savedb": "1",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "30",
                    "n_member_removep": "30",
                },
                {
                    "cgid": "7",
                    "name": "Voice",
                    "type": "1",
                    "iconid": "600",
                    "savedb": "1",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "25",
                    "n_member_removep": "25",
                },
                {
                    "cgid": "8",
                    "name": "Guest",
                    "type": "1",
                    "iconid": "0",
                    "savedb": "0",
                    "sortid": "0",
                    "namemode": "0",
                    "n_modifyp": "75",
                    "n_member_addp": "0",
                    "n_member_removep": "0",
                },
            ],
            id="test_multiple_data_complex",
        ),
    ),
)
def test_parse_data(input_str: str, excepted: list[dict[str, str]]) -> None:
    assert utils.parse_data(input_str) == excepted


@pytest.mark.parametrize(
    ("input_str", "excepted"),
    (
        pytest.param("", {}, id="test_empty"),
        pytest.param(
            "version=3.13.3 build=1608128225 platform=Windows",
            {"version": "3.13.3", "build": "1608128225", "platform": "Windows"},
            id="test_simple",
        ),
        pytest.param(
            "ctid=5 reasonid=1 invokerid=15 invokername=serveradmin invokeruid=serveradmin clid=13|clid=14|clid=15|clid=17",
            {
                "ctid": "5",
                "reasonid": "1",
                "invokerid": "15",
                "invokername": "serveradmin",
                "invokeruid": "serveradmin",
                "clid": "13,14,15,17",
            },
            id="test_param_block",
        ),
        pytest.param("error id=0 msg=ok", {"error": "", "id": "0", "msg": "ok"}, id="test_error_line"),
        pytest.param(
            "error id=2568 msg=insufficient\\sclient\\spermissions failed_permid=4",
            {"error": "", "id": "2568", "msg": "insufficient client permissions", "failed_permid": "4"},
            id="test_error_line_with_error",
        ),
    ),
)
def test_parse_line(input_str: str, excepted: dict[str, str]) -> None:
    assert utils.parse_line(input_str) == excepted


@pytest.mark.parametrize(
    ("input_str", "excepted"),
    (
        pytest.param("clid=12", ("clid", "12"), id="test_simple"),
        pytest.param("client_servergroups=6,16,20", ("client_servergroups", "6,16,20"), id="test_comma_sepparated"),
        pytest.param("clid=11|clid=12|clid=13", ("clid", "11,12,13"), id="test_param_block"),
        pytest.param("channel_name=Bot\\sCommands", ("channel_name", "Bot Commands"), id="test_value_unescape"),
        pytest.param("client_away_message", ("client_away_message", ""), id="test_empty_value"),
    ),
)
def test_parse_value(input_str: str, excepted: tuple[str, str]) -> None:
    assert utils.parse_value(input_str) == excepted


escape_params = (
    pytest.param("", "", id="test_empty"),
    pytest.param("TeamSpeak ]|[ Server", r"TeamSpeak\s]\p[\sServer", id="test_default_server_name"),
    pytest.param("Test token with custom set", r"Test\stoken\swith\scustom\sset", id="test_sentance"),
    pytest.param("		", r"\t\t", id="test_tabs"),
    pytest.param("| | | | | | |", r"\p\s\p\s\p\s\p\s\p\s\p\s\p", id="test_space_pipes"),
)


@pytest.mark.parametrize(("input_str", "excepted"), escape_params)
def test_escape(input_str: str, excepted: str) -> None:
    assert utils.escape(input_str) == excepted


@pytest.mark.parametrize(("excepted", "input_str"), escape_params)
def test_unescape(input_str: str, excepted: str) -> None:
    assert utils.unescape(input_str) == excepted


@pytest.mark.parametrize(
    ("input_str", "excepted_args", "excepted_kwargs"),
    (
        pytest.param("123 asd test", ("123", "asd", "test"), {}, id="test_args"),
        pytest.param("-asd test -name test_account", (), {"asd": "test", "name": "test_account"}, id="test_kwargs"),
        pytest.param("-asd -name test_account", (), {"asd": "", "name": "test_account"}, id="test_kwargs_2"),
        pytest.param("asd -name test_account 123", ("asd", "123"), {"name": "test_account"}, id="test_args_kwargs"),
    ),
)
def test_parse_args_kwargs(input_str: str, excepted_args: tuple[str], excepted_kwargs: dict[str, str]):
    assert utils.parse_args_kwargs(input_str) == (excepted_args, excepted_kwargs)
