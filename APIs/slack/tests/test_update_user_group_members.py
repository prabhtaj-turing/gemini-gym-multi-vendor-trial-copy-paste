"""
Test cases for the update_user_group_members function in the Slack Usergroups API.

This module contains comprehensive test cases for the update_user_group_members function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    UserGroupIdInvalidError,
    InvalidUsersError,
    UserGroupNotFoundError,
    UserNotFoundError,
)
from .. import update_user_group_members

class TestUpdateUserGroupMembers(BaseTestCaseWithErrorHandler):
    """Test cases for the update_user_group_members function."""

    def setUp(self):
        """Setup method to create a fresh DB for each test."""
        self.test_db = {
            "users": {
                "U123": {
                    "id": "U123",
                    "token": "U123",
                    "team_id": "T123",
                    "name": "User 1",
                },
                "U456": {
                    "id": "U456",
                    "token": "U456",
                    "team_id": "T123",
                    "name": "User 2",
                },
                "U789": {
                    "id": "U789",
                    "token": "U789",
                    "team_id": "T123",
                    "name": "User 3",
                },
            },
            "channels": {
                "C123": {"id": "C123", "name": "channel1"},
                "C456": {"id": "C456", "name": "channel2"},
            },
            "usergroups": {
                "UG123": {
                    "id": "UG123",
                    "team_id": "T123",
                    "name": "Test Group",
                    "handle": "test-group",
                    "users": [],
                    "user_count": 0,
                    "prefs": {"channels": [], "groups": []},  # Ensure prefs exist
                    "disabled": False,
                }
            },
            "files": {},
            "scheduled_messages": [],
            "ephemeral_messages": [],
        }

        # Start each test with a patch
        self.patcher = patch("slack.UsergroupUsers.DB", self.test_db)
        self.mock_db = self.patcher.start()
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def tearDown(self):
        """Clean up after each test."""
        self.patcher.stop()

    def test_update_users_success(self):
        """Test successful update of users in a usergroup."""
        # Update users in the usergroup
        result = update_user_group_members("UG123", "U456,U789")
        self.assertTrue(result["ok"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["users"], ["U456", "U789"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["updated_by"], "U456")  # First user in list

    def test_update_users_with_include_count(self):
        """Test update with include_count parameter."""
        # Test with include_count=True
        result = update_user_group_members("UG123", "U456,U789", include_count=True)
        self.assertTrue(result["ok"])
        self.assertIn("user_count", result["usergroup"])
        self.assertEqual(result["usergroup"]["user_count"], 2)

        # Test with include_count=False
        result = update_user_group_members("UG123", "U456,U789", include_count=False)
        self.assertTrue(result["ok"])
        self.assertNotIn("user_count", result["usergroup"])

    def test_update_users_with_date_update(self):
        """Test update with custom date_update."""
        custom_date = "1234567890.123456"
        result = update_user_group_members("UG123", "U456,U789", date_update=custom_date)
        self.assertTrue(result["ok"])
        self.assertEqual(result["usergroup"]["date_update"], custom_date)

    def test_update_users_invalid_usergroup(self):
        """Test update with invalid usergroup ID."""
        self.assert_error_behavior(
            update_user_group_members,
            UserGroupIdInvalidError,
            "Invalid property usergroup ",
            None,
            usergroup="",
            users="U456,U789"
        )

    def test_update_users_invalid_users(self):
        """Test update with invalid users string."""
        self.assert_error_behavior(
            update_user_group_members,
            InvalidUsersError,
            "Invalid property users ",
            None,
            usergroup="UG123",
            users=""
        )

    def test_update_users_usergroup_not_found(self):
        """Test update with non-existent usergroup."""
        self.assert_error_behavior(
            update_user_group_members,
            UserGroupNotFoundError,
            "User group invalid_usergroup not found",
            None,
            usergroup="invalid_usergroup",
            users="U456"
        )

    def test_update_users_user_not_found(self):
        """Test update with non-existent user."""
        self.assert_error_behavior(
            update_user_group_members,
            UserNotFoundError,
            "User invalid_user not found",
            None,
            usergroup="UG123",
            users="U456,invalid_user"
        )

    def test_update_users_single_user(self):
        """Test update with a single user."""
        result = update_user_group_members("UG123", "U123")
        self.assertTrue(result["ok"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["users"], ["U123"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["updated_by"], "U123")

    def test_update_users_empty_to_populated(self):
        """Test updating from empty users list to populated."""
        # Initially empty
        self.assertEqual(self.test_db["usergroups"]["UG123"]["users"], [])
        
        # Update with users
        result = update_user_group_members("UG123", "U123,U456,U789")
        self.assertTrue(result["ok"])
        self.assertEqual(len(self.test_db["usergroups"]["UG123"]["users"]), 3)
        self.assertIn("U123", self.test_db["usergroups"]["UG123"]["users"])
        self.assertIn("U456", self.test_db["usergroups"]["UG123"]["users"])
        self.assertIn("U789", self.test_db["usergroups"]["UG123"]["users"])

    def test_update_users_replace_existing(self):
        """Test replacing existing users with new ones."""
        # First update
        update_user_group_members("UG123", "U123,U456")
        self.assertEqual(self.test_db["usergroups"]["UG123"]["users"], ["U123", "U456"])
        
        # Replace with different users
        result = update_user_group_members("UG123", "U789")
        self.assertTrue(result["ok"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["users"], ["U789"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["updated_by"], "U789")

    def test_update_users_type_validation(self):
        """Test type validation for parameters."""
        # Test non-string usergroup
        self.assert_error_behavior(
            update_user_group_members,
            UserGroupIdInvalidError,
            "Invalid property usergroup 123",
            None,
            usergroup=123,
            users="U456"
        )

        # Test non-string users (passing a list instead of string)
        self.assert_error_behavior(
            update_user_group_members,
            InvalidUsersError,
            "Invalid property users ['U456', 'U789']",
            None,
            usergroup="UG123",
            users=["U456", "U789"]
        )

    def test_update_users_none_values(self):
        """Test with None values for optional parameters."""
        result = update_user_group_members(
            "UG123", 
            "U456", 
            include_count=None, 
            date_update=None
        )
        self.assertTrue(result["ok"])
        self.assertEqual(self.test_db["usergroups"]["UG123"]["users"], ["U456"])

    def test_update_users_usergroup_user_count_update(self):
        """Test that user_count is properly updated in the usergroup."""
        # Update with multiple users
        result = update_user_group_members("UG123", "U123,U456,U789", include_count=True)
        self.assertTrue(result["ok"])
        
        # Check that user_count in DB is updated
        self.assertEqual(self.test_db["usergroups"]["UG123"]["user_count"], 3)
        
        # Check that user_count in response is correct
        self.assertEqual(result["usergroup"]["user_count"], 3)
