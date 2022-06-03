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


def test_from_server_response():
    raw_data = "notifyclientmoved ctid=3 reasonid=0 clid=1"
    tsevent = TSEvent.from_server_response(raw_data=raw_data)

    assert tsevent.event == "clientmoved"
    assert tsevent.msg == None
    assert tsevent.ctx == dict(ctid="3", reasonid="0", clid="1")
