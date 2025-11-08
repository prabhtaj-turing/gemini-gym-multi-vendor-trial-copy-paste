# tests/common.py
import os
import json
from google_people import DB


def reset_db():
    """Reset the database to the default state with sample data."""
    # Try to load the default database file
    db_path = os.path.join(os.path.dirname(__file__), "../../../DBs/GooglePeopleDefaultDB.json")
    
    if os.path.exists(db_path):
        # Load the default database with sample data
        with open(db_path, 'r') as f:
            default_db = json.load(f)
        DB.clear()
        DB.update(default_db)
    else:
        # Fallback to empty database if default file not found
        new_db = {
            "people": {},
            "contactGroups": {},
            "otherContacts": {},
            "directoryPeople": {}
        }
        DB.clear()
        DB.update(new_db) 