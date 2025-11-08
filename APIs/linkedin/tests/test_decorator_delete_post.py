import unittest
from typing import Dict, Any

import linkedin as LinkedinAPI
from linkedin.Posts import delete_post
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler
Posts_delete_post = delete_post

class TestDeletePost(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state before each test."""
        reset_db()
        # Add some test posts
        LinkedinAPI.DB["posts"] = {"post1": "data1", "post2": "data2"}

    def test_valid_input_existing_post(self):
        """Test deleting an existing post with a valid string ID."""
        post_id_to_delete = "post1"
        result = Posts_delete_post(post_id=post_id_to_delete)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {"status": f"Post {post_id_to_delete} deleted."})
        self.assertNotIn(post_id_to_delete, LinkedinAPI.DB["posts"]) # Verify deletion from DB

    def test_valid_input_non_existing_post(self):
        """Test attempting to delete a non-existing post with a valid string ID."""
        post_id_to_delete = "post3"
        self.assert_error_behavior(
            func_to_call=Posts_delete_post,
            expected_exception_type=KeyError,
            expected_message="'Post not found with id: " + post_id_to_delete + "'",
            post_id=post_id_to_delete
        )

    def test_invalid_post_id_type_int(self):
        """Test that an integer post_id raises TypeError."""
        invalid_id = 123
        self.assert_error_behavior(
            func_to_call=Posts_delete_post,
            expected_exception_type=TypeError,
            expected_message=f"Argument 'post_id' must be a string, but got {type(invalid_id).__name__}.",
            post_id=invalid_id
        )

    def test_invalid_post_id_type_list(self):
        """Test that a list post_id raises TypeError."""
        invalid_id = ["post1"]
        self.assert_error_behavior(
            func_to_call=Posts_delete_post,
            expected_exception_type=TypeError,
            expected_message=f"Argument 'post_id' must be a string, but got {type(invalid_id).__name__}.",
            post_id=invalid_id
        )

    def test_invalid_post_id_type_none(self):
        """Test that a None post_id raises TypeError."""
        invalid_id = None
        self.assert_error_behavior(
            func_to_call=Posts_delete_post,
            expected_exception_type=TypeError,
            expected_message=f"Argument 'post_id' must be a string, but got {type(invalid_id).__name__}.",
            post_id=invalid_id
        )

    def test_valid_input_empty_string_id_not_found(self):
        """Test deleting with an empty string ID (assuming it doesn't exist)."""
        post_id_to_delete = ""
        self.assert_error_behavior(
            func_to_call=Posts_delete_post,
            expected_exception_type=KeyError,
            expected_message="'Post not found with id: " + post_id_to_delete + "'",
            post_id=post_id_to_delete
        )

    def test_valid_input_empty_string_id_found(self):
        """Test deleting with an empty string ID (if it exists)."""
        post_id_to_delete = ""
        LinkedinAPI.DB["posts"][""] = "empty_data" # Add empty string key to DB
        result = Posts_delete_post(post_id=post_id_to_delete)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {"status": f"Post {post_id_to_delete} deleted."})
        self.assertNotIn(post_id_to_delete, LinkedinAPI.DB["posts"])
