"""
Test suite for the Google Drive Comments API create_file_comment function.

This module contains comprehensive tests for the comments.create_file_comment function,
including validation tests, error handling tests, and successful creation scenarios.
"""

import unittest
from .. import (create_file_comment, update_file_comment)
from gdrive.SimulationEngine.custom_errors import ValidationError, FileNotFoundError, PermissionDeniedError
from gdrive.SimulationEngine.db import DB
from gdrive.SimulationEngine.utils import _ensure_user
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCommentsCreate(BaseTestCaseWithErrorHandler):
    """Test cases for the comments.create_file_comment function."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset the database to a clean state
        DB.clear()
        DB.update({
            'users': {
                'me': {
                    'about': {
                        'user': {
                            'displayName': 'Test User',
                            'emailAddress': 'test@example.com'
                        }
                    },
                    'files': {
                        'test_file_123': {
                            'id': 'test_file_123',
                            'name': 'Test File',
                            'owners': ['test@example.com'],
                            'permissions': [
                                {
                                    'id': 'permission-1',
                                    'role': 'owner',
                                    'type': 'user',
                                    'emailAddress': 'test@example.com'
                                }
                            ]
                        },
                        'commenter_file': {
                            'id': 'commenter_file',
                            'name': 'Commenter File',
                            'owners': ['owner@example.com'],
                            'permissions': [
                                {
                                    'id': 'permission-1',
                                    'role': 'owner',
                                    'type': 'user',
                                    'emailAddress': 'owner@example.com'
                                },
                                {
                                    'id': 'permission-2',
                                    'role': 'commenter',
                                    'type': 'user',
                                    'emailAddress': 'test@example.com'
                                }
                            ]
                        },
                        'no_permission_file': {
                            'id': 'no_permission_file',
                            'name': 'No Permission File',
                            'owners': ['owner@example.com'],
                            'permissions': [
                                {
                                    'id': 'permission-1',
                                    'role': 'owner',
                                    'type': 'user',
                                    'emailAddress': 'owner@example.com'
                                }
                            ]
                        }
                    },
                    'comments': {},
                    'counters': {
                        'comment': 0
                    }
                }
            }
        })
        # Ensure user exists
        _ensure_user("me")
    
    def tearDown(self):
        """Clean up after each test method."""
        DB.clear()
    
    # Success test cases
    def test_create_simple_comment_success(self):
        """Test successful creation of a simple comment."""
        file_id = "test_file_123"
        comment_data = {
            "content": "This is a test comment"
        }
        
        result = create_file_comment(file_id, comment_data)
        
        # Verify basic structure
        self.assertEqual(result['kind'], 'drive#comment')
        self.assertEqual(result['fileId'], file_id)
        self.assertEqual(result['content'], "This is a test comment")
        self.assertEqual(result['htmlContent'], "This is a test comment")
        self.assertEqual(result['resolved'], False)
        self.assertEqual(result['deleted'], False)
        self.assertIn('id', result)
        self.assertIn('createdTime', result)
        self.assertIn('modifiedTime', result)
        self.assertIn('author', result)
        self.assertEqual(result['author']['displayName'], 'Test User')
        self.assertEqual(result['author']['emailAddress'], 'test@example.com')
        self.assertEqual(result['author']['kind'], 'drive#user')
        self.assertTrue(result['author']['me'])
        self.assertEqual(result['replies'], [])
    
    def test_create_comment_with_custom_author(self):
        """Test creation of comment with custom author information."""
        file_id = "test_file_123"
        comment_data = {
            "content": "Comment with custom author",
            "author": {
                "displayName": "John Doe",
                "emailAddress": "john.doe@example.com"
            }
        }
        
        result = create_file_comment(file_id, comment_data)
        
        self.assertEqual(result['content'], "Comment with custom author")
        self.assertEqual(result['author']['displayName'], 'John Doe')
        self.assertEqual(result['author']['emailAddress'], 'john.doe@example.com')
        self.assertEqual(result['author']['kind'], 'drive#user')
    
    def test_create_comment_with_quoted_content(self):
        """Test creation of comment with quoted file content."""
        file_id = "test_file_123"
        comment_data = {
            "content": "Comment about this specific text",
            "quotedFileContent": {
                "value": "The quoted text from the document",
                "mimeType": "text/plain"
            }
        }
        
        result = create_file_comment(file_id, comment_data)
        
        self.assertEqual(result['content'], "Comment about this specific text")
        self.assertIn('quotedFileContent', result)
        self.assertEqual(result['quotedFileContent']['value'], "The quoted text from the document")
        self.assertEqual(result['quotedFileContent']['mimeType'], "text/plain")
    
    def test_create_comment_none_body(self):
        """Test creation with None comment parameter."""
        file_id = "test_file_123"
        
        self.assert_error_behavior(
            create_file_comment,
            TypeError,
            "body must be a dictionary.",
            fileId=file_id,
            body=None
        )
    
    def test_create_comment_database_storage(self):
        """Test that comment is properly stored in the database."""
        file_id = "test_file_123"
        comment_data = {"content": "Test storage"}
        
        result = create_file_comment(file_id, comment_data)
        comment_id = result['id']
        
        # Verify the comment was stored
        self.assertIn(comment_id, DB['users']['me']['comments'])
        stored_comment = DB['users']['me']['comments'][comment_id]
        self.assertEqual(stored_comment['content'], "Test storage")
        self.assertEqual(stored_comment['fileId'], file_id)

    # Validation Error Tests
    def test_create_comment_empty_file_id(self):
        """Test validation error for empty file ID."""
        self.assert_error_behavior(
            create_file_comment,
            ValidationError,
            "Validation failed: fileId: String should have at least 1 character",
            fileId="",
            body={"content": "Test comment"}
        )
    
    def test_create_comment_empty_content(self):
        """Test successful creation with empty content."""
        file_id = "test_file_123"
        comment_data = {"content": ""}
        
        result = create_file_comment(file_id, comment_data)
        
        # Verify basic structure
        self.assertEqual(result['kind'], 'drive#comment')
        self.assertEqual(result['fileId'], file_id)
        self.assertEqual(result['content'], "")
        self.assertEqual(result['htmlContent'], "")
        self.assertIn('id', result)
    
    def test_create_comment_missing_content(self):
        """Test validation error for missing content."""
        self.assert_error_behavior(
            create_file_comment,
            ValidationError,
            "Validation failed: content: Field required",
            fileId="test_file_123",
            body={}  # No content provided
        )

    # File existence and permission tests
    def test_create_comment_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        self.assert_error_behavior(
            create_file_comment,
            FileNotFoundError,
            "File not found: nonexistent_file",
            fileId="nonexistent_file",
            body={"content": "Test comment"}
        )
    
    def test_create_comment_owner_permission(self):
        """Test successful creation when user is file owner."""
        file_id = "test_file_123"
        comment_data = {"content": "Owner can comment"}
        
        result = create_file_comment(file_id, comment_data)
        
        self.assertEqual(result['kind'], 'drive#comment')
        self.assertEqual(result['content'], "Owner can comment")
        self.assertIn('id', result)
    
    def test_create_comment_commenter_permission(self):
        """Test successful creation when user has commenter permission."""
        file_id = "commenter_file"
        comment_data = {"content": "Commenter can comment"}
        
        result = create_file_comment(file_id, comment_data)
        
        self.assertEqual(result['kind'], 'drive#comment')
        self.assertEqual(result['content'], "Commenter can comment")
        self.assertIn('id', result)
    
    def test_create_comment_permission_denied(self):
        """Test PermissionDeniedError when user has no permission to comment."""
        self.assert_error_behavior(
            create_file_comment,
            PermissionDeniedError,
            "User does not have permission to create comments on this file",
            fileId="no_permission_file",
            body={"content": "Should fail"}
        )

    def test_update_file_comment_invalid_email_author(self):
        """Test that updating a file comment with invalid email in author raises a ValidationError."""
        # First create a comment
        comment = create_file_comment(fileId="test_file_123", body={"content": "Test comment"})
        
        self.assert_error_behavior(
            update_file_comment,
            ValidationError,
            "Invalid comment update data: 1 validation error for CommentUpdateBodyModel\nauthor.emailAddress\n  value is not a valid email address: An email address must have an @-sign. [type=value_error, input_value='invalid_email', input_type=str]",
            fileId="test_file_123",
            commentId=comment["id"],
            body={"author": {"displayName": "Test User", "emailAddress": "invalid_email"}}
        )
    
    def test_create_comment_writer_permission(self):
        """Test successful creation when user has writer permission."""
        # Add writer permission file to setup
        DB['users']['me']['files']['writer_file'] = {
            'id': 'writer_file',
            'name': 'Writer File',
            'owners': ['test@example.com'],
            'permissions': [
                {
                    'id': 'permission-1',
                    'role': 'writer',
                    'type': 'user',
                    'emailAddress': 'owner@example.com'
                }
            ]
        }
        
        file_id = "writer_file"
        comment_data = {"content": "Writer can comment"}
        
        result = create_file_comment(file_id, comment_data)
        
        self.assertEqual(result['kind'], 'drive#comment')
        self.assertEqual(result['content'], "Writer can comment")
        self.assertIn('id', result)


if __name__ == '__main__':
    unittest.main() 