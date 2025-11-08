"""
Test cases for the share_file function in the Slack Files API.

This module contains comprehensive test cases for the share_file function,
including success scenarios and all error conditions.
"""

import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import share_file
from ..SimulationEngine.custom_errors import (
    InvalidChannelIdError
)


class TestShareFile(BaseTestCaseWithErrorHandler):
    """Test cases for the share_file function."""

    def setUp(self):
        """Set up test fixtures with sample data."""
        self.test_db = {
            "files": {
                "F_TEST_FILE_1": {
                    "id": "F_TEST_FILE_1",
                    "name": "test_file.txt",
                    "title": "Test File",
                    "filetype": "txt",
                    "mimetype": "text/plain",
                    "size": 1024,
                    "channels": ["C_EXISTING_1"],
                    "content": "Test file content",
                    "created": 1640995200,
                    "user": "U_TEST_USER"
                },
                "F_TEST_FILE_2": {
                    "id": "F_TEST_FILE_2",
                    "name": "document.pdf",
                    "title": "Test Document",
                    "filetype": "pdf",
                    "mimetype": "application/pdf",
                    "size": 2048,
                    "channels": [],
                    "content": "base64encodedpdfcontent",
                    "created": 1640995200,
                    "user": "U_TEST_USER"
                }
            },
            "channels": {
                "C_EXISTING_1": {
                    "id": "C_EXISTING_1",
                    "name": "general",
                    "files": {
                        "F_TEST_FILE_1": True
                    }
                },
                "C_EXISTING_2": {
                    "id": "C_EXISTING_2",
                    "name": "random",
                    "files": {}
                },
                "C_EXISTING_3": {
                    "id": "C_EXISTING_3",
                    "name": "dev",
                    "files": {}
                }
            }
        }

    # Success test cases
    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_single_channel(self, mock_db):
        """Test successful file sharing to a single channel."""
        mock_db.update(self.test_db)
        
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["file_id"], "F_TEST_FILE_1")
        self.assertEqual(result["shared_to_channels"], ["C_EXISTING_2"])
        self.assertIn("file", result)
        
        # Verify file was added to channel
        self.assertIn("F_TEST_FILE_1", mock_db["channels"]["C_EXISTING_2"]["files"])
        
        # Verify file's channel list was updated
        expected_channels = ["C_EXISTING_1", "C_EXISTING_2"]
        self.assertEqual(set(result["file"]["channels"]), set(expected_channels))

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_multiple_channels(self, mock_db):
        """Test successful file sharing to multiple channels."""
        mock_db.update(self.test_db)
        
        result = share_file("F_TEST_FILE_2", "C_EXISTING_1,C_EXISTING_2,C_EXISTING_3")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["file_id"], "F_TEST_FILE_2")
        self.assertEqual(result["shared_to_channels"], ["C_EXISTING_1", "C_EXISTING_2", "C_EXISTING_3"])
        
        # Verify file was added to all channels
        for channel_id in ["C_EXISTING_1", "C_EXISTING_2", "C_EXISTING_3"]:
            self.assertIn("F_TEST_FILE_2", mock_db["channels"][channel_id]["files"])
        
        # Verify file's channel list was updated
        expected_channels = ["C_EXISTING_1", "C_EXISTING_2", "C_EXISTING_3"]
        self.assertEqual(set(result["file"]["channels"]), set(expected_channels))

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_with_whitespace_in_channel_ids(self, mock_db):
        """Test successful file sharing with whitespace in channel IDs."""
        mock_db.update(self.test_db)
        
        result = share_file("F_TEST_FILE_1", " C_EXISTING_2 , C_EXISTING_3 ")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["shared_to_channels"], ["C_EXISTING_2", "C_EXISTING_3"])
        
        # Verify file was added to channels
        self.assertIn("F_TEST_FILE_1", mock_db["channels"]["C_EXISTING_2"]["files"])
        self.assertIn("F_TEST_FILE_1", mock_db["channels"]["C_EXISTING_3"]["files"])

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_channel_without_files_key(self, mock_db):
        """Test successful file sharing when channel doesn't have files key."""
        test_db = self.test_db.copy()
        # Remove files key from channel
        del test_db["channels"]["C_EXISTING_2"]["files"]
        mock_db.update(test_db)
        
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2")
        
        self.assertEqual(result["ok"], True)
        
        # Verify files key was created and file was added
        self.assertIn("files", mock_db["channels"]["C_EXISTING_2"])
        self.assertIn("F_TEST_FILE_1", mock_db["channels"]["C_EXISTING_2"]["files"])

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_file_with_string_channels(self, mock_db):
        """Test file sharing when file has channels as string instead of list."""
        test_db = self.test_db.copy()
        # Set file channels as string
        test_db["files"]["F_TEST_FILE_1"]["channels"] = "C_EXISTING_1"
        mock_db.update(test_db)
        
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2")
        
        self.assertEqual(result["ok"], True)
        expected_channels = ["C_EXISTING_1", "C_EXISTING_2"]
        self.assertEqual(set(result["file"]["channels"]), set(expected_channels))

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_file_with_empty_string_channels(self, mock_db):
        """Test file sharing when file has empty string channels."""
        test_db = self.test_db.copy()
        # Set file channels as empty string
        test_db["files"]["F_TEST_FILE_1"]["channels"] = ""
        mock_db.update(test_db)
        
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["file"]["channels"], ["C_EXISTING_2"])

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_success_duplicate_channels(self, mock_db):
        """Test file sharing with duplicate channel IDs."""
        mock_db.update(self.test_db)
        
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2,C_EXISTING_2,C_EXISTING_3")
        
        self.assertEqual(result["ok"], True)
        # Should not have duplicates in the response
        expected_channels = ["C_EXISTING_1", "C_EXISTING_2", "C_EXISTING_3"]
        self.assertEqual(set(result["file"]["channels"]), set(expected_channels))

    # Type validation error test cases
    def test_share_file_file_id_not_string_integer(self):
        """Test TypeError when file_id is an integer."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "file_id must be a string.",
            None,
            123, "C_EXISTING_1"
        )

    def test_share_file_file_id_not_string_none(self):
        """Test TypeError when file_id is None."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "file_id must be a string.",
            None,
            None, "C_EXISTING_1"
        )

    def test_share_file_file_id_not_string_list(self):
        """Test TypeError when file_id is a list."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "file_id must be a string.",
            None,
            ["F_TEST_FILE_1"], "C_EXISTING_1"
        )

    def test_share_file_file_id_not_string_dict(self):
        """Test TypeError when file_id is a dictionary."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "file_id must be a string.",
            None,
            {"id": "F_TEST_FILE_1"}, "C_EXISTING_1"
        )

    def test_share_file_file_id_not_string_boolean(self):
        """Test TypeError when file_id is a boolean."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "file_id must be a string.",
            None,
            True, "C_EXISTING_1"
        )

    def test_share_file_file_id_not_string_float(self):
        """Test TypeError when file_id is a float."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "file_id must be a string.",
            None,
            123.45, "C_EXISTING_1"
        )

    def test_share_file_channel_ids_not_string_integer(self):
        """Test TypeError when channel_ids is an integer."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "channel_ids must be a string.",
            None,
            "F_TEST_FILE_1", 123
        )

    def test_share_file_channel_ids_not_string_none(self):
        """Test TypeError when channel_ids is None."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "channel_ids must be a string.",
            None,
            "F_TEST_FILE_1", None
        )

    def test_share_file_channel_ids_not_string_list(self):
        """Test TypeError when channel_ids is a list."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "channel_ids must be a string.",
            None,
            "F_TEST_FILE_1", ["C_EXISTING_1"]
        )

    def test_share_file_channel_ids_not_string_dict(self):
        """Test TypeError when channel_ids is a dictionary."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "channel_ids must be a string.",
            None,
            "F_TEST_FILE_1", {"channel": "C_EXISTING_1"}
        )

    def test_share_file_channel_ids_not_string_boolean(self):
        """Test TypeError when channel_ids is a boolean."""
        self.assert_error_behavior(
            share_file,
            TypeError,
            "channel_ids must be a string.",
            None,
            "F_TEST_FILE_1", False
        )

    # Value validation error test cases
    def test_share_file_file_id_empty_string(self):
        """Test ValueError when file_id is empty string."""
        self.assert_error_behavior(
            share_file,
            ValueError,
            "file_id is required and cannot be empty.",
            None,
            "", "C_EXISTING_1"
        )

    def test_share_file_file_id_whitespace_only(self):
        """Test ValueError when file_id contains only whitespace."""
        self.assert_error_behavior(
            share_file,
            ValueError,
            "file_id is required and cannot be empty.",
            None,
            "   ", "C_EXISTING_1"
        )

    def test_share_file_file_id_tabs_and_newlines(self):
        """Test ValueError when file_id contains only tabs and newlines."""
        self.assert_error_behavior(
            share_file,
            ValueError,
            "file_id is required and cannot be empty.",
            None,
            "\t\n\r", "C_EXISTING_1"
        )

    def test_share_file_channel_ids_empty_string(self):
        """Test ValueError when channel_ids is empty string."""
        self.assert_error_behavior(
            share_file,
            ValueError,
            "channel_ids is required and cannot be empty.",
            None,
            "F_TEST_FILE_1", ""
        )

    def test_share_file_channel_ids_whitespace_only(self):
        """Test ValueError when channel_ids contains only whitespace."""
        self.assert_error_behavior(
            share_file,
            ValueError,
            "channel_ids is required and cannot be empty.",
            None,
            "F_TEST_FILE_1", "   "
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_channel_ids_only_commas(self, mock_db):
        """Test ValueError when channel_ids contains only commas."""
        mock_db.update(self.test_db)
        
        self.assert_error_behavior(
            share_file,
            ValueError,
            "channel_ids must contain at least one valid channel ID.",
            None,
            "F_TEST_FILE_1", ",,,"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_channel_ids_empty_elements(self, mock_db):
        """Test ValueError when channel_ids has only empty elements after splitting."""
        mock_db.update(self.test_db)
        
        self.assert_error_behavior(
            share_file,
            ValueError,
            "channel_ids must contain at least one valid channel ID.",
            None,
            "F_TEST_FILE_1", " , , "
        )

    # Business logic error test cases
    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_file_not_found_empty_files_db(self, mock_db):
        """Test FileNotFoundError when files database is empty."""
        mock_db.update({"files": {}, "channels": self.test_db["channels"]})
        
        self.assert_error_behavior(
            share_file,
            FileNotFoundError,
            "File 'F_NONEXISTENT' not found.",
            None,
            "F_NONEXISTENT", "C_EXISTING_1"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_file_not_found_missing_files_key(self, mock_db):
        """Test FileNotFoundError when files key is missing from database."""
        mock_db.update({"channels": self.test_db["channels"]})
        
        self.assert_error_behavior(
            share_file,
            FileNotFoundError,
            "File 'F_TEST_FILE_1' not found.",
            None,
            "F_TEST_FILE_1", "C_EXISTING_1"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_file_not_found_nonexistent_file(self, mock_db):
        """Test FileNotFoundError when file doesn't exist."""
        mock_db.update(self.test_db)
        
        self.assert_error_behavior(
            share_file,
            FileNotFoundError,
            "File 'F_NONEXISTENT' not found.",
            None,
            "F_NONEXISTENT", "C_EXISTING_1"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_invalid_channel_id_single(self, mock_db):
        """Test InvalidChannelIdError for single invalid channel."""
        mock_db.update(self.test_db)
        
        self.assert_error_behavior(
            share_file,
            InvalidChannelIdError,
            "Invalid channel ID: 'C_NONEXISTENT'",
            None,
            "F_TEST_FILE_1", "C_NONEXISTENT"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_invalid_channel_id_multiple_first_invalid(self, mock_db):
        """Test InvalidChannelIdError when first channel in list is invalid."""
        mock_db.update(self.test_db)
        
        self.assert_error_behavior(
            share_file,
            InvalidChannelIdError,
            "Invalid channel ID: 'C_NONEXISTENT'",
            None,
            "F_TEST_FILE_1", "C_NONEXISTENT,C_EXISTING_1"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_invalid_channel_id_multiple_second_invalid(self, mock_db):
        """Test InvalidChannelIdError when second channel in list is invalid."""
        mock_db.update(self.test_db)
        
        self.assert_error_behavior(
            share_file,
            InvalidChannelIdError,
            "Invalid channel ID: 'C_NONEXISTENT'",
            None,
            "F_TEST_FILE_1", "C_EXISTING_1,C_NONEXISTENT"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_invalid_channel_id_missing_channels_key(self, mock_db):
        """Test InvalidChannelIdError when channels key is missing from database."""
        mock_db.update({"files": self.test_db["files"]})
        
        self.assert_error_behavior(
            share_file,
            InvalidChannelIdError,
            "Invalid channel ID: 'C_EXISTING_1'",
            None,
            "F_TEST_FILE_1", "C_EXISTING_1"
        )

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_invalid_channel_id_empty_channels_db(self, mock_db):
        """Test InvalidChannelIdError when channels database is empty."""
        mock_db.update({"files": self.test_db["files"], "channels": {}})
        
        self.assert_error_behavior(
            share_file,
            InvalidChannelIdError,
            "Invalid channel ID: 'C_EXISTING_1'",
            None,
            "F_TEST_FILE_1", "C_EXISTING_1"
        )

    # Edge cases and additional validation
    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_minimal_valid_ids(self, mock_db):
        """Test sharing with minimal valid IDs."""
        test_db = {
            "files": {
                "F": {
                    "id": "F",
                    "name": "f",
                    "channels": []
                }
            },
            "channels": {
                "C": {
                    "id": "C",
                    "files": {}
                }
            }
        }
        mock_db.update(test_db)
        
        result = share_file("F", "C")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["file_id"], "F")
        self.assertEqual(result["shared_to_channels"], ["C"])

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_unicode_ids(self, mock_db):
        """Test sharing with Unicode characters in IDs."""
        test_db = {
            "files": {
                "F_测试文件": {
                    "id": "F_测试文件",
                    "name": "test.txt",
                    "channels": []
                }
            },
            "channels": {
                "C_频道": {
                    "id": "C_频道",
                    "files": {}
                }
            }
        }
        mock_db.update(test_db)
        
        result = share_file("F_测试文件", "C_频道")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["file_id"], "F_测试文件")
        self.assertEqual(result["shared_to_channels"], ["C_频道"])

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_special_characters_in_ids(self, mock_db):
        """Test sharing with special characters in IDs."""
        test_db = {
            "files": {
                "F_test-file.123": {
                    "id": "F_test-file.123",
                    "name": "test.txt",
                    "channels": []
                }
            },
            "channels": {
                "C_channel-name.456": {
                    "id": "C_channel-name.456",
                    "files": {}
                }
            }
        }
        mock_db.update(test_db)
        
        result = share_file("F_test-file.123", "C_channel-name.456")
        
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["file_id"], "F_test-file.123")
        self.assertEqual(result["shared_to_channels"], ["C_channel-name.456"])

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_database_state_consistency(self, mock_db):
        """Test that database state remains consistent after sharing."""
        mock_db.update(self.test_db)
        
        # Share file to new channels
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2,C_EXISTING_3")
        
        # Verify file exists in all expected channels
        for channel_id in ["C_EXISTING_1", "C_EXISTING_2", "C_EXISTING_3"]:
            self.assertIn("F_TEST_FILE_1", mock_db["channels"][channel_id]["files"])
            self.assertTrue(mock_db["channels"][channel_id]["files"]["F_TEST_FILE_1"])
        
        # Verify file's channel list is correctly updated
        file_channels = mock_db["files"]["F_TEST_FILE_1"]["channels"]
        expected_channels = ["C_EXISTING_1", "C_EXISTING_2", "C_EXISTING_3"]
        self.assertEqual(set(file_channels), set(expected_channels))
        
        # Verify return value consistency
        self.assertEqual(set(result["file"]["channels"]), set(expected_channels))

    @patch("slack.Files.DB", new_callable=lambda: {})
    def test_share_file_preserves_other_file_data(self, mock_db):
        """Test that sharing preserves all other file data."""
        mock_db.update(self.test_db)
        
        original_file = mock_db["files"]["F_TEST_FILE_1"].copy()
        
        result = share_file("F_TEST_FILE_1", "C_EXISTING_2")
        
        # Verify all original data is preserved except channels
        returned_file = result["file"]
        for key, value in original_file.items():
            if key != "channels":
                self.assertEqual(returned_file[key], value)
        
        # Verify channels were updated correctly
        expected_channels = ["C_EXISTING_1", "C_EXISTING_2"]
        self.assertEqual(set(returned_file["channels"]), set(expected_channels))


if __name__ == "__main__":
    unittest.main() 