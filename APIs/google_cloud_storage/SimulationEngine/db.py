from common_utils.print_log import print_log
import json
import os

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "GoogleCloudStorageDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))

# ---------------------------------------------------------------------------------------
# Persistence Class
# ---------------------------------------------------------------------------------------

def save_state(filepath: str) -> None:
    """Saves the current API state to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(DB, f, indent=4)

def load_state(filepath: str) -> None:
    """Loads the API state from a JSON file."""
    global DB
    try:
        with open(filepath, 'r') as f:
            DB.update(json.load(f))
    except FileNotFoundError:
        print_log(f"File not found: {filepath}. Starting with an empty state.")
        DB.update({"buckets": {}})

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
