import unittest
from unittest.mock import patch

from .. import get_external_upload_url
from ..SimulationEngine.custom_errors import FileSizeLimitExceededError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGetExternalUploadUrlLimits(BaseTestCaseWithErrorHandler):
    """Additional tests covering new validation rules for get_external_upload_url."""

    def setUp(self):
        # Use a minimal DB for each test
        self.test_db = {"files": {}}

    # -------------------------------------------------------
    # File size validation
    # -------------------------------------------------------
    def test_size_exceeds_fifty_megabytes(self):
        """length > 50 MB should raise FileSizeLimitExceededError."""
        with patch("slack.Files.DB", self.test_db):
            self.assert_error_behavior(
                func_to_call=get_external_upload_url,
                expected_exception_type=FileSizeLimitExceededError,
                expected_message="File size exceeds the 50 MB limit.",
                filename="big.bin",
                length=52_428_801  # 1 byte over the 50MB limit
            )

    # -------------------------------------------------------
    # alt_txt length validation
    # -------------------------------------------------------
    def test_alt_txt_too_long(self):
        """alt_txt longer than 1000 characters should raise ValueError."""
        long_alt_txt = "a" * 1001
        with patch("slack.Files.DB", self.test_db):
            self.assert_error_behavior(
                func_to_call=get_external_upload_url,
                expected_exception_type=ValueError,
                expected_message="alt_txt cannot exceed 1000 characters.",
                filename="image.png",
                length=100,
                alt_txt=long_alt_txt
            )


class TestGetExternalUploadUrl(BaseTestCaseWithErrorHandler):
    """Comprehensive test suite for get_external_upload_url function."""
    
    def setUp(self):
        """Set up a clean, empty database for each test."""
        self.test_db = {"files": {}}
        # Import the function we need to test and check against
        from ..SimulationEngine.utils import _check_and_delete_pending_file
        self.cleanup_func = _check_and_delete_pending_file

    @patch("slack.Files.threading.Timer")
    @patch("slack.Files._generate_slack_file_id", return_value="F_MOCK_ID")
    def test_get_url_success(self, mock_gen_id, mock_timer):
        """Test successful URL generation and placeholder creation."""
        with patch("slack.Files.DB", self.test_db):
            response = get_external_upload_url("test.txt", 100, alt_txt="alt text")
            self.assertTrue(response["ok"])
            self.assertEqual(response["file_id"], "F_MOCK_ID")
            self.assertIn("upload_url", response)

            # Check that placeholder was created correctly in the DB
            created_file = self.test_db["files"].get("F_MOCK_ID")
            self.assertIsNotNone(created_file)
            self.assertEqual(created_file.get("status"), "pending_upload")
            self.assertEqual(created_file.get("filename"), "test.txt")
            self.assertEqual(created_file.get("alt_txt"), "alt text")

            # Check that the async timer was started with correct arguments
            mock_timer.assert_called_once()
            call_args = mock_timer.call_args
            self.assertEqual(call_args.args[0], 60.0)  # delay
            self.assertEqual(call_args.args[1], self.cleanup_func)  # callback function
            self.assertEqual(call_args.kwargs["args"], ["F_MOCK_ID"])  # callback args
            mock_timer.return_value.start.assert_called_once()

    def test_all_validation(self):
        """Test all input validation using assert_error_behavior."""
        self.assert_error_behavior(get_external_upload_url, TypeError, "filename must be a string.", filename=123, length=100)
        self.assert_error_behavior(get_external_upload_url, ValueError, "filename cannot be an empty string.", filename="", length=100)
        self.assert_error_behavior(get_external_upload_url, TypeError, "length must be an integer.", filename="f.txt", length="100")
        self.assert_error_behavior(get_external_upload_url, ValueError, "length must be a positive integer.", filename="f.txt", length=0)
        self.assert_error_behavior(get_external_upload_url, TypeError, "alt_txt must be a string.", filename="f.txt", length=100, alt_txt=False)
        self.assert_error_behavior(get_external_upload_url, TypeError, "snippet_type must be a string.", filename="f.txt", length=100, snippet_type=123)

    def test_cleanup_deletes_pending_file(self):
        """Test that the cleanup function deletes a file if its status is still 'pending'."""
        self.test_db["files"]["PENDING_FILE"] = {"status": "pending_upload"}
        with patch("slack.SimulationEngine.utils.DB", self.test_db):
             self.cleanup_func("PENDING_FILE")
        self.assertNotIn("PENDING_FILE", self.test_db["files"])

    def test_cleanup_ignores_completed_file(self):
        """Test that the cleanup function does not delete a file if its status has changed."""
        self.test_db["files"]["COMPLETED_FILE"] = {"status": "complete"}
        with patch("slack.SimulationEngine.utils.DB", self.test_db):
            self.cleanup_func("COMPLETED_FILE")
        self.assertIn("COMPLETED_FILE", self.test_db["files"]) 