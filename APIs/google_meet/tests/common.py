import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google_meet import DB


def reset_db():
    """
    Reset the database to a clean, empty state for testing.

    This function clears all existing data and initializes an empty database structure
    with all required collections. Each collection is initialized as an empty dictionary.
    """
    # Define the empty database structure
    empty_db = {
        "conferenceRecords": {},
        "recordings": {},
        "transcripts": {},
        "entries": {},
        "participants": {},
        "participantSessions": {},
        "spaces": {},
    }

    # Clear existing data and update with empty structure
    DB.clear()
    DB.update(empty_db)
