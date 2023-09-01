"""
    This module contains all the custom errors used by pygwalker.
"""


class BaseError(Exception):
    """Base class for all exceptions raised by pygwalker."""
    pass


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
