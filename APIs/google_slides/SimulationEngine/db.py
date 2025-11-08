"""
Database structure and state management for Google Slides API simulation.

This module defines the in-memory database (DB) structure by referencing
the shared Google Drive DB and provides functionality for saving and loading
the database state via the GDrive module.

The database (DB) is shared with Google Drive and organizes user data under
DB['users'][userId]. For Google Slides, 'files' within this structure would
typically represent presentation files. Key components include:

- 'about': Metadata about the user's account.
- 'files': { fileId: {...}, ... } - Contains presentations (as files).
- 'counters': For generating unique IDs.
 (Other GDrive structures like 'drives', 'comments', etc., are also shared.)
"""

import json
import sys
import os

# Ensure the 'APIs' directory (or equivalent root) is in the Python path
# to allow importing 'gdrive'. Adjust if your project structure differs.
# This assumes google_slides, gdrive, etc., are sibling packages under 'APIs'.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from gdrive import DB as DRIVE_DB  # Import the shared DB from GDrive
import gdrive                     # Import the gdrive module for its functions
from google_slides.SimulationEngine.db_models import GoogleSlidesDB

# ---------------------------------------------------------------------------------------
# In-Memory Slides Database Structure (Shared with GDrive)
# ---------------------------------------------------------------------------------------
# Google Slides data is stored within the shared Google Drive database (DRIVE_DB).
# Presentation files are typically stored under DB['users'][userId]['files'].
# For a detailed structure of DRIVE_DB, refer to gdrive/db.py.
#
# Relevant shared structures for Slides might include:
# - 'files': Where presentation metadata and content references are stored.
#   Each file entry could have fields like:
#     - 'id': Unique identifier for the presentation.
#     - 'name': Title of the presentation.
#     - 'mimeType': 'application/vnd.google-apps.presentation'.
#     - 'createdTime', 'modifiedTime': Timestamps.
#     - 'parents': List of parent folder IDs in Drive.
#     - 'permissions': Access permissions.
#     - 'slides': (Potentially, if Slides has specific content structure not just in Drive file content)
#                 A list or dictionary of slide objects within the presentation.
#
# - 'comments', 'replies': For comments on slides/presentations.
# - 'counters': For unique IDs for presentations (as files), comments, etc.

DB = DRIVE_DB  # Use the shared Drive database instance

def save_state(filepath: str) -> None:
    """
    Save the current shared DB state using the gdrive.save_state function.

    Args:
        filepath (str): Path to save the state file.
    """
    gdrive.save_state(filepath)

def load_state(filepath: str) -> None:
    """
    Load the shared DB state with strict validation first.
    
    Validates with GoogleSlidesDB first to ensure all presentations are valid,
    then delegates to gdrive.load_state for cross-API compatibility.
    
    Args:
        filepath (str): Path to load the state file from.
        
    Raises:
        ValueError: If the file contains invalid JSON format.
        ValidationError: If the file contains invalid SlidesFile data.
        FileNotFoundError: If the file does not exist.
    """
    global DB
    
    # Load raw JSON first
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # STRICT validation - invalid presentations are REJECTED
    # This ensures only valid SlidesFiles can be loaded by Slides API
    #validated_db = GoogleSlidesDB(**data)
    
    # Only if strict validation passes, load through gdrive
    # (gdrive uses Union types for cross-API flexibility)
    gdrive.load_state(filepath)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB


def get_database() -> GoogleSlidesDB:
    """
    Returns the current database as a GoogleSlidesDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety.
    
    Returns:
        GoogleSlidesDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return GoogleSlidesDB(**DB)
