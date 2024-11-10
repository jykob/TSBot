from __future__ import annotations


class TSException(Exception):  # noqa: N818
    """Exception related to TSBot."""


class TSResponseError(TSException):
    """Raised when a response from server has error_id set to other than 0."""

    def __init__(self, msg: str, error_id: int) -> None:
        self.msg = msg
        self.error_id = error_id

    def __str__(self) -> str:
        return f"Error {self.error_id}: {self.msg}"


class TSResponsePermissionError(TSResponseError):
    """
    Raised when a response has error_id of '2568', indicating that the client
    doesn't have the proper permissions to execute this query.
    """

    def __init__(self, msg: str, error_id: int, perm_id: int) -> None:
        super().__init__(msg, error_id)
        self.perm_id = perm_id

    def __str__(self) -> str:
        return f"Error {self.error_id}: {self.msg}, Failed on permission {self.perm_id}"


class TSCommandError(TSException):
    """
    Command handlers can raise this exception to indicate
    that something went wrong while running the handler.
    """


class TSPermissionError(TSException):
    """
    Command handlers can raise this exception to indicate
    that the user running this command doesn't have the
    proper permissions.
    """


class TSInvalidParameterError(TSException, TypeError):
    """
    Raised when a call to a command handler doesn't match the signature
    of the handler.
    """
