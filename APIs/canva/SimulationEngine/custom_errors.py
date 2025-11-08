class InvalidDesignIDError(ValueError):
    """Custom error for invalid design ID format."""
    pass
   
class InvalidAssetIDError(ValueError):
    """Custom error raised when asset_id is invalid (e.g., empty)."""
    pass

class InvalidTitleError(ValueError):
    """Custom error raised when title does not meet length requirements."""
    pass

class InvalidQueryError(ValueError):
    """Custom error for invalid query parameters."""
    pass

class InvalidOwnershipError(ValueError):
    """Custom error for invalid ownership filter values."""
    pass

class InvalidSortByError(ValueError):
    """Custom error for invalid sort_by options."""
    pass