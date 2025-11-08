# APIs/tiktok/SimulationEngine/db.py
import json
import os

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "TikTokDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))


def save_state(filepath: str):
    """
    Saves the current state of the database to a JSON file.

    Args:
        filepath (str): The path to the JSON file where the state should be saved.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=4)


def load_state(filepath: str) -> None:
    """
    Loads the database state from a JSON file.

    Args:
        filepath (str): The path to the JSON file to load the state from.
    """
    global DB
    try:
        with open(filepath, "r") as f:
            DB.update(json.load(f))
    except FileNotFoundError:
        DB.clear()  # Initialize to empty if file doesn't exist



def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
