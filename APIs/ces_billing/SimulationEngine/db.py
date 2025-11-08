# File: Project/APIs/CES_Billing/SimulationEngine/db.py

import json
import os
from typing import Optional



# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "CESBillingDefaultDB.json",
)

# Load default DB on import using direct with open
with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)

def reset_db_for_tests():
    """Reset DB to a clean state for tests."""
    global DB
    DB.clear()
    DB.update({
        "end_of_conversation_status": {"escalate": {}, "fail": {}, "cancel": {}, "ghost": {}, "done":{}, "autopay": {}},
        "use_real_datastore": False,
        "billing_interactions": {},
        "default_start_flows": {},
        "bills": {},
    })

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f)

def load_state(filepath: str) -> None:
    """Load state from a JSON file.

    Args:
        filepath: Path to load the state file from.
    """
    global DB
    with open(filepath, "r") as f:
        new_data = json.load(f)
    # Instead of reassigning DB, update it in place:
    DB.clear()
    DB.update(new_data)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
