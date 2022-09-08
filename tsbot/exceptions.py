class TSException(Exception):
    """Exception related to TSBot"""


class TSResponseError(TSException):
    """Raised when a response from server has error_id set to other than 0."""

    def __init__(self, message: str, error_id: int) -> None:
        self.message = message
        self.error_id = error_id

    def __str__(self) -> str:
        return f"Error {self.error_id}: {self.message}"


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
