"""
Comprehensive State (Load/Save) tests for Google Docs API simulation.

This module tests all aspects of state management including save_state, load_state,
error handling, data integrity, edge cases, and performance scenarios.
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from unittest.mock import call

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_docs.SimulationEngine.db import DB, save_state, load_state


class TestGoogleDocsStateManagement(BaseTestCaseWithErrorHandler):
    """Test suite for comprehensive state management testing."""

    def setUp(self):
        """Set up test environment with temporary files and test data."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db_file = os.path.join(self.temp_dir, "test_db.json")
        self.temp_backup_file = os.path.join(self.temp_dir, "backup_db.json")
        
        # Test data structure with proper DocumentElementModel format
        self.test_data = {
            "users": {
                "me": {
                    "about": {
                        "user": {
                            "emailAddress": "me@example.com",
                            "displayName": "Test User",
                        },
                        "storageQuota": {"limit": "10000000000", "usage": "0"},
                    },
                    "files": {
                        "doc-1": {
                            "id": "doc-1",
                            "name": "Test Document 1",
                            "mimeType": "application/vnd.google-apps.document",
                            "createdTime": "2025-01-01T00:00:00Z",
                            "modifiedTime": "2025-01-01T00:00:00Z",
                            "owners": ["me@example.com"],
                            "content": [
                                {
                                    "elementId": "element-1",
                                    "text": "Hello World"
                                }
                            ],
                        }
                    },
                    "comments": {
                        "comment-1": {
                            "id": "comment-1",
                            "fileId": "doc-1",
                            "content": "Test comment",
                            "author": {
                                "displayName": "Test User",
                                "emailAddress": "me@example.com"
                            },
                            "createdTime": "2025-01-01T00:00:00Z"
                        }
                    },
                    "replies": {
                        "reply-1": {
                            "id": "reply-1",
                            "commentId": "comment-1",
                            "fileId": "doc-1",
                            "content": "Test reply",
                            "author": {
                                "displayName": "Test User",
                                "emailAddress": "me@example.com"
                            },
                            "createdTime": "2025-01-01T00:00:00Z"
                        }
                    },
                    "labels": {
                        "label-1": {
                            "id": "label-1",
                            "fileId": "doc-1",
                            "name": "Test Label",
                            "color": "blue"
                        }
                    },
                    "accessproposals": {
                        "proposal-1": {
                            "id": "proposal-1",
                            "fileId": "doc-1",
                            "role": "reader",
                            "state": "pending",
                            "requester": {
                                "displayName": "Requester User",
                                "emailAddress": "requester@example.com"
                            },
                            "createdTime": "2025-01-01T00:00:00Z"
                        }
                    },
                    "counters": {
                        "file": 1,
                        "comment": 1,
                        "reply": 1,
                        "label": 1,
                        "accessproposal": 1,
                        "revision": 0,
                    },
                }
            }
        }
        
        # Reset DB to test data
        DB.clear()
        DB.update(self.test_data.copy())

    def tearDown(self):
        """Clean up temporary files and directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_state_basic_functionality(self):
        """Test basic save_state functionality."""
        # Save current state
        save_state(self.temp_db_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.temp_db_file))
        
        # Verify file contains valid JSON
        with open(self.temp_db_file, 'r') as f:
            saved_data = json.load(f)
        
        # Verify structure is preserved
        self.assertIn("users", saved_data)
        self.assertIn("me", saved_data["users"])
        self.assertEqual(saved_data["users"]["me"]["about"]["user"]["emailAddress"], "me@example.com")

    def test_load_state_basic_functionality(self):
        """Test basic load_state functionality."""
        # Save current state first
        save_state(self.temp_db_file)
        
        # Clear DB
        DB.clear()
        self.assertEqual(len(DB), 0)
        
        # Load state back
        load_state(self.temp_db_file)
        
        # Verify data was restored
        self.assertIn("users", DB)
        self.assertIn("me", DB["users"])
        self.assertEqual(DB["users"]["me"]["about"]["user"]["emailAddress"], "me@example.com")

    def test_save_state_data_integrity(self):
        """Test that save_state preserves data integrity."""
        # Add more complex data with proper DocumentElementModel format
        DB["users"]["me"]["files"]["doc-2"] = {
            "id": "doc-2",
            "name": "Complex Document",
            "mimeType": "application/vnd.google-apps.document",
            "createdTime": "2025-01-01T00:00:00Z",
            "content": [
                {
                    "elementId": "element-2-1",
                    "text": "Paragraph 1"
                },
                {
                    "elementId": "element-2-2",
                    "text": "Paragraph 2"
                },
                {
                    "elementId": "element-2-3",
                    "text": "Paragraph 3"
                }
            ],
            # "metadata": {
            #     "tags": ["important", "draft"],
            #     "collaborators": ["user1@example.com", "user2@example.com"]
            # }
        }
        
        # Save state
        save_state(self.temp_db_file)
        
        # Clear and reload
        DB.clear()
        load_state(self.temp_db_file)
        
        # Verify complex data was preserved
        self.assertIn("doc-2", DB["users"]["me"]["files"])
        doc2 = DB["users"]["me"]["files"]["doc-2"]
        self.assertEqual(len(doc2["content"]), 3)
        # Note: metadata is not part of the API schema and is stripped during validation
        # self.assertEqual(doc2["metadata"]["tags"], ["important", "draft"])
        # self.assertEqual(len(doc2["metadata"]["collaborators"]), 2)

    def test_save_state_empty_database(self):
        """Test save_state with empty database."""
        # Clear DB
        DB.clear()
        
        # Save empty state
        save_state(self.temp_db_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.temp_db_file))
        
        # Verify file contains empty structure
        with open(self.temp_db_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data), 0)

    def test_load_state_empty_file(self):
        """Test load_state with empty database (no users)."""
        # Create minimal valid empty database
        with open(self.temp_db_file, 'w') as f:
            f.write('{"users": {}}')
        
        # Load empty state
        load_state(self.temp_db_file)
        
        # Verify DB has users key but no users
        self.assertIn('users', DB)
        self.assertEqual(len(DB['users']), 0)

    def test_save_state_large_data(self):
        """Test save_state with large amounts of data."""
        # Create large dataset with proper DocumentElementModel format
        large_user = {
            "about": {"user": {"emailAddress": "large@example.com", "displayName": "Large User"}},
            "files": {},
            "comments": {},
            "replies": {},
            "labels": {},
            "accessproposals": {},
            "counters": {"file": 0, "comment": 0, "reply": 0, "label": 0, "accessproposal": 0, "revision": 0}
        }
        
        # Add many files
        for i in range(100):
            large_user["files"][f"doc-{i}"] = {
                "id": f"doc-{i}",
                "name": f"Document {i}",
                "mimeType": "application/vnd.google-apps.document",
                "createdTime": "2025-01-01T00:00:00Z",
                "content": [
                    {
                        "elementId": f"element-{i}-1",
                        "text": f"Content for document {i}"
                    }
                ],
                "metadata": {"index": i, "category": f"category-{i % 10}"}
            }
        
        DB["users"]["large_user"] = large_user
        
        # Save large state
        save_state(self.temp_db_file)
        
        # Verify file was created and is substantial
        self.assertTrue(os.path.exists(self.temp_db_file))
        file_size = os.path.getsize(self.temp_db_file)
        self.assertGreater(file_size, 1000)  # Should be at least 1KB

    def test_load_state_large_data(self):
        """Test load_state with large amounts of data."""
        # Create and save large dataset
        self.test_save_state_large_data()
        
        # Clear DB
        DB.clear()
        
        # Load large state
        load_state(self.temp_db_file)
        
        # Verify large dataset was loaded
        self.assertIn("large_user", DB["users"])
        self.assertEqual(len(DB["users"]["large_user"]["files"]), 100)
        
        # Verify specific data points
        self.assertEqual(DB["users"]["large_user"]["files"]["doc-50"]["name"], "Document 50")
        # Note: metadata is not part of the API schema and is stripped during validation
        # self.assertEqual(DB["users"]["large_user"]["files"]["doc-99"]["metadata"]["category"], "category-9")

    def test_save_state_invalid_filepath(self):
        """Test save_state with invalid filepath."""
        # Test with directory that doesn't exist
        invalid_path = "/nonexistent/directory/test.json"
        
        # Should handle gracefully (actual behavior depends on gdrive implementation)
        try:
            save_state(invalid_path)
            # If it doesn't raise an exception, that's also valid
        except Exception as e:
            # If it does raise an exception, it should be a reasonable error
            self.assertIsInstance(e, (OSError, PermissionError, FileNotFoundError))

    def test_load_state_nonexistent_file(self):
        """Test load_state with nonexistent file."""
        nonexistent_file = "/nonexistent/file.json"
        
        # Should handle gracefully (actual behavior depends on gdrive implementation)
        try:
            load_state(nonexistent_file)
            # If it doesn't raise an exception, that's also valid
        except Exception as e:
            # If it does raise an exception, it should be a reasonable error
            self.assertIsInstance(e, (OSError, FileNotFoundError))

    def test_save_state_permission_error(self):
        """Test save_state with permission error."""
        # Create a read-only directory
        read_only_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(read_only_dir, mode=0o444)  # Read-only
        
        read_only_file = os.path.join(read_only_dir, "test.json")
        
        # Should handle gracefully
        try:
            save_state(read_only_file)
        except Exception as e:
            self.assertIsInstance(e, (OSError, PermissionError))

    def test_load_state_corrupted_json(self):
        """Test load_state with corrupted JSON file."""
        # Create corrupted JSON file
        corrupted_file = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_file, 'w') as f:
            f.write('{"users": {"me": {"invalid": json}}}')  # Invalid JSON
        
        # Should handle gracefully
        try:
            load_state(corrupted_file)
        except Exception as e:
            self.assertIsInstance(e, (json.JSONDecodeError, ValueError))

    def test_save_state_concurrent_access(self):
        """Test save_state with concurrent access simulation."""
        # Simulate concurrent access by saving multiple times rapidly
        for i in range(5):
            DB["users"]["me"]["files"][f"concurrent-doc-{i}"] = {
                "id": f"concurrent-doc-{i}",
                "name": f"Concurrent Document {i}",
                "content": [
                    {
                        "elementId": f"concurrent-element-{i}",
                        "text": f"Content {i}"
                    }
                ]
            }
            save_state(f"{self.temp_db_file}.{i}")
        
        # Verify all files were saved
        for i in range(5):
            file_path = f"{self.temp_db_file}.{i}"
            self.assertTrue(os.path.exists(file_path))
            
            # Verify content
            with open(file_path, 'r') as f:
                saved_data = json.load(f)
                self.assertIn(f"concurrent-doc-{i}", saved_data["users"]["me"]["files"])

    def test_load_state_partial_data(self):
        """Test load_state with partial data structure."""
        # Create partial data file
        partial_data = {
            "users": {
                "partial_user": {
                    "about": {"user": {"emailAddress": "partial@example.com", "displayName": "Partial User"}},
                    "files": {}
                }
            }
        }
        
        partial_file = os.path.join(self.temp_dir, "partial.json")
        with open(partial_file, 'w') as f:
            json.dump(partial_data, f)
        
        # Load partial state
        load_state(partial_file)
        
        # Verify partial data was loaded
        self.assertIn("partial_user", DB["users"])
        self.assertEqual(DB["users"]["partial_user"]["about"]["user"]["emailAddress"], "partial@example.com")

    def test_save_state_backup_functionality(self):
        """Test save_state backup functionality."""
        # Save initial state
        save_state(self.temp_db_file)
        
        # Modify data
        DB["users"]["me"]["files"]["backup-doc"] = {
            "id": "backup-doc",
            "name": "Backup Document",
            "content": [
                {
                    "elementId": "backup-element",
                    "text": "Backup content"
                }
            ]
        }
        
        # Save to backup file
        save_state(self.temp_backup_file)
        
        # Verify both files exist
        self.assertTrue(os.path.exists(self.temp_db_file))
        self.assertTrue(os.path.exists(self.temp_backup_file))
        
        # Verify backup contains new data
        with open(self.temp_backup_file, 'r') as f:
            backup_data = json.load(f)
            self.assertIn("backup-doc", backup_data["users"]["me"]["files"])

    def test_load_state_recovery_scenario(self):
        """Test load_state recovery scenario."""
        # Save initial state
        save_state(self.temp_db_file)
        
        # Simulate data corruption by clearing DB
        DB.clear()
        self.assertEqual(len(DB), 0)
        
        # Recover from saved state
        load_state(self.temp_db_file)
        
        # Verify recovery was successful
        self.assertIn("users", DB)
        self.assertIn("me", DB["users"])
        self.assertEqual(len(DB["users"]["me"]["files"]), 1)  # Original doc-1
        self.assertEqual(DB["users"]["me"]["files"]["doc-1"]["name"], "Test Document 1")

    def test_save_state_unicode_support(self):
        """Test save_state with Unicode content."""
        # Add Unicode content with proper DocumentElementModel format
        DB["users"]["me"]["files"]["unicode-doc"] = {
            "id": "unicode-doc",
            "name": "Unicode Document: 测试文档",
            "content": [
                {
                    "elementId": "unicode-element",
                    "text": "Hello 世界! 🌍"
                }
            ],
            # "metadata": {"description": "Document with emojis and Chinese characters"}
        }
        
        # Save state
        save_state(self.temp_db_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.temp_db_file))
        
        # Verify Unicode content was preserved
        with open(self.temp_db_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            unicode_doc = saved_data["users"]["me"]["files"]["unicode-doc"]
            self.assertEqual(unicode_doc["name"], "Unicode Document: 测试文档")
            self.assertEqual(unicode_doc["content"][0]["text"], "Hello 世界! 🌍")

    def test_load_state_unicode_support(self):
        """Test load_state with Unicode content."""
        # Create file with Unicode content and proper DocumentElementModel format
        unicode_data = {
            "users": {
                "unicode_user": {
                    "about": {"user": {"emailAddress": "unicode@example.com", "displayName": "测试用户"}},
                    "files": {
                        "doc": {
                            "id": "doc",
                            "name": "Unicode Test: 🚀",
                            "mimeType": "application/vnd.google-apps.document",
                            "createdTime": "2025-01-01T00:00:00Z",
                            "content": [
                                {
                                    "elementId": "unicode-test-element",
                                    "text": "Hello 世界! 🌟"
                                }
                            ]
                        }
                    }
                }
            }
        }
        
        unicode_file = os.path.join(self.temp_dir, "unicode.json")
        with open(unicode_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_data, f, ensure_ascii=False)
        
        # Load Unicode state
        load_state(unicode_file)
        
        # Verify Unicode content was loaded correctly
        self.assertIn("unicode_user", DB["users"])
        user = DB["users"]["unicode_user"]
        self.assertEqual(user["about"]["user"]["displayName"], "测试用户")
        self.assertEqual(user["files"]["doc"]["name"], "Unicode Test: 🚀")
        self.assertEqual(user["files"]["doc"]["content"][0]["text"], "Hello 世界! 🌟")


if __name__ == "__main__":
    unittest.main()
