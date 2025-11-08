"""
Comprehensive tests for the get_comment_reply function in Google Drive API.
"""

import copy
import unittest
from typing import Dict, Any, Optional
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (get_comment_reply, Replies)
from gdrive.SimulationEngine.db import DB
from gdrive.SimulationEngine.custom_errors import ValidationError
from gdrive.SimulationEngine.utils import _ensure_user
from .. import get_comment_reply


class TestRepliesGet(BaseTestCaseWithErrorHandler):
    """Test cases for the Replies.get function."""
    
    def setUp(self):
        """Set up test environment before each test."""
        global DB
        self.db_backup = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "users": {
                "me": {
                    "about": {
                        "user": {
                            "displayName": "Test User",
                            "emailAddress": "test@example.com",
                            "photoLink": "https://example.com/photo.jpg",
                            "kind": "drive#user",
                            "me": True,
                            "permissionId": "user-perm-id"
                        }
                    },
                    "files": {},
                    "drives": {},
                    "comments": {},
                    "replies": {
                        "reply-1": {
                            "kind": "drive#reply",
                            "id": "reply-1",
                            "fileId": "file-1",
                            "commentId": "comment-1",
                            "content": "This is a test reply",
                            "createdTime": "2023-01-01T10:00:00Z",
                            "modifiedTime": "2023-01-01T10:00:00Z",
                            "author": {
                                "displayName": "Test User",
                                "emailAddress": "test@example.com",
                                "photoLink": "https://example.com/photo.jpg"
                            },
                            "deleted": False
                        },
                        "reply-2": {
                            "kind": "drive#reply",
                            "id": "reply-2",
                            "fileId": "file-1",
                            "commentId": "comment-1",
                            "content": "This reply was deleted",
                            "createdTime": "2023-01-01T11:00:00Z",
                            "modifiedTime": "2023-01-01T11:00:00Z",
                            "author": {
                                "displayName": "Test User",
                                "emailAddress": "test@example.com",
                                "photoLink": "https://example.com/photo.jpg"
                            },
                            "deleted": True
                        },
                        "reply-3": {
                            "kind": "drive#reply",
                            "id": "reply-3",
                            "fileId": "file-2",
                            "commentId": "comment-2",
                            "content": "Reply on different file",
                            "createdTime": "2023-01-01T12:00:00Z",
                            "modifiedTime": "2023-01-01T12:00:00Z",
                            "author": {
                                "displayName": "Other User",
                                "emailAddress": "other@example.com",
                                "photoLink": ""
                            },
                            "deleted": False
                        }
                    },
                    "labels": {},
                    "accessproposals": {},
                    "counters": {
                        "file": 0,
                        "drive": 0,
                        "comment": 0,
                        "reply": 3,
                        "label": 0,
                        "accessproposal": 0,
                        "revision": 0,
                        "change_token": 0
                    }
                }
            }
        })
        Replies.DB = DB

    def tearDown(self):
        """Clean up after each test."""
        global DB
        DB.clear()
        DB.update(self.db_backup)
    
    # --- SUCCESS TESTS ---
    
    def test_get_existing_reply_success(self):
        """Test successful retrieval of an existing reply."""
        result = get_comment_reply("file-1", "comment-1", "reply-1")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "reply-1")
        self.assertEqual(result["fileId"], "file-1")
        self.assertEqual(result["commentId"], "comment-1")
        self.assertEqual(result["content"], "This is a test reply")
        self.assertEqual(result["kind"], "drive#reply")
        self.assertFalse(result["deleted"])
        self.assertIn("author", result)
        self.assertEqual(result["author"]["displayName"], "Test User")
    
    def test_get_nonexistent_reply_returns_none(self):
        """Test that getting a non-existent reply returns None."""
        result = get_comment_reply("file-1", "comment-1", "nonexistent-reply")
        self.assertIsNone(result)
    
    def test_get_deleted_reply_without_include_deleted(self):
        """Test that deleted replies return None when includeDeleted is False."""
        result = get_comment_reply("file-1", "comment-1", "reply-2", includeDeleted=False)
        self.assertIsNone(result)
    
    def test_get_deleted_reply_with_include_deleted(self):
        """Test that deleted replies are returned when includeDeleted is True."""
        result = get_comment_reply("file-1", "comment-1", "reply-2", includeDeleted=True)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "reply-2")
        self.assertEqual(result["content"], "This reply was deleted")
        self.assertTrue(result["deleted"])
    
    def test_get_with_explicit_include_deleted_false(self):
        """Test explicit includeDeleted=False parameter."""
        result = get_comment_reply("file-1", "comment-1", "reply-1", includeDeleted=False)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "reply-1")
        self.assertFalse(result["deleted"])
    
    def test_get_reply_from_different_file(self):
        """Test getting a reply from a different file."""
        result = get_comment_reply("file-2", "comment-2", "reply-3")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "reply-3")
        self.assertEqual(result["fileId"], "file-2")
        self.assertEqual(result["commentId"], "comment-2")
        self.assertEqual(result["content"], "Reply on different file")
    
    def test_get_reply_wrong_file_returns_none(self):
        """Test that getting a reply with wrong fileId returns None."""
        result = get_comment_reply("wrong-file", "comment-1", "reply-1")
        self.assertIsNone(result)
    
    def test_get_reply_wrong_comment_returns_none(self):
        """Test that getting a reply with wrong commentId returns None."""
        result = get_comment_reply("file-1", "wrong-comment", "reply-1")
        self.assertIsNone(result)
    
    # --- INPUT VALIDATION TESTS ---
    
    # fileId validation tests
    def test_invalid_fileid_type_integer(self):
        """Test that integer fileId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "fileId must be a string.",
            fileId=123,
            commentId="comment-1",
            replyId="reply-1"
        )
    
    def test_invalid_fileid_type_none(self):
        """Test that None fileId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "fileId must be a string.",
            fileId=None,
            commentId="comment-1",
            replyId="reply-1"
        )
    
    def test_invalid_fileid_type_list(self):
        """Test that list fileId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "fileId must be a string.",
            fileId=["file-1"],
            commentId="comment-1",
            replyId="reply-1"
        )
    
    def test_invalid_fileid_empty_string(self):
        """Test that empty fileId raises ValidationError."""
        self.assert_error_behavior(
            get_comment_reply,
            ValidationError,
            "fileId cannot be empty.",
            fileId="",
            commentId="comment-1",
            replyId="reply-1"
        )
    
    # commentId validation tests
    def test_invalid_commentid_type_integer(self):
        """Test that integer commentId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "commentId must be a string.",
            fileId="file-1",
            commentId=123,
            replyId="reply-1"
        )
    
    def test_invalid_commentid_type_float(self):
        """Test that float commentId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "commentId must be a string.",
            fileId="file-1",
            commentId=3.14,
            replyId="reply-1"
        )
    
    def test_invalid_commentid_type_dict(self):
        """Test that dict commentId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "commentId must be a string.",
            fileId="file-1",
            commentId={"id": "comment-1"},
            replyId="reply-1"
        )
    
    def test_invalid_commentid_empty_string(self):
        """Test that empty commentId raises ValidationError."""
        self.assert_error_behavior(
            get_comment_reply,
            ValidationError,
            "commentId cannot be empty.",
            fileId="file-1",
            commentId="",
            replyId="reply-1"
        )
    
    # replyId validation tests
    def test_invalid_replyid_type_boolean(self):
        """Test that boolean replyId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "replyId must be a string.",
            fileId="file-1",
            commentId="comment-1",
            replyId=True
        )
    
    def test_invalid_replyid_type_tuple(self):
        """Test that tuple replyId raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "replyId must be a string.",
            fileId="file-1",
            commentId="comment-1",
            replyId=("reply-1",)
        )
    
    def test_invalid_replyid_empty_string(self):
        """Test that empty replyId raises ValidationError."""
        self.assert_error_behavior(
            get_comment_reply,
            ValidationError,
            "replyId cannot be empty.",
            fileId="file-1",
            commentId="comment-1",
            replyId=""
        )
    
    # includeDeleted validation tests
    def test_invalid_include_deleted_type_string(self):
        """Test that string includeDeleted raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "includeDeleted must be a boolean.",
            fileId="file-1",
            commentId="comment-1",
            replyId="reply-1",
            includeDeleted="true"
        )
    
    def test_invalid_include_deleted_type_integer(self):
        """Test that integer includeDeleted raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "includeDeleted must be a boolean.",
            fileId="file-1",
            commentId="comment-1",
            replyId="reply-1",
            includeDeleted=1
        )
    
    def test_invalid_include_deleted_type_none(self):
        """Test that None includeDeleted raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "includeDeleted must be a boolean.",
            fileId="file-1",
            commentId="comment-1",
            replyId="reply-1",
            includeDeleted=None
        )
    
    def test_invalid_include_deleted_type_list(self):
        """Test that list includeDeleted raises TypeError."""
        self.assert_error_behavior(
            get_comment_reply,
            TypeError,
            "includeDeleted must be a boolean.",
            fileId="file-1",
            commentId="comment-1",
            replyId="reply-1",
            includeDeleted=[False]
        )
    
    # --- EDGE CASE TESTS ---
    
    def test_get_with_valid_edge_case_ids(self):
        """Test with valid edge case ID formats."""
        # Add a reply with edge case ID
        DB["users"]["me"]["replies"]["a"] = {
            "kind": "drive#reply",
            "id": "a",
            "fileId": "b",
            "commentId": "c",
            "content": "Edge case reply",
            "createdTime": "2023-01-01T12:00:00Z",
            "modifiedTime": "2023-01-01T12:00:00Z",
            "author": {
                "displayName": "Edge User",
                "emailAddress": "edge@example.com",
                "photoLink": ""
            },
            "deleted": False
        }
        
        result = get_comment_reply("b", "c", "a")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "a")
        self.assertEqual(result["content"], "Edge case reply")
    
    def test_get_with_numeric_string_ids(self):
        """Test with numeric string IDs."""
        # Add a reply with numeric string ID
        DB["users"]["me"]["replies"]["123"] = {
            "kind": "drive#reply",
            "id": "123",
            "fileId": "456",
            "commentId": "789",
            "content": "Numeric ID reply",
            "createdTime": "2023-01-01T13:00:00Z",
            "modifiedTime": "2023-01-01T13:00:00Z",
            "author": {
                "displayName": "Numeric User",
                "emailAddress": "numeric@example.com",
                "photoLink": ""
            },
            "deleted": False
        }
        
        result = get_comment_reply("456", "789", "123")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["content"], "Numeric ID reply")
    
    def test_get_reply_without_deleted_field(self):
        """Test getting a reply that doesn't have a 'deleted' field."""
        # Add a reply without the 'deleted' field
        DB["users"]["me"]["replies"]["no-deleted-field"] = {
            "kind": "drive#reply",
            "id": "no-deleted-field",
            "fileId": "file-1",
            "commentId": "comment-1",
            "content": "Reply without deleted field",
            "createdTime": "2023-01-01T14:00:00Z",
            "modifiedTime": "2023-01-01T14:00:00Z",
            "author": {
                "displayName": "Test User",
                "emailAddress": "test@example.com",
                "photoLink": ""
            }
            # Note: No 'deleted' field
        }
        
        result = get_comment_reply("file-1", "comment-1", "no-deleted-field")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "no-deleted-field")
        self.assertEqual(result["content"], "Reply without deleted field")
    
    def test_get_reply_with_false_deleted_field(self):
        """Test getting a reply with deleted=False."""
        # Add a reply with explicit deleted=False
        DB["users"]["me"]["replies"]["explicit-false"] = {
            "kind": "drive#reply",
            "id": "explicit-false",
            "fileId": "file-1",
            "commentId": "comment-1",
            "content": "Reply with explicit false",
            "createdTime": "2023-01-01T15:00:00Z",
            "modifiedTime": "2023-01-01T15:00:00Z",
            "author": {
                "displayName": "Test User",
                "emailAddress": "test@example.com",
                "photoLink": ""
            },
            "deleted": False
        }
        
        result = get_comment_reply("file-1", "comment-1", "explicit-false")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "explicit-false")
        self.assertFalse(result["deleted"])
    
    def test_get_with_special_character_ids(self):
        """Test with IDs containing special characters (including spaces)."""
        # Add a reply with special character ID
        DB["users"]["me"]["replies"]["reply with spaces"] = {
            "kind": "drive#reply",
            "id": "reply with spaces",
            "fileId": "file with spaces",
            "commentId": "comment with spaces",
            "content": "Special character reply",
            "createdTime": "2023-01-01T16:00:00Z",
            "modifiedTime": "2023-01-01T16:00:00Z",
            "author": {
                "displayName": "Special User",
                "emailAddress": "special@example.com",
                "photoLink": ""
            },
            "deleted": False
        }
        
        result = get_comment_reply("file with spaces", "comment with spaces", "reply with spaces")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "reply with spaces")
        self.assertEqual(result["content"], "Special character reply")
    
    def test_get_with_empty_author_fields(self):
        """Test getting a reply with empty author fields."""
        # Add a reply with minimal author info
        DB["users"]["me"]["replies"]["minimal-author"] = {
            "kind": "drive#reply",
            "id": "minimal-author",
            "fileId": "file-1",
            "commentId": "comment-1",
            "content": "Reply with minimal author",
            "createdTime": "2023-01-01T17:00:00Z",
            "modifiedTime": "2023-01-01T17:00:00Z",
            "author": {
                "displayName": "",
                "emailAddress": "",
                "photoLink": ""
            },
            "deleted": False
        }
        
        result = get_comment_reply("file-1", "comment-1", "minimal-author")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "minimal-author")
        self.assertEqual(result["author"]["displayName"], "")
        self.assertEqual(result["author"]["emailAddress"], "")
        self.assertEqual(result["author"]["photoLink"], "")


if __name__ == '__main__':
    unittest.main() 