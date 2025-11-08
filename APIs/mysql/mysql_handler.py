"""
mysql_handler.py
===============

Helper layer on top of the global DuckDBManager instance.

Public helpers
--------------

- query(sql)
- get_resources_list()
- get_resource(uri)

Return envelopes
----------------

query
    { "content": [ { "type": "text", "text": "<string>" } ] }

get_resources_list
    { "resources":
        [ { "uri": "...", "mimeType": "application/json", "name": "..." } ] }

get_resource
    { "contents":
        [ { "uri": "...", "mimeType": "application/json", "text": "<json>" } ] }
"""

from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

import json
from typing import Any, Dict, List
from urllib.parse import quote

from sqlglot import parse_one

from .SimulationEngine.db import db_manager
from .SimulationEngine.utils import _query_type, _format_success, _tables_for_db, DateTimeEncoder, _validate_and_escape_identifier
from .SimulationEngine.custom_errors import InternalError

# ----------------------------------------------------------------------
# Public helpers
# ----------------------------------------------------------------------
@tool_spec(
    spec={
        'name': 'query',
        'description': 'Execute SQL and return a content envelope.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sql': {
                    'type': 'string',
                    'description': 'Non-empty SQL string.'
                }
            },
            'required': [
                'sql'
            ]
        }
    }
)
def query(sql: str) -> Dict[str, Any]:
    """
    Execute SQL and return a content envelope.

    Args:
        sql (str): Non-empty SQL string.

    Returns:
        Dict[str, Any]: A dictionary with the following structure:
            - content: List with one element
                - type (str): 'text'
                - text (str): result string (JSON rows or success message)

    Raises:
        ValueError: if `sql` is empty or not a string.
        InternalError: on execution error.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("`sql` must be a non-empty string")

    try:
        result = db_manager.execute_query(sql) # This is the patched db_manager
    except Exception as e:
        raise InternalError("An error occurred during query execution") from e

    qtype = _query_type(sql)

    body = None

    if qtype in {"insert", "update", "delete"}: # DML
        body = _format_success(sql, result)
    elif qtype in {"create", "alter", "drop", "truncatetable"}: # DDL
        body = _format_success(sql, result)
    elif qtype == "select": # SELECT queries
        # If 'data' key exists (even if list is empty), use it.
        # Otherwise (key missing or value is None), default to an empty list.
        body = json.dumps(result.get("data") or [], indent=2, cls=DateTimeEncoder)
    else: # Fallback for SHOW, PRAGMA, etc.
        body = json.dumps(result, indent=2, cls=DateTimeEncoder)

    return {"content": [{"type": "text", "text": body}]}


@tool_spec(
    spec={
        'name': 'get_resources_list',
        'description': 'Enumerate every user database and its tables.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_resources_list() -> Dict[str, Any]:
    """
    Enumerate every user database and its tables.

    Returns:
        Dict[str, Any]: A dictionary with the following structure
            - resources: List where each item has
                - uri (str): '<db>/<table>/schema'
                - mimeType (str): 'application/json'
                - name (str): '"<db>.<table>" database schema'
    """
    db_names = db_manager.get_db_names()

    resources = []
    for db_name in db_names:
        for table in _tables_for_db(db_name):
            resources.append(
                {
                    "uri": f"{quote(db_name)}/{quote(table)}/schema",
                    "mimeType": "application/json",
                    "name": f'"{db_name}.{table}" database schema',
                }
            )

    return {"resources": resources}


@tool_spec(
    spec={
        'name': 'get_resource',
        'description': 'Return column schema for a table resource.',
        'parameters': {
            'type': 'object',
            'properties': {
                'uri': {
                    'type': 'string',
                    'description': "Resource URI in the form '<db>/<table>/schema'."
                }
            },
            'required': [
                'uri'
            ]
        }
    }
)
def get_resource(uri: str) -> Dict[str, Any]:
    """
    Return column schema for a table resource.

    Args:
        uri (str): Resource URI in the form '<db>/<table>/schema'.

    Returns:
        Dict[str, Any]: A dictionary with the following structure
            - contents: List with one element having
                - uri (str): same URI passed in
                - mimeType (str): 'application/json'
                - text (str): JSON array of column objects, each with
                    - column_name (str)
                    - data_type (str)
                    - is_nullable (str)  ('YES' or 'NO')
                    - column_default (str or null)

    Raises:
        ValueError: if `uri` is malformed or contains invalid identifiers.
        InternalError: if an error occurs during query execution.
    """
    if not isinstance(uri, str) or uri.count("/") < 2:
        raise ValueError("`uri` must be in the form '<db>/<table>/schema'")

    db_name, table_name, tail = uri.split("/", 2)
    if tail != "schema":
        raise ValueError("`uri` must end with '/schema'")

    # Validate and escape database and table names to prevent SQL injection
    try:
        safe_db_name = _validate_and_escape_identifier(db_name, "database")
        safe_table_name = _validate_and_escape_identifier(table_name, "table")
    except ValueError as e:
        raise ValueError(f"Invalid URI: {str(e)}") from e

    try:
        # Use the safely escaped identifiers in SQL queries
        db_manager.execute_query(f"USE {safe_db_name}")
        describe_rows = db_manager.execute_query(f"DESCRIBE {safe_table_name}")["data"] or []
    except Exception as e:
        raise InternalError("An error occurred during query execution") from e

    cols = [
        {
            "column_name": name,
            "data_type": col_type,
            "is_nullable": null,
            "column_default": default,
        }
        for (name, col_type, null, _key, default, _extra) in describe_rows
    ]

    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(cols, indent=2, cls=DateTimeEncoder),
            }
        ]
    }