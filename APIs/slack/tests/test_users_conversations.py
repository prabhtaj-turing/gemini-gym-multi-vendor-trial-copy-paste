from typing import Dict, Any
from unittest.mock import patch

from ..SimulationEngine.custom_errors import UserNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import list_user_conversations
DB: Dict[str, Any] = {}

class TestUsersConversations(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state (DB) before each test."""
        global DB
        DB = {
            "channels": {
                "C001": {
                    "id": "C001",
                    "name": "general",
                    "is_private": False,
                    "is_archived": False,
                    "messages": [
                        {
                            "ts": "1234567890.123456",
                            "user": "U001",
                            "text": "Hello everyone!",
                            "reactions": [
                                {
                                    "name": "thumbsup",
                                    "users": ["U001", "U002"],
                                    "count": 2,
                                }
                            ],
                        },
                        {
                            "ts": "1234567891.123456",
                            "user": "U002",
                            "text": "Hi there!",
                            "reactions": [],
                        },
                    ],
                    "conversations": {},
                    "team_id": "T001",
                    "files": {},
                },
                "C002": {
                    "id": "C002",
                    "name": "private-channel",
                    "is_private": True,
                    "is_archived": False,
                    "messages": [
                        {
                            "ts": "1234567892.123456",
                            "user": "U001",
                            "text": "Private message",
                            "reactions": [
                                {"name": "eyes", "users": ["U003"], "count": 1}
                            ],
                        }
                    ],
                    "conversations": {},
                    "team_id": "T001",
                    "files": {},
                },
                "C003": {
                    "id": "C003",
                    "name": "archived-channel",
                    "is_private": False,
                    "is_archived": True,
                    "messages": [
                        {
                            "ts": "1234567893.123456",
                            "user": "U002",
                            "text": "This is archived",
                            "reactions": [],
                        }
                    ],
                    "conversations": {},
                    "team_id": "T001",
                    "files": {},
                },
                "C004": {
                    "id": "C004",
                    "name": "empty-channel",
                    "is_private": False,
                    "is_archived": False,
                    "messages": [],
                    "conversations": {},
                    "team_id": "T001",
                    "files": {},
                },
                "C005": {
                    "id": "C005",
                    "name": "im-channel",
                    "is_private": True,
                    "is_im": True,
                    "is_archived": False,
                    "messages": [
                        {
                            "ts": "1234567894.123456",
                            "user": "U001",
                            "text": "Direct message",
                            "reactions": [],
                        },
                        {
                            "ts": "1234567895.123456",
                            "user": "U004",
                            "text": "Reply to DM",
                            "reactions": [],
                        },
                    ],
                    "conversations": {},
                    "team_id": "T001",
                    "files": {},
                },
                "C006": {
                    "id": "C006",
                    "name": "mpim-channel",
                    "is_private": True,
                    "is_mpim": True,
                    "is_archived": False,
                    "messages": [
                        {
                            "ts": "1234567896.123456",
                            "user": "U001",
                            "text": "Group message",
                            "reactions": [
                                {
                                    "name": "rocket",
                                    "users": ["U002", "U003", "U004"],
                                    "count": 3,
                                }
                            ],
                        }
                    ],
                    "conversations": {},
                    "team_id": "T001",
                    "files": {},
                },
            },
            "users": {
                "U001": {"id": "U001", "name": "user1", "real_name": "User One"},
                "U002": {"id": "U002", "name": "user2", "real_name": "User Two"},
                "U003": {"id": "U003", "name": "user3", "real_name": "User Three"},
                "U004": {"id": "U004", "name": "user4", "real_name": "User Four"},
            },
        }

    # --- Successful Operation Tests ---
    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_basic_conversation_list_success(self, mock_db):
        """Test basic conversation listing for a user with message activity."""
        result = list_user_conversations(user_id="U001")

        self.assertTrue(result["ok"])
        self.assertIn("channels", result)
        self.assertIn("next_cursor", result)

        # U001 should be in channels: C001 (posted+reacted), C002 (posted), C005 (posted), C006 (posted)
        channel_ids = [channel["id"] for channel in result["channels"]]
        expected_channels = ["C001", "C002", "C005", "C006"]
        self.assertEqual(set(channel_ids), set(expected_channels))

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_user_with_reaction_only_activity(self, mock_db):
        """Test user who only reacted to messages (no posts)."""
        result = list_user_conversations(user_id="U003")

        self.assertTrue(result["ok"])

        # U003 should be in channels: C002 (reacted), C006 (reacted)
        channel_ids = [channel["id"] for channel in result["channels"]]
        expected_channels = ["C002", "C006"]
        self.assertEqual(set(channel_ids), set(expected_channels))

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_user_with_no_activity(self, mock_db):
        """Test user with no message or reaction activity."""
        result = list_user_conversations(user_id="U999")

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["channels"]), 0)
        self.assertIsNone(result["next_cursor"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_exclude_archived_channels(self, mock_db):
        """Test excluding archived channels from results."""
        result = list_user_conversations(user_id="U002", exclude_archived=True)

        self.assertTrue(result["ok"])

        # U002 should be in C001 (posted+reacted) but NOT C003 (archived)
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertIn("C001", channel_ids)
        self.assertNotIn("C003", channel_ids)

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_include_archived_channels(self, mock_db):
        """Test including archived channels in results."""
        result = list_user_conversations(user_id="U002", exclude_archived=False)

        self.assertTrue(result["ok"])

        # U002 should be in both C001 and C003 (archived)
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertIn("C001", channel_ids)
        self.assertIn("C003", channel_ids)

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_filter_by_types_public_channel(self, mock_db):
        """Test filtering by public_channel type only."""
        result = list_user_conversations(user_id="U001", types="public_channel")

        self.assertTrue(result["ok"])

        # U001 should only get C001 (public channel), not C002, C005, C006 (private/im/mpim)
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertEqual(channel_ids, ["C001"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_filter_by_types_private_channel(self, mock_db):
        """Test filtering by private_channel type only."""
        result = list_user_conversations(user_id="U001", types="private_channel")

        self.assertTrue(result["ok"])

        # U001 should only get C002 (private channel), not C005 (im) or C006 (mpim)
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertEqual(channel_ids, ["C002"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_filter_by_types_im(self, mock_db):
        """Test filtering by im type only."""
        result = list_user_conversations(user_id="U001", types="im")

        self.assertTrue(result["ok"])

        # U001 should only get C005 (im channel)
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertEqual(channel_ids, ["C005"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_filter_by_types_mpim(self, mock_db):
        """Test filtering by mpim type only."""
        result = list_user_conversations(user_id="U001", types="mpim")

        self.assertTrue(result["ok"])

        # U001 should only get C006 (mpim channel)
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertEqual(channel_ids, ["C006"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_filter_by_multiple_types(self, mock_db):
        """Test filtering by multiple channel types."""
        result = list_user_conversations(user_id="U001", types="public_channel,im")

        self.assertTrue(result["ok"])

        # U001 should get C001 (public) and C005 (im)
        channel_ids = [channel["id"] for channel in result["channels"]]
        expected_channels = ["C001", "C005"]
        self.assertEqual(set(channel_ids), set(expected_channels))

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_pagination_with_limit(self, mock_db):
        """Test pagination with limit parameter."""
        result = list_user_conversations(user_id="U001", limit=2)

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["channels"]), 2)
        self.assertIsNotNone(result["next_cursor"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_pagination_with_cursor(self, mock_db):
        """Test pagination with cursor parameter."""
        # First get initial results
        first_result = list_user_conversations(user_id="U001", limit=2)
        cursor = first_result["next_cursor"]

        # Then get next page
        result = list_user_conversations(user_id="U001", cursor=cursor, limit=2)

        self.assertTrue(result["ok"])
        self.assertIsInstance(result["channels"], list)

    # --- Input Validation Tests ---
    def test_invalid_user_id_type_integer(self):
        """Test that providing an integer for user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="user_id must be a non-empty string",
            user_id=12345,
        )

    def test_invalid_user_id_type_none(self):
        """Test that providing None for user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="user_id must be a non-empty string",
            user_id=None,
        )

    def test_empty_user_id_string(self):
        """Test that an empty user_id string raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="user_id must be a non-empty string",
            user_id="",
        )

    def test_whitespace_only_user_id(self):
        """Test that whitespace-only user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="user_id must be a non-empty string",
            user_id="   ",
        )

    def test_invalid_cursor_type(self):
        """Test that providing invalid cursor type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="cursor must be a string if provided",
            user_id="U001",
            cursor=123,
        )

    def test_invalid_cursor_value(self):
        """Test that providing invalid cursor value raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="cursor must be a valid integer string",
            user_id="U001",
            cursor="invalid",
        )

    def test_invalid_exclude_archived_type(self):
        """Test that providing invalid exclude_archived type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="exclude_archived must be a boolean",
            user_id="U001",
            exclude_archived="true",
        )

    def test_invalid_limit_type_string(self):
        """Test that providing string for limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer",
            user_id="U001",
            limit="100",
        )

    def test_invalid_limit_type_float(self):
        """Test that providing float for limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer",
            user_id="U001",
            limit=100.5,
        )

    def test_invalid_limit_value_zero(self):
        """Test that limit=0 raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="limit must be between 1 and 1000",
            user_id="U001",
            limit=0,
        )

    def test_invalid_limit_value_negative(self):
        """Test that negative limit raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="limit must be between 1 and 1000",
            user_id="U001",
            limit=-10,
        )

    def test_invalid_limit_value_too_large(self):
        """Test that limit > 1000 raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="limit must be between 1 and 1000",
            user_id="U001",
            limit=1001,
        )

    def test_invalid_types_type_integer(self):
        """Test that providing integer for types raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="types must be a string",
            user_id="U001",
            types=123,
        )

    def test_invalid_types_type_list(self):
        """Test that providing list for types raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=TypeError,
            expected_message="types must be a string",
            user_id="U001",
            types=["public_channel", "private_channel"],
        )

    def test_invalid_types_value_unknown_type(self):
        """Test that providing unknown channel type raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="types must be a comma-separated list of valid types: public_channel, private_channel, mpim, im",
            user_id="U001",
            types="unknown_type",
        )

    def test_invalid_types_value_empty_string(self):
        """Test that providing empty string for types raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="types must be a comma-separated list of valid types: public_channel, private_channel, mpim, im",
            user_id="U001",
            types="",
        )

    def test_invalid_types_value_mixed_valid_invalid(self):
        """Test that providing mix of valid and invalid types raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_conversations,
            expected_exception_type=ValueError,
            expected_message="types must be a comma-separated list of valid types: public_channel, private_channel, mpim, im",
            user_id="U001",
            types="public_channel,invalid_type",
        )

    # --- Edge Cases ---
    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_empty_channels_database(self, mock_db):
        """Test behavior when channels database is empty."""
        DB["channels"] = {}

        result = list_user_conversations(user_id="U001")

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["channels"]), 0)
        self.assertIsNone(result["next_cursor"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_missing_channels_key_in_database(self, mock_db):
        """Test behavior when channels key is missing from database."""
        del DB["channels"]

        result = list_user_conversations(user_id="U001")

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["channels"]), 0)
        self.assertIsNone(result["next_cursor"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_missing_users_key_in_database(self, mock_db):
        """Test behavior when users key is missing from database."""
        del DB["users"]

        result = list_user_conversations(user_id="U001")

        self.assertTrue(result["ok"])
        # Should still work, just return channels based on message activity
        self.assertIsInstance(result["channels"], list)

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_channel_with_malformed_messages(self, mock_db):
        """Test behavior with malformed message data."""
        DB["channels"]["C007"] = {
            "id": "C007",
            "name": "malformed",
            "is_private": False,
            "is_archived": False,
            "messages": [
                {
                    "ts": "1234567897.123456",
                    # Missing user field
                    "text": "Message without user",
                    "reactions": [],
                },
                {
                    "ts": "1234567898.123456",
                    "user": "U001",
                    "text": "Normal message",
                    "reactions": [
                        {
                            "name": "thumbsup",
                            # Missing users field
                            "count": 1,
                        }
                    ],
                },
            ],
            "conversations": {},
            "team_id": "T001",
            "files": {},
        }

        result = list_user_conversations(user_id="U001")

        self.assertTrue(result["ok"])
        # Should still include C007 because U001 posted a message there
        channel_ids = [channel["id"] for channel in result["channels"]]
        self.assertIn("C007", channel_ids)

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_types_with_whitespace(self, mock_db):
        """Test that types parameter handles whitespace correctly."""
        result = list_user_conversations(user_id="U001", types=" public_channel , im ")

        self.assertTrue(result["ok"])

        # Should get C001 (public) and C005 (im)
        channel_ids = [channel["id"] for channel in result["channels"]]
        expected_channels = ["C001", "C005"]
        self.assertEqual(set(channel_ids), set(expected_channels))

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_large_limit_within_bounds(self, mock_db):
        """Test that limit=1000 (maximum) works correctly."""
        result = list_user_conversations(user_id="U001", limit=1000)

        self.assertTrue(result["ok"])
        self.assertIsInstance(result["channels"], list)
        # Should return all channels for the user (no pagination needed)
        self.assertIsNone(result["next_cursor"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_cursor_at_end_of_results(self, mock_db):
        """Test cursor behavior when at end of results."""
        # Get total count first
        total_result = list_user_conversations(user_id="U001")
        total_count = len(total_result["channels"])

        # Use cursor at the end
        result = list_user_conversations(user_id="U001", cursor=str(total_count))

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["channels"]), 0)
        self.assertIsNone(result["next_cursor"])

    @patch("slack.Users.DB", new_callable=lambda: DB)
    def test_cursor_beyond_end_of_results(self, mock_db):
        """Test cursor behavior when beyond end of results."""
        result = list_user_conversations(user_id="U001", cursor="999")

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["channels"]), 0)
        self.assertIsNone(result["next_cursor"])
    
    def test_conversations_invalid_user_id(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test empty user_id
            with self.assertRaises(TypeError) as context:
                list_user_conversations("")
            self.assertEqual(
                str(context.exception), "user_id must be a non-empty string"
            )

            # Test None user_id
            with self.assertRaises(TypeError) as context:
                list_user_conversations(None)
            self.assertEqual(
                str(context.exception), "user_id must be a non-empty string"
            )

            # Test non-string user_id
            with self.assertRaises(TypeError) as context:
                list_user_conversations(123)
            self.assertEqual(
                str(context.exception), "user_id must be a non-empty string"
            )

            # Test whitespace-only user_id
            with self.assertRaises(TypeError) as context:
                list_user_conversations("   ")
            self.assertEqual(
                str(context.exception), "user_id must be a non-empty string"
            )

    def test_conversations_invalid_limit(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test string limit
            with self.assertRaises(TypeError) as context:
                list_user_conversations("U999", limit="100")
            self.assertEqual(str(context.exception), "limit must be an integer")

            # Test float limit
            with self.assertRaises(TypeError) as context:
                list_user_conversations("U999", limit=100.5)
            self.assertEqual(str(context.exception), "limit must be an integer")

            # Test boolean limit
            with self.assertRaises(TypeError) as context:
                list_user_conversations("U999", limit=True)
            self.assertEqual(str(context.exception), "limit must be an integer")

            # Test None limit
            with self.assertRaises(TypeError) as context:
                list_user_conversations("U999", limit=None)
            self.assertEqual(str(context.exception), "limit must be an integer")

    def test_conversations_invalid_exclude_archived(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test None exclude_archived
            with self.assertRaises(TypeError) as context:
                list_user_conversations("U123", exclude_archived=None)
            self.assertEqual(
                str(context.exception), "exclude_archived must be a boolean"
            )
    
    def test_conversations_limit_boundaries(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test limit = 0
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", limit=0)
            self.assertEqual(str(context.exception), "limit must be between 1 and 1000")

            # Test limit = -1
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", limit=-1)
            self.assertEqual(str(context.exception), "limit must be between 1 and 1000")

            # Test limit = 1001
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", limit=1001)
            self.assertEqual(str(context.exception), "limit must be between 1 and 1000")

    def test_conversations_types_validation(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test non-string types
            with self.assertRaises(TypeError) as context:
                list_user_conversations("U123", types=123)
            self.assertEqual(str(context.exception), "types must be a string")

            with self.assertRaises(TypeError) as context:
                list_user_conversations("U123", types=["public_channel"])
            self.assertEqual(str(context.exception), "types must be a string")

            # Test empty types string
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", types="")
            self.assertIn(
                "types must be a comma-separated list of valid types",
                str(context.exception),
            )

            # Test invalid channel type
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", types="invalid_type")
            self.assertIn(
                "types must be a comma-separated list of valid types",
                str(context.exception),
            )

            # Test mixed valid and invalid types
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", types="public_channel,invalid_type")
            self.assertIn(
                "types must be a comma-separated list of valid types",
                str(context.exception),
            )

    def test_conversations_invalid_cursor(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test non-integer string cursor
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", cursor="not_a_number")
            self.assertEqual(
                str(context.exception), "cursor must be a valid integer string"
            )

            # Test float string cursor
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", cursor="123.45")
            self.assertEqual(
                str(context.exception), "cursor must be a valid integer string"
            )

            # Test whitespace-only cursor
            with self.assertRaises(ValueError) as context:
                list_user_conversations("U123", cursor="   ")
            self.assertEqual(str(context.exception), "cursor must be a valid integer string")

    def test_conversations_default_types(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test with no types specified (should use defaults)
            result = list_user_conversations("U123")
            self.assertTrue(result["ok"])

            # Test with specific types
            result = list_user_conversations("U123", types="public_channel,private_channel")
            self.assertTrue(result["ok"])
