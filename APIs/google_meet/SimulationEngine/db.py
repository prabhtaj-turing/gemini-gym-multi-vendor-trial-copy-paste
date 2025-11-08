import json
import os


"""
Database structure for the Meet API simulation.
"""

# In-Memory Database Structure for Conference Records and Related Data
# This database stores conference records, recordings, transcripts, entries, participants, and participant sessions.

DB = {
    "conferenceRecords": {},
    "recordings": {},
    "transcripts": {},
    "entries": {},
    "participants": {},
    "participantSessions": {},
    "spaces": {} 
} 


def save_state(filepath: str) -> None:
    """
    Saves the current state of the in-memory database to a JSON file.

    Args:
        filepath (str): The path to the JSON file where the state should be saved.
    """
    with open(filepath, 'w') as f:
        json.dump(DB, f, indent=4)

def load_state(filepath: str) -> None:
    """
    Loads the state of the in-memory database from a JSON file.

    Args:
        filepath (str): The path to the JSON file from which the state should be loaded.
    """
    global DB
    try:
        with open(filepath, 'r') as f:
            DB.update(json.load(f))
    except FileNotFoundError:
        raise FileNotFoundError(f"State file {filepath} not found. Starting with default state.")

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB

def reset_db():
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()


# Load default data if available
def load_default_data():
    """Load default database from DBs directory"""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "DBs",
        "GoogleMeetDefaultDB.json"
    )
    if os.path.exists(db_path):
        load_state(db_path)