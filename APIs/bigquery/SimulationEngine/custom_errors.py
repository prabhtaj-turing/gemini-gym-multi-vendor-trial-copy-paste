"""
Error handling module for BigQuery API simulation.

This module defines custom exceptions used throughout the BigQuery API simulation.
These exceptions help provide clear error messages and proper error handling for
various scenarios that might occur during query execution and database operations.

Related Modules:
    - query_executor.py: Uses these exceptions for query execution errors
    - utils.py: Uses these exceptions for utility function errors
    - db.py: Uses these exceptions for database operation errors
"""

class BigQueryClientError(Exception):
    """Base exception for errors originating from the BigQuery client or interactions.
    
    This is the parent class for all BigQuery-related exceptions in the simulation.
    It provides a common base for error handling and allows catching all BigQuery
    related errors with a single exception handler.
    
    Example:
        try:
            execute_query("SELECT * FROM table")
        except BigQueryClientError as e:
            print(f"BigQuery error occurred: {e}")
    """
    pass


class InvalidQueryError(Exception):
    """
    Raised when a BigQuery SQL query is syntactically invalid or contains
    semantic errors that prevent it from being executed.

    Common scenarios:
        - Malformed SQL syntax
        - References to non-existent tables or columns
        - Invalid data type operations
        - Unsupported query types (e.g., non-SELECT queries)

    Example:
        try:
            execute_query("SELECT * FROM nonexistent_table")
        except InvalidQueryError as e:
            print(f"Invalid query: {e}")
    """
    pass

class InvalidInputError(BigQueryClientError):
    """
    Raised when the input provided to a BigQuery operation is invalid.
    This includes malformed table names, invalid characters in identifiers,
    or other input validation failures.
    """
    pass

class ProjectNotFoundError(BigQueryClientError):
    """
    Raised if the Google Cloud Project configured for the
    BigQuery client does not exist or is inaccessible.
    """
    pass

class DatasetNotFoundError(BigQueryClientError):
    """
    Raised if the operation is scoped to a dataset that does
    not exist (less common for a general list-tables unless a default
    dataset is assumed and not found).
    """
    pass

class TableNotFoundError(BigQueryClientError):
    """
    Raised when a requested table does not exist or is not accessible
    within the specified project and dataset.
    """
    pass

class InvalidDateTimeFormatError(BigQueryClientError):
    """
    Raised when a datetime string is not in the expected format.
    """
    pass