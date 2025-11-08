"""
Test cases for user photo management functions in the Slack Users API.

This module contains test cases for set_user_photo and delete_user_photo functions.
"""

import base64
import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import UserNotFoundError
from .. import (delete_user_photo, list_user_conversations, set_user_photo)

class TestUserPhoto(BaseTestCaseWithErrorHandler):
    """Test cases for user photo management functions."""

    def setUp(self):
        """Set up test database."""
        global DB
        DB = {
            "users": {
                "U123": {
                    "id": "U123",
                    "name": "user1",
                    "team_id": "T123",
                    "profile": {"email": "john.doe@example.com"},
                },
                "U456": {"id": "U456", "name": "user2", "team_id": "T123"},
                "U789": {"id": "U789", "name": "user3", "team_id": "T456"},
            },
        }
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def test_set_photo(self):
        """Test the setPhoto function for success and validation errors."""
        with patch("slack.Users.DB", DB):
            valid_image = base64.b64encode(b"test_image_data").decode("utf-8")

            # Test success case with all crop parameters
            result = set_user_photo("U123", valid_image, crop_x=10, crop_y=20, crop_w=30)
            self.assertTrue(result["ok"])
            self.assertEqual(DB["users"]["U123"]["profile"]["image"], valid_image)
            self.assertEqual(DB["users"]["U123"]["profile"]["image_crop_x"], 10)
            self.assertEqual(DB["users"]["U123"]["profile"]["image_crop_y"], 20)
            self.assertEqual(DB["users"]["U123"]["profile"]["image_crop_w"], 30)

            # Test invalid user_id type
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=TypeError,
                expected_message="user_id must be a string.",
                user_id=123,
                image=valid_image
            )

            # Test empty user_id value
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=ValueError,
                expected_message="user_id cannot be an empty string.",
                user_id="",
                image=valid_image
            )

            # Test empty image value
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=ValueError,
                expected_message="image cannot be an empty string.",
                user_id="U123",
                image=""
            )

            # Test invalid base64 image string
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=ValueError,
                expected_message="image must be a valid base64-encoded string.",
                user_id="U123",
                image="not-a-base64-string"
            )

            # Test user not found
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=UserNotFoundError,
                expected_message="User 'U999' not found.",
                user_id="U999",
                image=valid_image
            )

            # Test invalid crop parameter type
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=TypeError,
                expected_message="Cropping parameters (crop_x, crop_y, crop_w) must be integers.",
                user_id="U123",
                image=valid_image,
                crop_x="10"
            )

            # Test with specific types
            result = list_user_conversations(
                "U123", types="public_channel,private_channel"
            )
            self.assertTrue(result["ok"])
            # Test negative crop parameter value
            self.assert_error_behavior(
                func_to_call=set_user_photo,
                expected_exception_type=ValueError,
                expected_message="Cropping parameters must be non-negative.",
                user_id="U123",
                image=valid_image,
                crop_y=-10
            )

    @patch("slack.Users.DB", new_callable=lambda: {
        "users": {
            "U123": {"id": "U123", "profile": {"image": "image_data", "image_crop_x": 1}},
            "U456": {"id": "U456", "profile": {}},
        }
    })
    def test_deletePhoto_success(self, mock_db):
        """Test successful deletion of a user's profile photo."""
        response = delete_user_photo("U123")
        self.assertTrue(response["ok"])
        self.assertNotIn("image", mock_db["users"]["U123"]["profile"])
        self.assertNotIn("image_crop_x", mock_db["users"]["U123"]["profile"])

    def test_deletePhoto_invalid_user_id_type(self):
        """Test that deletePhoto raises TypeError for non-string user_id."""
        self.assert_error_behavior(
            func_to_call=delete_user_photo,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=123,
        )

    def test_deletePhoto_empty_user_id(self):
        """Test that deletePhoto raises ValueError for an empty user_id string."""
        self.assert_error_behavior(
            func_to_call=delete_user_photo,
            expected_exception_type=ValueError,
            expected_message="user_id must not be empty.",
            user_id="",
        )

    @patch("slack.Users.DB", new_callable=lambda: {"users": {}})
    def test_deletePhoto_user_not_found(self, mock_db):
        """Test that deletePhoto raises UserNotFoundError for a non-existent user."""
        self.assert_error_behavior(
            func_to_call=delete_user_photo,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID 'nonexistent' not found.",
            user_id="nonexistent",
        )

    @patch("slack.Users.DB", new_callable=lambda: {
        "users": {
            "U456": {"id": "U456", "profile": {}},
        }
    })
    def test_deletePhoto_no_photo_to_delete(self, mock_db):
        """Test that deletePhoto raises ValueError if the user has no photo."""
        self.assert_error_behavior(
            func_to_call=delete_user_photo,
            expected_exception_type=ValueError,
            expected_message="User has no profile photo to delete.",
            user_id="U456",
        )
