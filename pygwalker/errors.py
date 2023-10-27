"""
    This module contains all the custom errors used by pygwalker.
"""
from enum import Enum


class ErrorCode(int, Enum):
    UNKNOWN_ERROR = -1
    TOKEN_ERROR = 20001
    CLOUD_CONFIG_LIMIT = 20002


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
