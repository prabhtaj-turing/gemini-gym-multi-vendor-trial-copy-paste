import unittest
import os
import json
import builtins
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError
from common_utils.error_handling import get_package_error_mode
from .. import ( DB, _ensure_user, get_file_metadata_or_content )
from gdrive.SimulationEngine.custom_errors import InvalidPageSizeError, UserNotFoundError
from unittest.mock import patch
from gdrive.SimulationEngine.db import DB as SimulationDB

# Global DB for testing
DB = {}

# Mock functions
def _ensure_user(userId):
    """Minimal mock for _ensure_user, ensuring necessary DB structure."""
    if "users" not in DB:
        DB["users"] = {}
    if userId not in DB["users"]:
        DB["users"][userId] = {}
    if "drives" not in DB["users"][userId]:
        DB["users"][userId]["drives"] = {}
    if "about" not in DB["users"][userId]:
         DB["users"][userId]["about"] = {
            "kind": "drive#about",
            "storageQuota": {"limit": "107374182400", "usageInDrive": "0", "usageInDriveTrash": "0", "usage": "0"},
            "canCreateDrives": True, "user": {"emailAddress": "me@example.com"},
        }
    if "files" not in DB["users"][userId]: 
        DB["users"][userId]["files"] = {}
    if "comments" not in DB["users"][userId]: 
        DB["users"][userId]["comments"] = {}

def _parse_query(q_str):
    """Minimal mock for _parse_query."""
    if "error_on_parse" in q_str:
        raise ValueError("Invalid query string format (mocked error)")
    return []

def _apply_query_filter(drives_list, conditions):
    """Minimal mock for _apply_query_filter."""
    if not conditions:
        return drives_list
    return drives_list

class TestGetFileMetadataOrContent(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset DB and ensure user 'me' exists before each test."""
        # Clear and initialize the SimulationDB
        SimulationDB.clear()
        SimulationDB.update({
            "users": {
                "me": {
                    "files": {
                        "file123": {
                            "id": "file123",
                            "name": "My Test Document",
                            "mimeType": "application/vnd.google-apps.document",
                            "kind": "drive#file",
                            "parents": ["folder456"],
                            "createdTime": "2023-01-01T10:00:00Z",
                            "modifiedTime": "2023-01-02T12:00:00Z",
                            "trashed": False,
                            "starred": True,
                            "owners": ["me@example.com"],
                            "size": "1024",
                            "permissions": [{"id": "perm1", "type": "user", "role": "owner"}]
                        }
                    },
                    "about": {
                        "kind": "drive#about",
                        "storageQuota": {
                            "limit": "107374182400",
                            "usageInDrive": "0",
                            "usageInDriveTrash": "0",
                            "usage": "0"
                        },
                        "canCreateDrives": True,
                        "user": {"emailAddress": "me@example.com"}
                    }
                }
            }
        })
        _ensure_user("me")

    def test_get_existing_file_valid_id(self):
        """Test retrieving an existing file with a valid fileId."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], file_id)
        self.assertEqual(result["name"], "My Test Document")
        self.assertIn("mimeType", result)

    def test_get_file_not_found(self):
        """Test retrieving a non-existent file; should return None."""
        non_existent_file_id = "file_not_found_id"
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=FileNotFoundError,
            expected_message=f"File with ID '{non_existent_file_id}' not found.",
            fileId=non_existent_file_id
        )

    def test_invalid_file_id_type_integer(self):
        """Test that an integer fileId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId=12345
        )

    def test_invalid_file_id_type_none(self):
        """Test that a None fileId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=ValueError,
            expected_message="fileId cannot be None",
            fileId=None
        )

    def test_invalid_file_id_type_list(self):
        """Test that a list fileId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId=["id1"]
        )

    def test_empty_string_file_id(self):
        """Test behavior with an empty string fileId (should return None if not found)."""
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=ValueError,
            expected_message="fileId cannot be empty or consist only of whitespace.",
            fileId=""
        )

    def test_none_file_id(self):
        """Test behavior with a None fileId (should return None if not found)."""
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=ValueError,
            expected_message="fileId cannot be None",
            fileId=None
        )

    def test_user_not_found_error_if_user_structure_is_missing(self):
        """Test that UserNotFoundError is raised if user structure is missing."""
        SimulationDB.clear()
        # Don't add any users to the DB to trigger the UserNotFoundError

        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID 'me' not found. Cannot perform read operation for non-existent user.",
            fileId="anyFileId"
        )

    def test_metadata_completeness_created_time(self):
        """Test that createdTime field is properly populated and not empty."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        
        # Verify createdTime is present and not empty
        self.assertIn("createdTime", result)
        self.assertIsNotNone(result["createdTime"])
        self.assertNotEqual(result["createdTime"], "")
        self.assertIsInstance(result["createdTime"], str)
        
        # Verify it's a valid timestamp format
        from datetime import datetime
        try:
            datetime.fromisoformat(result["createdTime"].replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"createdTime '{result['createdTime']}' is not a valid ISO timestamp")

    def test_metadata_completeness_modified_time(self):
        """Test that modifiedTime field is properly populated and not empty."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        
        # Verify modifiedTime is present and not empty
        self.assertIn("modifiedTime", result)
        self.assertIsNotNone(result["modifiedTime"])
        self.assertNotEqual(result["modifiedTime"], "")
        self.assertIsInstance(result["modifiedTime"], str)
        
        # Verify it's a valid timestamp format
        from datetime import datetime
        try:
            datetime.fromisoformat(result["modifiedTime"].replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"modifiedTime '{result['modifiedTime']}' is not a valid ISO timestamp")

    def test_metadata_completeness_size(self):
        """Test that size field is properly populated and not 0."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        
        # Verify size is present and not 0
        self.assertIn("size", result)
        self.assertIsNotNone(result["size"])
        self.assertNotEqual(result["size"], "0")
        self.assertNotEqual(result["size"], 0)
        
        # Verify it's a valid size (string representation of number)
        self.assertIsInstance(result["size"], str)
        try:
            size_value = int(result["size"])
            self.assertGreater(size_value, 0)
        except ValueError:
            self.fail(f"size '{result['size']}' is not a valid integer")

    def test_metadata_completeness_parents(self):
        """Test that parents field is properly populated and not empty list."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        
        # Verify parents is present and not empty
        self.assertIn("parents", result)
        self.assertIsNotNone(result["parents"])
        self.assertIsInstance(result["parents"], list)
        self.assertGreater(len(result["parents"]), 0, "parents list should not be empty")
        
        # Verify all parent IDs are strings
        for parent_id in result["parents"]:
            self.assertIsInstance(parent_id, str)
            self.assertNotEqual(parent_id, "")

    def test_metadata_completeness_permissions(self):
        """Test that permissions field is properly populated and not empty list."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        
        # Verify permissions is present and not empty
        self.assertIn("permissions", result)
        self.assertIsNotNone(result["permissions"])
        self.assertIsInstance(result["permissions"], list)
        self.assertGreater(len(result["permissions"]), 0, "permissions list should not be empty")
        
        # Verify permission objects have required fields
        for permission in result["permissions"]:
            self.assertIsInstance(permission, dict)
            self.assertIn("id", permission)
            self.assertIn("role", permission)
            self.assertIn("type", permission)
            self.assertIsInstance(permission["id"], str)
            self.assertIsInstance(permission["role"], str)
            self.assertIsInstance(permission["type"], str)

    def test_metadata_completeness_all_required_fields(self):
        """Test that all documented metadata fields are present and properly populated."""
        file_id = "file123"
        result = get_file_metadata_or_content(fileId=file_id)
        
        # Required fields from the docstring
        required_fields = [
            'kind', 'id', 'name', 'mimeType', 'parents', 'createdTime', 
            'modifiedTime', 'trashed', 'starred', 'owners', 'size', 'permissions'
        ]
        
        # Verify all required fields are present
        for field in required_fields:
            self.assertIn(field, result, f"Required field '{field}' is missing from metadata")
            self.assertIsNotNone(result[field], f"Required field '{field}' is None")
        
        # Verify specific field types and values
        self.assertEqual(result['kind'], 'drive#file')
        self.assertEqual(result['id'], file_id)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['mimeType'], str)
        self.assertIsInstance(result['parents'], list)
        self.assertIsInstance(result['createdTime'], str)
        self.assertIsInstance(result['modifiedTime'], str)
        self.assertIsInstance(result['trashed'], bool)
        self.assertIsInstance(result['starred'], bool)
        self.assertIsInstance(result['owners'], list)
        self.assertIsInstance(result['size'], str)
        self.assertIsInstance(result['permissions'], list)
        
        # Verify non-empty values for critical fields
        self.assertNotEqual(result['createdTime'], "")
        self.assertNotEqual(result['modifiedTime'], "")
        self.assertNotEqual(result['size'], "0")
        self.assertGreater(len(result['parents']), 0)
        self.assertGreater(len(result['permissions']), 0)

    def test_metadata_with_file_with_content(self):
        """Test metadata completeness for a file that has content and revisions."""
        # Create a file with content in the database
        file_with_content = {
            "id": "file_with_content_123",
            "name": "Document with Content",
            "mimeType": "application/vnd.google-apps.document",
            "kind": "drive#file",
            "parents": ["folder789"],
            "createdTime": "2023-01-01T10:00:00Z",
            "modifiedTime": "2023-01-02T12:00:00Z",
            "trashed": False,
            "starred": False,
            "owners": ["me@example.com"],
            "size": "2048",
            "permissions": [
                {"id": "perm2", "type": "user", "role": "owner", "emailAddress": "me@example.com"}
            ],
            "content": {
                "data": "This is the document content",
                "encoding": "text",
                "checksum": "abc123def456",
                "version": "1.0",
                "lastContentUpdate": "2023-01-02T12:00:00Z"
            },
            "revisions": [
                {
                    "id": "rev1",
                    "mimeType": "application/vnd.google-apps.document",
                    "modifiedTime": "2023-01-02T12:00:00Z",
                    "keepForever": False,
                    "originalFilename": "Document with Content",
                    "size": "2048",
                    "content": {
                        "data": "This is the document content",
                        "encoding": "text",
                        "checksum": "abc123def456"
                    }
                }
            ]
        }
        
        # Add the file to the database
        SimulationDB['users']['me']['files']['file_with_content_123'] = file_with_content
        
        # Test the metadata
        result = get_file_metadata_or_content(fileId="file_with_content_123")
        
        # Verify all basic metadata fields are present and correct
        self.assertEqual(result['id'], "file_with_content_123")
        self.assertEqual(result['name'], "Document with Content")
        self.assertEqual(result['size'], "2048")
        self.assertNotEqual(result['createdTime'], "")
        self.assertNotEqual(result['modifiedTime'], "")
        self.assertGreater(len(result['parents']), 0)
        self.assertGreater(len(result['permissions']), 0)
        
        # Verify content and revisions are present
        self.assertIn('content', result)
        self.assertIn('revisions', result)
        self.assertIsInstance(result['content'], dict)
        self.assertIsInstance(result['revisions'], list)
        self.assertGreater(len(result['revisions']), 0)
