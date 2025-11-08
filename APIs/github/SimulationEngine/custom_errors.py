class GitHubAPIError(Exception):
    """Base class for exceptions related to GitHub API interactions."""
    pass

class NotFoundError(GitHubAPIError):
    """Raised if the repository does not exist."""
    pass

class ValidationError(GitHubAPIError):
    """Raised if required fields are missing or invalid."""
    pass


class InvalidInputError(Exception):
    """Raised when user-provided input is syntactically or semantically incorrect."""
    pass


class MethodNotAllowedError(Exception):
    """If the pull request is not mergeable (e.g., conflicts, checks pending)."""
    pass

class ConflictError(Exception):
    """Raised if updating a file and the provided 'sha' does not match
    the latest file SHA (blob SHA)."""
    pass

class ForbiddenError(Exception):
    """If the merge cannot be performed due to conflicts or if the head commit of the pull request has changed since the merge was initiated."""
    pass

class InternalError(Exception):
    """Custom exception for internal errors."""
    pass

class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    def __init__(self, message="The request is not authenticated."):
        self.message = message
        super().__init__(self.message)

class UnprocessableEntityError(Exception):
    """Raised if the repository cannot be created due to semantic reasons,
    such as the repository name already existing for the user/organization,
    or other server-side validation failures not related to input format."""
    pass

class RateLimitError(GitHubAPIError):
    """Raised when the API rate limit has been exceeded."""
    def __init__(self, message="API rate limit exceeded."):
        self.message = message
        super().__init__(self.message)

class InvalidDateTimeFormatError(ValueError):
    """Raised when a datetime string is not in the expected format."""
    pass
