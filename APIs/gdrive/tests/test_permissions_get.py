"""
Test suite for Google Drive Permissions.get function.
This module contains comprehensive tests for the permissions.get function,
covering normal operations, edge cases, error conditions, and different
access patterns including shared drives and domain admin access.
"""

import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (DB, _ensure_user, get_permission)

class TestPermissionsGet(BaseTestCaseWithErrorHandler):
    """Test class for Permissions.get function."""

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()
        # Reset DB before each test
        global DB
        DB.update({
            "users": {
                "me": {
                    "about": {
                        "kind": "drive#about",
                        "user": {
                            "displayName": "Test User",
                            "kind": "drive#user",
                            "me": True,
                            "permissionId": "1234567890",
                            "emailAddress": "me@example.com",
                        },
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
                        "permission": 0,
                    },
                }
            }
        })
        _ensure_user("me")

        # Create a test file with permissions
        self.file_id = "test_file_123"
        self.permission_id = "permission_456"

        DB["users"]["me"]["files"][self.file_id] = {
            "id": self.file_id,
            "name": "Test File",
            "mimeType": "application/vnd.google-apps.document",
            "permissions": [
                {
                    "kind": "drive#permission",
                    "id": self.permission_id,
                    "role": "reader",
                    "type": "user",
                    "emailAddress": "test@example.com",
                    "domain": "",
                    "allowFileDiscovery": False,
                    "expirationTime": ""
                },
                {
                    "kind": "drive#permission", 
                    "id": "permission_owner",
                    "role": "owner",
                    "type": "user",
                    "emailAddress": "me@example.com",
                    "domain": "",
                    "allowFileDiscovery": False,
                    "expirationTime": ""
                }
            ]
        }

    def test_get_basic_permission_success(self):
        """Test successful retrieval of a basic permission."""
        permission = get_permission(self.file_id, self.permission_id)

        self.assertIsNotNone(permission)
        self.assertEqual(permission["id"], self.permission_id)
        self.assertEqual(permission["role"], "reader")
        self.assertEqual(permission["type"], "user")
        self.assertEqual(permission["emailAddress"], "test@example.com")
        self.assertEqual(permission["kind"], "drive#permission")

    def test_get_permission_not_found(self):
        """Test behavior when permission is not found."""
        permission = get_permission(self.file_id, "nonexistent_permission")
        self.assertIsNone(permission)

    def test_get_permission_file_not_found(self):
        """Test behavior when file is not found - should still work due to _ensure_file."""
        permission = get_permission("nonexistent_file", self.permission_id)
        self.assertIsNone(permission)

    def test_input_validation_empty_file_id(self):
        """Test input validation for empty fileId."""
        with self.assertRaises(ValueError) as context:
            get_permission("", self.permission_id)
        self.assertIn("fileId cannot be empty or whitespace", str(context.exception))

    def test_input_validation_whitespace_file_id(self):
        """Test input validation for whitespace-only fileId."""
        with self.assertRaises(ValueError) as context:
            get_permission("   ", self.permission_id)
        self.assertIn("fileId cannot be empty or whitespace", str(context.exception))

    def test_input_validation_none_file_id(self):
        """Test input validation for None fileId."""
        with self.assertRaises(TypeError) as context:
            get_permission(None, self.permission_id)
        self.assertIn("fileId must be a string", str(context.exception))

    def test_input_validation_integer_file_id(self):
        """Test input validation for integer fileId."""
        with self.assertRaises(TypeError) as context:
            get_permission(123, self.permission_id)
        self.assertIn("fileId must be a string", str(context.exception))

    def test_input_validation_empty_permission_id(self):
        """Test input validation for empty permissionId."""
        with self.assertRaises(ValueError) as context:
            get_permission(self.file_id, "")
        self.assertIn("permissionId cannot be empty or whitespace", str(context.exception))

    def test_input_validation_none_permission_id(self):
        """Test input validation for None permissionId."""
        with self.assertRaises(TypeError) as context:
            get_permission(self.file_id, None)
        self.assertIn("permissionId must be a string", str(context.exception))

    def test_input_validation_invalid_supports_all_drives(self):
        """Test input validation for invalid supportsAllDrives type."""
        with self.assertRaises(TypeError) as context:
            get_permission(self.file_id, self.permission_id, supportsAllDrives="true")
        self.assertIn("supportsAllDrives must be a boolean", str(context.exception))

    def test_input_validation_invalid_supports_team_drives(self):
        """Test input validation for invalid supportsTeamDrives type."""
        with self.assertRaises(TypeError) as context:
            get_permission(self.file_id, self.permission_id, supportsTeamDrives=1)
        self.assertIn("supportsTeamDrives must be a boolean", str(context.exception))

    def test_input_validation_invalid_use_domain_admin_access(self):
        """Test input validation for invalid useDomainAdminAccess type."""
        with self.assertRaises(TypeError) as context:
            get_permission(self.file_id, self.permission_id, useDomainAdminAccess="false")
        self.assertIn("useDomainAdminAccess must be a boolean", str(context.exception))

    def test_get_with_supports_all_drives(self):
        """Test get with supportsAllDrives enabled."""
        permission = get_permission(
            self.file_id, 
            self.permission_id, 
            supportsAllDrives=True
        )

        self.assertIsNotNone(permission)
        self.assertEqual(permission["id"], self.permission_id)

    def test_get_with_supports_team_drives(self):
        """Test get with supportsTeamDrives enabled (deprecated)."""
        permission = get_permission(
            self.file_id, 
            self.permission_id, 
            supportsTeamDrives=True
        )

        self.assertIsNotNone(permission)
        self.assertEqual(permission["id"], self.permission_id)

    def test_get_with_domain_admin_access(self):
        """Test get with useDomainAdminAccess enabled."""
        permission = get_permission(
            self.file_id, 
            self.permission_id, 
            useDomainAdminAccess=True
        )

        self.assertIsNotNone(permission)
        self.assertEqual(permission["id"], self.permission_id)

    def test_all_boolean_combinations(self):
        """Test various combinations of boolean parameters."""
        # Test all combinations of boolean parameters
        combinations = [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (False, False, True),
            (True, True, False),
            (True, False, True),
            (False, True, True),
            (True, True, True),
        ]

        for supports_all, supports_team, use_domain in combinations:
            permission = get_permission(
                self.file_id,
                self.permission_id,
                supportsAllDrives=supports_all,
                supportsTeamDrives=supports_team,
                useDomainAdminAccess=use_domain
            )

            # Should always find the basic permission
            self.assertIsNotNone(permission)
            self.assertEqual(permission["id"], self.permission_id)

    def test_get_permission_different_types(self):
        """Test retrieving permissions of different types."""
        # Add different permission types
        permissions_to_add = [
            {
                "kind": "drive#permission",
                "id": "group_permission",
                "role": "writer",
                "type": "group",
                "emailAddress": "group@example.com",
                "domain": "",
                "allowFileDiscovery": True,
                "expirationTime": ""
            },
            {
                "kind": "drive#permission",
                "id": "domain_permission",
                "role": "commenter",
                "type": "domain",
                "emailAddress": "",
                "domain": "example.com",
                "allowFileDiscovery": True,
                "expirationTime": ""
            },
            {
                "kind": "drive#permission",
                "id": "anyone_permission",
                "role": "reader",
                "type": "anyone",
                "emailAddress": "",
                "domain": "",
                "allowFileDiscovery": True,
                "expirationTime": ""
            }
        ]

        DB["users"]["me"]["files"][self.file_id]["permissions"].extend(permissions_to_add)

        # Test each permission type
        for perm in permissions_to_add:
            permission = get_permission(self.file_id, perm["id"])
            self.assertIsNotNone(permission)
            self.assertEqual(permission["id"], perm["id"])
            self.assertEqual(permission["type"], perm["type"])
            self.assertEqual(permission["role"], perm["role"])


if __name__ == "__main__":
    unittest.main()