"""
Custom error classes for the contacts API.
"""

class ValidationError(Exception):
    """Exception raised for input validation errors."""
    pass


class ContactsCollectionNotFoundError(Exception):
    """Exception raised when the contacts collection doesn't exist in the database."""
    pass

class ContactNotFoundError(Exception):
    """Exception raised when a contact is not found."""
    pass

class DataIntegrityError(Exception):
    """Exception raised for data integrity issues, like validation failures on fetched data."""
    pass