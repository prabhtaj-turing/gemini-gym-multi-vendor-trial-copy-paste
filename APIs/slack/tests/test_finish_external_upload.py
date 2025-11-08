"""
Unit tests for the finish_external_upload function in the Slack Files API.
This test suite verifies that the function behaves as specified in its docstring.
"""
from unittest.mock import patch
import unittest

# Use relative imports
from .. import finish_external_file_upload
from ..SimulationEngine.custom_errors import ChannelNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestFinishExternalUpload(BaseTestCaseWithErrorHandler):
    """Test cases for finish_external_upload function."""

    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        
        # Set up a clean test DB for each test
        self.test_db = {
            "files": {},
            "channels": {}
        }

    def test_finish_external_upload_success(self):
        """Test successful external file upload completion."""
        with patch("slack.Files.DB", self.test_db):
            # Create a file first
            self.test_db["files"]["F123"] = {
                "id": "F123",
                "external_id": "ext_123",
                "external_url": "https://example.com/file"
            }
            # Create a channel
            self.test_db["channels"]["C123"] = {"id": "C123"}
            
            # Test the function with valid inputs
            files_data = [{"id": "F123", "title": "Updated Title"}]
            result = finish_external_file_upload(
                files=files_data, 
                channel_id="C123",
                initial_comment="Test comment",
                thread_ts="1234.5678"
            )
            
            # Verify result
            self.assertTrue(result["ok"])
            
            # Verify file was updated
            self.assertEqual(self.test_db["files"]["F123"]["title"], "Updated Title")
            self.assertEqual(self.test_db["files"]["F123"]["initial_comment"], "Test comment")
            self.assertEqual(self.test_db["files"]["F123"]["thread_ts"], "1234.5678")
            
            # Verify channel association
            self.assertIn("files", self.test_db["channels"]["C123"])
            self.assertTrue(self.test_db["channels"]["C123"]["files"].get("F123"))
    
    def test_finish_external_upload_multiple_files(self):
        """Test finishing upload with multiple files."""
        with patch("slack.Files.DB", self.test_db):
            # Create files
            self.test_db["files"]["F123"] = {"id": "F123"}
            self.test_db["files"]["F456"] = {"id": "F456"}
            
            # Create channel
            self.test_db["channels"]["C123"] = {"id": "C123"}
            
            # Test with multiple files
            files_data = [
                {"id": "F123", "title": "File 1"},
                {"id": "F456", "title": "File 2"}
            ]
            result = finish_external_file_upload(files=files_data, channel_id="C123")
            
            # Verify result
            self.assertTrue(result["ok"])
            
            # Verify both files were updated
            self.assertEqual(self.test_db["files"]["F123"]["title"], "File 1")
            self.assertEqual(self.test_db["files"]["F456"]["title"], "File 2")
            
            # Verify both files are associated with the channel
            self.assertTrue(self.test_db["channels"]["C123"]["files"].get("F123"))
            self.assertTrue(self.test_db["channels"]["C123"]["files"].get("F456"))
    
    def test_finish_external_upload_without_channel(self):
        """Test finishing upload without specifying a channel."""
        with patch("slack.Files.DB", self.test_db):
            # Create a file
            self.test_db["files"]["F123"] = {"id": "F123"}
            
            # Test without channel_id
            files_data = [{"id": "F123", "title": "Updated Title"}]
            result = finish_external_file_upload(files=files_data)
            
            # Verify result
            self.assertTrue(result["ok"])
            
            # Verify file was updated
            self.assertEqual(self.test_db["files"]["F123"]["title"], "Updated Title")
    
    # Type validation tests - these should test the TypeError cases in the docstring
    
    def test_finish_external_upload_files_not_list(self):
        """Test that a TypeError is raised when files is not a list."""
        with patch("slack.Files.DB", self.test_db):
            # Test with non-list files parameter
            self.assert_error_behavior(
                finish_external_file_upload,
                TypeError,
                "files must be a list.",
                None,
                files="not a list"
            )
    
    def test_finish_external_upload_channel_id_not_string(self):
        """Test that a TypeError is raised when channel_id is not a string or None."""
        with patch("slack.Files.DB", self.test_db):
            # Test with non-string channel_id
            self.assert_error_behavior(
                finish_external_file_upload,
                TypeError,
                "channel_id must be a string or None.",
                None,
                files=[{"id": "F123"}],
                channel_id=123
            )
    
    def test_finish_external_upload_initial_comment_not_string(self):
        """Test that a TypeError is raised when initial_comment is not a string or None."""
        with patch("slack.Files.DB", self.test_db):
            # Test with non-string initial_comment
            self.assert_error_behavior(
                finish_external_file_upload,
                TypeError,
                "initial_comment must be a string or None.",
                None,
                files=[{"id": "F123"}],
                initial_comment=123
            )
    
    def test_finish_external_upload_thread_ts_not_string(self):
        """Test that a TypeError is raised when thread_ts is not a string or None."""
        with patch("slack.Files.DB", self.test_db):
            # Test with non-string thread_ts
            self.assert_error_behavior(
                finish_external_file_upload,
                TypeError,
                "thread_ts must be a string or None.",
                None,
                files=[{"id": "F123"}],
                thread_ts=123
            )
    
    # Value validation tests - these should test the ValueError cases in the docstring
    
    def test_finish_external_upload_empty_files_list(self):
        """Test that a ValueError is raised when files list is empty."""
        with patch("slack.Files.DB", self.test_db):
            # Test with empty files list
            self.assert_error_behavior(
                finish_external_file_upload,
                ValueError,
                "files list cannot be empty.",
                None,
                files=[]
            )
    
    def test_finish_external_upload_file_object_not_dict(self):
        """Test that a ValueError is raised when a file object is not a dictionary."""
        with patch("slack.Files.DB", self.test_db):
            # Test with non-dictionary file object
            self.assert_error_behavior(
                finish_external_file_upload,
                ValueError,
                "Each file object must be a dictionary.",
                None,
                files=["not a dictionary"]
            )
    
    def test_finish_external_upload_file_missing_id(self):
        """Test that a ValueError is raised when a file object is missing an id field."""
        with patch("slack.Files.DB", self.test_db):
            # Test with file object missing id
            self.assert_error_behavior(
                finish_external_file_upload,
                ValueError,
                "Each file object must contain an 'id' field.",
                None,
                files=[{"title": "Missing ID"}]
            )
    
    # Resource validation tests - these should test the custom error cases in the docstring
    
    def test_finish_external_upload_channel_not_found(self):
        """Test that a ChannelNotFoundError is raised when channel_id doesn't exist."""
        with patch("slack.Files.DB", self.test_db):
            # Set up DB but don't add the channel
            self.test_db["files"]["F123"] = {"id": "F123"}
            
            # Test with non-existent channel
            self.assert_error_behavior(
                finish_external_file_upload,
                ChannelNotFoundError,
                "Channel 'C999' not found.",
                None,
                files=[{"id": "F123"}],
                channel_id="C999"
            )
    
    def test_finish_external_upload_file_not_found(self):
        """Test that a FileNotFoundError is raised when a file_id doesn't exist."""
        with patch("slack.Files.DB", self.test_db):
            # Set up channel but don't add the file
            self.test_db["channels"]["C123"] = {"id": "C123"}
            
            # Test with non-existent file
            self.assert_error_behavior(
                finish_external_file_upload,
                FileNotFoundError,
                "File 'F999' not found.",
                None,
                files=[{"id": "F999"}],
                channel_id="C123"
            )


if __name__ == "__main__":
    unittest.main() 