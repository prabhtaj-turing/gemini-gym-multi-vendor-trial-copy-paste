from unittest.mock import patch


from ..SimulationEngine.custom_errors import InvalidUserError, ChannelNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import invite_to_conversation

DB = {}

class TestConversationsInvite(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the test DB before each test."""
        global DB
        # Reset DB to a known state for each test
        DB = {
            "users": {"user1", "user2", "user3", "valid_user"},
            "channels": {
                "channel1": {
                    "conversations": {
                        "members": ["user1"]
                    }
                },
                "empty_channel": {},
                "channel_no_conv": {}
            }
        }

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_new_users(self, mock_db):
        """Test inviting valid users not already in the channel."""
        result = invite_to_conversation(channel="channel1", users="user2,user3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])  # Order doesn't matter
        self.assertNotIn("error", result)
        self.assertCountEqual(DB["channels"]["channel1"]["conversations"]["members"], ["user1", "user2", "user3"])

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_some_existing_users(self, mock_db):
        """Test inviting a mix of existing and new valid users."""
        result = invite_to_conversation(channel="channel1", users="user1,user2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2"])  # Only user2 was newly added
        self.assertNotIn("error", result)
        self.assertCountEqual(DB["channels"]["channel1"]["conversations"]["members"], ["user1", "user2"])

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_all_existing_users(self, mock_db):
        """Test inviting only users already in the channel."""
        result = invite_to_conversation(channel="channel1", users="user1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], [])  # No users were newly added
        self.assertNotIn("error", result)
        self.assertCountEqual(DB["channels"]["channel1"]["conversations"]["members"], ["user1"])

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_force_false_with_invalid_users(self, mock_db):
        """Test invite fails (returns error) with invalid users when force=False."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=InvalidUserError,
            expected_message="invalid user found.",
            channel="channel1", users="user2,invalid_user", force=False
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_force_true_with_invalid_users(self, mock_db):
        """Test invite succeeds for valid users with invalid users when force=True."""
        result = invite_to_conversation(channel="channel1", users="user2,invalid_user,user3", force=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])  # user2 and user3 are valid and added
        self.assertCountEqual(result["invalid_users"], ["invalid_user"])  # user2 and user3 are valid and added
        self.assertCountEqual(DB["channels"]["channel1"]["conversations"]["members"], ["user1", "user2", "user3"])


    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_channel_not_found(self, mock_db):
        """Test inviting to a non-existent channel."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=ChannelNotFoundError,
            expected_message="channel not found.",
            channel="nonexistent_channel",
            users="user1"
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_channel_exists_but_no_members_key(self, mock_db):
        """Test inviting to a channel that exists with 'conversations' but lacks 'members'."""
        DB["channels"]["channel_no_members"] = {"conversations": {}}  # Add channel for test case
        result = invite_to_conversation(channel="channel_no_members", users="user3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel_no_members")
        self.assertCountEqual(result["invited"], ["user3"])
        self.assertIn("members", DB["channels"]["channel_no_members"]["conversations"])
        self.assertCountEqual(DB["channels"]["channel_no_members"]["conversations"]["members"], ["user3"])

    # --- Input Validation Tests ---

    def test_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=TypeError,
            expected_message="Argument 'channel' must be a string, but got int",
            channel=123,
            users="user1"
        )

    def test_empty_channel_string(self):
        """Test that an empty string channel raises ValueError."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=ValueError,
            expected_message="Argument 'channel' cannot be an empty string.",
            channel="",
            users="user1"
        )

    def test_invalid_users_type(self):
        """Test that non-string users raises TypeError."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=TypeError,
            expected_message="Argument 'users' must be a string, but got list",
            channel="channel1",
            users=["user1"]
        )

    def test_empty_users_string(self):
        """Test that an empty string users raises ValueError."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=ValueError,
            expected_message="Argument 'users' cannot be an empty string.",
            channel="channel1",
            users=""
        )

    def test_invalid_force_type(self):
        """Test that non-boolean force raises TypeError."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=TypeError,
            expected_message="Argument 'force' must be a boolean, but got str",
            channel="channel1",
            users="user1",
            force="not-a-bool"
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_force_default_value(self, mock_db):
        """Test that force defaults to False and invalid users cause failure."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=InvalidUserError,
            expected_message="invalid user found.",
            channel="channel1", users="user2,invalid_user"
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_users_with_whitespace(self, mock_db):
        """Test that user IDs with surrounding whitespace are handled correctly."""
        result = invite_to_conversation(channel="channel1", users=" user2 , user3 ")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])
        self.assertCountEqual(DB["channels"]["channel1"]["conversations"]["members"], ["user1", "user2", "user3"])

    # ==================== ALREADY_IN_CHANNEL_USERS FEATURE TEST CASES ====================

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_single_user(self, mock_db):
        """Test that a single user already in channel is reported in already_in_channel_users."""
        result = invite_to_conversation(channel="channel1", users="user1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertEqual(result["invited"], [])  # No new users added
        self.assertEqual(result["already_in_channel_users"], ["user1"])
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"], ["user1"]
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_multiple_users(self, mock_db):
        """Test that multiple users already in channel are reported in already_in_channel_users."""
        # First add user2 to the channel
        DB["channels"]["channel1"]["conversations"]["members"].append("user2")

        result = invite_to_conversation(channel="channel1", users="user1,user2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertEqual(result["invited"], [])  # No new users added
        self.assertCountEqual(result["already_in_channel_users"], ["user1", "user2"])
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"], ["user1", "user2"]
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_mixed_scenario(self, mock_db):
        """Test mix of new users and users already in channel."""
        # user1 is already in channel, user2 and user3 are new
        result = invite_to_conversation(channel="channel1", users="user1,user2,user3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])  # New users added
        self.assertEqual(
            result["already_in_channel_users"], ["user1"]
        )  # Already in channel
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"],
            ["user1", "user2", "user3"],
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_with_invalid_users_force_true(self, mock_db):
        """Test already_in_channel_users with invalid users when force=True."""
        result = invite_to_conversation(
            channel="channel1", users="user1,invalid_user", force=True
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertEqual(result["invited"], [])  # No new users added
        self.assertEqual(
            result["already_in_channel_users"], ["user1"]
        )  # Already in channel
        self.assertEqual(result["invalid_users"], ["invalid_user"])  # Invalid user
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"], ["user1"]
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_with_invalid_users_force_false(self, mock_db):
        """Test that already_in_channel_users is not returned when force=False and invalid users exist."""
        self.assert_error_behavior(
            func_to_call=invite_to_conversation,
            expected_exception_type=InvalidUserError,
            expected_message="invalid user found.",
            channel="channel1",
            users="user1,invalid_user",
            force=False,
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_not_present_when_no_existing_users(self, mock_db):
        """Test that already_in_channel_users is not present when no users are already in channel."""
        result = invite_to_conversation(channel="channel1", users="user2,user3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])
        self.assertNotIn(
            "already_in_channel_users", result
        )  # Key should not be present
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"],
            ["user1", "user2", "user3"],
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_duplicate_invitation(self, mock_db):
        """Test inviting the same user multiple times in one call."""
        result = invite_to_conversation(channel="channel1", users="user1,user1,user2")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2"])  # user2 added once
        self.assertCountEqual(
            result["already_in_channel_users"], ["user1", "user1"]
        )  # user1 appears twice
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"], ["user1", "user2"]
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_complex_mixed_scenario(self, mock_db):
        """Test complex scenario with new users, existing users, and invalid users."""
        # Setup: user1 already in channel, user2 and user3 are new, invalid_user is invalid
        result = invite_to_conversation(
            channel="channel1", users="user1,user2,user3,invalid_user", force=True
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])  # New valid users
        self.assertEqual(
            result["already_in_channel_users"], ["user1"]
        )  # Already in channel
        self.assertEqual(result["invalid_users"], ["invalid_user"])  # Invalid user
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"],
            ["user1", "user2", "user3"],
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_all_users_already_in_channel(self, mock_db):
        """Test when all users are already in the channel."""
        # Add user2 and user3 to channel first
        DB["channels"]["channel1"]["conversations"]["members"].extend(
            ["user2", "user3"]
        )

        result = invite_to_conversation(channel="channel1", users="user1,user2,user3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertEqual(result["invited"], [])  # No new users added
        self.assertCountEqual(
            result["already_in_channel_users"], ["user1", "user2", "user3"]
        )
        self.assertCountEqual(
            DB["channels"]["channel1"]["conversations"]["members"],
            ["user1", "user2", "user3"],
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_already_in_channel_users_response_structure(self, mock_db):
        """Test that the response structure is correct when already_in_channel_users is present."""
        result = invite_to_conversation(channel="channel1", users="user1")

        # Verify response structure
        self.assertIn("ok", result)
        self.assertIn("channel", result)
        self.assertIn("invited", result)
        self.assertIn("already_in_channel_users", result)

        # Verify types
        self.assertIsInstance(result["ok"], bool)
        self.assertIsInstance(result["channel"], str)
        self.assertIsInstance(result["invited"], list)
        self.assertIsInstance(result["already_in_channel_users"], list)

        # Verify values
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertEqual(result["invited"], [])
        self.assertEqual(result["already_in_channel_users"], ["user1"])

    # --- Tests for Validation Order Bug Fix ---

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_channel_validation_before_user_validation(self, mock_db):
        """Test that channel validation happens before user validation for efficiency."""
        # Test with invalid channel and invalid users
        # Before the fix: would validate users first, then fail on channel
        # After the fix: should fail on channel immediately without processing users
        with self.assertRaises(ChannelNotFoundError) as context:
            invite_to_conversation(channel="nonexistent_channel", users="invalid_user1,invalid_user2")
        
        self.assertEqual(str(context.exception), "channel not found.")
        
        # Verify that the function failed fast on channel validation
        # and didn't process the invalid users (which would be inefficient)

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_efficient_validation_with_force_true_invalid_channel(self, mock_db):
        """Test that force=True doesn't help when channel is invalid (validation order fix)."""
        # Even with force=True, invalid channel should fail immediately
        with self.assertRaises(ChannelNotFoundError) as context:
            invite_to_conversation(
                channel="nonexistent_channel", 
                users="invalid_user1,invalid_user2", 
                force=True
            )
        
        self.assertEqual(str(context.exception), "channel not found.")

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_validation_order_preserves_user_information(self, mock_db):
        """Test that validation order doesn't lose user information when channel is valid."""
        # Test with valid channel but invalid users
        with self.assertRaises(InvalidUserError) as context:
            invite_to_conversation(channel="channel1", users="invalid_user1,invalid_user2")
        
        self.assertEqual(str(context.exception), "invalid user found.")
        
        # Verify that user validation still works correctly when channel is valid

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_efficiency_with_large_user_list_invalid_channel(self, mock_db):
        """Test efficiency improvement with large user list and invalid channel."""
        # Create a large list of users (some valid, some invalid)
        large_user_list = ",".join([f"user{i}" for i in range(1, 51)])  # 50 users
        
        # With invalid channel, should fail immediately without processing 50 users
        with self.assertRaises(ChannelNotFoundError) as context:
            invite_to_conversation(channel="nonexistent_channel", users=large_user_list)
        
        self.assertEqual(str(context.exception), "channel not found.")

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_validation_order_with_valid_channel_invalid_users(self, mock_db):
        """Test that valid channel allows proper user validation."""
        # Valid channel, invalid users - should get InvalidUserError, not ChannelNotFoundError
        with self.assertRaises(InvalidUserError) as context:
            invite_to_conversation(channel="channel1", users="invalid_user1,invalid_user2")
        
        self.assertEqual(str(context.exception), "invalid user found.")

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_validation_order_with_valid_channel_valid_users(self, mock_db):
        """Test that valid channel and valid users work correctly."""
        result = invite_to_conversation(channel="channel1", users="user2,user3")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_validation_order_force_true_scenario(self, mock_db):
        """Test validation order with force=True and mixed valid/invalid users."""
        # Valid channel, mix of valid and invalid users with force=True
        result = invite_to_conversation(
            channel="channel1", 
            users="user2,invalid_user1,user3,invalid_user2", 
            force=True
        )
        
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "channel1")
        self.assertCountEqual(result["invited"], ["user2", "user3"])
        self.assertCountEqual(result["invalid_users"], ["invalid_user1", "invalid_user2"])

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_validation_order_performance_improvement(self, mock_db):
        """Test that the validation order improvement works as expected."""
        # This test demonstrates the performance improvement
        # Before fix: would process all users, then fail on channel
        # After fix: fails immediately on channel validation
        
        # Test with a scenario that would be inefficient with the old order
        many_users = ",".join([f"user{i}" for i in range(1, 21)])  # 20 users
        
        # Should fail immediately on channel, not after processing 20 users
        start_time = __import__('time').time()
        with self.assertRaises(ChannelNotFoundError):
            invite_to_conversation(channel="nonexistent_channel", users=many_users)
        end_time = __import__('time').time()
        
        # The operation should be fast (channel validation is O(1))
        # This is more of a conceptual test - the real benefit is in avoiding
        # unnecessary user processing when channel is invalid
        self.assertLess(end_time - start_time, 1.0)  # Should complete quickly

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_validation_order_consistency_with_other_functions(self, mock_db):
        """Test that validation order is consistent with other conversation functions."""
        # This test ensures that the invite function follows the same pattern
        # as other functions that validate primary resources first
        
        # Test that channel validation happens first (consistent with other functions)
        with self.assertRaises(ChannelNotFoundError) as context:
            invite_to_conversation(channel="nonexistent_channel", users="user1")
        
        self.assertEqual(str(context.exception), "channel not found.")
        
        # Verify that the function follows the same validation pattern
        # as other conversation functions (channel first, then users)
