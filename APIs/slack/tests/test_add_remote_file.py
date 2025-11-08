"""
Comprehensive test suite for the add_remote_file function.

This module provides 100% test coverage of all documented behavior including:
- Success cases with various parameter combinations
- TypeError exceptions for invalid parameter types 
- ValueError exceptions for empty/invalid parameter values
- Edge cases and boundary conditions

Uses assert_error_behavior utility for consistent exception testing.
"""

import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import add_remote_file

class TestAddRemoteFile(BaseTestCaseWithErrorHandler):
    """Comprehensive test class for add_remote_file function with 100% docstring coverage."""

    def setUp(self):
        """Set up test environment with mock database."""
        self.test_db = {
            "files": {},
            "channels": {},
            "users": {},
        }

    # ==================== SUCCESS CASES ====================

    def test_add_remote_file_success_required_params_only(self):
        """Test successful file addition with only required parameters."""
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file("ext_123", "https://example.com/file.pdf", "My Test File")
            
            # Should return a dictionary with ok=True and file object
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            self.assertIn("file", result)
            file_id = result["file"]["id"]
            self.assertIsInstance(file_id, str)
            self.assertTrue(len(file_id) > 0)
            
            # Verify file was added to database
            self.assertIn(file_id, self.test_db["files"])
            file_data = self.test_db["files"][file_id]
            self.assertEqual(file_data["external_id"], "ext_123")
            self.assertEqual(file_data["external_url"], "https://example.com/file.pdf")
            self.assertEqual(file_data["title"], "My Test File")
            self.assertIsNone(file_data["filetype"])
            self.assertIsNone(file_data["indexable_file_contents"])

    def test_add_remote_file_success_all_params(self):
        """Test successful file addition with all parameters provided."""
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file(
                "ext_456", 
                "https://example.com/document.docx", 
                "Complete Document",
                "docx",
                "searchable content here"
            )
            
            # Should return a dictionary with ok=True and file object
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            self.assertIn("file", result)
            file_id = result["file"]["id"]
            self.assertIsInstance(file_id, str)
            self.assertTrue(len(file_id) > 0)
            
            # Verify file was added with all parameters
            file_data = self.test_db["files"][file_id]
            self.assertEqual(file_data["external_id"], "ext_456")
            self.assertEqual(file_data["external_url"], "https://example.com/document.docx")
            self.assertEqual(file_data["title"], "Complete Document")
            self.assertEqual(file_data["filetype"], "docx")
            self.assertEqual(file_data["indexable_file_contents"], "searchable content here")

    def test_add_remote_file_success_explicit_none_optionals(self):
        """Test successful file addition with explicit None for optional parameters."""
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file("ext_789", "https://example.com/file.txt", "Text File", None, None)
            
            # Should return a dictionary with ok=True and file object
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            self.assertIn("file", result)
            file_id = result["file"]["id"]
            
            # Verify optional parameters are None
            file_data = self.test_db["files"][file_id]
            self.assertIsNone(file_data["filetype"])
            self.assertIsNone(file_data["indexable_file_contents"])

    # ==================== TYPEERROR TESTS ====================

    def test_add_remote_file_external_id_not_string_integer(self):
        """Test TypeError when external_id is an integer."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="external_id must be a string",
            external_id=123,
            external_url="https://example.com/file.pdf",
            title="Test File"
        )

    def test_add_remote_file_external_id_not_string_list(self):
        """Test TypeError when external_id is a list."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="external_id must be a string",
            external_id=["ext_id"],
            external_url="https://example.com/file.pdf",
            title="Test File"
        )

    def test_add_remote_file_external_id_not_string_none(self):
        """Test TypeError when external_id is None."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="external_id must be a string",
            external_id=None,
            external_url="https://example.com/file.pdf",
            title="Test File"
        )

    def test_add_remote_file_external_url_not_string_integer(self):
        """Test TypeError when external_url is an integer."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="external_url must be a string",
            external_id="ext_123",
            external_url=12345,
            title="Test File"
        )

    def test_add_remote_file_external_url_not_string_dict(self):
        """Test TypeError when external_url is a dictionary."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="external_url must be a string",
            external_id="ext_123",
            external_url={"url": "https://example.com"},
            title="Test File"
        )

    def test_add_remote_file_title_not_string_integer(self):
        """Test TypeError when title is an integer."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="title must be a string",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title=42
        )

    def test_add_remote_file_title_not_string_boolean(self):
        """Test TypeError when title is a boolean."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="title must be a string",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title=True
        )

    def test_add_remote_file_filetype_not_string_or_none_integer(self):
        """Test TypeError when filetype is an integer."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="filetype must be a string or None",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=123
        )

    def test_add_remote_file_filetype_not_string_or_none_list(self):
        """Test TypeError when filetype is a list."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="filetype must be a string or None",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=["pdf"]
        )

    def test_add_remote_file_indexable_contents_not_string_or_none_integer(self):
        """Test TypeError when indexable_file_contents is an integer."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="indexable_file_contents must be a string or None",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=None,
            indexable_file_contents=456
        )

    def test_add_remote_file_indexable_contents_not_string_or_none_dict(self):
        """Test TypeError when indexable_file_contents is a dictionary."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=TypeError,
            expected_message="indexable_file_contents must be a string or None",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=None,
            indexable_file_contents={"content": "text"}
        )

    # ==================== VALUEERROR TESTS ====================

    def test_add_remote_file_external_id_empty_string(self):
        """Test ValueError when external_id is an empty string."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="external_id cannot be empty",
            external_id="",
            external_url="https://example.com/file.pdf",
            title="Test File"
        )

    def test_add_remote_file_external_id_whitespace_only(self):
        """Test ValueError when external_id contains only whitespace."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="external_id cannot be empty",
            external_id="   \t\n  ",
            external_url="https://example.com/file.pdf",
            title="Test File"
        )

    def test_add_remote_file_external_url_empty_string(self):
        """Test ValueError when external_url is an empty string."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="external_url cannot be empty",
            external_id="ext_123",
            external_url="",
            title="Test File"
        )

    def test_add_remote_file_external_url_whitespace_only(self):
        """Test ValueError when external_url contains only whitespace."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="external_url cannot be empty",
            external_id="ext_123",
            external_url="  \t  ",
            title="Test File"
        )

    def test_add_remote_file_title_empty_string(self):
        """Test ValueError when title is an empty string."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="title cannot be empty",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title=""
        )

    def test_add_remote_file_title_whitespace_only(self):
        """Test ValueError when title contains only whitespace."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="title cannot be empty",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="   \n\t   "
        )

    def test_add_remote_file_filetype_empty_string(self):
        """Test ValueError when filetype is an empty string (not None)."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="filetype cannot be empty string",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=""
        )

    def test_add_remote_file_filetype_whitespace_only(self):
        """Test ValueError when filetype contains only whitespace."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="filetype cannot be empty string",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype="  \t  "
        )

    def test_add_remote_file_indexable_contents_empty_string(self):
        """Test ValueError when indexable_file_contents is an empty string (not None)."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="indexable_file_contents cannot be empty string",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=None,
            indexable_file_contents=""
        )

    def test_add_remote_file_indexable_contents_whitespace_only(self):
        """Test ValueError when indexable_file_contents contains only whitespace."""
        self.assert_error_behavior(
            func_to_call=add_remote_file,
            expected_exception_type=ValueError,
            expected_message="indexable_file_contents cannot be empty string",
            external_id="ext_123",
            external_url="https://example.com/file.pdf",
            title="Test File",
            filetype=None,
            indexable_file_contents="   \n   "
        )

    # ==================== EDGE CASES ====================

    def test_add_remote_file_minimal_valid_strings(self):
        """Test with minimal valid strings (single character)."""
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file("a", "b", "c")
            
            # Should succeed
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            file_id = result["file"]["id"]
            
            # Verify data
            file_data = self.test_db["files"][file_id]
            self.assertEqual(file_data["external_id"], "a")
            self.assertEqual(file_data["external_url"], "b")
            self.assertEqual(file_data["title"], "c")

    def test_add_remote_file_unicode_characters(self):
        """Test with Unicode characters in string parameters."""
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file(
                "ext_ñ_🔥", 
                "https://例え.com/ファイル.pdf", 
                "Título con acentós 🎉"
            )
            
            # Should succeed
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            file_id = result["file"]["id"]
            
            # Verify Unicode data preserved
            file_data = self.test_db["files"][file_id]
            self.assertEqual(file_data["external_id"], "ext_ñ_🔥")
            self.assertEqual(file_data["external_url"], "https://例え.com/ファイル.pdf")
            self.assertEqual(file_data["title"], "Título con acentós 🎉")

    def test_add_remote_file_very_long_strings(self):
        """Test with very long strings."""
        long_string = "x" * 1000
        
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file(long_string, long_string, long_string)
            
            # Should succeed
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            file_id = result["file"]["id"]
            
            # Verify long data preserved
            file_data = self.test_db["files"][file_id]
            self.assertEqual(len(file_data["external_id"]), 1000)
            self.assertEqual(len(file_data["external_url"]), 1000)
            self.assertEqual(len(file_data["title"]), 1000)

    def test_add_remote_file_special_characters(self):
        """Test with special characters and escape sequences."""
        with patch("slack.Files.DB", self.test_db):
            result = add_remote_file(
                "ext_id\n\t\"'\\",
                "https://example.com/file with spaces & symbols!@#$%^&*()_+",
                "Title: \"Quotes\" & 'Apostrophes' \\Backslashes\\ /Slashes/"
            )
            
            # Should succeed
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            file_id = result["file"]["id"]
            
            # Verify special characters preserved
            file_data = self.test_db["files"][file_id]
            self.assertIn("\n\t\"'\\", file_data["external_id"])
            self.assertIn("spaces & symbols", file_data["external_url"])
            self.assertIn("\"Quotes\"", file_data["title"])

    def test_add_remote_file_database_initialization(self):
        """Test that function properly initializes files key in database if missing."""
        # Start with empty DB (no 'files' key)
        empty_db = {}
        
        with patch("slack.Files.DB", empty_db):
            result = add_remote_file("test_id", "test_url", "test_title")
            
            # Should succeed and create 'files' key
            self.assertIsInstance(result, dict)
            self.assertTrue(result["ok"])
            file_id = result["file"]["id"]
            self.assertIn("files", empty_db)
            self.assertIn(file_id, empty_db["files"])

    def test_add_remote_file_return_value_consistency(self):
        """Test that function consistently returns unique file IDs."""
        with patch("slack.Files.DB", self.test_db):
            # Create multiple files
            results = []
            file_ids = []
            for i in range(5):
                result = add_remote_file(f"ext_{i}", f"url_{i}", f"title_{i}")
                results.append(result)
                file_ids.append(result["file"]["id"])
            
            # All results should be dictionaries
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertTrue(result["ok"])
                self.assertIn("file", result)
                self.assertIsInstance(result["file"]["id"], str)
                self.assertTrue(len(result["file"]["id"]) > 0)
            
            # All file IDs should be unique
            self.assertEqual(len(file_ids), len(set(file_ids)))
            
            # All files should be in database
            for file_id in file_ids:
                self.assertIn(file_id, self.test_db["files"])


if __name__ == "__main__":
    unittest.main() 