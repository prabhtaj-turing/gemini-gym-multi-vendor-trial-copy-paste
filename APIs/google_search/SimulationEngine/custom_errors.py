"""
Custom error classes for the google_search API.
"""

class ValidationError(Exception):
    """Exception raised for input validation errors."""
    pass

class SearchError(Exception):
    """Exception raised when a search operation fails."""
    pass

class WebContentNotFoundError(Exception):
    """Exception raised when web content is not found in the database."""
    pass

class SearchIndexError(Exception):
    """Exception raised when there are issues with the search index."""
    pass

class DataIntegrityError(Exception):
    """Exception raised for data integrity issues, like validation failures on fetched data."""
    pass
