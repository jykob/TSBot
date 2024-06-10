import pytest

from tsbot import exceptions


@pytest.mark.parametrize(
    ("error_id", "message"),
    (
        pytest.param(1234, "Test exception", id="test_response_error_1"),
        pytest.param(524, "client is flooding", id="test_response_error_2"),
    ),
)
def test_ts_response_error(error_id: int, message: str):
    error = exceptions.TSResponseError(message, error_id)

    assert error.error_id == error_id
    assert error.msg == message

    assert str(error)
