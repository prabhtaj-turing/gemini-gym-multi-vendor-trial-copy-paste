class InvalidRequestError(Exception):
    pass


class AuthenticationFailedError(Exception):
    """Raised when customer authentication fails."""

    pass


class InvalidSessionError(Exception):
    """Raised when the session is invalid or expired."""

    pass


class OfferEnrollmentError(Exception):
    """Raised when failing to enroll a customer in a loyalty offer."""

    pass


class CustomerNotEligibleError(Exception):
    """Raised when the customer is not eligible for an offer."""

    pass


class NotFoundError(Exception):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(Exception):
    """Custom exception for input argument validation failures."""

    pass
