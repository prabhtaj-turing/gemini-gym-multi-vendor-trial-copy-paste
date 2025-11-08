from __future__ import annotations

from typing import Any, Dict, List
import json
import datetime

import duckdb
from sqlglot import parse_one
import re
from urllib.parse import quote, unquote


from .db import db_manager

# ----------------------------------------------------------------------
# JSON Serialization
# ----------------------------------------------------------------------
class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that converts datetime objects to ISO format strings.
    
    This encoder handles datetime.datetime, datetime.date, and datetime.time objects
    by converting them to their ISO format string representation, which is compatible
    with JSON and can be parsed by most datetime libraries.
    """
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        return super().default(obj)

# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _query_type(sql: str) -> str: # pragma: no cover
    """Return first SQL keyword in lower-case (`select`, `insert`, …)."""
    try:
        expr = parse_one(sql, error_level="ignore")
        if expr:
            return expr.key.lower()
    except Exception:
        pass
    return sql.lstrip().split(None, 1)[0].lower()


def _current_schema() -> str: # pragma: no cover
    """Return the currently selected database alias, or 'default'."""
    alias = db_manager._current_db_alias  # pylint: disable=protected-access
    return alias or "default"


def _format_success(sql: str, result: Dict[str, Any]) -> str: # pragma: no cover
    """Generate human success strings identical to the TS MCP helpers."""
    qtype = _query_type(sql)
    schema = _current_schema()
    affected = result.get("affected_rows", 0)

    if qtype == "insert":
        last_id = affected if affected else 0
        return (
            f"Insert successful on schema '{schema}'. "
            f"Affected rows: {affected}, Last insert ID: {last_id}"
        )
    if qtype == "update":
        changed = affected
        return (
            f"Update successful on schema '{schema}'. "
            f"Affected rows: {affected}, Changed rows: {changed}"
        )
    if qtype == "delete":
        return f"Delete successful on schema '{schema}'. Affected rows: {affected}"
    return f"DDL operation successful on schema '{schema}'."


def _tables_for_db(db_name: str) -> List[str]: # pragma: no cover
    """Return table names for `db_name` and restore previous context."""
    # Store the current context before switching
    original_context = db_manager._current_db_alias  # pylint: disable=protected-access
    try:
        
        # Switch to the target database
        db_manager.execute_query(f"USE {db_name}") 
        
        # Query tables from the current database context
        # Using SHOW TABLES is more reliable than information_schema with catalog filtering
        result = db_manager.execute_query("SHOW TABLES")
        rows = result.get("data", []) or []
        return [r[0] for r in rows]
        
    except duckdb.CatalogException:
        # Database doesn't exist or has no tables
        # NOTE: Unlike MySQL, DuckDB's duckdb_databases() doesn't list empty attached databases because it only tracks databases with at least one table or view.
        return []
    except Exception:
        # Any other error (including ValueError), return empty list
        return []
    finally:
        # Always restore the original context if it was changed
        if original_context and original_context != db_manager._current_db_alias:
            try:
                db_manager.execute_query(f"USE {original_context}")
            except (ValueError, duckdb.CatalogException):
                # If we can't restore original context, at least try to go to main
                try:
                    main_alias = db_manager._main_db_alias  # pylint: disable=protected-access
                    if main_alias:
                        db_manager.execute_query(f"USE {main_alias}")
                except (ValueError, duckdb.CatalogException):
                    pass  # Give up on context restoration
                  
def _validate_and_escape_identifier(identifier: str, identifier_type: str = "identifier") -> str:
    """
    Validate and safely escape a SQL identifier (database or table name).
    
    Args:
        identifier (str): The identifier to validate and escape
        identifier_type (str): Type of identifier for error messages ('database' or 'table')
    
    Returns:
        str: Safely escaped identifier
    
    Raises:
        ValueError: If identifier contains invalid characters or patterns
    """
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError(f"{identifier_type} name cannot be empty")
    
    # URL decode in case the identifier was URL-encoded
    decoded_identifier = unquote(identifier)
    
    # Character-based patterns: check for exact character sequences
    character_patterns = [
        ';',           # Statement separator 
        '--',          # SQL comments
        '/*',          # Block comments start
        '*/',          # Block comments end
    ]
    
    # Keyword-based patterns: check as whole words only to avoid false positives
    keyword_patterns = [
        'DROP',        # Dangerous keywords
        'DELETE',
        'UPDATE',
        'INSERT',
        'CREATE',
        'ALTER',
        'TRUNCATE',
        'EXEC',
        'EXECUTE'
    ]
    
    # Check for character-based patterns (exact substring match)
    for pattern in character_patterns:
        if pattern in decoded_identifier:
            raise ValueError(f"Invalid {identifier_type} name: contains forbidden pattern '{pattern}'")
    
    # Check for keyword-based patterns (whole word match only)
    identifier_upper = decoded_identifier.upper()
    for keyword in keyword_patterns:
        if re.search(rf'\b{re.escape(keyword)}\b', identifier_upper):
            raise ValueError(f"Invalid {identifier_type} name: contains forbidden keyword '{keyword}'")
    
    # Validate identifier format - should only contain alphanumeric, underscore, dash, dot
    # This is a conservative approach for security
    if not re.match(r'^[a-zA-Z0-9_.-]+$', decoded_identifier):
        raise ValueError(f"Invalid {identifier_type} name: contains invalid characters. Only letters, numbers, underscore, dot, and dash are allowed")
    
    # Additional length check
    if len(decoded_identifier) > 64:  # MySQL identifier length limit
        raise ValueError(f"{identifier_type} name too long (max 64 characters)")
    
    # Escape the identifier by wrapping in backticks and escaping any existing backticks
    escaped_identifier = '`' + decoded_identifier.replace('`', '``') + '`'
    
    return escaped_identifier                  
