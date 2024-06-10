from __future__ import annotations

import asyncio
from typing import Any, NamedTuple

import asyncssh
import pytest

from tsbot import connection

# pyright: reportPrivateUsage=false


class ConnectionInfo(NamedTuple):
    username: str
    password: str
    address: str
    port: int = 10022


@pytest.fixture
def conn_info():
    return ConnectionInfo("testuser", "password", "localhost", 10022)


async def mock_connect(*args: Any, **kwargs: Any):
    return MockClientConnection()


@pytest.fixture
def conn(monkeypatch: pytest.MonkeyPatch, conn_info: ConnectionInfo):
    monkeypatch.setattr(asyncssh, "connect", mock_connect)

    return connection.TSConnection(
        conn_info.username, conn_info.password, conn_info.address, conn_info.port
    )


@pytest.fixture
def connected_conn(monkeypatch: pytest.MonkeyPatch, conn_info: ConnectionInfo):
    monkeypatch.setattr(asyncssh, "connect", mock_connect)

    c = connection.TSConnection(
        conn_info.username, conn_info.password, conn_info.address, conn_info.port
    )
    asyncio.run(c.connect())
    return c


class MockClientConnection:
    def __init__(self) -> None:
        self._is_closing: bool = False
        self._closed: bool = False

    async def open_session(self):
        return MockWriter(), MockReader(), MockReader()

    def close(self):
        self._is_closing = True

    async def wait_closed(self):
        self._closed = self._is_closing


class MockReader:
    def __init__(self) -> None:
        self._lines_read = 0

    async def readuntil(self, *args: Any, **kwargs: Any) -> str:
        self._lines_read += 1
        return f"line {self._lines_read}\n\r"


class MockWriter:
    def __init__(self) -> None:
        self._is_closing: bool = False
        self._closed: bool = False

        self._write_buffer = ""
        self._write_actual = ""

    def is_closing(self):
        return self._closed

    def close(self):
        self._is_closing = True

    async def wait_closed(self):
        self._closed = self._is_closing

    def write(self, data: str):
        self._write_buffer += data

    async def drain(self):
        self._write_actual += self._write_buffer
        self._write_buffer = ""


def test_create_connection(conn_info: ConnectionInfo):
    conn = connection.TSConnection(
        conn_info.username, conn_info.password, conn_info.address, conn_info.port
    )

    assert conn.username == conn_info.username
    assert conn.password == conn_info.password
    assert conn.address == conn_info.address
    assert conn.port == conn_info.port

    assert conn._connection is None
    assert conn._writer is None
    assert conn._reader is None


def test_connection_connect(conn: connection.TSConnection):
    asyncio.run(conn.connect())

    assert isinstance(conn._connection, MockClientConnection)
    assert isinstance(conn._writer, MockWriter)
    assert isinstance(conn._reader, MockReader)


def test_connection_close(connected_conn: connection.TSConnection):
    asyncio.run(connected_conn.close())

    assert connected_conn._writer and connected_conn._writer.is_closing()
    assert (
        isinstance(connected_conn._connection, MockClientConnection)
        and connected_conn._connection._closed
    )


@pytest.mark.parametrize(
    ("number_of_lines"),
    (
        pytest.param(1, id="test_read_lines=1"),
        pytest.param(3, id="test_read_lines=3"),
        pytest.param(8, id="test_read_lines=8"),
    ),
)
def test_read_lines(
    monkeypatch: pytest.MonkeyPatch, connected_conn: connection.TSConnection, number_of_lines: int
):
    counter = 0

    async def _read() -> str | None:
        nonlocal counter
        counter += 1

        return f"line {counter}"

    monkeypatch.setattr(connected_conn, "_read", _read)

    lines_read: list[str] = []

    async def async_wrapper():
        async for data in connected_conn.read_lines(number_of_lines):
            lines_read.append(data)

    asyncio.run(async_wrapper())

    assert len(lines_read) == number_of_lines


@pytest.mark.parametrize(
    ("number_of_lines", "break_at"),
    (
        pytest.param(5, 2, id="test_read_lines_break_at=5"),
        pytest.param(8, 8, id="test_read_lines_break_at=8"),
        pytest.param(5, 10, id="test_read_lines_break_at=10"),
    ),
)
def test_read_lines_break_on_empty(
    monkeypatch: pytest.MonkeyPatch,
    connected_conn: connection.TSConnection,
    number_of_lines: int,
    break_at: int,
):
    counter = 0

    async def _read() -> str | None:
        nonlocal counter
        counter += 1

        if counter > break_at:
            return None

        return f"line {counter}"

    monkeypatch.setattr(connected_conn, "_read", _read)

    lines_read: list[str] = []

    async def async_wrapper():
        async for data in connected_conn.read_lines(number_of_lines):
            lines_read.append(data)

    asyncio.run(async_wrapper())

    if number_of_lines < break_at:
        assert len(lines_read) == number_of_lines

    else:
        assert len(lines_read) == break_at


@pytest.mark.parametrize(
    ("break_after"),
    (
        pytest.param(1, id="test_read_break_after=1"),
        pytest.param(5, id="test_read_break_after=5"),
        pytest.param(8, id="test_read_break_after=10"),
    ),
)
def test_read(
    monkeypatch: pytest.MonkeyPatch, connected_conn: connection.TSConnection, break_after: int
):
    counter = 0

    async def _read() -> str | None:
        nonlocal counter
        counter += 1

        if counter > break_after:
            return None

        return f"line {counter}"

    monkeypatch.setattr(connected_conn, "_read", _read)

    lines_read: list[str] = []

    async def async_wrapper():
        async for data in connected_conn.read():
            lines_read.append(data)

    asyncio.run(async_wrapper())
    assert len(lines_read) == break_after


def test_internal_read(connected_conn: connection.TSConnection):
    line = asyncio.run(connected_conn._read())

    assert isinstance(line, str)
    assert line == "line 1"


def test_internal_read_exception_incomplete(
    monkeypatch: pytest.MonkeyPatch, connected_conn: connection.TSConnection
):
    def readuntil(*args: Any, **kwargs: Any):
        raise asyncio.IncompleteReadError(b"test exception", expected=0)

    monkeypatch.setattr(connected_conn._reader, "readuntil", readuntil)

    line = asyncio.run(connected_conn._read())

    assert line is None


def test_internal_read_on_closed_channel(conn: connection.TSConnection):
    with pytest.raises(ConnectionResetError):
        asyncio.run(conn._read())


@pytest.mark.parametrize(
    ("to_write"),
    (
        pytest.param(["test string"], id="test_write"),
        pytest.param(["test string 1", "test string 2", "test string 3"], id="test_write_multiple"),
    ),
)
def test_write(connected_conn: connection.TSConnection, to_write: list[str]):
    async def async_wrapper():
        for line in to_write:
            await connected_conn.write(line)

    asyncio.run(async_wrapper())

    assert isinstance(connected_conn._writer, MockWriter)

    should_have_written = "\n\r".join(to_write) + "\n\r"
    assert connected_conn._writer._write_actual == should_have_written


def test_write_excpetion_while_writing(
    monkeypatch: pytest.MonkeyPatch, connected_conn: connection.TSConnection
):
    def drain():
        raise Exception("test exception")

    monkeypatch.setattr(connected_conn._writer, "drain", drain)

    asyncio.run(connected_conn.write("test"))


def test_write_on_closed_channel(
    conn: connection.TSConnection, connected_conn: connection.TSConnection
):
    async def async_wrapper():
        await connected_conn.close()
        await connected_conn.write("hello")

    with pytest.raises(BrokenPipeError):
        asyncio.run(async_wrapper())

    with pytest.raises(BrokenPipeError):
        asyncio.run(conn.write("hello"))
