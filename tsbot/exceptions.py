class TSException(Exception):
    """Exception related to tsbot"""


class TSResponseError(TSException):
    """Raised when response from server has error_id set to other than 0."""


class TSCommandException(TSException):
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


class TSEventException(TSException):
    """Exception happend during event handling"""
