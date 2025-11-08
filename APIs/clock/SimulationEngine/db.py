import json
import os
import sys

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "ClockDefaultDB.json",
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

def reset_db() -> None:
    """Reset the DB to the default state by loading from the default database file."""
    global DB
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_db_path = os.path.join(current_dir, "../../../DBs/ClockDefaultDB.json")
    if os.path.exists(default_db_path):
        with open(default_db_path, "r", encoding="utf-8") as f:
            default_data = json.load(f)
            DB.clear()
            DB.update(default_data)
    else:
        # Fallback to the current structure if default file doesn't exist
        DB.clear()
        DB.update({
            "alarms": {},
            "timers": {},
            "stopwatch": {
                "state": "STOPPED",
                "start_time": None,
                "elapsed_time": 0,
                "laps": []
            },
            "settings": {
                "default_alarm_sound": "default",
                "default_timer_sound": "default",
                "snooze_duration": 600,
                "alarm_volume": 0,
                "timer_volume": 0.7,
                "time_format": "12_hour",
                "show_seconds": "false"
            }
        }) 

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
