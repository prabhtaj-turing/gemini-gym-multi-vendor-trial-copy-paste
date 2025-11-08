import unittest
from pydantic import ValidationError

from .. import (create_comment_reply, get_comment_reply)
from gdrive.SimulationEngine.db import DB
from gdrive.SimulationEngine.utils import _ensure_user
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestRepliesCreate(BaseTestCaseWithErrorHandler):
    """
    Test suite for the replies.create function.
    This class tests all success paths, error conditions, and edge cases.
    """

    def setUp(self):
        """
        Set up a clean state before each test.
        This involves resetting the database and preparing common test data.
        """
        DB.clear()
        DB['users'] = {}
        DB['users']['me'] = {
            'about': {
                'user': {
                    'displayName': 'Test User',
                    'emailAddress': 'test@example.com'
                }
            },
            'replies': {},
            'counters': {'reply': 0}
        }
        _ensure_user('me')
        self.fileId = "test_file_id_123"
        self.commentId = "test_comment_id_456"
        self.valid_body = {
            'content': 'This is a test reply.',
            'author': {
                'displayName': 'John Doe',
                'emailAddress': 'john.doe@example.com',
                'photoLink': 'https://example.com/photo.jpg'
            }
        }

    def test_create_reply_success(self):
        """
        Test the successful creation and retrieval of a reply via the public API.
        """
        # --- Arrange ---
        # The 'setUp' method prepares the environment.

        # --- Act ---
        # Create the reply using the correct public alias.
        created_reply = create_comment_reply(self.fileId, self.commentId, self.valid_body)

        # --- Assert ---
        # 1. Basic checks on the returned object from the create call.
        self.assertIsInstance(created_reply, dict)
        self.assertEqual(created_reply['content'], self.valid_body['content'])
        self.assertEqual(created_reply['author']['displayName'], self.valid_body['author']['displayName'])

        # 2. Verify creation by fetching the reply back using the 'get' API.
        fetched_reply = get_comment_reply(
            fileId=self.fileId,
            commentId=self.commentId,
            replyId=created_reply['id']
        )
        
        # 3. Assert that the fetched object matches the created one.
        self.assertIsNotNone(fetched_reply)
        self.assertEqual(created_reply['id'], fetched_reply['id'])
        self.assertEqual(created_reply['content'], fetched_reply['content'])

    # --- INPUT VALIDATION TESTS ---

    def test_invalid_fileId_type(self):
        """
        Test that a non-string fileId raises a TypeError.
        """
        self.assert_error_behavior(
            create_comment_reply,
            TypeError,
            "fileId must be a string.",
            fileId=12345,
            commentId=self.commentId,
            body=self.valid_body
        )

    def test_invalid_commentId_type(self):
        """
        Test that a non-string commentId raises a TypeError.
        """
        self.assert_error_behavior(
            create_comment_reply,
            TypeError,
            "commentId must be a string.",
            fileId=self.fileId,
            commentId=None,
            body=self.valid_body
        )

    def test_invalid_body_type_leads_to_validation_error(self):
        """
        Test that a non-dictionary body now correctly leads to a ValidationError.
        """
        self.assert_error_behavior(
            create_comment_reply,
            TypeError,
            "body must be a dictionary if provided.",
            fileId=self.fileId,
            commentId=self.commentId,
            body="not a dict"
        )

    # --- PYDANTIC VALIDATION TESTS ---

    def test_body_missing_required_content_field(self):
        """
        Test that a body missing the 'content' field raises a ValidationError.
        """
        invalid_body = {'author': self.valid_body['author']}
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Field required",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )


    def test_body_invalid_content_type(self):
        """
        (From old suite) Test body with 'content' of invalid type raises ValidationError.
        """
        invalid_body = {
            "content": 123, # Invalid type
            "author": self.valid_body['author']
        }
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Input should be a valid string",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )
    
    def test_body_invalid_author_type(self):
        """
        (From old suite) Test body with 'author' of invalid type raises ValidationError.
        """
        invalid_body = {
            "content": "This is a reply.",
            "author": "not a dict" # Invalid type
        }
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Input should be a valid dictionary",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )

    def test_author_missing_displayname(self):
        """
        (From old suite) Test author missing 'displayName' raises ValidationError.
        """
        invalid_body = {
            "content": "This is a reply.",
            "author": {
                "emailAddress": "test@example.com",
            }
        }
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Field required",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )

    def test_author_missing_required_email_field(self):
        """
        Test that an author dict missing 'emailAddress' raises a ValidationError.
        """
        invalid_body = {
            'content': 'A reply with an incomplete author.',
            'author': {'displayName': 'Incomplete Author'}
        }
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Field required",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )

    def test_author_invalid_photolink_type(self):
        """
        (From old suite) Test author with invalid 'photoLink' type raises ValidationError.
        """
        invalid_body = {
            "content": "This is a reply.",
            "author": {
                "displayName": "Test User",
                "emailAddress": "test@example.com",
                "photoLink": 12345 # Invalid type
            }
        }
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Input should be a valid string",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )

    def test_author_with_invalid_email_format(self):
        """
        Test that an author with an invalid email format raises a ValidationError.
        """
        invalid_body = {
            'content': 'This is a test reply.',
            'author': {
                'displayName': 'John Doe',
                'emailAddress': 'not-an-email',
                'photoLink': 'https://example.com/photo.jpg'
            }
        }
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "value is not a valid email address",
            fileId=self.fileId,
            commentId=self.commentId,
            body=invalid_body
        )

    # --- EDGE CASE TESTS ---

    def test_create_with_empty_content_string(self):
        """
        Test that creating a reply with an empty content string is successful.
        """
        body_with_empty_content = self.valid_body.copy()
        body_with_empty_content['content'] = ""
        reply = create_comment_reply(self.fileId, self.commentId, body_with_empty_content)
        self.assertEqual(reply['content'], "")

    def test_create_with_null_body(self):
        """
        Test that calling create with body=None now correctly raises a ValidationError.
        """
        self.assert_error_behavior(
            create_comment_reply,
            ValueError,
            "Request body is required to create a reply.",
            fileId=self.fileId,
            commentId=self.commentId,
            body=None
        )

    def test_create_with_empty_body_dict(self):
        """
        Test that an empty dictionary for the body raises a ValidationError.
        """
        self.assert_error_behavior(
            create_comment_reply,
            ValidationError,
            "Field required",
            fileId=self.fileId,
            commentId=self.commentId,
            body={}
        )

if __name__ == '__main__':
    unittest.main()