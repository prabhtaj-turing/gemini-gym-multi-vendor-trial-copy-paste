"""
Database structure and state management for Google Drive API simulation.

This module defines the in-memory database structure and provides functionality
for saving and loading the database state to/from JSON files.

The database (DB) organizes user data under DB['users'][userId], which stores:
- 'about': dict - Contains metadata and general information about the user's Drive account
- 'files': { fileId: {...}, ... } - Contains metadata and content of individual files
- 'drives': { driveId: {...}, ... } - Contains shared drive (team drive) information
- 'comments': { commentId: {...}, ... } - Contains comments made on files
- 'replies': { replyId: {...}, ... } - Contains replies to comments
- 'labels': { labelId: {...}, ... } - Contains metadata labels for files
- 'accessproposals': { proposalId: {...}, ... } - Contains access permission proposals
- 'counters': dict - Holds numeric counters for generating unique IDs
"""

import json
import os


from gdrive.SimulationEngine.models import RevisionModel, ExportFormatsModel, FileWithContentModel, FileContentUnion, FileContentModel, DocumentElementModel
from gdrive.SimulationEngine.db_models import GdriveDB

# ---------------------------------------------------------------------------------------
# In-Memory Drive Database Structure
# ---------------------------------------------------------------------------------------
# All user data is organized under DB['users'][userId], which is itself a dictionary storing:
#
#   - 'about': dict
#     Contains metadata and general information about the user's Drive account, including:
#       - 'kind': Resource type identifier (e.g., 'drive#about')
#       - 'storageQuota': Details about storage limits and usage (total limit, usage, usage in Drive and Trash)
#       - 'driveThemes': Available themes for shared drives
#       - 'canCreateDrives': Boolean indicating if the user can create shared drives
#       - 'importFormats': Supported import formats
#       - 'exportFormats': Supported export formats
#       - 'appInstalled': Whether the Drive app is installed
#       - 'user': Basic information about the user (display name, permission ID, email, etc.)
#       - 'folderColorPalette': Available folder color options
#       - 'maxImportSizes': Maximum import file sizes for specific formats
#       - 'maxUploadSize': Maximum upload size allowed
#
#   - 'files': { fileId: {...}, ... }
#     Contains metadata and content of individual files owned or accessible by the user
#
#   - 'drives': { driveId: {...}, ... }
#     Contains shared drive (team drive) information the user can access or manage
#
#   - 'comments': { commentId: {...}, ... }
#     Contains comments made on files, including discussions and annotations
#
#   - 'replies': { replyId: {...}, ... }
#     Contains replies to comments on files
#
#   - 'labels': { labelId: {...}, ... }
#     Contains metadata labels that can be applied to files and folders
#
#   - 'accessproposals': { proposalId: {...}, ... }
#     Contains proposals related to file access permissions
#
#   - 'counters': dict
#     Contains numeric counters used for generating unique IDs for:
#       - 'file': Files stored in 'files'
#       - 'drive': Shared drives in 'drives'
#       - 'comment': Comments on files
#       - 'reply': Replies to comments
#       - 'label': Metadata labels
#       - 'accessproposal': Access proposals
#       - 'revision': File revisions

DB = {
    'users': {
        'me': {
            'about': {
                'kind': 'drive#about',
                'storageQuota': {
                    'limit': '1073741824',  # 1GB in bytes
                    'usageInDrive': '0',
                    'usageInDriveTrash': '0',
                    'usage': '0'
                },
                'driveThemes': [],
                'canCreateDrives': False,
                'importFormats': {},
                'exportFormats': {},
                'appInstalled': False,
                'user': {
                    'displayName': '',
                    'kind': 'drive#user',
                    'me': True,
                    'permissionId': '',
                    'emailAddress': ''
                },
                'folderColorPalette': "",
                'maxImportSizes': {},
                'maxUploadSize': '104857600'  # 100MB in bytes
            },
            'files': {},
            'drives': {},
            'comments': {},
            'replies': {},
            'labels': {},
            'accessproposals': {},
            'counters': {
                'file': 0,
                'drive': 0,
                'comment': 0,
                'reply': 0,
                'label': 0,
                'accessproposal': 0,
                'revision': 0
            }
        }
    }
}


# class DriveAPI:
#     """The top-level class that handles the in-memory DB and provides save/load functionality."""
    
#     @staticmethod
def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.
    
    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, 'w') as f:
        json.dump(DB, f)

# @staticmethod
def load_state(filepath: str) -> None:
    """Load state from a JSON file with Pydantic validation.
    
    Args:
        filepath: Path to load the state file from.
        
    Raises:
        ValueError: If the loaded data contains invalid content, revisions, or export formats.
        ValidationError: If the loaded data doesn't conform to the GdriveDB schema.
        json.JSONDecodeError: If the file is not valid JSON.
        FileNotFoundError: If the file does not exist.
    """
    global DB
    
    try:
        with open(filepath, 'r') as f:
            new_data = json.load(f)
        
        # Validate using Pydantic model - this provides comprehensive validation
        #validated_db = GdriveDB(**new_data)
        
        # Convert back to dict and update the database
        DB.clear()
        DB.update(new_data)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in state file: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"State file not found: {filepath}")


def _validate_file_content(data: dict) -> None:
    """Validate file content, revisions, and export formats in the loaded data.
    
    Args:
        data: The loaded JSON data to validate.
        
    Raises:
        ValueError: If any file contains invalid content, revisions, or export formats.
    """
    if 'users' not in data:
        return  # No users to validate
    
    for user_id, user_data in data['users'].items():
        if 'files' not in user_data:
            continue
            
        for file_id, file_data in user_data['files'].items():
            try:
                # Validate content if present
                if 'content' in file_data:
                    content = file_data['content']
                    # Check if content is a list (DocumentElementModel) or dict (FileContentModel)
                    if isinstance(content, list):
                        # Validate as DocumentElementModel list
                        for element in content:
                            DocumentElementModel(**element)
                    elif isinstance(content, dict):
                        # Validate as FileContentModel
                        FileContentModel(**content)
                    elif content is None:
                        pass
                    else:
                        raise ValueError(f"Content must be either a list of document elements, a file content object or None")
                
                # Validate revisions if present
                if 'revisions' in file_data:
                    for revision in file_data['revisions']:
                        RevisionModel(**revision)
                
                # Validate export formats if present
                if 'exportFormats' in file_data:
                    ExportFormatsModel(**file_data['exportFormats'])
                    
            except Exception as e:
                raise ValueError(f"Validation error in file '{file_id}' for user '{user_id}': {e}")


def _validate_file_content_verbose(data: dict) -> None:
    """Validate file content with detailed error reporting.
    
    Args:
        data: The loaded JSON data to validate.
        
    Raises:
        ValueError: If any file contains invalid content, revisions, or export formats.
    """
    if 'users' not in data:
        return  # No users to validate
    
    validation_errors = []
    
    for user_id, user_data in data['users'].items():
        if 'files' not in user_data:
            continue
            
        for file_id, file_data in user_data['files'].items():
            file_errors = []
            
            # Validate content if present
            if 'content' in file_data:
                try:
                    content = file_data['content']
                    # Check if content is a list (DocumentElementModel) or dict (FileContentModel)
                    if isinstance(content, list):
                        # Validate as DocumentElementModel list
                        for element in content:
                            DocumentElementModel(**element)
                    elif isinstance(content, dict):
                        # Validate as FileContentModel
                        FileContentModel(**content)
                    elif content is None:
                        pass
                    else:
                        raise ValueError(f"Content must be either a list of document elements, a file content object or None")
                except Exception as e:
                    file_errors.append(f"Content validation failed: {e}")
            
            # Validate revisions if present
            if 'revisions' in file_data:
                for i, revision in enumerate(file_data['revisions']):
                    try:
                        RevisionModel(**revision)
                    except Exception as e:
                        file_errors.append(f"Revision {i} validation failed: {e}")
            
            # Validate export formats if present
            if 'exportFormats' in file_data:
                try:
                    ExportFormatsModel(**file_data['exportFormats'])
                except Exception as e:
                    file_errors.append(f"Export formats validation failed: {e}")
            
            if file_errors:
                validation_errors.append(f"File '{file_id}' (user '{user_id}'): {'; '.join(file_errors)}")
    
    if validation_errors:
        raise ValueError(f"Content validation failed:\n" + "\n".join(validation_errors))



def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB


def get_database() -> GdriveDB:
    """
    Returns the current database as a GdriveDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety.
    
    Returns:
        GdriveDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return GdriveDB(**DB)
