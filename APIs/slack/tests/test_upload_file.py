"""
Test cases for the upload_file function in the Slack Files API.

This module contains comprehensive test cases for the upload_file function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    MissingContentOrFilePathError,
    InvalidChannelIdError,
    FileSizeLimitExceededError,
    FileReadError
)
from .. import upload_file

class TestUploadFile(BaseTestCaseWithErrorHandler):
    """Test class specifically for upload_file functionality."""

    def setUp(self):
        """Set up test database and file manager."""
        self.test_db = {
            "current_user": {"id": "U123USER"},
            "channels": {
                "C123": {"id": "C123", "name": "general", "files": {}},
                "C456": {"id": "C456", "name": "random", "files": {}},
            },
            "files": {},
        }

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_success_with_content(self, mock_file_id, mock_time):
        """Test successful file upload with text content."""
        with patch("slack.Files.DB", self.test_db):
            result = upload_file(
                content="Test file content", filename="test.txt", title="Test File"
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check all expected fields
            self.assertEqual(file_data["id"], "F_TEST_123")
            self.assertEqual(file_data["name"], "test.txt")
            self.assertEqual(file_data["title"], "Test File")
            self.assertEqual(file_data["content"], "Test file content")
            self.assertEqual(file_data["filetype"], "txt")
            self.assertEqual(file_data["mimetype"], "text/plain")
            self.assertEqual(
                file_data["size"], 17
            )  # len("Test file content".encode('utf-8'))
            self.assertEqual(file_data["channels"], [])
            self.assertEqual(file_data["created"], 1640995200)
            self.assertEqual(file_data["user"], "U123USER")
            self.assertIsNone(file_data["initial_comment"])
            self.assertIsNone(file_data["thread_ts"])

            # Check file is stored in database
            self.assertIn("F_TEST_123", self.test_db["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    @patch("slack.Files.read_file")
    def test_upload_file_success_with_file_path(
        self, mock_read_file, mock_file_id, mock_time
    ):
        """Test successful file upload with file_path (auto-extracted filename)."""
        # Mock file reading
        mock_read_file.return_value = {
            "content": "File content from disk",
            "size_bytes": 21,
            "mime_type": "text/plain",
        }

        with patch("slack.Files.DB", self.test_db):
            result = upload_file(file_path="/path/to/document.txt")

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check filename was auto-extracted
            self.assertEqual(file_data["name"], "document.txt")
            self.assertEqual(file_data["title"], "document.txt")  # Defaults to filename
            self.assertEqual(file_data["content"], "File content from disk")
            self.assertEqual(file_data["filetype"], "txt")
            self.assertEqual(file_data["mimetype"], "text/plain")
            self.assertEqual(file_data["size"], 21)

            # Verify read_file was called correctly
            mock_read_file.assert_called_once_with("/path/to/document.txt", 50)

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    @patch("slack.Files.read_file")
    def test_upload_file_binary_file_detection(
        self, mock_read_file, mock_file_id, mock_time
    ):
        """Test binary file handling with base64 encoding."""
        # Mock binary file reading
        mock_read_file.return_value = {
            "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk",
            "size_bytes": 1024,
            "mime_type": "image/png",
        }

        with patch("slack.Files.DB", self.test_db):
            result = upload_file(file_path="/path/to/image.png")

            self.assertTrue(result["ok"])
            file_data = result["file"]

            self.assertEqual(file_data["name"], "image.png")
            self.assertEqual(file_data["filetype"], "png")
            self.assertEqual(file_data["mimetype"], "image/png")
            self.assertEqual(file_data["size"], 1024)

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    @patch("slack.Files.get_mime_type", return_value="application/pdf")
    def test_upload_file_content_with_binary_filename_no_encoding(
        self, mock_mime, mock_file_id, mock_time
    ):
        """Test content upload with binary filename does NOT trigger base64 encoding (bug fix)."""
        with patch("slack.Files.DB", self.test_db):

            result = upload_file(content="binary data", filename="document.pdf")

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Content should NOT be base64 encoded - this is the bug fix
            self.assertEqual(file_data["content"], "binary data")
            self.assertEqual(file_data["mimetype"], "application/pdf")
            self.assertEqual(file_data["filetype"], "pdf")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_with_channels(self, mock_file_id, mock_time):
        """Test file upload with multiple channels."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):

            result = upload_file(
                content="Shared content",
                filename="shared.txt",
                channels="C123, C456",  # Test with spaces
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check channels in file data
            self.assertEqual(file_data["channels"], ["C123", "C456"])

            # Check file association in channels
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])
            self.assertIn("F_TEST_123", self.test_db["channels"]["C456"]["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_with_all_optional_params(self, mock_file_id, mock_time):
        """Test file upload with all optional parameters."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):

            result = upload_file(
                content="Complete test content",
                filename="complete.json",
                filetype="json",
                title="Complete Test File",
                initial_comment="This is a comprehensive test",
                thread_ts="1234567890.123456",
                channels="C123",
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            self.assertEqual(file_data["name"], "complete.json")
            self.assertEqual(file_data["filetype"], "json")  # Explicit override
            self.assertEqual(file_data["title"], "Complete Test File")
            self.assertEqual(
                file_data["initial_comment"], "This is a comprehensive test"
            )
            self.assertEqual(file_data["thread_ts"], "1234567890.123456")
            self.assertEqual(file_data["channels"], ["C123"])

    def test_upload_file_missing_content_and_file_path(self):
        """Test error when both content and file_path are missing."""
        with patch("slack.Files.DB", self.test_db):

            with self.assertRaises(MissingContentOrFilePathError) as context:
                upload_file(filename="test.txt")
            self.assertEqual(
                str(context.exception), "Either content or file_path must be provided"
            )

    @patch("slack.Files.read_file")
    def test_upload_file_file_path_without_mocked_file(self, mock_read_file):
        """Test that FileNotFoundError is raised when file_path doesn't exist."""
        # Mock read_file to raise FileNotFoundError
        mock_read_file.side_effect = FileNotFoundError("File not found: /path/to/file.txt")
        
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(FileNotFoundError) as context:
                upload_file(file_path="/path/to/file.txt")
            self.assertEqual(
                str(context.exception),
                "File not found: /path/to/file.txt",
            )

    def test_upload_file_invalid_channel_id(self):
        """Test error for invalid channel ID."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            with self.assertRaises(InvalidChannelIdError) as context:
                upload_file(content="Test content", channels="C999")
            self.assertEqual(str(context.exception), "Invalid channel ID: C999")

    def test_upload_file_invalid_channel_in_list(self):
        """Test error when one channel in list is invalid."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            with self.assertRaises(InvalidChannelIdError) as context:
                upload_file(content="Test content", channels="C123,C999")
            self.assertEqual(str(context.exception), "Invalid channel ID: C999")

    @patch("slack.Files.read_file")
    def test_upload_file_file_not_found_error(self, mock_read_file):
        """Test that FileNotFoundError is raised (not wrapped) when file doesn't exist."""
        mock_read_file.side_effect = FileNotFoundError("File not found")

        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(FileNotFoundError) as context:
                upload_file(file_path="/nonexistent/file.txt")
            self.assertEqual(str(context.exception), "File not found")

    @patch("slack.Files.read_file")
    def test_upload_file_other_exceptions_wrapped_in_file_read_error(self, mock_read_file):
        """Test that other unexpected exceptions are wrapped in FileReadError."""
        # Mock read_file to raise an unexpected exception (e.g., PermissionError)
        mock_read_file.side_effect = PermissionError("Permission denied")

        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(FileReadError) as context:
                upload_file(file_path="/path/to/file.txt")
            self.assertIn("Failed to read file", str(context.exception))
            self.assertIn("Permission denied", str(context.exception))

    # Type validation tests
    def test_upload_file_type_error_channels(self):
        """Test TypeError for non-string channels parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(content="Test", channels=123)
            self.assertEqual(
                str(context.exception), "channels must be a string or None."
            )

    def test_upload_file_type_error_content(self):
        """Test TypeError for non-string content parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(content=123)
            self.assertEqual(
                str(context.exception), "content must be a string or None."
            )

    def test_upload_file_type_error_file_path(self):
        """Test TypeError for non-string file_path parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(file_path=123)
            self.assertEqual(
                str(context.exception), "file_path must be a string or None."
            )

    def test_upload_file_type_error_filename(self):
        """Test TypeError for non-string filename parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(content="Test", filename=123)
            self.assertEqual(
                str(context.exception), "filename must be a string or None."
            )

    def test_upload_file_type_error_filetype(self):
        """Test TypeError for non-string filetype parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(content="Test", filetype=123)
            self.assertEqual(
                str(context.exception), "filetype must be a string or None."
            )

    def test_upload_file_type_error_initial_comment(self):
        """Test TypeError for non-string initial_comment parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:

                upload_file(content="Test", initial_comment=123)
            self.assertEqual(
                str(context.exception), "initial_comment must be a string or None."
            )

    def test_upload_file_type_error_thread_ts(self):
        """Test TypeError for non-string thread_ts parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(content="Test", thread_ts=123)
            self.assertEqual(
                str(context.exception), "thread_ts must be a string or None."
            )

    def test_upload_file_type_error_title(self):
        """Test TypeError for non-string title parameter."""
        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(TypeError) as context:
                upload_file(content="Test", title=123)
            self.assertEqual(str(context.exception), "title must be a string or None.")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_default_filename(self, mock_file_id, mock_time):
        """Test default filename 'untitled' when no filename provided."""
        with patch("slack.Files.DB", self.test_db):
            result = upload_file(content="Test content")
            self.assertTrue(result["ok"])
            self.assertEqual(result["file"]["name"], "untitled")
            self.assertEqual(result["file"]["title"], "untitled")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_creates_files_db_if_missing(self, mock_file_id, mock_time):
        """Test that files DB is created if it doesn't exist."""
        with patch("slack.Files.DB", self.test_db):
            # Remove files key
            del self.test_db["files"]

            result = upload_file(content="Test content")
            self.assertTrue(result["ok"])
            self.assertIn("files", self.test_db)
            self.assertIn("F_TEST_123", self.test_db["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_creates_channel_files_if_missing(
        self, mock_file_id, mock_time
    ):
        """Test that channel files dict is created if it doesn't exist."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            # Create channel without files key
            self.test_db["channels"]["C123"] = {"id": "C123"}

            result = upload_file(content="Test content", channels="C123")
            self.assertTrue(result["ok"])
            self.assertIn("files", self.test_db["channels"]["C123"])
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_priority_over_file_path(self, mock_file_id, mock_time):
        """Test that content takes priority when both content and file_path are provided."""
        with patch("slack.Files.DB", self.test_db):
            result = upload_file(
                content="Direct content",
                file_path="/some/file.txt",  # This should be ignored
                filename="test.txt",
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Content should be used, not file_path
            self.assertEqual(file_data["content"], "Direct content")
            self.assertEqual(file_data["size"], 14)  # len("Direct content")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_auto_detection_without_filename(self, mock_file_id, mock_time):
        """Test file type detection without explicit filename."""
        with patch("slack.Files.DB", self.test_db):
            result = upload_file(content="{'key': 'value'}")

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Should use defaults for unknown type
            self.assertEqual(file_data["filetype"], "txt")
            self.assertEqual(file_data["mimetype"], "text/plain")

    def test_upload_file_content_size_validation(self):
        """Test size validation for direct content upload."""
        with patch("slack.Files.DB", self.test_db):
            # Create content larger than 50MB (50*1024*1024 = 52428800 bytes)
            large_content = "x" * (50 * 1024 * 1024 + 1)

            with self.assertRaises(FileSizeLimitExceededError) as context:
                upload_file(content=large_content)
            self.assertIn("Content too large", str(context.exception))

    def test_upload_file_base64_encoding_size_validation(self):
        """Test size validation for binary files - validates original content size."""
        with patch("slack.Files.DB", self.test_db):
            # Content larger than 50MB
            content = "x" * (50 * 1024 * 1024 + 1)

            with self.assertRaises(FileSizeLimitExceededError) as context:
                upload_file(
                    content=content,
                    filename="test.pdf",  # Binary file triggers base64 encoding
                )
            self.assertIn("Content too large", str(context.exception))

    @patch("slack.Files.read_file")
    def test_upload_file_file_size_limit_exceeded(self, mock_read_file):
        """Test that ValueError for file size is converted to FileSizeLimitExceededError."""
        # Mock read_file to raise ValueError with "File too large" message (as it actually does)
        mock_read_file.side_effect = ValueError(
            "File too large: 52428801 bytes (max: 52428800)"
        )

        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(FileSizeLimitExceededError) as context:
                upload_file(file_path="/path/to/large_file.txt")
            self.assertIn("File too large", str(context.exception))

            # Verify read_file was called with 50MB limit
            mock_read_file.assert_called_once_with("/path/to/large_file.txt", 50)

    @patch("slack.Files.read_file")
    def test_upload_file_value_error_for_decode_wrapped_in_file_read_error(self, mock_read_file):
        """Test that ValueError for decode errors is wrapped in FileReadError."""
        # Mock read_file to raise ValueError for a decode error (not size related)
        mock_read_file.side_effect = ValueError("Could not decode file: /path/to/file.txt")

        with patch("slack.Files.DB", self.test_db):
            with self.assertRaises(FileReadError) as context:
                upload_file(file_path="/path/to/file.txt")
            self.assertIn("Failed to read file", str(context.exception))
            self.assertIn("Could not decode file", str(context.exception))

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_handles_large_file_gracefully(self, mock_file_id, mock_time):
        """Test that large files are handled with appropriate error messages."""
        with patch("slack.Files.DB", self.test_db):
            # Test with moderately large content (should work)
            moderate_content = "x" * (10 * 1024 * 1024)  # 10MB
            result = upload_file(content=moderate_content)
            self.assertTrue(result["ok"])
            self.assertEqual(result["file"]["size"], 10 * 1024 * 1024)

    # --- Tests for Base64 Encoding Bug Fix ---

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_never_base64_encoded(self, mock_file_id, mock_time):
        """Test that content parameter is never Base64-encoded regardless of filename."""
        with patch("slack.Files.DB", self.test_db):
            # Test with various binary filename extensions
            test_cases = [
                ("Hello World", "document.pdf"),
                ("Image data", "photo.jpg"),
                ("Binary content", "file.exe"),
                ("Archive data", "archive.zip"),
            ]
            
            for content, filename in test_cases:
                result = upload_file(content=content, filename=filename)
                self.assertTrue(result["ok"])
                file_data = result["file"]
                
                # Content should always be preserved as-is (never Base64-encoded)
                self.assertEqual(file_data["content"], content)
                self.assertEqual(file_data["name"], filename)
                # MIME type should be detected (but exact value varies by platform)
                self.assertIsNotNone(file_data["mimetype"])
                self.assertIsInstance(file_data["mimetype"], str)
                self.assertTrue(len(file_data["mimetype"]) > 0)

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_preserves_already_base64_encoded(self, mock_file_id, mock_time):
        """Test that already Base64-encoded content is not double-encoded."""
        with patch("slack.Files.DB", self.test_db):
            # Simulate content that is already Base64-encoded
            already_encoded_content = "SGVsbG8gV29ybGQ="  # "Hello World" in Base64
            
            result = upload_file(content=already_encoded_content, filename="data.bin")
            self.assertTrue(result["ok"])
            file_data = result["file"]
            
            # Content should be preserved exactly as provided (no double-encoding)
            self.assertEqual(file_data["content"], already_encoded_content)
            self.assertEqual(file_data["name"], "data.bin")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_text_files_unchanged(self, mock_file_id, mock_time):
        """Test that text files with content parameter are handled correctly."""
        with patch("slack.Files.DB", self.test_db):
            # Test various text file types
            test_cases = [
                ("print('Hello World')", "script.py", "text/x-python"),
                ("<html><body>Hello</body></html>", "page.html", "text/html"),
                ('{"key": "value"}', "data.json", "application/json"),
                ("# Markdown content", "readme.md", "text/markdown"),
            ]
            
            for content, filename, expected_mime in test_cases:
                result = upload_file(content=content, filename=filename)
                self.assertTrue(result["ok"])
                file_data = result["file"]
                
                # Text content should be preserved exactly
                self.assertEqual(file_data["content"], content)
                self.assertEqual(file_data["name"], filename)
                self.assertEqual(file_data["mimetype"], expected_mime)

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_json_data_preserved(self, mock_file_id, mock_time):
        """Test that JSON data is preserved correctly without encoding issues."""
        with patch("slack.Files.DB", self.test_db):
            json_content = '{"name": "test", "value": 123, "nested": {"key": "value"}}'
            
            result = upload_file(content=json_content, filename="config.json")
            self.assertTrue(result["ok"])
            file_data = result["file"]
            
            # JSON should be preserved exactly as provided
            self.assertEqual(file_data["content"], json_content)
            self.assertEqual(file_data["name"], "config.json")
            self.assertEqual(file_data["mimetype"], "application/json")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_binary_filename_behavior_fix(self, mock_file_id, mock_time):
        """Test the specific bug fix: binary filenames don't trigger Base64 encoding of content."""
        with patch("slack.Files.DB", self.test_db):
            # This is the exact scenario that was buggy before
            text_content = "This is plain text content"
            binary_filename = "document.pdf"
            
            result = upload_file(content=text_content, filename=binary_filename)
            self.assertTrue(result["ok"])
            file_data = result["file"]
            
            # Before fix: content would be Base64-encoded
            # After fix: content should be preserved as-is
            self.assertEqual(file_data["content"], text_content)
            self.assertEqual(file_data["name"], binary_filename)
            self.assertEqual(file_data["mimetype"], "application/pdf")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_no_filename_always_text(self, mock_file_id, mock_time):
        """Test that content without filename is always treated as text."""
        with patch("slack.Files.DB", self.test_db):
            content = "Some content without filename"
            
            result = upload_file(content=content)
            self.assertTrue(result["ok"])
            file_data = result["file"]
            
            # Should be treated as text file
            self.assertEqual(file_data["content"], content)
            self.assertEqual(file_data["name"], "untitled")
            self.assertEqual(file_data["mimetype"], "text/plain")
            self.assertEqual(file_data["filetype"], "txt")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_unicode_preserved(self, mock_file_id, mock_time):
        """Test that Unicode content is preserved correctly."""
        with patch("slack.Files.DB", self.test_db):
            unicode_content = "Hello 世界 🌍 测试"
            
            result = upload_file(content=unicode_content, filename="unicode.txt")
            self.assertTrue(result["ok"])
            file_data = result["file"]
            
            # Unicode should be preserved exactly
            self.assertEqual(file_data["content"], unicode_content)
            self.assertEqual(file_data["name"], "unicode.txt")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_content_vs_file_path_distinction(self, mock_file_id, mock_time):
        """Test that content parameter and file_path parameter are handled differently."""
        with patch("slack.Files.DB", self.test_db):
            # Content parameter should never be Base64-encoded
            content_result = upload_file(content="text content", filename="binary.pdf")
            self.assertTrue(content_result["ok"])
            self.assertEqual(content_result["file"]["content"], "text content")
            
            # file_path parameter should use read_file which handles binary files correctly
            # (This is tested in other test cases that mock read_file)
    # Channel name and ID support tests
    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_with_channel_name(self, mock_file_id, mock_time):
        """Test file upload with channel name instead of channel ID."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            result = upload_file(
                content="Test content for channel name",
                filename="test.txt",
                channels="general"  # Using channel name instead of C123
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check channels in file data (should be resolved to channel ID)
            self.assertEqual(file_data["channels"], ["C123"])

            # Check file association in channels
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_with_multiple_channel_names(self, mock_file_id, mock_time):
        """Test file upload with multiple channel names."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            result = upload_file(
                content="Test content for multiple channels",
                filename="test.txt",
                channels="general, random"  # Using channel names
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check channels in file data (should be resolved to channel IDs)
            self.assertEqual(set(file_data["channels"]), {"C123", "C456"})

            # Check file association in both channels
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])
            self.assertIn("F_TEST_123", self.test_db["channels"]["C456"]["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_with_mixed_channel_names_and_ids(self, mock_file_id, mock_time):
        """Test file upload with mixed channel names and IDs."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            result = upload_file(
                content="Test content for mixed channels",
                filename="test.txt",
                channels="general, C456"  # Mix of channel name and ID
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check channels in file data (should be resolved to channel IDs)
            self.assertEqual(set(file_data["channels"]), {"C123", "C456"})

            # Check file association in both channels
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])
            self.assertIn("F_TEST_123", self.test_db["channels"]["C456"]["files"])

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_with_channel_names_and_spaces(self, mock_file_id, mock_time):
        """Test file upload with channel names containing spaces in the list."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            result = upload_file(
                content="Test content with spaces",
                filename="test.txt",
                channels=" general , random "  # Channel names with spaces
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Check channels in file data (should be resolved to channel IDs)
            self.assertEqual(set(file_data["channels"]), {"C123", "C456"})

            # Check file association in both channels
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])
            self.assertIn("F_TEST_123", self.test_db["channels"]["C456"]["files"])

    def test_upload_file_invalid_channel_name(self):
        """Test error for invalid channel name."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            with self.assertRaises(InvalidChannelIdError) as context:
                upload_file(content="Test content", channels="nonexistent-channel")
            self.assertEqual(str(context.exception), "Invalid channel ID: nonexistent-channel")

    def test_upload_file_invalid_channel_name_in_mixed_list(self):
        """Test error when one channel name in mixed list is invalid."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            with self.assertRaises(InvalidChannelIdError) as context:
                upload_file(content="Test content", channels="general, nonexistent-channel")
            self.assertEqual(str(context.exception), "Invalid channel ID: nonexistent-channel")

    def test_upload_file_invalid_channel_id_in_mixed_list(self):
        """Test error when one channel ID in mixed list is invalid."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            with self.assertRaises(InvalidChannelIdError) as context:
                upload_file(content="Test content", channels="general, C999")
            self.assertEqual(str(context.exception), "Invalid channel ID: C999")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_channel_name_case_sensitive(self, mock_file_id, mock_time):
        """Test that channel name resolution is case sensitive."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            with self.assertRaises(InvalidChannelIdError) as context:
                upload_file(content="Test content", channels="General")  # Wrong case
            self.assertEqual(str(context.exception), "Invalid channel ID: General")

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_empty_channel_name(self, mock_file_id, mock_time):
        """Test handling of empty channel names in the list."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            result = upload_file(
                content="Test content",
                filename="test.txt",
                channels="general, , random"  # Empty channel name in middle
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Should only process valid channels (empty ones are filtered out)
            self.assertEqual(set(file_data["channels"]), {"C123", "C456"})

    @patch("slack.Files.time.time", return_value=1640995200)
    @patch("slack.Files._generate_slack_file_id", return_value="F_TEST_123")
    def test_upload_file_duplicate_channel_names_and_ids(self, mock_file_id, mock_time):
        """Test handling of duplicate channel names and IDs in the list."""
        with patch("slack.Files.DB", self.test_db), \
             patch("slack.SimulationEngine.utils.DB", self.test_db):
            result = upload_file(
                content="Test content",
                filename="test.txt",
                channels="general, C123, random, C456"  # Duplicates and mixed types
            )

            self.assertTrue(result["ok"])
            file_data = result["file"]

            # Should handle duplicates gracefully (no duplicates in final result)
            self.assertEqual(set(file_data["channels"]), {"C123", "C456"})

            # Check file association in both channels
            self.assertIn("F_TEST_123", self.test_db["channels"]["C123"]["files"])
            self.assertIn("F_TEST_123", self.test_db["channels"]["C456"]["files"])
