import os
import unittest
from unittest.mock import patch

# Slack modules
from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine.db import save_state, load_state
from .. import invite_admin_user

DB = {
    "current_user": {
        "id": "U123",
        "is_admin": True
    },
    "channels": {
        "C123": {
            "id": "C123",
            "name": "general",
            "is_private": False,
            "team_id": None,
            "conversations": {"members": ["U123"]},  # Initial member
            "messages": [
                {"ts": "1678886400.000000", "user": "U123", "text": "Hello", "reactions": []},
                {"ts": "1678886460.000000", "user": "U123", "text": "World", "reactions": []},
            ],
            "files": {}
        },
        "C456": {
            "id": "C456",
            "name": "random",
            "is_private": False,
            "team_id": None,
            "conversations": {"members": []},
            "messages": [],
            "files": {}
        },
        "C789": {  # For testing open and replies
            "id": "C789",
            "name": "private-channel",
            "is_private": True,
            "team_id": None,
            "conversations": {
                "members": ["U123", "U456"],
                "purpose": "Initial Purpose",
                "topic": "Initial Topic",
            },
            "messages": [
                {
                    "ts": "1678886400.000100",
                    "user": "U123",
                    "text": "Parent Message",
                    "reactions": [],
                    "replies": [
                        {"ts": "1678886401.000100", "text": "Reply 1"},
                        {"ts": "1678886402.000100", "text": "Reply 2"},
                    ],
                },
            ],
            "files": {}
        },
        "G123": {
            "id": "G123",
            "name": "U123,U456",
            "is_private": False,
            "team_id": None,
            "conversations": {"id": "G123", "users": ["U123", "U456"]},
            "messages": [],
            "files": {}
        },
        "IM123": {  # For testing open with channel
            "id": "IM123",
            "name": "U123",
            "is_private": True,
            "team_id": None,
            "conversations": {"id": "IM123", "users": ["U123"]},
            "messages": [],
            "files": {}
        },
    },
    "users": {
        "U123": {
            "id": "U123",
            "name": "user1",
            "team_id": None,
            "real_name": "User One",
            "profile": {
                "email": "user1@example.com",
                "display_name": "User1",
                "image": "base64image1",
                "image_crop_x": 0,
                "image_crop_y": 0,
                "image_crop_w": 100,
                "title": "Developer"
            },
            "is_admin": True,
            "is_bot": False,
            "deleted": False,
            "presence": "active"
        },
        "U456": {
            "id": "U456",
            "name": "user2",
            "team_id": None,
            "real_name": "User Two",
            "profile": {
                "email": "user2@example.com",
                "display_name": "User2",
                "image": "base64image2",
                "image_crop_x": 0,
                "image_crop_y": 0,
                "image_crop_w": 100,
                "title": "Designer"
            },
            "is_admin": False,
            "is_bot": False,
            "deleted": False,
            "presence": "active"
        },
        "U789": {
            "id": "U789",
            "name": "user3",
            "team_id": None,
            "real_name": "User Three",
            "profile": {
                "email": "user3@example.com",
                "display_name": "User3",
                "image": "base64image3",
                "image_crop_x": 0,
                "image_crop_y": 0,
                "image_crop_w": 100,
                "title": "Manager"
            },
            "is_admin": False,
            "is_bot": False,
            "deleted": False,
            "presence": "away"
        },
    },
    "scheduled_messages": [],
    "ephemeral_messages": [],
    "files": {},
    "reminders": {},
    "usergroups": {},
}

for channel_id, channel_data in DB["channels"].items():
    if "conversations" not in channel_data:
        channel_data["conversations"] = {}
    if "members" not in channel_data["conversations"]:
        channel_data["conversations"]["members"] = []


class TestAdminUsersInvite(BaseTestCaseWithErrorHandler):
    """
    Unit tests for the AdminUsers invite_admin_user API.
    """

    def setUp(self):
        """
        Set up the test environment by assigning a fresh initial state to DB.
        """
        # Reset DB to initial state by assigning a new dictionary literal
        global DB
        DB = {
            "current_user": {
                "id": "U123",
                "is_admin": True
            },
            "channels": {
                "C123": {
                    "id": "C123",
                    "name": "general",
                    "is_private": False,
                    "team_id": None,
                    "conversations": {"members": ["U123"]},  # Initial member
                    "messages": [
                        {"ts": "1678886400.000000", "user": "U123", "text": "Hello", "reactions": []},
                        {"ts": "1678886460.000000", "user": "U123", "text": "World", "reactions": []},
                    ],
                    "files": {}
                },
                "C456": {
                    "id": "C456",
                    "name": "random",
                    "is_private": False,
                    "team_id": None,
                    "conversations": {"members": []},
                    "messages": [],
                    "files": {}
                },
                "C789": {  # For testing open and replies
                    "id": "C789",
                    "name": "private-channel",
                    "is_private": True,
                    "team_id": None,
                    "conversations": {
                        "members": ["U123", "U456"],
                        "purpose": "Initial Purpose",
                        "topic": "Initial Topic",
                    },
                    "messages": [
                        {
                            "ts": "1678886400.000100",
                            "user": "U123",
                            "text": "Parent Message",
                            "reactions": [],
                            "replies": [
                                {"ts": "1678886401.000100", "text": "Reply 1"},
                                {"ts": "1678886402.000100", "text": "Reply 2"},
                            ],
                        },
                    ],
                    "files": {}
                },
                "G123": {
                    "id": "G123",
                    "name": "U123,U456",
                    "is_private": False,
                    "team_id": None,
                    "conversations": {"id": "G123", "users": ["U123", "U456"]},
                    "messages": [],
                    "files": {}
                },
                "IM123": {  # For testing open with channel
                    "id": "IM123",
                    "name": "U123",
                    "is_private": True,
                    "team_id": None,
                    "conversations": {"id": "IM123", "users": ["U123"]},
                    "messages": [],
                    "files": {}
                },
            },
            "users": {
                "U123": {
                    "id": "U123",
                    "name": "user1",
                    "team_id": None,
                    "real_name": "User One",
                    "profile": {
                        "email": "user1@example.com",
                        "display_name": "User1",
                        "image": "base64image1",
                        "image_crop_x": 0,
                        "image_crop_y": 0,
                        "image_crop_w": 100,
                        "title": "Developer"
                    },
                    "is_admin": True,
                    "is_bot": False,
                    "deleted": False,
                    "presence": "active"
                },
                "U456": {
                    "id": "U456",
                    "name": "user2",
                    "team_id": None,
                    "real_name": "User Two",
                    "profile": {
                        "email": "user2@example.com",
                        "display_name": "User2",
                        "image": "base64image2",
                        "image_crop_x": 0,
                        "image_crop_y": 0,
                        "image_crop_w": 100,
                        "title": "Designer"
                    },
                    "is_admin": False,
                    "is_bot": False,
                    "deleted": False,
                    "presence": "active"
                },
                "U789": {
                    "id": "U789",
                    "name": "user3",
                    "team_id": None,
                    "real_name": "User Three",
                    "profile": {
                        "email": "user3@example.com",
                        "display_name": "User3",
                        "image": "base64image3",
                        "image_crop_x": 0,
                        "image_crop_y": 0,
                        "image_crop_w": 100,
                        "title": "Manager"
                    },
                    "is_admin": False,
                    "is_bot": False,
                    "deleted": False,
                    "presence": "away"
                },
            },
            "scheduled_messages": [],
            "ephemeral_messages": [],
            "files": {},
            "reminders": {},
            "usergroups": {},
        }
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def test_invite_user(self):
        """
        Test inviting a user.
        """
        # Use patch to ensure the invite function uses the DB instance from setUp
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-user@example.com", real_name="Test User"
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-user@example.com")
        self.assertEqual(result["user"]["real_name"], "Test User")
        self.assertTrue(result["user"]["id"].startswith("U"))

    # Patch the DB used by invite_admin_user for this test
    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_invite_with_optional_params(self, mock_db):
        """
        Test inviting a user with optional parameters.
        """
        # The setUp method already initializes C123 and C456 with the necessary structure.
        # No need to overwrite DB["channels"] here.
        result = invite_admin_user(
            email="test-optional@example.com",
            channel_ids="C123,C456",
            real_name="Test User",
            team_id="T789",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["user"]["profile"]["email"], "test-optional@example.com"
        )
        self.assertEqual(result["user"]["real_name"], "Test User")
        self.assertEqual(result["user"]["team_id"], "T789")
        user_id = result["user"]["id"]
        # Directly check if the user is in the members list
        self.assertIn(user_id, DB["channels"]["C123"]["conversations"]["members"])

    def test_save_load_state(self):
        """
        Test saving and loading API state.
        """
        with patch("slack.AdminUsers.DB", DB):
            invite_admin_user(email="test@example.com")
        with patch("slack.SimulationEngine.db.DB", DB):
            save_state("test_state.json")
            DB.clear()
            load_state("test_state.json")
        # for user_id, user_data in DB["users"].items():
        for user_id, user_data in DB.get("users", {}).items():
            if user_data["profile"]["email"] == "test@example.com":
                self.assertTrue(user_data)
                break

    def test_invite_with_blank_channel_ids(self):
        """
        Test inviting a user with blank channel IDs (empty string).
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-blank@example.com",
                channel_ids=""
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-blank@example.com")
        # User should be created but not added to any channels
        user_id = result["user"]["id"]
        # Check that user is not added to any existing channels
        for channel_id, channel_data in DB["channels"].items():
            if "conversations" in channel_data and "members" in channel_data["conversations"]:
                self.assertNotIn(user_id, channel_data["conversations"]["members"])

    def test_invite_with_whitespace_only_channel_ids(self):
        """
        Test inviting a user with whitespace-only channel IDs.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-whitespace@example.com",
                channel_ids="   ,  ,  \t  ,  \n  "
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-whitespace@example.com")
        # User should be created but not added to any channels
        user_id = result["user"]["id"]
        # Check that user is not added to any existing channels
        for channel_id, channel_data in DB["channels"].items():
            if "conversations" in channel_data and "members" in channel_data["conversations"]:
                self.assertNotIn(user_id, channel_data["conversations"]["members"])

    def test_invite_with_mixed_valid_blank_channel_ids(self):
        """
        Test inviting a user with mixed valid and blank/whitespace channel IDs.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-mixed@example.com",
                channel_ids="C123,  , C456, \t , C789"
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-mixed@example.com")
        user_id = result["user"]["id"]
        
        # User should be added to valid channels (C123, C456, C789) but not blank ones
        self.assertIn(user_id, DB["channels"]["C123"]["conversations"]["members"])
        self.assertIn(user_id, DB["channels"]["C456"]["conversations"]["members"])
        self.assertIn(user_id, DB["channels"]["C789"]["conversations"]["members"])

    def test_invite_with_leading_trailing_whitespace_channel_ids(self):
        """
        Test inviting a user with channel IDs that have leading/trailing whitespace.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-trim@example.com",
                channel_ids="  C123  ,  C456  "
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-trim@example.com")
        user_id = result["user"]["id"]
        
        # User should be added to channels after whitespace is trimmed
        self.assertIn(user_id, DB["channels"]["C123"]["conversations"]["members"])
        self.assertIn(user_id, DB["channels"]["C456"]["conversations"]["members"])

    def test_invite_with_comma_only_channel_ids(self):
        """
        Test inviting a user with only commas as channel IDs.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-comma@example.com",
                channel_ids=",,,"
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-comma@example.com")
        # User should be created but not added to any channels
        user_id = result["user"]["id"]
        # Check that user is not added to any existing channels
        for channel_id, channel_data in DB["channels"].items():
            if "conversations" in channel_data and "members" in channel_data["conversations"]:
                self.assertNotIn(user_id, channel_data["conversations"]["members"])

    def test_invite_with_tab_newline_whitespace_channel_ids(self):
        """
        Test inviting a user with various whitespace characters in channel IDs.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-tab-newline@example.com",
                channel_ids="\tC123\n,\rC456\t"
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["profile"]["email"], "test-tab-newline@example.com")
        user_id = result["user"]["id"]
        
        # User should be added to channels after all whitespace is trimmed
        self.assertIn(user_id, DB["channels"]["C123"]["conversations"]["members"])
        self.assertIn(user_id, DB["channels"]["C456"]["conversations"]["members"])

    def test_invite_creates_channel_with_correct_structure(self):
        """
        Test that inviting a user to a non-existent channel creates the channel with the correct structure.
        """
        # Verify the new channel doesn't exist initially
        self.assertNotIn("C999", DB["channels"])
        
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-new-channel@example.com",
                channel_ids="C999"
            )
        
        self.assertTrue(result["ok"])
        user_id = result["user"]["id"]
        
        # Verify the new channel was created
        self.assertIn("C999", DB["channels"])
        new_channel = DB["channels"]["C999"]
        
        # Verify the channel has the correct structure (no top-level "members" key)
        self.assertIn("id", new_channel)
        self.assertIn("name", new_channel)
        self.assertIn("is_private", new_channel)
        self.assertIn("team_id", new_channel)
        self.assertIn("conversations", new_channel)
        self.assertIn("messages", new_channel)
        self.assertIn("files", new_channel)
        
        # Verify it does NOT have a top-level "members" key (this was the bug)
        self.assertNotIn("members", new_channel)
        
        # Verify the conversations structure is correct
        conversations = new_channel["conversations"]
        self.assertIn("id", conversations)
        self.assertIn("read_cursor", conversations)
        self.assertIn("members", conversations)
        self.assertIn("topic", conversations)
        self.assertIn("purpose", conversations)
        
        # Verify the user was added to the correct location (conversations.members)
        self.assertIn(user_id, conversations["members"])
        
        # Verify the channel structure matches the expected format
        self.assertEqual(new_channel["id"], "C999")
        self.assertEqual(new_channel["name"], "channel_C999")
        self.assertEqual(new_channel["is_private"], False)
        self.assertEqual(new_channel["team_id"], None)
        self.assertEqual(conversations["read_cursor"], 0)
        self.assertEqual(conversations["topic"], "")
        self.assertEqual(conversations["purpose"], "")
        self.assertEqual(new_channel["messages"], [])
        self.assertEqual(new_channel["files"], {})

    def test_invite_creates_multiple_channels_with_correct_structure(self):
        """
        Test that inviting a user to multiple non-existent channels creates all channels with correct structure.
        """
        # Verify the new channels don't exist initially
        self.assertNotIn("C888", DB["channels"])
        self.assertNotIn("C777", DB["channels"])
        
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="test-multiple-channels@example.com",
                channel_ids="C888,C777"
            )
        
        self.assertTrue(result["ok"])
        user_id = result["user"]["id"]
        
        # Verify both new channels were created
        self.assertIn("C888", DB["channels"])
        self.assertIn("C777", DB["channels"])
        
        # Verify both channels have correct structure
        for channel_id in ["C888", "C777"]:
            channel = DB["channels"][channel_id]
            
            # Verify it does NOT have a top-level "members" key (this was the bug)
            self.assertNotIn("members", channel)
            
            # Verify the conversations structure is correct
            conversations = channel["conversations"]
            self.assertIn("members", conversations)
            self.assertIn(user_id, conversations["members"])
            
            # Verify basic structure
            self.assertEqual(channel["id"], channel_id)
            self.assertEqual(channel["name"], f"channel_{channel_id}")
            self.assertEqual(channel["is_private"], False)
            self.assertEqual(channel["team_id"], None)
    def test_display_name_consistency_with_real_name(self):
        """
        Test that display_name is not truncated when real_name is provided.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="michael.brown@example.com",
                real_name="Michael Brown"
            )
        self.assertTrue(result["ok"])
        # Display name should be the full real_name, not truncated to 5 characters
        self.assertEqual(result["user"]["profile"]["display_name"], "Michael Brown")
        self.assertEqual(result["user"]["real_name"], "Michael Brown")

    def test_display_name_consistency_without_real_name(self):
        """
        Test that display_name is not truncated when derived from email.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="michaelb@example.com"
            )
        self.assertTrue(result["ok"])
        # Display name should be the full email prefix capitalized, not truncated to 5 characters
        self.assertEqual(result["user"]["profile"]["display_name"], "Michaelb")
        self.assertEqual(result["user"]["real_name"], "Michaelb")

    def test_display_name_consistency_long_names(self):
        """
        Test that display_name is not truncated for long names.
        """
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="christopher.alexander@example.com",
                real_name="Christopher Alexander"
            )
        self.assertTrue(result["ok"])
        # Display name should be the full real_name, not truncated
        self.assertEqual(result["user"]["profile"]["display_name"], "Christopher Alexander")
        self.assertEqual(result["user"]["real_name"], "Christopher Alexander")

    def test_display_name_consistency_with_existing_users(self):
        """
        Test that new users have consistent display_name format with existing users.
        """
        # Check existing users have display names that are not truncated
        existing_display_names = [
            user["profile"]["display_name"] 
            for user in DB["users"].values()
        ]
        
        # All existing users have display names that are not artificially truncated
        for display_name in existing_display_names:
            self.assertGreaterEqual(len(display_name), 5, 
                             f"Existing user display_name '{display_name}' is shorter than expected")
        
        # Invite a new user
        with patch("slack.AdminUsers.DB", DB):
            result = invite_admin_user(
                email="newuser@example.com",
                real_name="New User"
            )
        
        # New user should also have full display name, not truncated
        self.assertEqual(result["user"]["profile"]["display_name"], "New User")
        self.assertGreater(len(result["user"]["profile"]["display_name"]), 5)

    def test_display_name_consistency_edge_cases(self):
        """
        Test display_name consistency with various edge cases.
        """
        test_cases = [
            ("john.doe@example.com", "John Doe", "John Doe"),
            ("a@example.com", "A", "A"),
            ("verylongname@example.com", "Very Long Name", "Very Long Name"),
            ("test@example.com", None, "Test"),  # No real_name provided
        ]
        
        for email, real_name, expected_display_name in test_cases:
            with patch("slack.AdminUsers.DB", DB):
                result = invite_admin_user(
                    email=email,
                    real_name=real_name
                )
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["profile"]["display_name"], expected_display_name)
            # Verify it's not truncated (unless the name itself is short)
            if len(expected_display_name) > 5:
                self.assertGreater(len(result["user"]["profile"]["display_name"]), 5)


if __name__ == "__main__":
    unittest.main()
