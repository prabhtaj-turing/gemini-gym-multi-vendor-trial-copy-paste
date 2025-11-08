import json
from typing import Dict, Any
import os

# Global in-memory "database" following the provided structure.
DB: Dict[str, Any] = {
    "people": {},
    "organizations": {},
    "organizationAcls": {},
    "posts": {},
    "next_person_id": 0,
    "next_org_id": 0,
    "next_acl_id": 0,
    "next_post_id": 0,
    "current_person_id": ""
}

# Persistence functions
def save_state(filepath: str) -> None:
    """
    Save the current state (DB) to a JSON file.
    """
    with open(filepath, 'w') as f:
        json.dump(DB, f)

def load_state(filepath: str) -> None:
    global DB
    with open(filepath, 'r') as f:
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
