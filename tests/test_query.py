import pytest

from tsbot import query


params = (
    pytest.param(query.TSQuery("serverlist"), "serverlist", id="test_command_only"),
    pytest.param(
        query.TSQuery("clientlist").option("uid", "away").option("groups"),
        "clientlist -uid -away -groups",
        id="test_options",
    ),
    pytest.param(
        query.TSQuery("sendtextmessage").params(targetmode=2, target=12).params(msg="Hello World!"),
        r"sendtextmessage targetmode=2 target=12 msg=Hello\sWorld!",
        id="test_params",
    ),
    pytest.param(
        query.TSQuery("clientkick")
        .params(reasonid=5, reasonmsg="Go away!")
        .param_block(clid=1)
        .param_block(clid=2)
        .param_block(clid=3),
        r"clientkick reasonid=5 reasonmsg=Go\saway! clid=1|clid=2|clid=3",
        id="test_param_block_single",
    ),
    pytest.param(
        query.TSQuery("servergroupaddperm")
        .params(sgid=13)
        .param_block(permid=17276, permvalue=50, permnegated=0, permskip=0)
        .param_block(permid=21415, permvalue=20, permnegated=0),
        "servergroupaddperm sgid=13 permid=17276 permvalue=50 permnegated=0 permskip=0|permid=21415 permvalue=20 permnegated=0",
        id="test_param_block_multiple",
    ),
)


@pytest.mark.parametrize(("input_query", "excepted"), params)
def test_query_compile(input_query: query.TSQuery, excepted: str) -> None:
    assert input_query.compile() == excepted


def test_empty_query():
    with pytest.raises(ValueError):
        query.TSQuery("")
