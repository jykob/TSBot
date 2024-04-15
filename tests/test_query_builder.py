from __future__ import annotations

import pytest

from tsbot.query_builder import TSQuery, query

# pyright: reportPrivateUsage=false


def test_add_options():
    q = query("channellist")
    assert len(q._options) == 0

    q = q.option("topic", "flags", "voice")
    assert q._options == ("topic", "flags", "voice")


def test_add_params():
    q = query("channelmove")
    assert q._parameters == {}

    q = q.params(cid=16, cpid=1, order=0)
    assert q._parameters == {"cid": 16, "cpid": 1, "order": 0}


def test_add_param_blocks():
    q = query("permidgetbyname")
    assert len(q._parameter_blocks) == 0

    q = q.param_block(permsid="b_serverinstance_help_view")
    q = q.param_block(permsid="b_serverinstance_info_view")

    assert {"permsid": "b_serverinstance_help_view"} in q._parameter_blocks
    assert {"permsid": "b_serverinstance_info_view"} in q._parameter_blocks


def test_add_param_blocks_list():
    q = query("permidgetbyname")
    assert len(q._parameter_blocks) == 0

    q = q.param_block(
        [
            {"permsid": "b_serverinstance_help_view"},
            {"permsid": "b_serverinstance_info_view"},
        ],
    )

    q = q.param_block(
        {"permsid": perm}
        for perm in ("b_serverinstance_permission_list", "b_serverinstance_binding_list")
    )

    assert {"permsid": "b_serverinstance_help_view"} in q._parameter_blocks
    assert {"permsid": "b_serverinstance_info_view"} in q._parameter_blocks
    assert {"permsid": "b_serverinstance_permission_list"} in q._parameter_blocks
    assert {"permsid": "b_serverinstance_binding_list"} in q._parameter_blocks


@pytest.mark.parametrize(
    ("input_query", "expected"),
    (
        pytest.param(query("serverlist"), "serverlist", id="test_command_only"),
        pytest.param(
            query("clientlist").option("uid", "away").option("groups"),
            "clientlist -uid -away -groups",
            id="test_options",
        ),
        pytest.param(
            query("sendtextmessage").params(targetmode=2, target=12).params(msg="Hello World!"),
            r"sendtextmessage targetmode=2 target=12 msg=Hello\sWorld!",
            id="test_params",
        ),
        pytest.param(
            query("clientkick")
            .params(reasonid=5, reasonmsg="Go away!")
            .param_block(clid=1)
            .param_block(clid=2)
            .param_block(clid=3),
            r"clientkick reasonid=5 reasonmsg=Go\saway! clid=1|clid=2|clid=3",
            id="test_param_block_single",
        ),
        pytest.param(
            query("servergroupaddperm")
            .params(sgid=13)
            .param_block(permid=17276, permvalue=50, permnegated=0, permskip=0)
            .param_block(permid=21415, permvalue=20, permnegated=0),
            "servergroupaddperm sgid=13 permid=17276 permvalue=50 permnegated=0 permskip=0|permid=21415 permvalue=20 permnegated=0",
            id="test_param_block_multiple",
        ),
        pytest.param(
            query("ftdeletefile")
            .params(cid=2, cpw="")
            .param_block(name="/Pic1.PNG")
            .param_block(name="/Pic2.PNG"),
            r"ftdeletefile cid=2 cpw= name=\/Pic1.PNG|name=\/Pic2.PNG",
            id="test_empty_param",
        ),
    ),
)
def test_query_compile(input_query: TSQuery, expected: str) -> None:
    assert input_query.compile() == expected


def test_caching():
    q = query("channelmove")
    q.params(cid=16, cpid=1, order=0)

    first_compile = q.compile()

    assert q._cached_query
    assert first_compile is q.compile()


def test_cache_invalid():
    q = query("channelmove").params(cid=16, cpid=1, order=0)
    first_compile = q.compile()

    q = q.option("continueonerror")

    assert not q._cached_query
    assert first_compile != q.compile()


@pytest.mark.parametrize(
    ("q", "includes"),
    (
        pytest.param(
            query("channeldelete").params(cid=1, force=True),
            "force=1",
            id="test_boolean_conversion_true",
        ),
        pytest.param(
            query("channeldelete").params(cid=1, force=False),
            "force=0",
            id="test_boolean_conversion_false",
        ),
    ),
)
def test_boolean_params(q: TSQuery, includes: str):
    assert includes in q.compile()
