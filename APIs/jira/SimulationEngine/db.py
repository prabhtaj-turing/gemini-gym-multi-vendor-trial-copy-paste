import json
import os

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "JiraDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))

###############################################################################
def save_state(filepath: str) -> None:
    """Save the current DB state to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str) -> None:
    """Load DB state from a JSON file, replacing the current in-memory DB."""
    global DB
    if os.path.isfile(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            DB.update(json.load(f))

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
