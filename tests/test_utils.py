import pytest

from tsbot import utils


params = (
    pytest.param("", "", id="test_empty"),
    pytest.param("TeamSpeak ]|[ Server", r"TeamSpeak\s]\p[\sServer", id="test_default_server_name"),
    pytest.param("Test token with custom set", r"Test\stoken\swith\scustom\sset", id="test_sentance"),
    pytest.param("		", r"\t\t", id="test_tabs"),
    pytest.param("| | | | | | |", r"\p\s\p\s\p\s\p\s\p\s\p\s\p", id="test_space_pipes"),
)


@pytest.mark.parametrize(("input_str", "excepted"), params)
def test_escape(input_str: str, excepted: str) -> None:
    assert utils.escape(input_str) == excepted


@pytest.mark.parametrize(("excepted", "input_str"), params)
def test_unescape(input_str: str, excepted: str) -> None:
    assert utils.unescape(input_str) == excepted
