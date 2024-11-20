from __future__ import annotations

import pytest

from tsbot import parsers


@pytest.mark.parametrize(
    ("input_str", "expected"),
    (
        pytest.param("", (), id="test_empty"),
        pytest.param("ip=0.0.0.0|ip=::", ({"ip": "0.0.0.0"}, {"ip": "::"}), id="test_simple"),
        pytest.param(
            "clid=14 client_nickname=Sven|clid=17 client_nickname=SvenBot",
            (
                {"clid": "14", "client_nickname": "Sven"},
                {"clid": "17", "client_nickname": "SvenBot"},
            ),
            id="test_multiple_data_simple",
        ),
        pytest.param(
            "cgid=1 name=Channel\\sAdmin type=0 iconid=100 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=50 n_member_removep=50|cgid=2 name=Operator type=0 iconid=200 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=30 n_member_removep=30|cgid=3 name=Voice type=0 iconid=600 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=25 n_member_removep=25|cgid=4 name=Guest type=0 iconid=0 savedb=0 sortid=0 namemode=0 n_modifyp=75 n_member_addp=0 n_member_removep=0|cgid=5 name=Channel\\sAdmin type=1 iconid=100 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=50 n_member_removep=50|cgid=6 name=Operator type=1 iconid=200 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=30 n_member_removep=30|cgid=7 name=Voice type=1 iconid=600 savedb=1 sortid=0 namemode=0 n_modifyp=75 n_member_addp=25 n_member_removep=25|cgid=8 name=Guest type=1 iconid=0 savedb=0 sortid=0 namemode=0 n_modifyp=75 n_member_addp=0 n_member_removep=0",
            (
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
            ),
            id="test_multiple_data_complex",
        ),
    ),
)
def test_parse_data(input_str: str, expected: list[dict[str, str]]) -> None:
    assert parsers.parse_data(input_str) == expected


@pytest.mark.parametrize(
    ("input_str", "expected"),
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
        pytest.param(
            "error id=0 msg=ok", {"error": "", "id": "0", "msg": "ok"}, id="test_error_line"
        ),
        pytest.param(
            "error id=2568 msg=insufficient\\sclient\\spermissions failed_permid=4",
            {
                "error": "",
                "id": "2568",
                "msg": "insufficient client permissions",
                "failed_permid": "4",
            },
            id="test_error_line_with_error",
        ),
    ),
)
def test_parse_line(input_str: str, expected: dict[str, str]) -> None:
    assert parsers.parse_line(input_str) == expected


@pytest.mark.parametrize(
    ("input_str", "expected"),
    (
        pytest.param("clid=12", ("clid", "12"), id="test_simple"),
        pytest.param(
            "client_servergroups=6,16,20",
            ("client_servergroups", "6,16,20"),
            id="test_comma_separated",
        ),
        pytest.param("clid=11|clid=12|clid=13", ("clid", "11,12,13"), id="test_multiple_values"),
        pytest.param(
            "channel_name=Bot\\sCommands",
            ("channel_name", "Bot Commands"),
            id="test_value_unescape",
        ),
        pytest.param("client_away_message", ("client_away_message", ""), id="test_empty_value"),
    ),
)
def test_parse_value(input_str: str, expected: tuple[str, str]) -> None:
    assert parsers.parse_value(input_str) == expected


@pytest.mark.parametrize(
    ("input_str", "expected_args", "expected_kwargs"),
    (
        pytest.param("123 asd test", ("123", "asd", "test"), {}, id="test_args"),
        pytest.param(
            "-asd test -name test_account",
            (),
            {"asd": "test", "name": "test_account"},
            id="test_kwargs",
        ),
        pytest.param(
            "-asd -name test_account -other",
            (),
            {"asd": "", "name": "test_account", "other": ""},
            id="test_kwargs_with_flags",
        ),
        pytest.param(
            "asd -name test_account 123",
            ("asd", "123"),
            {"name": "test_account"},
            id="test_args_kwargs",
        ),
        pytest.param(
            "asd   -name\ntest_account\t123",
            ("asd", "123"),
            {"name": "test_account"},
            id="test_whitespaces",
        ),
        pytest.param(
            '-name "test account" "1 2 3" "123"',
            ("1 2 3", "123"),
            {"name": "test account"},
            id="test_double_quotes",
        ),
        pytest.param(
            "-name 'test account' '1 2 3' '123'",
            ("1 2 3", "123"),
            {"name": "test account"},
            id="test_single_quotes",
        ),
        pytest.param(
            """'test "quote" test' -test "test 'quote' test" """,
            ('test "quote" test',),
            {"test": "test 'quote' test"},
            id="test_quote_within_a_quote",
        ),
        pytest.param(
            '-name "test account "1 2',
            ("account", '"1', "2"),
            {"name": '"test'},
            id="test_mismatch_double_quote",
        ),
        pytest.param(
            "-name 'test account '1 2",
            ("account", "'1", "2"),
            {"name": "'test"},
            id="test_mismatch_single_quote",
        ),
        pytest.param(
            "-amount '-14' '-123'", ("-123",), {"amount": "-14"}, id="test_negative_numbers"
        ),
        pytest.param(
            '''-text 'lorem ipsum\ntest\nnewline' 'asd\nasd' -other "asd\nasd\tasd"''',
            ("asd\nasd",),
            {"text": "lorem ipsum\ntest\nnewline", "other": "asd\nasd\tasd"},
            id="test_multiline_quotes",
        ),
        pytest.param("asd '", ("asd", "'"), {}, id="test_ending_in_quote"),
    ),
)
def test_parse_args_kwargs(
    input_str: str, expected_args: tuple[str], expected_kwargs: dict[str, str]
):
    assert parsers.parse_args_kwargs(input_str) == (expected_args, expected_kwargs)


@pytest.mark.parametrize(
    ("input_str", "maxsplit", "expected"),
    (
        pytest.param("asd asd asd", -1, ("asd", "asd", "asd"), id="test_split_no_limit"),
        pytest.param("asd asd asd", 1, ("asd", "asd asd"), id="test_split_one"),
        pytest.param("asd asd asd", 2, ("asd", "asd", "asd"), id="test_split_two"),
        pytest.param("asd asd asd", 3, ("asd", "asd", "asd", ""), id="test_split_fills"),
    ),
)
def test_split_ensure_splits(input_str: str, maxsplit: int, expected: tuple[str, ...]):
    assert parsers.split_ensure_splits(input_str, maxsplit=maxsplit) == expected
