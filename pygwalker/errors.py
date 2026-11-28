"""
This module contains all the custom errors used by pygwalker.
"""

from enum import Enum


class ErrorCode(int, Enum):
    UNKNOWN_ERROR = -1
    INVALID_REQUEST = 10001
    TOKEN_ERROR = 20001
    CLOUD_CONFIG_LIMIT = 20002
    CLOUD_CHART_NOT_FOUND = 20003


class BaseError(Exception):
    """Base class for all exceptions raised by pygwalker."""

    def __init__(self, *args, code: ErrorCode = ErrorCode.UNKNOWN_ERROR) -> None:
        super().__init__(*args)
        self.code = code


class InvalidConfigIdError(BaseError):
    """Raised when the config is invalid."""

    pass


class PrivacyError(BaseError):
    """Raised when the privacy setting is invalid."""

    pass


class CloudFunctionError(BaseError):
    """Raised when the cloud function is invalid."""

    pass


class CsvFileTooLargeError(BaseError):
    """Raised when the csv file is too large."""

    pass


class ViewSqlSameColumnError(BaseError):
    """Raised when the view sql is invalid."""

    pass


class CommProtocolError(BaseError):
    """Raised when a frontend communication payload is invalid."""

    def __init__(self, *args) -> None:
        super().__init__(*args, code=ErrorCode.INVALID_REQUEST)


class UnsafeSqlError(BaseError):
    """Raised when a SQL query violates the read-only safety policy."""

    def __init__(self, message: str = "SQL query rejected by security policy.") -> None:
        super().__init__(message, code=ErrorCode.INVALID_REQUEST)


class SqlSandboxError(BaseError):
    """Raised when the isolated DuckDB query sandbox cannot be initialized safely."""

    def __init__(self, message: str = "Failed to initialize isolated SQL execution sandbox.") -> None:
        super().__init__(message, code=ErrorCode.UNKNOWN_ERROR)


class StreamlitPygwalkerApiError(BaseError):
    """Raised when the config is invalid."""

    def __init__(self) -> None:
        super().__init__(
            "Adding pygwalker web api to streamlit failed. If possible, please report this case to the pygwalker team. Thanks!",
            code=ErrorCode.UNKNOWN_ERROR,
        )
