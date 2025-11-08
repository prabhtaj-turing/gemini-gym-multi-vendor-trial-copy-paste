# APIs/youtube/SimulationEngine/db.py
import json
import os

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "YoutubeDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))

# -------------------------------------------------------------------
# Persistence Helpers
# -------------------------------------------------------------------


def save_state(filepath: str) -> None:
    """Saves the in-memory DB to a file."""
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> object:
    """Loads the DB from a file."""
    global DB
    with open(filepath, "r") as f:
        state = json.load(f)
    # Instead of reassigning DB, update it in place:
    DB.clear()
    DB.update(state)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
