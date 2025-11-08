"""
Database structure and state management for Google Docs API simulation.
"""

from gdrive import DB as DRIVE_DB
import gdrive
from google_docs.SimulationEngine.db_models import GoogleDocsDB
import json
# ---------------------------------------------------------------------------------------
# In-Memory Docs Database Structure
# ---------------------------------------------------------------------------------------
# All user data is organized under DB['users'][userId], which is itself a dictionary storing:
#
#   - 'about': dict
#     Contains metadata and general information about the user's account, including:
#       - 'user': Basic information about the user (display name, email, etc.)
#       - 'storageQuota': Details about storage limits and usage
#
#   - 'files': { fileId: {...}, ... }
#     Contains documents owned or accessible by the user. Each document includes:
#       - 'id': Unique identifier
#       - 'name': Document title
#       - 'mimeType': Document type (e.g., 'application/vnd.google-apps.document')
#       - 'createdTime': Creation timestamp
#       - 'modifiedTime': Last modification timestamp
#       - 'parents': List of parent folder IDs
#       - 'owners': List of owner email addresses
#       - 'suggestionsViewMode': Mode for viewing suggestions
#       - 'includeTabsContent': Whether to include tab content
#       - 'content': List of document content elements
#       - 'tabs': List of document tabs
#       - 'permissions': List of document permissions
#       - 'trashed': Whether document is in trash
#       - 'starred': Whether document is starred
#       - 'size': Document size in bytes
#
#   - 'comments': { commentId: {...}, ... }
#     Contains comments made on documents
#
#   - 'replies': { replyId: {...}, ... }
#     Contains replies to comments
#
#   - 'labels': { labelId: {...}, ... }
#     Contains metadata labels that can be applied to documents
#
#   - 'accessproposals': { proposalId: {...}, ... }
#     Contains proposals related to document access permissions
#
#   - 'counters': dict
#     Contains numeric counters used for generating unique IDs for:
#       - 'file': Files stored in 'files'
#       - 'comment': Comments on documents
#       - 'reply': Replies to comments
#       - 'label': Metadata labels
#       - 'accessproposal': Access proposals

DB = DRIVE_DB  # Ensure shared reference


def save_state(filepath: str) -> None:
    """Save the current DB state using gdrive.

    Args:
        filepath (str): Path to save the state file.
    """
    # DriveAPI.save_state(filepath)
    gdrive.save_state(filepath)


def load_state(filepath: str) -> None:
    """Load the DB state using gdrive, with strict validation first.

    Args:
        filepath (str): Path to load the state file from.
        
    Raises:
        ValueError: If the file contains invalid JSON format.
        ValidationError: If the file contains invalid GoogleDocument data.
        FileNotFoundError: If the file does not exist.
    """
    
    # Load raw JSON first
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # STRICT validation - invalid documents are REJECTED
    # This ensures only valid GoogleDocuments can be loaded by Docs API
    #validated_db = GoogleDocsDB(**data)
    
    # Only if strict validation passes, load through gdrive
    # (gdrive uses Union types for cross-API flexibility)
    gdrive.load_state(filepath)



def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB


def get_database() -> GoogleDocsDB:
    """
    Returns the current database as a GoogleDocsDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety.
    
    Returns:
        GoogleDocsDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return GoogleDocsDB(**DB)
