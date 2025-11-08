import sys
import os
import json

# Shared reference to the database
DB = {}

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.
    
    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, 'w') as f:
        json.dump(DB, f)

def load_state(filepath: str) -> None:
    """Load state from a JSON file.
    
    Args:
        filepath: Path to load the state file from.
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
