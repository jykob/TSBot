from __future__ import annotations

import pytest

from tsbot import encoders

escape_params = (
    pytest.param("", "", id="test_empty"),
    pytest.param("TeamSpeak ]|[ Server", r"TeamSpeak\s]\p[\sServer", id="test_default_server_name"),
    pytest.param(
        "Test token with custom set", r"Test\stoken\swith\scustom\sset", id="test_sentance"
    ),
    pytest.param("		", r"\t\t", id="test_tabs"),
    pytest.param("| | | | | | |", r"\p\s\p\s\p\s\p\s\p\s\p\s\p", id="test_space_pipes"),
)


@pytest.mark.parametrize(("input_str", "expected"), escape_params)
def test_escape(input_str: str, expected: str) -> None:
    assert encoders.escape(input_str) == expected


@pytest.mark.parametrize(("expected", "input_str"), escape_params)
def test_unescape(input_str: str, expected: str) -> None:
    assert encoders.unescape(input_str) == expected
