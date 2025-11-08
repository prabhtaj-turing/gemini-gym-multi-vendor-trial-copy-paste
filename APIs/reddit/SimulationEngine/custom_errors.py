class InvalidRecipientError(ValueError):
    """Raised when the recipient identifier is invalid (e.g., empty or whitespace)."""
    pass

class EmptySubjectError(ValueError):
    """Raised when the message subject is empty or consists only of whitespace."""
    pass

class EmptyMessageTextError(ValueError):
    """Raised when the message text is empty or consists only of whitespace."""
    pass
