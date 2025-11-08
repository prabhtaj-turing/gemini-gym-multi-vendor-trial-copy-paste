class MissingPartParameterError(ValueError):
    """Raised when the 'part' parameter is missing or empty."""
    pass

class InvalidMaxResultsError(ValueError):
    """Raised when 'max_results' is provided but is not a positive integer."""

class InvalidPartParameterError(ValueError):
    """Custom error raised when the 'part' parameter is invalid."""
    pass


class InvalidActivityFilterError(ValueError):
    """Raised when the filtering condition is not met (exactly one of 'channelId' or 'mine' must be provided)."""
    pass


class InvalidFilterParameterError(ValueError):
    """Exactly one of 'channel_id', 'section_id', or 'mine' must be provided."""
    pass

class MaxResultsOutOfRangeError(ValueError):
    """Custom error for when max_results is outside the allowed range (1-50)."""
    def __init__(self, message="max_results must be between 1 and 50, inclusive."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class InvalidCommentIdError(ValueError):
    """Raised when comment_id is not a string, is empty, or contains only whitespace."""
    pass

class InvalidModerationStatusError(ValueError):
    """Raised when moderation_status is not a string or not one of the valid values."""
    pass

class InvalidBanAuthorError(ValueError):
    """Raised when ban_author is not a boolean."""
    pass

class InvalidCommentInsertError(ValueError):
    """Custom exception for invalid comment insertion parameters."""
    pass
class InvalidThreadIDError(Exception):
    """Custom exception for invalid thread ID."""
    pass
class VideoIdNotFoundError(Exception):
    """Custom exception for video ID not found."""
    pass
class InvalidVideoIdError(Exception):
    """Custom exception for invalid video ID."""
    pass
