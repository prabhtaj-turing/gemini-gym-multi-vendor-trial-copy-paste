class InvalidRequestError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


class ValidationError(Exception):
    """Custom exception for input argument validation failures."""

    pass

class ActionNotSupportedError(Exception):
    """Raised when an action is not supported."""

    pass

class AccountNotFoundError(Exception):
    """Raised when an account is not found in the database."""

    pass


class DeviceNotFoundError(Exception):
    """Raised when a device is not found in the database."""

    pass


class ServicePlanNotFoundError(Exception):
    """Raised when a service plan is not found in the database."""

    pass


class InsufficientPermissionsError(Exception):
    """Raised when the user doesn't have sufficient permissions for the operation."""

    pass


class DuplicateAccountError(Exception):
    """Raised when trying to create an account that already exists."""

    pass


class InvalidUpgradeEligibilityError(Exception):
    """Raised when a device upgrade eligibility check fails."""

    pass


class ServiceModificationError(Exception):
    """Raised when a service plan or feature modification fails."""

    pass


class PaymentMethodNotFoundError(Exception):
    """Raised when a payment method is not found."""

    pass


class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for the operation."""

    pass


class ParseError(Exception):
    """Raised when JSON parsing fails."""

    pass
