import unittest
import copy
from unittest.mock import patch

from .. import remove_remote_file
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestRemoveRemoteFile(BaseTestCaseWithErrorHandler):
    """Comprehensive test suite for the `remove_remote_file` helper."""

    def setUp(self):
        # Build a minimal but representative in-memory database
        base_db = {
            "files": {
                # A remote file identified by Slack ID *and* external_id
                "F111": {
                    "id": "F111",
                    "external_id": "X-AAA",
                    "filename": "remote.pdf",
                    "title": "Remote PDF",
                    "filetype": "pdf",
                },
                # A normal (non-remote) file for negative-path testing
                "F222": {
                    "id": "F222",
                    "filename": "local.txt",
                    "title": "Local text",
                    "filetype": "txt",
                },
                # Additional files for comprehensive testing
                "F_FILE_1": {"id": "F_FILE_1", "external_id": "ext_id_1"},
                "F_FILE_2": {"id": "F_FILE_2", "external_id": "ext_id_2"},
            },
            "channels": {
                "C123": {
                    "id": "C123",
                    "name": "general",
                    "files": {
                        "F111": True,
                        "F222": True,
                        "F_FILE_1": True,
                    },
                },
                "C456": {
                    "id": "C456", 
                    "name": "random",
                    "files": {
                        "F_FILE_2": True,
                    },
                }
            },
        }
        # Use a deep copy to ensure test isolation
        self.test_db = copy.deepcopy(base_db)

    # ------------------------------------------------------------------
    # Success cases
    # ------------------------------------------------------------------
    def test_remove_by_file_id_success(self):
        """Removing via *file_id* succeeds and cleans up references."""
        with patch("slack.Files.DB", self.test_db):
            result = remove_remote_file(file_id="F111")
            self.assertEqual(result, {"ok": True})
            # File no longer exists
            self.assertNotIn("F111", self.test_db["files"])
            self.assertNotIn("F111", self.test_db["channels"]["C123"]["files"])

    def test_remove_by_external_id_success(self):
        """Removing via *external_id* succeeds and cleans up references."""
        with patch("slack.Files.DB", self.test_db):
            result = remove_remote_file(external_id="X-AAA")
            self.assertEqual(result, {"ok": True})
            self.assertNotIn("F111", self.test_db["files"])
            self.assertNotIn("F111", self.test_db["channels"]["C123"]["files"])

    def test_remove_by_file_id_success_alternative(self):
        """Test successful removal of a remote file using its file_id (alternative test structure)."""
        with patch("slack.Files.DB", self.test_db):
            result = remove_remote_file(file_id="F_FILE_1")
            self.assertTrue(result["ok"])
            self.assertNotIn("F_FILE_1", self.test_db["files"])
            self.assertNotIn("F_FILE_1", self.test_db["channels"]["C123"]["files"])

    def test_remove_by_external_id_success_alternative(self):
        """Test successful removal of a remote file using its external_id (alternative test structure)."""
        with patch("slack.Files.DB", self.test_db):
            result = remove_remote_file(external_id="ext_id_2")
            self.assertTrue(result["ok"])
            self.assertNotIn("F_FILE_2", self.test_db["files"])
            self.assertNotIn("F_FILE_2", self.test_db["channels"]["C456"]["files"])

    # ------------------------------------------------------------------
    # Validation: exclusivity & presence
    # ------------------------------------------------------------------
    def test_neither_id_provided(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=ValueError,
            expected_message="Either file_id or external_id must be provided."
        )

    def test_remove_no_id_provided(self):
        """Test that an error is raised if neither file_id nor external_id is provided (alternative structure)."""
        self.assert_error_behavior(
            remove_remote_file,
            ValueError,
            "Either file_id or external_id must be provided."
        )

    def test_both_ids_provided(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=ValueError,
            expected_message="Provide *either* file_id *or* external_id, not both (too_many_ids).",
            file_id="F111",
            external_id="X-AAA"
        )

    # ------------------------------------------------------------------
    # Type validation
    # ------------------------------------------------------------------
    def test_file_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=TypeError,
            expected_message="file_id must be a string.",
            file_id=123
        )

    def test_external_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=TypeError,
            expected_message="external_id must be a string.",
            external_id=["X-AAA"]
        )

    def test_remove_invalid_file_id_type(self):
        """Test that a TypeError is raised for a non-string file_id (alternative structure)."""
        self.assert_error_behavior(
            remove_remote_file,
            TypeError,
            "file_id must be a string.",
            file_id=12345
        )

    def test_remove_invalid_external_id_type(self):
        """Test that a TypeError is raised for a non-string external_id (alternative structure)."""
        self.assert_error_behavior(
            remove_remote_file,
            TypeError,
            "external_id must be a string.",
            external_id=12345
        )

    # ------------------------------------------------------------------
    # Empty-string validation
    # ------------------------------------------------------------------
    def test_file_id_empty_string(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=ValueError,
            expected_message="file_id cannot be an empty string.",
            file_id="  "
        )

    def test_external_id_empty_string(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=ValueError,
            expected_message="external_id cannot be an empty string.",
            external_id=""
        )

    # ------------------------------------------------------------------
    # Not-found
    # ------------------------------------------------------------------
    def test_file_not_found_by_id(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=FileNotFoundError,
            expected_message="File not found.",
            file_id="F999"
        )

    def test_file_not_found_by_external_id(self):
        self.assert_error_behavior(
            func_to_call=remove_remote_file,
            expected_exception_type=FileNotFoundError,
            expected_message="File not found.",
            external_id="NON_EXISTENT"
        )

    def test_remove_file_not_found(self):
        """Test that an error is raised when trying to remove a non-existent file (alternative structure)."""
        with patch("slack.Files.DB", self.test_db):
            self.assert_error_behavior(
                remove_remote_file,
                FileNotFoundError,
                "File not found.",
                file_id="nonexistent_id",
            ) 