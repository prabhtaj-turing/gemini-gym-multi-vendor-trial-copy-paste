"""
Test cases for the list_user_reactions function in the Slack Reactions API.

This module contains comprehensive test cases for the list_user_reactions function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import InvalidCursorValueError
from .. import list_user_reactions

class TestListUserReactions(BaseTestCaseWithErrorHandler):
    """Test cases for the list_user_reactions function."""

    def setUp(self):
        """Setup method to create a fresh DB for each test."""
        global DB
        from ..SimulationEngine.db import DB
        DB.clear()
        DB.update(
            {
                "channels": {
                    "C123": {
                        "messages": [
                            {
                                "ts": "1678886300.000000",
                                "user": "U01234567",
                                "text": "Hello!",
                                "reactions": [],
                            }
                        ]
                    },
                    "C456": {
                        "messages": [
                            {
                                "ts": "1678886400.000000",
                                "user": "U01234568",
                                "text": "Another message.",
                                "reactions": [
                                    {
                                        "name": "+1",
                                        "users": ["U01234567"],
                                        "count": 1,
                                    }
                                ],
                            }
                        ]
                    },
                },
                "users": {
                    "U01234567": {"id": "U01234567", "name": "user1"},
                    "U01234568": {"id": "U01234568", "name": "user2"},
                },
                "files": {},
                "scheduled_messages": [],
                "ephemeral_messages": [],
            }
        )

    def test_list_all_reactions(self):
        """Test listing all reactions without filters."""
        with patch("slack.Reactions.DB", DB):
            # List all reactions
            result = list_user_reactions()
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["reactions"]), 1)
            self.assertEqual(result["reactions"][0]["name"], "+1")
            self.assertEqual(result["reactions"][0]["channel"], "C456")

    def test_list_reactions_by_user(self):
        """Test filtering reactions by specific user."""
        with patch("slack.Reactions.DB", DB):
            # List reactions by a specific user
            result = list_user_reactions(user_id="U01234567")
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["reactions"]), 1)

            # List reactions by a different user (none should be found)
            result = list_user_reactions(user_id="U999")
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["reactions"]), 0)

    def test_list_reactions_pagination(self):
        """Test pagination functionality."""
        with patch("slack.Reactions.DB", DB):
            # First, add more reactions for pagination testing
            for i in range(250):  # Add enough for multiple pages
                DB["channels"]["C456"]["messages"][0]["reactions"].append(
                    {"name": f"test{i}", "users": ["U123"], "count": 1}
                )

            result = list_user_reactions(limit=100)  # using default
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["reactions"]), 100)  # First page
            self.assertIsNotNone(result["response_metadata"]["next_cursor"])

            result = list_user_reactions(
                limit=100, cursor=result["response_metadata"]["next_cursor"]
            )
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["reactions"]), 100)  # Second page
            self.assertIsNotNone(
                result["response_metadata"]["next_cursor"]
            )  # Should still have more

            # Get last page
            result = list_user_reactions(
                limit=100, cursor=result["response_metadata"]["next_cursor"]
            )
            self.assertTrue(result["ok"])
            self.assertEqual(
                len(result["reactions"]), 51
            )  # Check correct number of items
            self.assertIsNone(
                result["response_metadata"]["next_cursor"]
            )  # Should be none.

    def test_list_reactions_invalid_cursor(self):
        """Test error handling for invalid cursor values."""
        with patch("slack.Reactions.DB", DB):
            # Test invalid cursor - should raise InvalidCursorValueError
            self.assert_error_behavior(
                list_user_reactions,
                InvalidCursorValueError,
                "cursor must be a string representing a valid integer, got: 'invalid'",
                None,
                limit=100, cursor="invalid"
            )
            
            # Test negative cursor
            self.assert_error_behavior(
                list_user_reactions,
                InvalidCursorValueError,
                "cursor must be a string representing a valid integer, got: '-1'",
                None,
                cursor="-1"
            )

    def test_list_reactions_invalid_types(self):
        """Test that invalid parameter types raise TypeError."""
        with patch("slack.Reactions.DB", DB):
            # Test invalid user_id type
            self.assert_error_behavior(
                list_user_reactions,
                TypeError,
                "user_id must be a string or None.",
                None,
                user_id=123
            )
            
            # Test invalid full type
            self.assert_error_behavior(
                list_user_reactions,
                TypeError,
                "full must be a boolean.",
                None,
                full="true"
            )
            
            # Test invalid limit type
            self.assert_error_behavior(
                list_user_reactions,
                TypeError,
                "limit must be an integer.",
                None,
                limit="100"
            )
            
            # Test invalid cursor type
            self.assert_error_behavior(
                list_user_reactions,
                TypeError,
                "cursor must be a string or None.",
                None,
                cursor=123
            )

    def test_list_reactions_invalid_values(self):
        """Test that invalid parameter values raise appropriate errors."""
        with patch("slack.Reactions.DB", DB):
            # Test empty user_id
            self.assert_error_behavior(
                list_user_reactions,
                ValueError,
                "user_id cannot be empty.",
                None,
                user_id=""
            )
            
            # Test empty cursor
            self.assert_error_behavior(
                list_user_reactions,
                ValueError,
                "cursor cannot be empty.",
                None,
                cursor=""
            )
            
            # Test non-positive limit
            self.assert_error_behavior(
                list_user_reactions,
                ValueError,
                "limit must be a positive integer.",
                None,
                limit=0
            )

    def test_list_reactions_invalid_limit_bool_true(self):
        """Test that boolean True for limit raises TypeError."""
        with patch("slack.Reactions.DB", DB):
            self.assert_error_behavior(
                list_user_reactions,
                TypeError,
                "limit must be an integer.",
                None,
                limit=True
            )

    def test_list_reactions_invalid_limit_bool_false(self):
        """Test that boolean False for limit raises TypeError."""
        with patch("slack.Reactions.DB", DB):
            self.assert_error_behavior(
                list_user_reactions,
                TypeError,
                "limit must be an integer.",
                None,
                limit=False
            )


if __name__ == "__main__":
    import unittest
    unittest.main()
