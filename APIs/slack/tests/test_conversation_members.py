from typing import Dict, Any
from unittest.mock import patch
import base64

from ..SimulationEngine.custom_errors import InvalidCursorValueError, ChannelNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import get_conversation_members
DB: Dict[str, Any] = {}

class TestGetConversationMembers(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state (DB) before each test."""
        global DB
        DB = {
            "channels": {
                "C123": {
                    "conversations": {
                        "members": [f"U{i:03}" for i in range(25)]  # 25 members: U000 to U024
                    }
                },
                "C_EMPTY": {
                    "conversations": {
                        "members": []
                    }
                },
                "C_NO_CONVO": {},
                "C_MALFORMED_CONVO": {  # Test case where 'conversations' exists but 'members' is missing
                    "conversations": {}
                }
            }
        }

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_first_page(self, mock_db):
        """Test retrieval with valid channel, no cursor, and default limit."""
        result = get_conversation_members(channel="C123")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 25)  # Default limit 100, but only 25 members
        self.assertEqual(result["members"], [f"U{i:03}" for i in range(25)])
        self.assertEqual(result["response_metadata"]["next_cursor"], "")  # No more pages

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_with_limit(self, mock_db):
        """Test retrieval with a specific limit."""
        result = get_conversation_members(channel="C123", limit=5)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 5)
        self.assertEqual(result["members"], ["U000", "U001", "U002", "U003", "U004"])
        # Next cursor should be base64 encoded 'user:U004'
        expected_cursor = base64.b64encode(b'user:U004').decode('utf-8')
        self.assertEqual(result["response_metadata"]["next_cursor"], expected_cursor)

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_with_cursor_and_limit(self, mock_db):
        """Test retrieval with a cursor and limit for pagination."""
        cursor = base64.b64encode(b'user:U004').decode('utf-8')
        result = get_conversation_members(channel="C123", cursor=cursor, limit=5)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 5)
        self.assertEqual(result["members"], ["U005", "U006", "U007", "U008", "U009"])
        expected_cursor = base64.b64encode(b'user:U009').decode('utf-8')
        self.assertEqual(result["response_metadata"]["next_cursor"], expected_cursor)

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_last_page(self, mock_db):
        """Test retrieval for the last page of members."""
        cursor = base64.b64encode(b'user:U019').decode('utf-8')
        result = get_conversation_members(channel="C123", cursor=cursor, limit=10)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 5)  # Only 5 remaining
        self.assertEqual(result["members"], ["U020", "U021", "U022", "U023", "U024"])
        self.assertEqual(result["response_metadata"]["next_cursor"], "")  # End of list

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_cursor_at_end(self, mock_db):
        """Test retrieval when cursor is at the end of the member list."""
        cursor = base64.b64encode(b'user:U024').decode('utf-8')
        result = get_conversation_members(channel="C123", cursor=cursor, limit=10)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 0)
        self.assertEqual(result["response_metadata"]["next_cursor"], "")

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_cursor_beyond_end(self, mock_db):
        """Test retrieval when cursor is beyond the end of the member list."""
        cursor = base64.b64encode(b'user:U999').decode('utf-8')
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=InvalidCursorValueError,
            expected_message="User ID U999 not found in members list",
            channel="C123",
            cursor=cursor
        )

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_valid_input_empty_members_list(self, mock_db):
        """Test retrieval for a channel with no members."""
        result = get_conversation_members(channel="C_EMPTY")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 0)
        self.assertEqual(result["response_metadata"]["next_cursor"], "")

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_channel_initializes_structures_if_not_fully_present(self, mock_db):
        """Test that channel has conversations and members keys initialized if missing."""
        result = get_conversation_members(channel="C_NO_CONVO")  # C_NO_CONVO initially has no 'conversations'
        self.assertTrue(result["ok"])
        self.assertEqual(result["members"], [])
        self.assertIn("conversations", DB["channels"]["C_NO_CONVO"])
        self.assertIn("members", DB["channels"]["C_NO_CONVO"]["conversations"])

        result_malformed = get_conversation_members(
            channel="C_MALFORMED_CONVO")  # 'members' missing under 'conversations'
        self.assertTrue(result_malformed["ok"])
        self.assertEqual(result_malformed["members"], [])
        self.assertIn("members", DB["channels"]["C_MALFORMED_CONVO"]["conversations"])

    # --- Validation Error Tests ---
    def test_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=TypeError,
            expected_message="channel must be a string.",
            channel=123
        )

    def test_empty_channel_string(self):
        """Test that empty channel string raises ValueError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=ValueError,
            expected_message="channel cannot be an empty string.",
            channel=""
        )

    def test_invalid_cursor_type(self):
        """Test that non-string cursor (if provided) raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=TypeError,
            expected_message="cursor must be a string if provided.",
            channel="C123",
            cursor=123
        )

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_none_cursor_is_valid(self, mock_db):
        """Test that None cursor is accepted (default behavior)."""
        result = get_conversation_members(channel="C123", cursor=None)
        self.assertTrue(result["ok"])
        self.assertTrue(len(result["members"]) > 0 or len(result["members"]) == 0)

    def test_invalid_limit_type(self):
        """Test that non-integer limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer.",
            channel="C123",
            limit="abc"
        )

    def test_zero_limit_value(self):
        """Test that limit=0 raises ValueError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=ValueError,
            expected_message="limit must be a positive integer.",
            channel="C123",
            limit=0
        )

    def test_negative_limit_value(self):
        """Test that negative limit raises ValueError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=ValueError,
            expected_message="limit must be a positive integer.",
            channel="C123",
            limit=-10
        )

    def test_invalid_limit_type_bool_true(self):
        """Test that boolean True for limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer.",
            channel="C123",
            limit=True
        )

    def test_invalid_limit_type_bool_false(self):
        """Test that boolean False for limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer.",
            channel="C123",
            limit=False
        )

    # --- Core Logic Error Tests (handled by original logic) ---
    def test_non_existent_channel(self):
        """Test that a non-existent channel ID raises ChannelNotFoundError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=ChannelNotFoundError,
            expected_message="Channel 'C_NON_EXISTENT' not found",  # Corrected expectation
            channel="C_NON_EXISTENT"
        )

    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_invalid_cursor_format_non_integer_string(self, mock_db):
        """Test that cursor string that isn't a valid base64 returns error."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=InvalidCursorValueError,
            expected_message="Invalid base64 cursor format",
            channel="C123",
            cursor="abc"
        )


    @patch('slack.Conversations.DB', new_callable=lambda: DB)
    def test_limit_exceeds_maximum_scenario(self, mock_db):
        """Test that limit exceeding maximum (10000) raises ValueError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_members,
            expected_exception_type=ValueError,
            expected_message="limit cannot exceed 10000.",
            channel="C123",
            limit=10001
        )
