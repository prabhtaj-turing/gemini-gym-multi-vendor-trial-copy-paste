"""
Comprehensive State Management Tests for Google Slides API

This module tests all aspects of state management including save_state, load_state,
get_database, error handling, data integrity, edge cases, and performance scenarios.
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_slides.SimulationEngine.db import DB, save_state, load_state, get_database
from google_slides.SimulationEngine.db_models import GoogleSlidesDB
from google_slides.SimulationEngine import models


class TestGoogleSlidesStateManagement(BaseTestCaseWithErrorHandler):
    """Test suite for comprehensive state management testing."""

    def setUp(self):
        """Set up test environment with temporary files and test data."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db_file = os.path.join(self.temp_dir, "test_db.json")
        self.temp_backup_file = os.path.join(self.temp_dir, "backup_db.json")
        
        # Load the default database structure
        default_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "DBs",
            "GoogleSlidesDefaultDB.json"
        )
        with open(default_db_path, 'r') as f:
            self.test_data = json.load(f)
        
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
        # Check that about and files exist
        self.assertIn("about", saved_data["users"]["me"])
        self.assertIn("files", saved_data["users"]["me"])

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
        self.assertIn("about", DB["users"]["me"])
        self.assertIn("files", DB["users"]["me"])

    def test_get_database_returns_pydantic_model(self):
        """Test that get_database returns a valid GoogleSlidesDB Pydantic model."""
        # Get database as Pydantic model
        db_model = get_database()
        
        # Verify it's the correct type
        self.assertIsInstance(db_model, GoogleSlidesDB)
        
        # Verify data integrity
        self.assertIn("me", db_model.users)
        self.assertIsNotNone(db_model.users["me"].about)
        self.assertIn("pres1", db_model.users["me"].files)
        
        # Verify presentation data (strict validation - all files are SlidesFile objects)
        pres = db_model.users["me"].files["pres1"]
        # With strict validation, pres is a SlidesFile object, not a dict
        self.assertEqual(pres.presentationId, "pres1")
        self.assertEqual(pres.title, "Test Presentation 1")
        self.assertEqual(len(pres.slides), 2)  # Default DB has 2 slides
        self.assertEqual(pres.slides[0].objectId, "slide1_page1")


    def test_get_database_validation(self):
        """Test that get_database validates data against Pydantic schema."""
        # Add invalid data to DB
        DB["users"]["invalid_user"] = {
            "about": None,  # Invalid - about is required
            "files": {}
        }
        
        # get_database should raise ValidationError
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            get_database()
        
        # Restore valid data
        DB.clear()
        DB.update(self.test_data.copy())

    def test_save_state_data_integrity(self):
        """Test that save_state preserves data integrity."""
        # Add more complex presentation data
        DB["users"]["me"]["files"]["pres-2"] = {
            "id": "pres-2",
            "driveId": "drive-1",
            "name": "Complex Presentation",
            "mimeType": "application/vnd.google-apps.presentation",
            "createdTime": "2025-01-02T00:00:00Z",
            "modifiedTime": "2025-01-02T00:00:00Z",
            "presentationId": "pres-2",
            "title": "Complex Presentation",
            "slides": [
                {
                    "objectId": "slide-2-1",
                    "pageType": "SLIDE",
                    "revisionId": "rev-2-1",
                    "slideProperties": {
                        "layoutObjectId": "layout-1"
                    },
                    "pageElements": [
                        {
                            "objectId": "elem-1",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                    "textElements": [
                                        {
                                            "textRun": {
                                                "content": "Hello World"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            ],
            "masters": [],
            "layouts": [],
            "locale": "en-US",
            "owners": ["test@example.com"],
            "parents": [],
            "trashed": False,
            "starred": False,
            "size": "2048",
            "permissions": []
        }
        
        # Save state
        save_state(self.temp_db_file)
        
        # Clear and reload
        DB.clear()
        load_state(self.temp_db_file)
        
        # Verify complex data was preserved
        self.assertIn("pres-2", DB["users"]["me"]["files"])
        pres2 = DB["users"]["me"]["files"]["pres-2"]
        self.assertEqual(pres2["title"], "Complex Presentation")
        self.assertEqual(len(pres2["slides"]), 1)
        self.assertEqual(len(pres2["slides"][0]["pageElements"]), 1)
        # Check that shape and text exist in the structure
        self.assertIn("shape", pres2["slides"][0]["pageElements"][0])
        self.assertIn("text", pres2["slides"][0]["pageElements"][0]["shape"])

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
        self.assertIn("users", DB)
        self.assertEqual(len(DB["users"]), 0)

    def test_save_state_large_data(self):
        """Test save_state with large amounts of data."""
        # Create large dataset
        large_user = {
            "about": {
                "kind": "drive#about",
                "user": {
                    "displayName": "Large User",
                    "kind": "drive#user",
                    "me": True,
                    "permissionId": "large-user",
                    "emailAddress": "large@example.com"
                },
                "storageQuota": {"limit": "10000000000", "usage": "0", "usageInDrive": "0", "usageInDriveTrash": "0"},
                "driveThemes": [],
                "canCreateDrives": True,
                "importFormats": {},
                "exportFormats": {},
                "appInstalled": False,
                "folderColorPalette": "#000000",
                "maxImportSizes": {},
                "maxUploadSize": "5242880000"
            },
            "files": {},
            "drives": {},
            "comments": {},
            "replies": {},
            "labels": {},
            "accessproposals": {},
            "counters": {"file": 0, "presentation": 0}
        }
        
        # Add many presentations
        for i in range(50):
            large_user["files"][f"pres-{i}"] = {
                "id": f"pres-{i}",
                "driveId": "drive-1",
                "name": f"Presentation {i}",
                "mimeType": "application/vnd.google-apps.presentation",
                "createdTime": "2025-01-01T00:00:00Z",
                "modifiedTime": "2025-01-01T00:00:00Z",
                "presentationId": f"pres-{i}",
                "title": f"Presentation {i}",
                "slides": [],
                "masters": [],
                "layouts": [],
                "locale": "en-US",
                "owners": ["large@example.com"],
                "parents": [],
                "trashed": False,
                "starred": False,
                "size": "1024",
                "permissions": []
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
        self.assertEqual(len(DB["users"]["large_user"]["files"]), 50)
        
        # Verify specific data points
        self.assertEqual(DB["users"]["large_user"]["files"]["pres-25"]["title"], "Presentation 25")
        self.assertEqual(DB["users"]["large_user"]["files"]["pres-49"]["title"], "Presentation 49")

    def test_save_state_invalid_filepath(self):
        """Test save_state with invalid filepath."""
        # Test with directory that doesn't exist
        invalid_path = "/nonexistent/directory/test.json"
        
        # Should handle gracefully
        try:
            save_state(invalid_path)
        except Exception as e:
            self.assertIsInstance(e, (OSError, PermissionError, FileNotFoundError))

    def test_load_state_nonexistent_file(self):
        """Test load_state with nonexistent file."""
        nonexistent_file = "/nonexistent/file.json"
        
        # Should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            load_state(nonexistent_file)

    def test_load_state_corrupted_json(self):
        """Test load_state with corrupted JSON file."""
        # Create corrupted JSON file
        corrupted_file = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_file, 'w') as f:
            f.write('{"users": {"me": {"invalid": json}}}')  # Invalid JSON
        
        # Should raise ValueError (from gdrive wrapping JSONDecodeError)
        with self.assertRaises(ValueError):
            load_state(corrupted_file)

    def test_save_state_concurrent_access(self):
        """Test save_state with concurrent access simulation."""
        # Simulate concurrent access by saving multiple times rapidly
        for i in range(5):
            DB["users"]["me"]["files"][f"concurrent-pres-{i}"] = {
                "id": f"concurrent-pres-{i}",
                "driveId": "drive-1",
                "name": f"Concurrent Presentation {i}",
                "mimeType": "application/vnd.google-apps.presentation",
                "createdTime": "2025-01-01T00:00:00Z",
                "modifiedTime": "2025-01-01T00:00:00Z",
                "presentationId": f"concurrent-pres-{i}",
                "title": f"Concurrent Presentation {i}",
                "slides": [],
                "masters": [],
                "layouts": [],
                "locale": "en-US",
                "owners": ["test@example.com"],
                "parents": [],
                "trashed": False,
                "starred": False,
                "size": "1024",
                "permissions": []
            }
            save_state(f"{self.temp_db_file}.{i}")
        
        # Verify all files were saved
        for i in range(5):
            file_path = f"{self.temp_db_file}.{i}"
            self.assertTrue(os.path.exists(file_path))
            
            # Verify content
            with open(file_path, 'r') as f:
                saved_data = json.load(f)
                self.assertIn(f"concurrent-pres-{i}", saved_data["users"]["me"]["files"])

    def test_save_state_backup_functionality(self):
        """Test save_state backup functionality."""
        # Save initial state
        save_state(self.temp_db_file)
        
        # Modify data
        DB["users"]["me"]["files"]["backup-pres"] = {
            "id": "backup-pres",
            "driveId": "drive-1",
            "name": "Backup Presentation",
            "mimeType": "application/vnd.google-apps.presentation",
            "createdTime": "2025-01-01T00:00:00Z",
            "modifiedTime": "2025-01-01T00:00:00Z",
            "presentationId": "backup-pres",
            "title": "Backup Presentation",
            "slides": [],
            "masters": [],
            "layouts": [],
            "locale": "en-US",
            "owners": ["test@example.com"],
            "parents": [],
            "trashed": False,
            "starred": False,
            "size": "1024",
            "permissions": []
        }
        
        # Save to backup file
        save_state(self.temp_backup_file)
        
        # Verify both files exist
        self.assertTrue(os.path.exists(self.temp_db_file))
        self.assertTrue(os.path.exists(self.temp_backup_file))
        
        # Verify backup contains new data
        with open(self.temp_backup_file, 'r') as f:
            backup_data = json.load(f)
            self.assertIn("backup-pres", backup_data["users"]["me"]["files"])

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
        # Should have at least the original presentation from default DB
        self.assertGreaterEqual(len(DB["users"]["me"]["files"]), 1)
        self.assertIn("pres1", DB["users"]["me"]["files"])
        self.assertEqual(DB["users"]["me"]["files"]["pres1"]["title"], "Test Presentation 1")

    def test_save_state_unicode_support(self):
        """Test save_state with Unicode content."""
        # Add Unicode content
        DB["users"]["me"]["files"]["unicode-pres"] = {
            "id": "unicode-pres",
            "driveId": "drive-1",
            "name": "Unicode Presentation: 测试演示",
            "mimeType": "application/vnd.google-apps.presentation",
            "createdTime": "2025-01-01T00:00:00Z",
            "modifiedTime": "2025-01-01T00:00:00Z",
            "presentationId": "unicode-pres",
            "title": "Unicode Presentation: 测试演示",
            "slides": [
                {
                    "objectId": "unicode-slide",
                    "pageType": "SLIDE",
                    "revisionId": "rev-unicode",
                    "slideProperties": {
                        "layoutObjectId": "layout-1"
                    },
                    "pageElements": [
                        {
                            "objectId": "unicode-elem",
                            "shape": {
                                "shapeType": "TEXT_BOX",
                                "text": {
                                    "textElements": [
                                        {
                                            "textRun": {
                                                "content": "Hello 世界! 🌍"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            ],
            "masters": [],
            "layouts": [],
            "locale": "zh-CN",
            "owners": ["test@example.com"],
            "parents": [],
            "trashed": False,
            "starred": False,
            "size": "2048",
            "permissions": []
        }
        
        # Save state
        save_state(self.temp_db_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.temp_db_file))
        
        # Verify Unicode content was preserved
        with open(self.temp_db_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            unicode_pres = saved_data["users"]["me"]["files"]["unicode-pres"]
            self.assertEqual(unicode_pres["title"], "Unicode Presentation: 测试演示")
            # Check that Unicode text is preserved in structure
            self.assertIn("slides", unicode_pres)
            self.assertGreater(len(unicode_pres["slides"]), 0)

    def test_load_state_unicode_support(self):
        """Test load_state with Unicode content."""
        # Save Unicode content first
        self.test_save_state_unicode_support()
        
        # Clear and reload
        DB.clear()
        load_state(self.temp_db_file)
        
        # Verify Unicode content was loaded correctly
        unicode_pres = DB["users"]["me"]["files"]["unicode-pres"]
        self.assertEqual(unicode_pres["title"], "Unicode Presentation: 测试演示")
        # Verify the unicode locale was preserved
        self.assertEqual(unicode_pres.get("locale"), "zh-CN")

    def test_save_load_round_trip(self):
        """Test that save and load operations are symmetric."""
        # Set up DB with test data
        DB.clear()
        DB.update(self.test_data)
        
        # Save state
        save_state(self.temp_db_file)
        
        # Modify DB
        DB.clear()
        DB.update({"different": "data"})
        
        # Load state
        load_state(self.temp_db_file)
        
        # Verify important data structure is preserved (not exact match due to Pydantic defaults)
        self.assertIn("users", DB)
        self.assertIn("me", DB["users"])
        self.assertIn("about", DB["users"]["me"])
        self.assertIn("files", DB["users"]["me"])
        
        # Verify presentation data
        self.assertIn("pres1", DB["users"]["me"]["files"])
        pres = DB["users"]["me"]["files"]["pres1"]
        
    
        self.assertEqual(pres["id"], "pres1")
        self.assertEqual(pres["presentationId"], "pres1")
        self.assertEqual(pres["title"], "Test Presentation 1")
        self.assertEqual(len(pres["slides"]), 2)
    
    def test_save_load_preserve_counters(self):
        """Test that counters are preserved through save/load."""
        # Set specific counter values
        DB["users"]["me"]["counters"]["file"] = 10
        DB["users"]["me"]["counters"]["drive"] = 5
        DB["users"]["me"]["counters"]["comment"] = 25
        DB["users"]["me"]["counters"]["revision"] = 100
        
        # Save and reload
        save_state(self.temp_db_file)
        DB.clear()
        load_state(self.temp_db_file)
        
        # Verify counters
        counters = DB["users"]["me"]["counters"]
        self.assertEqual(counters["file"], 10)
        self.assertEqual(counters["drive"], 5)
        self.assertEqual(counters["comment"], 25)
        self.assertEqual(counters["revision"], 100)

    def test_multiple_users_save_load(self):
        """Test save/load with multiple users."""
        # Create data for multiple users
        for user_id in ['user1', 'user2', 'user3']:
            DB["users"][user_id] = {
                "about": {
                    "kind": "drive#about",
                    "user": {
                        "displayName": f"User {user_id}",
                        "kind": "drive#user",
                        "me": False,
                        "permissionId": f"perm-{user_id}",
                        "emailAddress": f"{user_id}@example.com"
                    },
                    "storageQuota": {"limit": "10000000000", "usage": "0", "usageInDrive": "0", "usageInDriveTrash": "0"},
                    "driveThemes": [],
                    "canCreateDrives": True,
                    "importFormats": {},
                    "exportFormats": {},
                    "appInstalled": False,
                    "folderColorPalette": "#000000",
                    "maxImportSizes": {},
                    "maxUploadSize": "5242880000"
                },
                "files": {
                    f"pres-{user_id}": {
                        "id": f"pres-{user_id}",
                        "driveId": "drive-1",
                        "name": f"Presentation for {user_id}",
                        "mimeType": "application/vnd.google-apps.presentation",
                        "createdTime": "2025-01-01T00:00:00Z",
                        "modifiedTime": "2025-01-01T00:00:00Z",
                        "presentationId": f"pres-{user_id}",
                        "title": f"Presentation for {user_id}",
                        "slides": [],
                        "masters": [],
                        "layouts": [],
                        "locale": "en-US",
                        "owners": [f"{user_id}@example.com"],
                        "parents": [],
                        "trashed": False,
                        "starred": False,
                        "size": "1024",
                        "permissions": []
                    }
                },
                "drives": {},
                "comments": {},
                "replies": {},
                "labels": {},
                "accessproposals": {},
                "counters": {"file": 1}
            }
        
        # Save state
        save_state(self.temp_db_file)
        
        # Clear and reload
        DB.clear()
        load_state(self.temp_db_file)
        
        # Verify all users were restored
        for user_id in ['user1', 'user2', 'user3']:
            self.assertIn(user_id, DB["users"])
            self.assertIn(f"pres-{user_id}", DB["users"][user_id]["files"])


if __name__ == "__main__":
    unittest.main()

