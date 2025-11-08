"""
Database structure and state management for Google SAPConcur API simulation.

"""

import json
import os
from typing import Dict, Any

# ---------------------------------------------------------------------------------------
# In-Memory SAPConcur Database Structure
# ---------------------------------------------------------------------------------------
# The database organizes data hierarchically:
# DB['projects'][project_id]['datasets'][dataset_id]['tables'][table_id]
#
# Each table contains:
#   - 'schema': List of column definitions with:
#     - 'name': Column name
#     - 'type': Data type (STRING, INT64, TIMESTAMP, etc.)
#     - 'mode': NULLABLE, REQUIRED, or REPEATED
#     - 'description': Column description
#     - 'defaultValue': Default value for the column
#
#   - 'rows': List of data rows, each containing values matching the schema
#
#   - 'type': Type of table (e.g., 'TABLE')
#
#   - 'creation_time': Timestamp of when the table was created
#
#   - 'last_modified_time': Timestamp of last modification
#
#   - 'expiration_time': Timestamp when the table expires

DB: Dict[str, Any] = {
}



def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.
    
    Args:
        filepath (str): Path to save the state file.
            Must be a valid file path with write permissions.
    
    Raises:
        IOError: If the file cannot be written.
        json.JSONDecodeError: If the state cannot be serialized to JSON.
    
    Example:
        >>> save_state("./state.json")
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str = '../../DBs/SAPConcurDefaultDB.json') -> None:
    """Load state from a JSON file.
    """
    global DB
    with open(filepath, 'r') as f:
        new_data = json.load(f)
        DB.clear()
        DB.update(new_data)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB

def reset_db() -> None:
    """Reset the database to an empty state.
    
    This function clears all data from the database, useful for testing.
    """
    global DB
    DB.clear()
