from __future__ import annotations

import pytest
from tsbot import context, events


@pytest.mark.parametrize(
    ("event", "ctx"),
    (
        pytest.param(
            "textmessage",
            context.TSCtx({"targetmode": "3", "msg": "hello", "invokerid": "1"}),
            id="test_event",
        ),
        pytest.param("close", {}, id="test_internal_event"),
        pytest.param(
            "permission_error",
            context.TSCtx(
                {
                    "exception": "TSPermissionError",
                    "exception_msg": "Client doesn't have permission to run this command",
                }
            ),
            id="test_exception_event",
        ),
    ),
)
def test_create_event(event: str, ctx: context.TSCtx):
    tsevent = events.TSEvent(event, ctx)

    assert tsevent.event == event
    assert tsevent.ctx == ctx


@pytest.mark.parametrize(
    ("raw_data", "expected_event", "expected_ctx"),
    (
        pytest.param(
            "notifyclientmoved ctid=3 reasonid=0 clid=1",
            "clientmoved",
            context.TSCtx({"ctid": "3", "reasonid": "0", "clid": "1"}),
            id="test_clientmove",
        ),
        pytest.param(
            "notifyclientleftview cfid=12 ctid=0 reasonid=8 reasonmsg=leaving clid=1",
            "clientleftview",
            context.TSCtx(
                {"cfid": "12", "ctid": "0", "reasonid": "8", "reasonmsg": "leaving", "clid": "1"}
            ),
            id="test_clientleftview",
        ),
    ),
)
def test_from_server_response(raw_data: str, expected_event: str, expected_ctx: context.TSCtx):
    tsevent = events.TSEvent.from_server_response(raw_data=raw_data)

    assert tsevent.event == expected_event
    assert tsevent.ctx == expected_ctx
