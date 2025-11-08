class InvalidRequestError(Exception):
    pass

class ResourceNotFoundError(Exception):
    pass

class ValidationError(Exception):
    """Custom exception for input argument validation failures."""
    pass

class ProductNotFoundError(Exception):
    pass

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database."""
    pass

class ReservationNotFoundError(Exception):
    """Raised when a reservation is not found in the database."""
    pass

class ReservationAlreadyCancelledError(Exception):
    """Raised when a reservation is already cancelled."""
    pass

class FlightNotFoundError(Exception):
    """Raised when a flight is not found in the database."""
    pass

class InvalidExpressionError(Exception):
    """Raised when a mathematical expression contains invalid characters."""
    pass

class PaymentMethodNotFoundError(Exception):
    """Raised when a payment method is not found for a user."""
    pass

class InsufficientFundsError(Exception):
    """Raised when a payment method has insufficient funds."""
    pass

class SeatsUnavailableError(Exception):
    """Raised when there are not enough available seats on a flight."""
    pass

class CertificateUpdateError(Exception):
    """Raised when a certificate is used for an update operation."""
    pass

class MismatchedPassengerCountError(Exception):
    """Raised when the number of passengers in an update does not match the original reservation."""
    pass

class InvalidDateTimeFormatError(Exception):
    """Raised when a datetime string is not in the expected format."""
    pass