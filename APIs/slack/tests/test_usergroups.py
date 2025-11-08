from unittest.mock import patch

from .. import (
    Usergroups,
    UsergroupUsers,
    DB
)

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    UserGroupIdInvalidError,
    UserGroupNotFoundError,
    UserGroupAlreadyDisabledError,
)
from .. import (create_user_group, disable_user_group, enable_user_group, list_user_groups, update_user_group)

DB = {
    "channels": {
        "C123": {
            "id": "C123",
            "name": "general",
            "conversations": {"members": ["U123"]},
            "is_archived": False,
            "messages": [
                {"ts": "1678886400.000000", "text": "Hello"},
                {"ts": "1678886460.000000", "text": "World"},
            ],
            "type": "public_channel",
        },
        "C456": {
            "id": "C456",
            "name": "random",
            "conversations": {"members": []},
            "is_archived": True,
            "type": "public_channel",
        },
        "C789": {  # For testing open and replies
            "id": "C789",
            "name": "private-channel",
            "is_private": True,
            "type": "private_channel",
            "conversations": {
                "members": ["U123", "U456"],
                "purpose": "Initial Purpose",
                "topic": "Initial Topic",
            },
            "messages": [
                {
                    "ts": "1678886400.000100",
                    "text": "Parent Message",
                    "replies": [
                        {"ts": "1678886401.000100", "text": "Reply 1"},
                        {"ts": "1678886402.000100", "text": "Reply 2"},
                    ],
                },
            ],
        },
        "G123": {
            "id": "G123",
            "name": "U123,U456",
            "conversations": {"id": "G123", "users": ["U123", "U456"]},
            "messages": [],
        },
        "IM123": {  # For testing open with channel
            "id": "IM123",
            "name": "U123",
            "is_im": True,
            "conversations": {"id": "IM123", "users": ["U123"]},
            "messages": [],
        },
    },
    "users": {
        "U123": {"id": "U123", "name": "user1"},
        "U456": {"id": "U456", "name": "user2"},
        "U789": {"id": "U789", "name": "user3"},
    },
    "scheduled_messages": [],
    "ephemeral_messages": [],
    "files": {},
    "reactions": {},
    "reminders": {},
    "usergroups": {},
    "usergroup_users": {},
}
class TestUsergroups(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup method to create a fresh DB for each test."""
        global DB
        DB.clear()
        DB.update(
            {
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
                    "ug1": {
                        "id": "ug1", "name": "Usergroup 1", "handle": "ug1-handle", "team_id": "teamA",
                        "disabled": False, "users": ["U1", "U2"],
                        "prefs": {"channels": [], "groups": []}, "description": "Test UG 1",
                        "date_create": "1700000000", "date_update": "1700000000",
                        "created_by": "test_user", "updated_by": "test_user", "user_count": 2
                    },
                    "ug2": {
                        "id": "ug2", "name": "Usergroup 2 Disabled", "handle": "ug2-handle", "team_id": "teamB",
                        "disabled": True, "users": [],
                        "prefs": {"channels": [], "groups": []}, "description": "Test UG 2 (Disabled)",
                        "date_create": "1700000001", "date_update": "1700000001",
                        "created_by": "test_user", "updated_by": "test_user", "user_count": 0
                    },
                    "ug3": {
                        "id": "ug3", "name": "Usergroup 3", "handle": "ug3-handle", "team_id": "teamA",
                        "disabled": False, # No 'users' key for this one
                        "prefs": {"channels": [], "groups": []}, "description": "Test UG 3",
                        "date_create": "1700000002", "date_update": "1700000002",
                        "created_by": "test_user", "updated_by": "test_user", "user_count": 0
                    }
                },
                "files": {},
                "scheduled_messages": [],
                "ephemeral_messages": [],
            }
        )
        # self.usergroups = Usergroups() # REMOVED
        # self.usergroup_users = UsergroupUsers() # REMOVED

        # In TestUsergroups.setUp after DB setup:
        self.usergroups = Usergroups  # Provide module reference
        self.usergroup_users = UsergroupUsers  # Provide module reference

    def test_create_usergroup(self):
        # Patch the DB in the Usergroups module with our test DB
        with patch("slack.Usergroups.DB", DB):
            # Test successful creation
            result = create_user_group(
                name="Test Group",
                created_at="1768239023",
                handle="test-group",
                description="A test group",
                channel_ids=["C123"],
            )
            self.assertTrue(result["ok"])
            usergroup_id = result["usergroup"]["id"]  # Get created ID
            self.assertEqual(result["usergroup"]["name"], "Test Group")
            self.assertEqual(result["usergroup"]["handle"], "test-group")
            self.assertEqual(result["usergroup"]["prefs"]["channels"], ["C123"])
            self.assertIn(usergroup_id, DB["usergroups"])

            # Test missing name
            self.assert_error_behavior(
                create_user_group,
                ValueError,
                "'name' cannot be empty.",
                name="",
                handle="test-group"
            )

            # Test invalid Channel ID
            self.assert_error_behavior(
                create_user_group,
                ValueError,
                "Invalid channel ID: 'CInvalid'",
                name="Test Group",
                handle="test-group",
                channel_ids=["CInvalid"]
            )

            # Test duplicate name (case-insensitive)
            # First, ensure a group exists to cause a duplicate name error
            if not any(ug["name"].lower() == "test group" for ug in DB["usergroups"].values()):
                 create_user_group(name="Test Group", handle="some-unique-handle-for-dupe-name-test")

            self.assert_error_behavior(
                create_user_group,
                ValueError,
                "A user group with the name 'test group' already exists.",
                name="test group",
                handle="test-group-2"
            )


            # Test duplicate handle (case-insensitive)
            # Create group first to ensure there's a handle to duplicate
            _ = create_user_group(
                name="Test Group 3", handle="test-group-3"
            )
            self.assert_error_behavior(
                create_user_group,
                ValueError,
                "A user group with the handle 'TesT-grOUp-3' already exists.",
                name="Test Group 4",
                handle="TesT-grOUp-3"
            )

    def test_create_usergroup_type_errors(self):
        with patch("slack.Usergroups.DB", DB):
            # Test TypeError for 'name'
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "User Group 'name' must be a string.",
                name=123
            )

            # Test TypeError for 'handle'
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "User Group 'handle' must be a string if provided.",
                name="Valid Name",
                handle=123
            )

            # Test TypeError for 'team_id'
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "User Group 'team_id' must be a string if provided.",
                name="Valid Name",
                team_id=123
            )

            # Test TypeError for 'description'
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "User Group 'description' must be a string if provided.",
                name="Valid Name",
                description=123
            )

            # Test TypeError for 'channel_ids' not being a list
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "User Group 'channel_ids' must be a list if provided.",
                name="Valid Name",
                channel_ids="not_a_list"
            )

            # Test TypeError for items in 'channel_ids' not being strings
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "All elements in 'channel_ids' must be strings.",
                name="Valid Name",
                channel_ids=["C123", 456]
            )

            # Test TypeError for 'created_at'
            self.assert_error_behavior(
                create_user_group,
                TypeError,
                "User Group 'created_at' must be a string if provided.",
                name="Valid Name",
                created_at=1234567890.0
            )

    def test_create_usergroup_initializes_db_usergroups_key(self):
        # Create a local DB copy for this test, without the 'usergroups' key
        local_db_without_usergroups_key = {
            "users": {
                "U123": {"id": "U123", "token": "U123", "team_id": "T123", "name": "User 1"},
            },
            "channels": {
                "C123": {"id": "C123", "name": "channel1"},
            },
            # 'usergroups' key is intentionally missing
            "files": {},
            "scheduled_messages": [],
            "ephemeral_messages": [],
        }
        with patch("slack.Usergroups.DB", local_db_without_usergroups_key):

            self.assertNotIn("usergroups", local_db_without_usergroups_key)

            result = create_user_group(
                name="Test Group For DB Init",
                handle="test-db-init",
                channel_ids=["C123"]
            )
            self.assertTrue(result["ok"])
            
            self.assertIn("usergroups", local_db_without_usergroups_key)
            self.assertIn(result["usergroup"]["id"], local_db_without_usergroups_key["usergroups"])

    def test_list_usergroups(self):
        # Patch the DB in the Usergroups module with our test DB
        with patch("slack.Usergroups.DB", DB):
            # Create some usergroups
            result1 = create_user_group(name="Group 1", handle="group-1")
            result2 = create_user_group(name="Group 2", handle="group-2")
            usergroup_id1 = result1["usergroup"]["id"]  # Get created ID
            usergroup_id2 = result2["usergroup"]["id"]
            DB["usergroups"][usergroup_id1]["disabled"] = True  # Disable one group

            # List all usergroups
            result = list_user_groups()
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 3)  # Now 3 enabled

            # Include disabled usergroups
            result = list_user_groups(include_disabled=True)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 5)

    def test_update_usergroup_validation_errors(self):
        """Test the actual update method with validation errors to cover missing lines."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup to update
            create_result = create_user_group(
                name="Test Group",
                handle="test-group",
                description="Original description",
                channel_ids=["C123"],
            )
            usergroup_id = create_result["usergroup"]["id"]

            # Test invalid usergroup_id type
            self.assert_error_behavior(
                update_user_group,
                UserGroupIdInvalidError,
                "usergroup_id must be a non-empty string",
                usergroup_id=123
            )

            # Test empty usergroup_id
            self.assert_error_behavior(
                update_user_group,
                UserGroupIdInvalidError,
                "usergroup_id must be a non-empty string",
                usergroup_id=""
            )

            # Test None usergroup_id
            self.assert_error_behavior(
                update_user_group,
                UserGroupIdInvalidError,
                "usergroup_id must be a non-empty string",
                usergroup_id=None
            )

            # Test invalid name type
            self.assert_error_behavior(
                update_user_group,
                TypeError,
                "name must be a string if provided",
                usergroup_id=usergroup_id,
                name=123
            )

            # Test empty name
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "name cannot be empty or whitespace-only",
                usergroup_id=usergroup_id,
                name=""
            )

            # Test whitespace-only name
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "name cannot be empty or whitespace-only",
                usergroup_id=usergroup_id,
                name="   "
            )

            # Test invalid handle type
            self.assert_error_behavior(
                update_user_group,
                TypeError,
                "handle must be a string if provided",
                usergroup_id=usergroup_id,
                handle=123
            )

            # Test empty handle
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "handle cannot be empty or whitespace-only",
                usergroup_id=usergroup_id,
                handle=""
            )

            # Test whitespace-only handle
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "handle cannot be empty or whitespace-only",
                usergroup_id=usergroup_id,
                handle="   "
            )

            # Test invalid description type
            self.assert_error_behavior(
                update_user_group,
                TypeError,
                "description must be a string if provided",
                usergroup_id=usergroup_id,
                description=123
            )

            # Test invalid channel_ids type (not a list)
            self.assert_error_behavior(
                update_user_group,
                TypeError,
                "channel_ids must be a list if provided",
                usergroup_id=usergroup_id,
                channel_ids="not_a_list"
            )

            # Test invalid channel_ids elements (not strings)
            self.assert_error_behavior(
                update_user_group,
                TypeError,
                "all elements in channel_ids must be strings",
                usergroup_id=usergroup_id,
                channel_ids=["C123", 456]
            )

            # Test invalid date_update type
            self.assert_error_behavior(
                update_user_group,
                TypeError,
                "date_update must be a string if provided",
                usergroup_id=usergroup_id,
                date_update=1234567890
            )

            # Test usergroup not found
            self.assert_error_behavior(
                update_user_group,
                UserGroupNotFoundError,
                "User group nonexistent_id not found",
                usergroup_id="nonexistent_id"
            )

    def test_update_usergroup_duplicate_validation(self):
        """Test duplicate name and handle validation in update method."""
        with patch("slack.Usergroups.DB", DB):
            # Create two usergroups
            create_result1 = create_user_group(
                name="Group One",
                handle="group-one",
                description="First group"
            )
            usergroup_id1 = create_result1["usergroup"]["id"]

            create_result2 = create_user_group(
                name="Group Two",
                handle="group-two",
                description="Second group"
            )
            usergroup_id2 = create_result2["usergroup"]["id"]

            # Test duplicate name (case-insensitive)
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "A user group with the name 'GROUP ONE' already exists",
                usergroup_id=usergroup_id2,
                name="GROUP ONE"
            )

            # Test duplicate handle (case-insensitive)
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "A user group with the handle 'GROUP-ONE' already exists",
                usergroup_id=usergroup_id2,
                handle="GROUP-ONE"
            )

            # Test duplicate handle when target usergroup has no handle
            # First, create a usergroup without a handle
            create_result3 = create_user_group(
                name="Group Three",
                description="Third group"
            )
            usergroup_id3 = create_result3["usergroup"]["id"]
            
            # Remove handle from the usergroup in DB
            DB["usergroups"][usergroup_id3].pop("handle", None)

            # Test duplicate handle against usergroup with no handle
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "A user group with the handle 'group-one' already exists",
                usergroup_id=usergroup_id3,
                handle="group-one"
            )

    def test_update_usergroup_invalid_channel_ids(self):
        """Test invalid channel IDs validation in update method."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group",
                handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]

            # Test invalid channel ID
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "Invalid channel ID: 'invalid_channel'",
                usergroup_id=usergroup_id,
                channel_ids=["invalid_channel"]
            )

            # Test multiple invalid channel IDs
            self.assert_error_behavior(
                update_user_group,
                ValueError,
                "Invalid channel ID: 'invalid_channel1'",
                usergroup_id=usergroup_id,
                channel_ids=["invalid_channel1", "invalid_channel2"]
            )

    def test_update_usergroup_successful_updates(self):
        """Test successful updates with various parameter combinations."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Original Name",
                handle="original-handle",
                description="Original description",
                channel_ids=["C123"]
            )
            usergroup_id = create_result["usergroup"]["id"]

            # Test updating only name
            result = update_user_group(
                usergroup_id=usergroup_id,
                name="Updated Name"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["name"], "Updated Name")
            self.assertEqual(result["usergroup"]["handle"], "original-handle")
            self.assertEqual(result["usergroup"]["description"], "Original description")

            # Test updating only handle
            result = update_user_group(
                usergroup_id=usergroup_id,
                handle="updated-handle"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["handle"], "updated-handle")

            # Test updating only description
            result = update_user_group(
                usergroup_id=usergroup_id,
                description="Updated description"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["description"], "Updated description")

            # Test updating only channel_ids
            result = update_user_group(
                usergroup_id=usergroup_id,
                channel_ids=["C456"]
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["prefs"]["channels"], ["C456"])

            # Test updating with custom date_update
            custom_date = "1712345678.000000"
            result = update_user_group(
                usergroup_id=usergroup_id,
                date_update=custom_date
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["date_update"], custom_date)

            # Test updating multiple fields at once
            result = update_user_group(
                usergroup_id=usergroup_id,
                name="Final Name",
                handle="final-handle",
                description="Final description",
                channel_ids=["C123", "C456"],
                date_update="1712345679.000000"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["name"], "Final Name")
            self.assertEqual(result["usergroup"]["handle"], "final-handle")
            self.assertEqual(result["usergroup"]["description"], "Final description")
            self.assertEqual(result["usergroup"]["prefs"]["channels"], ["C123", "C456"])
            self.assertEqual(result["usergroup"]["date_update"], "1712345679.000000")
            self.assertEqual(result["usergroup"]["updated_by"], "")

    def test_update_usergroup_empty_channel_ids(self):
        """Test updating with empty channel_ids list."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup with some channels
            create_result = create_user_group(
                name="Test Group",
                handle="test-group",
                channel_ids=["C123", "C456"]
            )
            usergroup_id = create_result["usergroup"]["id"]

            # Update with empty channel_ids
            result = update_user_group(
                usergroup_id=usergroup_id,
                channel_ids=[]
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["prefs"]["channels"], [])

    def test_update_usergroup_handle_with_none_values(self):
        """Test updating handle when some usergroups have None handle values."""
        with patch("slack.Usergroups.DB", DB):
            # Create usergroups with different handle states
            create_result1 = create_user_group(
                name="Group One",
                handle="group-one"
            )
            usergroup_id1 = create_result1["usergroup"]["id"]

            create_result2 = create_user_group(
                name="Group Two"
                # No handle specified
            )
            usergroup_id2 = create_result2["usergroup"]["id"]

            # Manually set handle to None for second group
            DB["usergroups"][usergroup_id2]["handle"] = None

            # Test updating handle of first group (should work)
            result = update_user_group(
                usergroup_id=usergroup_id1,
                handle="new-handle"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["handle"], "new-handle")

            # Test updating handle of second group (should work)
            result = update_user_group(
                usergroup_id=usergroup_id2,
                handle="another-handle"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["usergroup"]["handle"], "another-handle")

    def test_update_usergroup_auto_timestamp(self):
        """Test that date_update is automatically set when not provided."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group",
                handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]

            # Get original timestamp
            original_timestamp = DB["usergroups"][usergroup_id]["date_update"]

            # Update without providing date_update
            result = update_user_group(
                usergroup_id=usergroup_id,
                name="Updated Name"
            )
            self.assertTrue(result["ok"])
            
            # Check that timestamp was updated
            new_timestamp = result["usergroup"]["date_update"]
            self.assertNotEqual(original_timestamp, new_timestamp)
            
            # Verify it's a valid timestamp (numeric string)
            self.assertTrue(new_timestamp.replace(".", "").isdigit())

    def test_disable_usergroup(self):
        # Patch the DB in the Usergroups module with our test DB
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group", handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]  # Get created ID

            # Disable the usergroup
            result = disable_user_group(usergroup_id)
            self.assertTrue(result["ok"])
            self.assertTrue(DB["usergroups"][usergroup_id]["disabled"])

    def test_disable_usergroup_empty_id(self):
        """Test disabling a usergroup with an empty ID."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                disable_user_group,
                UserGroupIdInvalidError,
                "usergroup_id cannot be empty.",
                None,
                "",
            )

    def test_disable_usergroup_invalid_type(self):
        """Test disabling a usergroup with invalid type."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                disable_user_group,
                TypeError,
                "usergroup_id must be a string.",
                None,
                123
            )

    def test_disable_usergroup_nonexistent(self):
        """Test disabling a usergroup that doesn't exist."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                disable_user_group,
                UserGroupNotFoundError,
                "User group UG_NONEXISTENT not found.",
                None,
                "UG_NONEXISTENT"  # Non-existent usergroup_id
            )

    def test_disable_usergroup_already_disabled(self):
        """Test disabling a usergroup that is already disabled."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group", handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]
            
            # Disable it first
            disable_user_group(usergroup_id)
            
            # Try to disable it again
            self.assert_error_behavior(
                disable_user_group,
                UserGroupAlreadyDisabledError,
                f"User group {usergroup_id} is already disabled.",
                None,
                usergroup_id
            )

    def test_disable_usergroup_invalid_date_delete_type(self):
        """Test disabling a usergroup with invalid date_delete parameter."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group", handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]
            
            # Try to disable with invalid date_delete type
            self.assert_error_behavior(
                disable_user_group,
                TypeError,
                "date_delete must be a string if provided.",
                None,
                usergroup_id,  # Valid usergroup_id
                123  # Invalid date_delete type
            )

    def test_disable_usergroup_with_custom_date(self):
        """Test disabling a usergroup with custom date_delete parameter."""
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group", handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]
            
            custom_date = "1712345678.000000"
            
            # Disable with custom date
            result = disable_user_group(usergroup_id, date_delete=custom_date)
            self.assertTrue(result["ok"])
            self.assertTrue(DB["usergroups"][usergroup_id]["disabled"])
            self.assertEqual(DB["usergroups"][usergroup_id]["date_delete"], custom_date)

    def test_enable_usergroup(self):
        # Patch the DB in the Usergroups module with our test DB
        with patch("slack.Usergroups.DB", DB):
            # Create a usergroup
            create_result = create_user_group(
                name="Test Group", handle="test-group"
            )
            usergroup_id = create_result["usergroup"]["id"]

            # Disable Usergroup
            disable_user_group(usergroup_id)

            # Enable the usergroup
            result = enable_user_group(usergroup_id)
            self.assertTrue(result["ok"])
            self.assertFalse(DB["usergroups"][usergroup_id]["disabled"])

            # Test missing usergroup id
            self.assert_error_behavior(
                enable_user_group,
                UserGroupIdInvalidError,
                "usergroup_id cannot be empty.",
                None,
                ""
            )

    def test_valid_input_defaults(self):
        """Test with default arguments."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups()
            self.assertTrue(result["ok"])
            self.assertIsInstance(result["usergroups"], list)
            # By default, disabled groups are excluded, count and users are not included.
            self.assertEqual(len(result["usergroups"]), 2)
            for ug in result["usergroups"]:
                self.assertNotIn("user_count", ug)
                self.assertNotIn("users", ug)
                self.assertFalse(ug.get("disabled", False))

    def test_valid_input_with_team_id(self):
        """Test filtering by team_id."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups(team_id="teamA")
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 2) # ug1, ug3 are in teamA
            for ug in result["usergroups"]:
                self.assertEqual(ug["team_id"], "teamA")

    def test_valid_input_include_disabled(self):
        """Test with include_disabled=True."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups(include_disabled=True)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 3) # ug1, ug2, ug3

    def test_valid_input_include_count(self):
        """Test with include_count=True."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups(include_count=True)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 2) # ug1, ug3
            # Check if user_count is present for non-disabled groups
            ug1_data = next(filter(lambda x: x["id"] == "ug1", result["usergroups"]), None)
            ug3_data = next(filter(lambda x: x["id"] == "ug3", result["usergroups"]), None)
            self.assertIsNotNone(ug1_data)
            self.assertIn("user_count", ug1_data)
            self.assertEqual(ug1_data["user_count"], "2")  # user_count is string per Slack API
            self.assertIsNotNone(ug3_data)
            self.assertIn("user_count", ug3_data)
            self.assertEqual(ug3_data["user_count"], "0")  # user_count is string per Slack API


    def test_valid_input_include_users(self):
        """Test with include_users=True."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups(include_users=True)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 2) # ug1, ug3
            ug1_data = next(filter(lambda x: x["id"] == "ug1", result["usergroups"]), None)
            self.assertIsNotNone(ug1_data)
            self.assertIn("users", ug1_data)
            self.assertEqual(ug1_data["users"], ["U1", "U2"])
            # ug3 might not have 'users' key in source DB, so check it's not there or empty
            ug3_data = next(filter(lambda x: x["id"] == "ug3", result["usergroups"]), None)
            self.assertIsNotNone(ug3_data)
            self.assertNotIn("users", ug3_data) # As per original logic, if not in source, it's not added


    def test_valid_input_all_flags_true_and_team_id(self):
        """Test with all boolean flags True and a specific team_id."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups(
                team_id="teamA",
                include_disabled=True, # teamA has no disabled groups, so this won't change teamA results
                include_count=True,
                include_users=True
            )
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 2) # ug1, ug3 from teamA
            for ug in result["usergroups"]:
                self.assertEqual(ug["team_id"], "teamA")
                self.assertIn("user_count", ug)
                if ug["id"] == "ug1": # Only ug1 has users list
                    self.assertIn("users", ug)


    def test_invalid_team_id_type(self):
        """Test that invalid team_id type raises TypeError."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                func_to_call=list_user_groups,
                expected_exception_type=TypeError,
                expected_message="Argument 'team_id' must be a string or None, but got int.",
                team_id=123
            )

    def test_invalid_include_disabled_type(self):
        """Test that invalid include_disabled type raises TypeError."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                func_to_call=list_user_groups,
                expected_exception_type=TypeError,
                expected_message="Argument 'include_disabled' must be a boolean, but got str.",
                include_disabled="true"
            )

    def test_invalid_include_count_type(self):
        """Test that invalid include_count type raises TypeError."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                func_to_call=list_user_groups,
                expected_exception_type=TypeError,
                expected_message="Argument 'include_count' must be a boolean, but got int.",
                include_count=1
            )

    def test_invalid_include_users_type(self):
        """Test that invalid include_users type raises TypeError."""
        with patch("slack.Usergroups.DB", DB):
            self.assert_error_behavior(
                func_to_call=list_user_groups,
                expected_exception_type=TypeError,
                expected_message="Argument 'include_users' must be a boolean, but got list.",
                include_users=[]
            )

    def test_team_id_not_found(self):
        """Test with a team_id that has no user groups."""
        with patch("slack.Usergroups.DB", DB):
            result = list_user_groups(team_id="non_existent_team")
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["usergroups"]), 0)
