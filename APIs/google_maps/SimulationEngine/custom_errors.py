class InvalidPlaceIdError(ValueError):
    """Custom error for invalid place_id format."""
    pass

class ZeroResultsError(ValueError):
    """Custom error for when an API call returns zero results."""
    pass 