import unittest
import datetime
from instagram.Comment import add_comment
from instagram.SimulationEngine.custom_errors import MediaNotFoundError, UserNotFoundError
from typing import Dict, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler
from instagram.SimulationEngine.db import DB
from .test_common import reset_db

class TestCommentAddComment(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state before each test."""
        reset_db()
        # Initialize DB with some data for testing MediaNotFoundError and successful cases
        DB["media"] = {"existing_media_id": {"title": "Test Media"}}
        DB["comments"] = {}
        self.valid_media_id = "existing_media_id"
        self.valid_user_id = "user_test_123"
        self.valid_message = "A valid comment message."

    def test_successful_comment_creation(self):
        """Test that a comment is successfully created with valid inputs."""
        with self.assertRaises(UserNotFoundError):
            result = add_comment(
                media_id=self.valid_media_id,
                user_id=self.valid_user_id,
                message=self.valid_message
            )
            self.assertIsInstance(result, dict)
            self.assertIn("id", result)
            self.assertEqual(result["media_id"], self.valid_media_id)
            self.assertEqual(result["user_id"], self.valid_user_id)
            self.assertEqual(result["message"], self.valid_message)
            self.assertTrue(datetime.datetime.fromisoformat(result["timestamp"])) # Check if timestamp is valid ISO format

            # Verify the comment was added to the DB
            self.assertIn(result["id"], DB["comments"])
            self.assertEqual(DB["comments"][result["id"]]["message"], self.valid_message)

    # Test cases for media_id validation
    def test_invalid_media_id_type_integer(self):
        """Test TypeError for non-string media_id (integer)."""
        self.assert_error_behavior(
            add_comment,
            TypeError,
            "Argument 'media_id' must be a string.",
            media_id=123, # type: ignore
            user_id=self.valid_user_id,
            message=self.valid_message
        )

    def test_invalid_media_id_type_none(self):
        """Test TypeError for non-string media_id (None)."""
        self.assert_error_behavior(
            add_comment,
            TypeError,
            "Argument 'media_id' must be a string.",
            media_id=None, # type: ignore
            user_id=self.valid_user_id,
            message=self.valid_message
        )

    def test_empty_media_id_string(self):
        """Test ValueError for empty media_id string."""
        self.assert_error_behavior(
            add_comment,
            ValueError,
            "Field media_id cannot be empty.",
            media_id="",
            user_id=self.valid_user_id,
            message=self.valid_message
        )

    # Test cases for user_id validation
    def test_invalid_user_id_type(self):
        """Test TypeError for non-string user_id."""
        self.assert_error_behavior(
            add_comment,
            TypeError,
            "Argument 'user_id' must be a string.",
            media_id=self.valid_media_id,
            user_id=False, # type: ignore
            message=self.valid_message
        )

    def test_empty_user_id_string(self):
        """Test ValueError for empty user_id string."""
        self.assert_error_behavior(
            add_comment,
            ValueError,
            "Field user_id cannot be empty.",
            media_id=self.valid_media_id,
            user_id="",
            message=self.valid_message
        )

    # Test cases for message validation
    def test_invalid_message_type(self):
        """Test TypeError for non-string message."""
        self.assert_error_behavior(
            add_comment,
            TypeError,
            "Argument 'message' must be a string.",
            media_id=self.valid_media_id,
            user_id=self.valid_user_id,
            message=["list", "is", "not", "string"] # type: ignore
        )

    def test_empty_message_string(self):
        """Test ValueError for empty message string."""
        self.assert_error_behavior(
            add_comment,
            ValueError,
            "Field message cannot be empty.",
            media_id=self.valid_media_id,
            user_id=self.valid_user_id,
            message=""
        )

    # Test for core logic error: MediaNotFoundError
    def test_media_not_found(self):
        """Test that MediaNotFoundError is raised for a non-existent media_id."""
        self.assert_error_behavior(
            add_comment,
            MediaNotFoundError,
            "Media does not exist.", # Exact message from the function's core logic
            media_id="non_existent_media",
            user_id=self.valid_user_id,
            message=self.valid_message
        )

# Note: To run this test suite, ensure BaseTestCaseWithErrorHandler is available
# or replace the inheritance and self.assert_error_behavior calls with standard
# unittest mechanisms as shown in the example `assert_error_behavior` method.
# Example: if __name__ == '__main__': unittest.main()