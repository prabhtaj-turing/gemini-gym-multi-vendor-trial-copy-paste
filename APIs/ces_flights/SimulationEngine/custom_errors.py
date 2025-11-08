class FlightBookingError(Exception):
    """Base exception for flight booking service errors."""
    pass

class EmptyFieldError(FlightBookingError):
    """Raised when a required field is empty."""
    pass

class InvalidDateError(FlightBookingError):
    """Raised when date format or range is invalid."""
    pass

class InvalidDateRangeError(FlightBookingError):
    """Raised when date range relationships are invalid (e.g., earliest date after latest date, return before departure)."""
    pass

class FlightDataError(FlightBookingError):
    """Raised when flight data is invalid or corrupted."""
    pass

class BookingError(FlightBookingError):
    """Raised when booking operations fail."""
    pass

class EscalationError(FlightBookingError):
    """Raised when escalation fails."""
    pass

class ConversationCompletionError(FlightBookingError):
    """Raised when conversation completion fails."""
    pass

class ConversationFailureError(FlightBookingError):
    """Raised when recording conversation failure fails."""
    pass

class ConversationCancellationError(FlightBookingError):
    """Raised when recording conversation cancellation fails."""
    pass

class ValidationError(FlightBookingError):
    """Raised when data validation fails."""
    pass

class DatabaseError(FlightBookingError):
    """Raised when database operations fail."""
    pass