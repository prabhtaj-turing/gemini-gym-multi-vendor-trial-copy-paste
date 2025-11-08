"""Custom exceptions for CES Billing service."""


class BillingServiceError(Exception):
    """Base exception for billing service errors."""
    pass


class EmptyFieldError(BillingServiceError):
    """Raised when a required field is empty."""
    pass


class MissingRequiredFieldError(BillingServiceError):
    """Raised when a required field is missing."""
    pass


class InvalidMdnError(BillingServiceError):
    """Raised when MDN format is invalid."""
    pass


class InvalidAccountRoleError(BillingServiceError):
    """Raised when account role is invalid."""
    pass


class BillingDataError(BillingServiceError):
    """Raised when billing data is invalid or corrupted."""
    pass


class PaymentProcessingError(BillingServiceError):
    """Raised when payment processing fails."""
    pass


class AutoPayError(BillingServiceError):
    """Raised when AutoPay operations fail."""
    pass


class EscalationError(BillingServiceError):
    """Raised when escalation fails."""
    pass


class ValidationError(BillingServiceError):
    """Raised when data validation fails."""
    pass


class DatabaseError(BillingServiceError):
    """Raised when database operations fail."""
    pass


class AuthenticationError(BillingServiceError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(BillingServiceError):
    """Raised when authorization fails."""
    pass


class BillingRequestError(BillingServiceError):
    """Raised when a billing request fails."""
    pass


class ServiceUnavailableError(BillingServiceError):
    """Raised when the billing service is unavailable."""
    pass


class RateLimitError(BillingServiceError):
    """Raised when rate limit is exceeded."""
    pass


class BillingTimeoutError(BillingServiceError):
    """Raised when operation times out."""
    pass
