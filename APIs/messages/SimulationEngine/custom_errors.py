class InvalidRecipientError(ValueError):
    """Custom error raised when an invalid recipient is provided."""
    pass


class InvalidPhoneNumberError(ValueError):
    """Custom error raised when an invalid phone number is provided."""
    pass


class MessageBodyRequiredError(ValueError):
    """Custom error raised when message body is required but not provided."""
    pass


class RecipientNotFoundError(ValueError):
    """Custom error raised when a recipient is not found."""
    pass


class InvalidMediaAttachmentError(ValueError):
    """Custom error raised when an invalid media attachment is provided."""
    pass


class ValidationError(ValueError):
    """Custom error for validation errors."""
    pass 