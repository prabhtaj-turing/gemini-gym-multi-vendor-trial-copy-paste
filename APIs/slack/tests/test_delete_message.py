"""
Test cases for the delete_chat_message function in the Slack Chat API.

This module contains comprehensive test cases for the delete_chat_message function,
including success scenarios and all error conditions.
"""

import time
from contextlib import contextmanager
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import ChannelNotFoundError, MessageNotFoundError
from .. import (delete_chat_message, post_chat_message)

DB = {}

@contextmanager
def patch_both_dbs(test_db):
    """Helper to patch both Chat.DB and utils.DB with the same test database."""
    with patch("slack.Chat.DB", test_db), patch("slack.SimulationEngine.utils.DB", test_db):
        yield


class TestDeleteMessage(BaseTestCaseWithErrorHandler):
    """Test cases for the delete_chat_message function."""

    def setUp(self):
        """Initialize test state."""
        global DB
        DB.clear()
        DB.update(
            {
                "current_user": {"id": "U123", "name": "user1", "is_admin": True},
                "users": {
                    "U123": {"id": "U123", "name": "user1"},
                    "U456": {"id": "U456", "name": "user2"},
                },
                "channels": {
                    "C123": {
                        "id": "C123",
                        "name": "general",
                        "is_archived": False,
                        "messages": [
                            {
                                "user": "U123",
                                "text": "Hello, World!",
                                "ts": "123456789.12345",
                                "thread_ts": "123456789.12345",
                                "replies": [
                                    {
                                        "user": "U456",
                                        "text": "Reply",
                                        "ts": "123456790.12345",
                                    }
                                ],
                            }
                        ],
                    },
                    "C456": {
                        "id": "C456",
                        "name": "random",
                        "is_archived": False,
                        "messages": [],
                    },
                    "C789": {
                        "id": "C789",
                        "name": "private-channel",
                        "is_archived": True,
                        "messages": [],
                    },
                },
                "scheduled_messages": [],
                "ephemeral_messages": [],
            }
        )

    def test_delete_non_admin_cannot_delete_others_message(self):
        """
        Ensure a non-admin user cannot delete another user's message.
        """
        with patch_both_dbs(DB):
            # Set current user to non-admin U456
            DB["current_user"] = {"id": "U456", "name": "user2", "is_admin": False}

            # Message by U123 already exists in setUp in channel C123
            target_ts = "123456789.12345"  # ts of message by U123

            self.assert_error_behavior(
                func_to_call=delete_chat_message,
                expected_exception_type=PermissionError,
                expected_message="You can only delete your own messages",
                channel="C123",
                ts=target_ts,
            )

    def test_delete_success(self):
        """Test successful message deletion."""
        # Use channel C123 (general) which exists and has messages
        with patch_both_dbs(DB):
            # Add a new message to delete to avoid conflicts with setUp state
            post_result = post_chat_message("C123", text="Message to delete")
            ts = post_result["message"]["ts"]
            result = delete_chat_message("C123", ts)
        self.assertEqual(result["ok"], True)

    def test_delete_message_required_params(self):
        """
        Test missing required parameters for delete message.
        """
        base_params = {
            "channel": "test_channel",
            "ts": "123",
        }

        required_params_tests = [
            ("channel", "channel is required"),
            ("ts", "ts is required"),
        ]

        for param_name, error_message in required_params_tests:
            self._test_required_parameter(
                delete_chat_message, param_name, error_message, **base_params
            )

    def test_delete_message_invalid_parameter_types(self):
        """
        Test invalid parameter types for delete message function.
        """
        base_params = {
            "channel": "test_channel",
            "ts": "123",
        }

        type_validation_tests = [
            ("channel", "channel must be a string"),
            ("ts", "ts must be a string"),
        ]

        for param_name, error_message in type_validation_tests:
            self._test_invalid_parameter_types(
                delete_chat_message,  # function under test
                param_name,  # parameter to replace with invalid types
                error_message,  # expected error message
                invalid_types=[
                    123,
                    [1, 2, 3],
                    {"key": "value"},
                ],  # invalid types to test
                **base_params,  # other valid parameters
            )

        # test that ts is a string of numbers
        self._test_invalid_parameter_types(
            delete_chat_message,  # function under test
            "ts",  # parameter to replace with invalid types
            "ts must be a string representing a number",  # expected error message
            invalid_types=[
                "string",
            ],  # invalid types to test
            **base_params,  # other valid parameters
        )

    def test_delete_channel_not_found(self):
        """Test delete message with non-existent channel."""
        # No DB modification, no patch needed
        self.assert_error_behavior(
            func_to_call=delete_chat_message,
            expected_exception_type=ChannelNotFoundError,
            expected_message="channel_not_found",
            channel="unknown",
            ts="12345",
        )

    def test_delete_message_not_found(self):
        """Test delete message with non-existent message timestamp."""
        # Use existing channel C123
        with patch_both_dbs(DB):
            self.assert_error_behavior(
                func_to_call=delete_chat_message,
                expected_exception_type=MessageNotFoundError,
                expected_message="message_not_found",
                channel="C123",
                ts="12131434",
            )

    def test_delete_message_with_channel_id(self):
        """Test delete_chat_message using channel ID (delete functions only support IDs)."""
        with patch_both_dbs(DB):
            # Add a test message first
            DB["channels"]["C456"] = {
                "id": "C456",
                "name": "test-channel", 
                "messages": [{"ts": "12345.000", "text": "Original message", "user": "U123"}]
            }
            
            result = delete_chat_message(channel="C456", ts="12345.000")
            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "C456")
            self.assertEqual(result["ts"], "12345.000")
            
            # Verify message was deleted from correct channel
            self.assertEqual(len(DB["channels"]["C456"]["messages"]), 0)

    def test_delete_message_nonexistent_channel_id(self):
        """Test delete_chat_message with non-existent channel ID."""
        with patch_both_dbs(DB):
            self.assert_error_behavior(
                delete_chat_message, 
                ChannelNotFoundError,
                "channel_not_found",
                channel="nonexistent", 
                ts="12345.000"
            )

    def _test_required_parameter(
        self, func_to_call, param_name, error_message, **base_kwargs
    ):
        """
        Helper method to test required parameters by setting them to None.

        Args:
            param_name: Name of the parameter to test
            error_message: Expected error message
            **base_kwargs: Base parameters for the API call
        """
        test_kwargs = base_kwargs.copy()
        test_kwargs[param_name] = None

        self.assert_error_behavior(
            func_to_call=func_to_call,
            expected_exception_type=ValueError,
            expected_message=error_message,
            **test_kwargs,
        )

    def _test_invalid_parameter_types(
        self,
        func_to_call,
        param_name,
        error_message_template,
        invalid_types,
        **base_kwargs,
    ):
        """
        Helper method to test invalid parameter types.

        Args:
            param_name: Name of the parameter to test
            error_message_template: Template for error message (e.g., "{} must be a string")
            **base_kwargs: Base parameters for the API call

        """
        for invalid_value in invalid_types:
            test_kwargs = base_kwargs.copy()
            test_kwargs[param_name] = invalid_value

            self.assert_error_behavior(
                func_to_call=func_to_call,
                expected_exception_type=ValueError,
                expected_message=error_message_template,
                **test_kwargs,
            )
