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
