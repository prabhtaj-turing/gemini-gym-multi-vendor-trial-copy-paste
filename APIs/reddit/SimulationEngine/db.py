# reddit/SimulationEngine/db.py

import json
import os

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "RedditDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))

###############################################################################
# HELPER FUNCTIONS FOR PERSISTENCE
###############################################################################
# def save_state(filepath: str) -> None:
#     """
#     Save the current DB state to a JSON file at `filepath`.
#     """
#     with open(filepath, 'w', encoding='utf-8') as f:
#         json.dump(DB, f, indent=2)


# def load_state(filepath: str) -> None:
#     """
#     Load the DB state from a JSON file at `filepath`.
#     Overwrites the current in-memory DB with the loaded content.
#     """
#     global DB
#     if not os.path.isfile(filepath):
#         return
#     with open(filepath, 'r', encoding='utf-8') as f:
#         loaded = json.load(f)
#     DB = loaded


def save_state(filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> None:
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
