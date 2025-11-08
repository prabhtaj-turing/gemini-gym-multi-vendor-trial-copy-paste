"""Custom exceptions for the Google Home API."""


class GoogleHomeError(Exception):
    """Base exception for all Google Home API errors."""

    pass


class InvalidInputError(GoogleHomeError):
    """Raised when the input to an API function is invalid."""

    pass


class DeviceNotFoundError(GoogleHomeError):
    """Raised when a device is not found."""

    pass


class NoSchedulesFoundError(GoogleHomeError):
    """Raised when there are no schedules to cancel for the given selection."""

    pass
