"""
Database structure and state management for Google Docs API simulation.
"""

import json
from typing import Dict, Any, List
import sys
import os

# Add the APIs directory to the Python path
# sys.path.append(os.path.join(os.path.dirname(__file__), "../../../APIs"))
sys.path.append("APIs")
from home_assistant.SimulationEngine.db import DB as home_assistant_DB
import home_assistant

DB = home_assistant_DB  # Ensure shared reference
STATE_DICTS = {}
INFLUENCING_IDS = []
SERVED_IMAGES = {"EVENT_IMAGES" : list(), "STREAM_IMAGES" : list()}
ONGOING_STREAMS = []

def set_state_env(influencing_ids:List[str]):
    global INFLUENCING_IDS
    INFLUENCING_IDS = influencing_ids


def reset_state_env() -> None:
    """
    Reset the INFLUENCING_IDS.
    """
    global INFLUENCING_IDS
    INFLUENCING_IDS = []


def update_state_dict(map_dict: dict) -> None:
    """
    Update the STATE_DICTS with new dictionaries.

    Args:
        map_dict (dict): The dict containing the list of dictionaries to update the STATE_DICTS with.
    """
    global STATE_DICTS
    STATE_DICTS.clear()
    STATE_DICTS.update(map_dict)


def save_state(filepath: str) -> None:
    """Save the current DB state using gdrive.

    Args:
        filepath (str): Path to save the state file.
    """
    home_assistant.SimulationEngine.db.save_state(filepath)


def load_state(filepath: str) -> None:
    """Load the DB state using gdrive.

    Args:
        filepath (str): Path to load the state file from.
    """
    home_assistant.SimulationEngine.db.load_state(filepath)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
