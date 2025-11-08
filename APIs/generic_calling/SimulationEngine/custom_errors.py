class InvalidRecipientError(Exception):
    """Raised when recipient data is invalid."""
    pass

class NoPhoneNumberError(Exception):
    """Raised when no phone number can be determined."""
    pass

class MultipleEndpointsError(Exception):
    """Raised when multiple endpoints require user choice."""
    pass

class MultipleRecipientsError(Exception):
    """Raised when multiple recipients require user choice."""
    pass

class GeofencingPolicyError(Exception):
    """Raised when geofencing policy applies."""
    pass

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass 

class ResourceNotFoundError(Exception):
    """Raised when a specified resource could not be found."""
    pass

class ChatNotFoundError(Exception):
    """Raised when a chat with the specified JID does not exist."""
    pass

class ContactNotFoundError(Exception):
    """Raised when a contact with the specified JID or phone number does not exist."""
    pass

class MessageNotFoundError(Exception):
    """Raised when a message with the specified ID does not exist in the given chat."""
    pass

class LocalFileNotFoundError(Exception):
    """Raised when a media file cannot be found at the specified local path."""
    pass

class MediaUnavailableError(Exception):
    """Raised when a message contains no media or the media has expired."""
    pass

class InvalidInputError(Exception):
    """Raised when invalid or malformed input parameters from the client."""
    pass

class InvalidQueryError(Exception):
    """Raised when a search query is invalid, too short, or poorly formatted."""
    pass

class InvalidParameterError(Exception):
    """Raised for generally invalid parameters, like a bad date format."""
    pass

class PaginationError(Exception):
    """Raised when a requested page number is out of the valid range."""
    pass
        
class InvalidSortByError(Exception):
    """Raised when the 'sort_by' parameter is not one of the allowed values."""
    pass

class InvalidJIDError(Exception):
    """Raised when a provided JID is not in a valid format."""
    pass

class InvalidPhoneNumberError(Exception):
    """Raised when a provided phone number is not a valid format."""
    pass

class InvalidDateTimeFormatError(Exception):
    """Raised when a provided datetime string is not in a valid format."""
    pass

class UnsupportedMediaTypeError(Exception):
    """Raised if the file type of a media upload is not supported."""
    pass

class OperationFailedError(Exception):
    """Raised when an operation failed during execution for reasons other than bad input."""
    pass

class MessageSendFailedError(Exception):
    """Raised when a message could not be sent due to a server-side or network error."""
    pass

class MediaUploadFailedError(Exception):
    """Raised when uploading a media file to the server fails."""
    pass

class DownloadFailedError(Exception):
    """Raised when a media download fails due to a network or server issue."""
    pass

class AudioProcessingError(Exception):
    """Raised if there is an error processing an audio file (e.g., conversion fails)."""
    pass

class LocalStorageError(Exception):
    """Raised if there is an error saving a downloaded file to local storage."""
    pass

class InternalSimulationError(Exception):
    """Raised when there is an internal inconsistency in the simulation's data. For example, data retrieved from the mock DB fails Pydantic validation."""
    pass

class ServiceError(Exception):
    """Raised when a general service-level error occurs like timeouts or rate limiting."""
    pass

class APITimeoutError(Exception):
    """Raised when a request to the underlying WhatsApp service times out."""
    pass

class RateLimitExceededError(Exception):
    """Raised when the sending rate limit has been exceeded."""
    pass

class ContactAlreadyExistsError(Exception):
    """Raised when a contact with the given phone number already exists in the address book."""
    pass