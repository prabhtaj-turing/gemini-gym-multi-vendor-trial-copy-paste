# APIs/hubspot/SimulationEngine/db.py

import json
from typing import Dict, Any
import os

DB: Dict[str, Any] = {
    "events": {},
    "attendees": {},
    "transactional_emails": {},
    "templates": {},
    "contacts": {},
    "marketing_emails": {},
    "campaigns": {},
    "events": {},
    "attendees": {},
    "forms": {},
    "marketing_events": {},
    "subscription_definitions": [],
    "subscriptions": {},
}


# -------------------------------------------------------------------
# Persistence Helpers
# -------------------------------------------------------------------
def save_state(filepath: str) -> None:
    """Saves the current state of the API to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> None:
    """Loads the API state from a JSON file."""
    try:
        with open(filepath, "r") as f:
            global DB
            DB.update(json.load(f))
    except FileNotFoundError:
        pass

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
