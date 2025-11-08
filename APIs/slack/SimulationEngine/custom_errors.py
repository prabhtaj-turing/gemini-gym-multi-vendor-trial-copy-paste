"""
Custom exception definitions for Slack API–related errors.

This module defines specialized exceptions that can be used to handle
various error conditions encountered when interacting with the Slack API.
"""

class UserNotInConversationError(ValueError):
    """Custom error raised when a user is not part of a specified conversation."""
    def __init__(self, message="User not in conversation"):
        super().__init__(message)

class MissingUserIDError(ValueError):
    """Custom error raised when user_id is missing or empty."""
    pass

class ChannelNotFoundError(ValueError):
    """Custom exception raised when a channel is not found in the database."""
    pass

class MessageNotFoundError(ValueError):
    """Custom exception raised when a message is not found in a channel."""
    pass

class InvalidLimitError(ValueError):
    """Custom error for invalid limit values."""
    pass

class InvalidChannelError(ValueError):
    """Custom error for invalid channel input."""
    pass

class InvalidTextError(ValueError):
    """Custom error for invalid text input."""
    pass

class ChannelNameMissingError(ValueError):
    """Custom error for when the channel name is missing or empty."""
    pass

class ChannelNameTakenError(ValueError):
    """Custom error for when the channel name is already taken."""
    pass

class UserGroupIdInvalidError(ValueError):
    """Custom error for invalid usergroup_id format or content."""
    pass

class IncludeDisabledInvalidError(ValueError):
    """Custom error for invalid include_disabled format or content."""
    pass

class UserGroupNotFoundError(ValueError):  # Or ValueError, depending on desired hierarchy
    """Custom error raised when a user group is not found."""
    pass

class UserGroupAlreadyDisabledError(ValueError):
    """Custom error raised when attempting to disable an already disabled user group."""
    pass

class EmptyEmailError(ValueError):
    """Custom error raised when an empty email string is provided as input."""
    pass

class InvalidEmailFormatError(ValueError):
    """Custom error raised when an email address has an invalid format."""
    pass

class InvalidCursorValueError(ValueError):
    """Custom error raised when a cursor has invalid value."""
    pass

class InvalidUserError(ValueError):
    """Custom error raised when an invalid user is found."""
    pass

class UserNotFoundError(ValueError):
    """Custom error raised when a user ID does not exist in the database."""
    pass

class AlreadyReactionError(ValueError):
    """Custom error raised when a user already reacted with the emoji."""
    pass
  
class InvalidTimestampFormatError(ValueError):
    """Custom error raised when a timestamp string cannot be parsed correctly."""
    pass

class InvalidDateTimeFormatError(ValueError):
    """Raised when a datetime string is not in the expected format."""
    pass

class InvalidLimitValueError(ValueError):
    """Custom error raised when the limit parameter has an invalid value (e.g., negative)."""
    pass

class InvalidCursorFormatError(ValueError):
    """Custom error raised when a cursor string cannot be parsed to a non-negative integer."""
    pass

class CursorOutOfBoundsError(ValueError):
    """Custom error raised when the cursor is out of bounds for the current dataset."""
    pass

class MissingChannelOrUsersError(ValueError):
    """Raised when neither channel nor users are provided to open_conversation."""
    pass

class ChannelAndUsersMutuallyExclusiveError(ValueError):
    """Raised when both channel and users are provided to open_conversation."""
    pass

class TimestampError(Exception):
    """Raised for timestamp-related errors."""
    pass

class UserAlreadyInvitedError(ValueError):
    """Raised when trying to invite an already invited user"""
    pass

class InvalidUsersError(ValueError):
    """Custom error raised when the users string is empty or invalid."""
    pass

class InconsistentDataError(ValueError):
    """Raised when there is an inconsistency in the database, such as a user being in a usergroup but not in the users database."""
    pass

class MissingReminderIdError(ValueError):
    """Custom error raised when reminder_id is missing or empty."""
    pass

class ReminderNotFoundError(ValueError):
    """Custom error raised when a reminder ID does not exist in the database."""
    pass

class MissingCompleteTimestampError(ValueError):
    """Custom error raised when complete_ts is missing or empty."""
    pass

class InvalidCompleteTimestampError(ValueError):
    """Custom error raised when complete_ts has an invalid format and cannot be parsed as a timestamp."""
    pass

class ReminderAlreadyCompleteError(ValueError):
    """Custom error raised when attempting to complete a reminder that is already completed."""
    pass


class InvalidProfileError(ValueError):
    """Custom error raised when profile data is invalid."""
    pass
  
class MissingRequiredArgumentsError(ValueError):
    """Custom error raised when required arguments are missing or empty."""
    pass

class NoReactionsOnMessageError(ValueError):
    """Custom error raised when trying to remove a reaction from a message that has no reactions."""
    pass

class ReactionNotFoundError(ValueError):
    """Custom error raised when a specific reaction is not found on a message."""
    pass

class UserHasNotReactedError(ValueError):
    """Custom error raised when trying to remove a reaction from a user who hasn't reacted."""
    pass

class NotAllowedError(ValueError):
    """Custom error raised when an operation is not allowed on a specific channel type."""
    pass
  


class MissingPurposeError(ValueError):
    """Custom error raised when purpose is missing or empty."""
    pass

class FileSizeLimitExceededError(ValueError):
    """Custom error raised when a file exceeds the maximum allowed size."""
    pass

class InvalidChannelIdError(ValueError):
    """Custom error raised when an invalid channel ID is provided."""
    pass

class MissingContentOrFilePathError(ValueError):
    """Custom error raised when neither content nor file_path is provided for file upload."""
    pass

class FileReadError(ValueError):
    """Custom error raised when a file cannot be read from the specified path."""
    pass

class CurrentUserNotSetError(ValueError):
    """Custom error raised when an operation requires a current user but none is set."""
    pass


