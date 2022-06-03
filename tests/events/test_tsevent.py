import pytest

from tsbot.events import TSEvent


@pytest.mark.parametrize(
    ("event", "msg", "ctx"),
    (
        pytest.param(
            "textmessage",
            None,
            {"targetmode": "3", "msg": "hello", "invokerid": "1"},
            id="test_event",
        ),
        pytest.param("close", None, {}, id="test_internal_event"),
        pytest.param(
            "permission_error", "Client doesn't have permission to run this command", {}, id="test_exception_event"
        ),
    ),
)
def test_create_event(event: str, msg: str | None, ctx: dict[str, str]):
    tsevent = TSEvent(event, msg, ctx)

    assert tsevent.event == event
    assert tsevent.msg == msg
    assert tsevent.ctx == ctx


@pytest.mark.parametrize(
    ("raw_data", "excepted_event", "excepted_msg", "excepted_ctx"),
    (
        pytest.param(
            "notifyclientmoved ctid=3 reasonid=0 clid=1",
            "clientmoved",
            None,
            dict(ctid="3", reasonid="0", clid="1"),
            id="test_clientmove",
        ),
        pytest.param(
            "notifyclientleftview cfid=12 ctid=0 reasonid=8 reasonmsg=leaving clid=1",
            "clientleftview",
            None,
            dict(cfid="12", ctid="0", reasonid="8", reasonmsg="leaving", clid="1"),
            id="test_clientleftview",
        ),
    ),
)
def test_from_server_response(
    raw_data: str, excepted_event: str, excepted_msg: str | None, excepted_ctx: dict[str, str]
):
    tsevent = TSEvent.from_server_response(raw_data=raw_data)

    assert tsevent.event == excepted_event
    assert tsevent.msg == excepted_msg
    assert tsevent.ctx == excepted_ctx
