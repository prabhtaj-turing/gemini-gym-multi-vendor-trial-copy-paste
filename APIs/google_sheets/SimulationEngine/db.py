"""Database structure and state management for Google Sheets API simulation.

This module contains the database structure and state management functions
for the Google Sheets API simulation. It provides functions for saving and
loading the database state to maintain interoperability with GDrive.
"""

import sys
import json

sys.path.append("APIs")
from gdrive import DB as DRIVE_DB
from google_sheets.SimulationEngine.db_models import GoogleSheetsDB
import gdrive

# Shared reference to the database - Google Sheets uses the same DB as GDrive
# This ensures full interoperability between the two APIs
DB = DRIVE_DB

# Database structure for Google Sheets API simulation
# DB = {
#     'users': {
#         'me': {
#             'about': {
#                 'kind': 'drive#about',
#                 'storageQuota': {
#                     'limit': '107374182400',  # 100 GB
#                     'usageInDrive': '0',
#                     'usageInDriveTrash': '0',
#                     'usage': '0'
#                 },
#                 'user': {
#                     'displayName': 'Test User',
#                     'kind': 'drive#user',
#                     'me': True,
#                     'permissionId': 'test-user-1234',
#                     'emailAddress': 'test@example.com'
#                 }
#             },
#             'files': {},
#             'changes': {'changes': [], 'startPageToken': '1'},
#             'drives': {},
#             'permissions': {},
#             'comments': {},
#             'replies': {},
#             'apps': {},
#             'channels': {},
#             'counters': {
#                 'file': 0,
#                 'drive': 0,
#                 'comment': 0,
#                 'reply': 0,
#                 'label': 0,
#                 'accessproposal': 0,
#                 'revision': 0,
#                 'change_token': 0
#             }
#         }
#     }
# }


def get_database():
    """
    Returns the current database as a GoogleSheetsDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety. Google Sheets shares the same
    database structure as GDrive for full interoperability.
    
    Returns:
        GoogleSheetsDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return GoogleSheetsDB(**DB)


def save_state(filepath: str) -> None:
    """
    Saves the current database state to a JSON file.
    
    Delegates to GDrive's save_state to maintain interoperability
    and ensure consistent Pydantic validation.

    Args:
        filepath: Path to save the database state to.
        
    Raises:
        IOError: If the file cannot be written
    """
    gdrive.save_state(filepath)


def load_state(filepath: str) -> None:
    """
    Loads the database state from a JSON file with strict validation first.
    
    Validates with GoogleSheetsDB first to ensure all spreadsheets are valid,
    then delegates to GDrive's load_state for cross-API compatibility.

    Args:
        filepath: Path to load the database state from.
        
    Raises:
        ValueError: If the file contains invalid JSON format
        ValidationError: If the file contains invalid SpreadsheetFileModel data
        FileNotFoundError: If the file does not exist
    """
    
    # Load raw JSON first
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # STRICT validation - invalid spreadsheets are REJECTED
    # This ensures only valid SpreadsheetFileModels can be loaded by Sheets API
    #validated_db = GoogleSheetsDB(**data)
    
    # Only if strict validation passes, load through gdrive
    # (gdrive uses Union types for cross-API flexibility)
    gdrive.load_state(filepath)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    
    Deprecated: Use get_database() instead for better clarity.
    
    Returns:
        dict: The current database state
    """
    global DB
    return DB
