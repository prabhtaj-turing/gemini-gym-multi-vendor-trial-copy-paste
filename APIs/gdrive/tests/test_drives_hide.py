"""
Comprehensive tests for the hide_shared_drive() function.
This test file focuses specifically on testing the hide function with various
edge cases, input validation, and API compliance scenarios.
"""

import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (DB, hide_shared_drive, _ensure_user, create_shared_drive, get_shared_drive_metadata)

class TestDrivesHideFunction(BaseTestCaseWithErrorHandler):
    """Test cases for the hide_shared_drive() function."""

    def setUp(self):
        """Set up test environment before each test."""
        # Reset DB before each test
        global DB
        DB.update({
            "users": {
                "me": {
                    "about": {
                        "kind": "drive#about",
                        "storageQuota": {
                            "limit": "107374182400",
                            "usageInDrive": "0",
                            "usageInDriveTrash": "0",
                            "usage": "0",
                        },
                        "driveThemes": False,
                        "canCreateDrives": True,
                        "importFormats": {},
                        "exportFormats": {},
                        "appInstalled": False,
                        "user": {
                            "displayName": "Example User",
                            "kind": "drive#user",
                            "me": True,
                            "permissionId": "1234567890",
                            "emailAddress": "me@example.com",
                        },
                        "folderColorPalette": "",
                        "maxImportSizes": {},
                        "maxUploadSize": "52428800",
                    },
                    "files": {},
                    "drives": {},
                    "comments": {},
                    "replies": {},
                    "labels": {},
                    "accessproposals": {},
                    "apps": {},
                    "channels": {},
                    "changes": {"startPageToken": "1", "changes": []},
                    "counters": {
                        "file": 0,
                        "drive": 0,
                        "comment": 0,
                        "reply": 0,
                        "label": 0,
                        "accessproposal": 0,
                        "revision": 0,
                        "change_token": 0,
                    },
                }
            }
        })
        _ensure_user("me")

    def test_hide_existing_drive(self):
        """Test hiding an existing drive."""
        # Create a test drive
        drive = create_shared_drive("test-drive-1", {"name": "Test Drive"})
        drive_id = drive["id"]

        # Verify drive is not hidden initially
        self.assertFalse(drive.get("hidden", False))

        # Hide the drive
        result = hide_shared_drive(drive_id)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], drive_id)
        self.assertTrue(result["hidden"])
        self.assertEqual(result["name"], "Test Drive")

        # Verify the drive is hidden in the database
        stored_drive = get_shared_drive_metadata(drive_id)
        self.assertTrue(stored_drive["hidden"])

    def test_hide_nonexistent_drive(self):
        """Test hiding a drive that doesn't exist."""
        result = hide_shared_drive("nonexistent-drive-id")
        self.assertIsNone(result)

    def test_hide_already_hidden_drive(self):
        """Test hiding a drive that is already hidden (idempotency)."""
        # Create a test drive
        drive = create_shared_drive("test-drive-2", {"name": "Test Drive 2"})
        drive_id = drive["id"]

        # Hide the drive once
        result1 = hide_shared_drive(drive_id)
        self.assertTrue(result1["hidden"])

        # Hide the drive again
        result2 = hide_shared_drive(drive_id)
        self.assertTrue(result2["hidden"])

        # Both results should be identical
        self.assertEqual(result1, result2)

    def test_hide_input_validation_none(self):
        """Test hide function with None input."""
        with self.assertRaises(ValueError) as context:
            hide_shared_drive(None)
        self.assertIn("driveId must be a string", str(context.exception))

    def test_hide_input_validation_non_string(self):
        """Test hide function with non-string input."""
        with self.assertRaises(ValueError) as context:
            hide_shared_drive(123)
        self.assertIn("driveId must be a string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            hide_shared_drive([])
        self.assertIn("driveId must be a string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            hide_shared_drive({})
        self.assertIn("driveId must be a string", str(context.exception))

    def test_hide_input_validation_empty_string(self):
        """Test hide function with empty string input."""
        with self.assertRaises(ValueError) as context:
            hide_shared_drive("")
        self.assertIn("driveId cannot be empty", str(context.exception))

    def test_hide_input_validation_whitespace_only(self):
        """Test hide function with whitespace-only input."""
        with self.assertRaises(ValueError) as context:
            hide_shared_drive("   ")
        self.assertIn("driveId cannot be empty", str(context.exception))

        with self.assertRaises(ValueError) as context:
            hide_shared_drive("\t\n")
        self.assertIn("driveId cannot be empty", str(context.exception))

    def test_hide_input_normalization(self):
        """Test that driveId is properly normalized (whitespace stripped)."""
        # Create a test drive
        drive = create_shared_drive("test-drive-3", {"name": "Test Drive 3"})
        drive_id = drive["id"]

        # Hide the drive with whitespace around the ID
        result = hide_shared_drive(f"  {drive_id}  ")

        # Should work correctly
        self.assertIsNotNone(result)
        self.assertTrue(result["hidden"])
        self.assertEqual(result["id"], drive_id)

    def test_hide_preserves_other_properties(self):
        """Test that hiding preserves all other drive properties."""
        # Create a drive with various properties
        drive_data = {
            "name": "Test Drive with Properties",
            "restrictions": {
                "adminManagedRestrictions": True,
                "copyRequiresWriterPermission": False,
                "domainUsersOnly": True,
                "driveMembersOnly": False
            },
            "themeId": "test-theme-123"
        }

        drive = create_shared_drive("test-drive-4", drive_data)
        drive_id = drive["id"]

        # Store original properties
        original_name = drive["name"]
        original_restrictions = drive.get("restrictions")
        original_theme_id = drive.get("themeId")

        # Hide the drive
        result = hide_shared_drive(drive_id)

        # Verify hidden flag is set
        self.assertTrue(result["hidden"])

        # Verify other properties are preserved
        self.assertEqual(result["name"], original_name)
        self.assertEqual(result.get("restrictions"), original_restrictions)
        self.assertEqual(result.get("themeId"), original_theme_id)

    def test_hide_returns_complete_drive_object(self):
        """Test that hide returns a complete drive object."""
        # Create a test drive
        drive = create_shared_drive("test-drive-5", {"name": "Complete Drive Test"})
        drive_id = drive["id"]

        # Hide the drive
        result = hide_shared_drive(drive_id)

        # Verify the result contains expected fields
        self.assertIsNotNone(result)
        self.assertIn("kind", result)
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertIn("hidden", result)

        # Verify the values
        self.assertEqual(result["kind"], "drive#drive")
        self.assertEqual(result["id"], drive_id)
        self.assertEqual(result["name"], "Complete Drive Test")
        self.assertTrue(result["hidden"])

    def test_hide_multiple_drives(self):
        """Test hiding multiple different drives."""
        # Create multiple drives
        drive1 = create_shared_drive("test-drive-6", {"name": "Drive 1"})
        drive2 = create_shared_drive("test-drive-7", {"name": "Drive 2"})
        drive3 = create_shared_drive("test-drive-8", {"name": "Drive 3"})

        # Hide all drives
        result1 = hide_shared_drive(drive1["id"])
        result2 = hide_shared_drive(drive2["id"])
        result3 = hide_shared_drive(drive3["id"])

        # Verify all are hidden
        self.assertTrue(result1["hidden"])
        self.assertTrue(result2["hidden"])
        self.assertTrue(result3["hidden"])

        # Verify they maintain their individual properties
        self.assertEqual(result1["name"], "Drive 1")
        self.assertEqual(result2["name"], "Drive 2")
        self.assertEqual(result3["name"], "Drive 3")

    def test_hide_with_special_characters_in_id(self):
        """Test hiding drives with special characters in drive ID."""
        # Create drives with various ID formats
        special_ids = [
            "drive-with-hyphens",
            "drive_with_underscores",
            "drive.with.dots",
            "0123456789"
        ]

        for drive_id in special_ids:
            with self.subTest(drive_id=drive_id):
                # Create drive
                drive = create_shared_drive(drive_id, {"name": f"Drive {drive_id}"})

                # Hide drive
                result = hide_shared_drive(drive_id)

                # Verify
                self.assertIsNotNone(result)
                self.assertTrue(result["hidden"])
                self.assertEqual(result["id"], drive_id)


if __name__ == "__main__":
    unittest.main() 