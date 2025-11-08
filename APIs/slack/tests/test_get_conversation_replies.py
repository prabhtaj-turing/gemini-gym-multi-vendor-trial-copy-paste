"""
Test cases for the get_conversation_replies function in the Slack Conversations API.

This module contains comprehensive test cases for retrieving conversation replies.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import ChannelNotFoundError, MessageNotFoundError
from .. import get_conversation_replies

class TestGetConversationReplies(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """
        Set up the test environment by patching the DB for conversation replies tests.
        """
        # Reset DB to initial state by creating specific test data
        global DB

        # Set up special test data for conversation replies tests
        DB = {
            "channels": {
                "C123": {
                    "id": "C123",
                    "name": "test-channel",
                    "messages": [
                        {
                            "ts": "1700000000.000000",
                            "text": "Parent Message",
                            "replies": [
                                {"ts": "1700000001.000000", "text": "Reply 1"},
                                {"ts": "1700000002.000000", "text": "Reply 2"},
                                {"ts": "1700000003.000000", "text": "Reply 3"},
                                {"ts": "1700000004.000000", "text": "Reply 4"},
                            ],
                        }
                    ],
                },
                "C_NO_MESSAGES": {"id": "C_NO_MESSAGES", "name": "no-messages"},
                "C_NO_REPLIES_THREAD": {
                    "id": "C_NO_REPLIES_THREAD",
                    "name": "no-replies-thread",
                    "messages": [
                        {
                            "ts": "1700000100.000000",
                            "text": "Thread with no replies attribute",
                        }
                    ],
                },
                "C_EMPTY_REPLIES": {
                    "id": "C_EMPTY_REPLIES",
                    "name": "empty-replies",
                    "messages": [
                        {
                            "ts": "1700000200.000000",
                            "text": "Thread with empty replies",
                            "replies": [],
                        }
                    ],
                },
            }
        }

        # Setup patch for all tests in this class
        self.patcher = patch("slack.Conversations.DB", DB)
        self.mock_db = self.patcher.start()

    def tearDown(self):
        """Clean up patches after tests"""
        self.patcher.stop()

    def test_valid_input_retrieves_replies(self):
        """Test that valid input successfully retrieves replies."""
        result = get_conversation_replies(channel="C123", ts="1700000000.000000")
        self.assertTrue(result.get("ok"))
        self.assertIsInstance(result.get("messages"), list)
        self.assertEqual(
            len(result.get("messages")), 4
        )  # There are 4 replies in our test data
        self.assertEqual(result.get("messages")[0]["text"], "Reply 1")

    def test_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="channel must be a string.",
            channel=123,  # Invalid type
            ts="1700000000.000000",
        )

    def test_invalid_ts_type(self):
        """Test that non-string ts raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="ts must be a string.",
            channel="C123",
            ts=123.456,  # Invalid type
        )

    def test_invalid_cursor_type(self):
        """Test that non-string cursor (when provided) raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="cursor must be a string or None.",
            channel="C123",
            ts="1700000000.000000",
            cursor=123,  # Invalid type
        )

    def test_valid_cursor_none(self):
        """Test that cursor=None is accepted."""
        result = get_conversation_replies(
            channel="C123", ts="1700000000.000000", cursor=None
        )
        self.assertTrue(result.get("ok"))

    def test_invalid_include_all_metadata_type(self):
        """Test that non-boolean include_all_metadata raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="include_all_metadata must be a boolean.",
            channel="C123",
            ts="1700000000.000000",
            include_all_metadata="true",  # Invalid type
        )

    def test_invalid_inclusive_type(self):
        """Test that non-boolean inclusive raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="inclusive must be a boolean.",
            channel="C123",
            ts="1700000000.000000",
            inclusive="yes",  # Invalid type
        )

    def test_invalid_latest_type(self):
        """Test that non-string latest (when provided) raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="latest must be a string or None.",
            channel="C123",
            ts="1700000000.000000",
            latest=12345.67,  # Invalid type
        )

    def test_valid_latest_none(self):
        """Test that latest=None is accepted."""
        result = get_conversation_replies(
            channel="C123", ts="1700000000.000000", latest=None
        )
        self.assertTrue(result.get("ok"))
        # Check if messages are filtered reasonably with latest=None (current time)
        # This depends on how 'current_time' is mocked or handled.
        # Our setup uses a recent enough time that some messages should appear.
        self.assertTrue(len(result.get("messages", [])) > 0)

    def test_invalid_limit_type(self):
        """Test that non-integer limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer.",
            channel="C123",
            ts="1700000000.000000",
            limit="10",  # Invalid type
        )

    def test_invalid_limit_type_bool_true(self):
        """Test that boolean True for limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer.",
            channel="C123",
            ts="1700000000.000000",
            limit=True,
        )

    def test_invalid_limit_type_bool_false(self):
        """Test that boolean False for limit raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="limit must be an integer.",
            channel="C123",
            ts="1700000000.000000",
            limit=False,
        )

    def test_invalid_oldest_type(self):
        """Test that non-string oldest raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=TypeError,
            expected_message="oldest must be a string.",
            channel="C123",
            ts="1700000000.000000",
            oldest=0,  # Invalid type
        )

    # Tests for core logic (to ensure validation doesn't break existing behavior)
    # These tests interact with the original logic via the mocked DB.
    def test_channel_not_found(self):
        """Test behavior when channel does not exist."""
        from slack.SimulationEngine.custom_errors import ChannelNotFoundError

        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=ChannelNotFoundError,
            expected_message="the C_NON_EXISTENT is not present in channels",
            channel="C_NON_EXISTENT",
            ts="1700000000.000000",
        )

    def test_thread_not_found(self):
        """Test behavior when thread (ts) does not exist in channel."""
        from slack.SimulationEngine.custom_errors import MessageNotFoundError

        self.assert_error_behavior(
            func_to_call=get_conversation_replies,
            expected_exception_type=MessageNotFoundError,
            expected_message="No message found against the ts: 0000000000.000000",
            channel="C123",
            ts="0000000000.000000",  # Non-existent ts
        )

    def test_limit_and_pagination(self):
        """Test limit and cursor-based pagination."""
        # Get first page (limit 1)
        result1 = get_conversation_replies(
            channel="C123", ts="1700000000.000000", limit=1, oldest="0"
        )
        self.assertTrue(result1.get("ok"))
        self.assertEqual(len(result1.get("messages")), 1)
        self.assertEqual(
            result1["messages"][0]["ts"], "1700000001.000000"
        )  # Oldest reply first
        self.assertTrue(result1.get("has_more"))
        next_cursor = result1.get("response_metadata", {}).get("next_cursor")
        self.assertIsNotNone(next_cursor)
        self.assertEqual(next_cursor, "1700000002.000000")  # TS of the *next* message

        # Get second page using cursor
        result2 = get_conversation_replies(
            channel="C123",
            ts="1700000000.000000",
            limit=1,
            cursor=next_cursor,
            oldest="0",
        )
        self.assertTrue(result2.get("ok"))
        self.assertEqual(len(result2.get("messages")), 1)
        self.assertEqual(
            result2["messages"][0]["ts"], "1700000003.000000"
        )  # This depends on the test data ordering & filtering

    def test_inclusive_filtering(self):
        """Test inclusive True/False for oldest/latest timestamps."""
        # Using fixed timestamps for reliable comparison
        parent_ts = "1700000000.000000"  # C123 parent
        # Replies in C123: ...001, ...002, ...003
        # Test inclusive=True
        result_incl = get_conversation_replies(
            channel="C123",
            ts=parent_ts,
            inclusive=True,
            oldest="1700000001.000000",
            latest="1700000002.000000",
        )
        self.assertTrue(result_incl.get("ok"))
        self.assertEqual(len(result_incl.get("messages")), 2)
        self.assertTrue(
            any(m["ts"] == "1700000001.000000" for m in result_incl["messages"])
        )
        self.assertTrue(
            any(m["ts"] == "1700000002.000000" for m in result_incl["messages"])
        )

        # Test inclusive=False
        result_excl = get_conversation_replies(
            channel="C123",
            ts=parent_ts,
            inclusive=False,
            oldest="1700000000.000000",
            latest="1700000003.000000",  # Range that should catch 001 and 002
        )
        self.assertTrue(result_excl.get("ok"))
        self.assertEqual(len(result_excl.get("messages")), 2)
        self.assertTrue(
            any(m["ts"] == "1700000001.000000" for m in result_excl["messages"])
        )
        self.assertTrue(
            any(m["ts"] == "1700000002.000000" for m in result_excl["messages"])
        )
        # Ensure boundaries are excluded
        self.assertFalse(
            any(m["ts"] == "1700000000.000000" for m in result_excl["messages"])
        )
        self.assertFalse(
            any(m["ts"] == "1700000003.000000" for m in result_excl["messages"])
        )

    def test_no_replies_in_thread_attribute(self):
        """Test channel with a thread that does not have a 'replies' attribute."""
        result = get_conversation_replies(
            channel="C_NO_REPLIES_THREAD", ts="1700000100.000000"
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(len(result.get("messages", [])), 0)
        self.assertFalse(result.get("has_more"))

    def test_empty_replies_list(self):
        """Test channel with a thread that has an empty 'replies' list."""
        result = get_conversation_replies(
            channel="C_EMPTY_REPLIES", ts="1700000200.000000"
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(len(result.get("messages", [])), 0)
        self.assertFalse(result.get("has_more"))

    def test_channel_with_no_messages_key(self):
        """Test channel that exists but has no 'messages' key (original logic path)."""
        result = get_conversation_replies(
            channel="C_NO_MESSAGES", ts="1700000000.000000"
        )
        self.assertTrue(result.get("ok"))  # As per original logic
        self.assertEqual(len(result.get("messages", [])), 0)
        self.assertFalse(result.get("has_more"))
