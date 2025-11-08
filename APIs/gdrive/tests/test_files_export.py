import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (DB, export_google_doc, _ensure_user)

class TestFilesExport(BaseTestCaseWithErrorHandler):
    """Test class for export_google_doc function with comprehensive coverage."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset DB before each test
        global DB
        DB.update(
            {
                "users": {
                    "me": {
                        "about": {
                            "kind": "drive#about",
                            "storageQuota": {
                                "limit": "107374182400",
                                "usageInDrive": "0",
                                "usageInDriveTrash": "0",
                                "usage": "0",
                            },
                            "user": {
                                "displayName": "Test User",
                                "kind": "drive#user",
                                "me": True,
                                "permissionId": "test_permission_id",
                                "emailAddress": "test@example.com",
                            },
                        },
                        "files": {
                            "test_doc_id": {
                                "id": "test_doc_id",
                                "name": "Test Document",
                                "mimeType": "application/vnd.google-apps.document",
                                "kind": "drive#file",
                                "size": "1024",
                                "createdTime": "2025-06-30T10:00:00Z",
                                "modifiedTime": "2025-06-30T10:00:00Z",
                                "owners": ["test@example.com"],
                                "trashed": False,
                                "starred": False,
                                "parents": [],
                                "permissions": [],
                            },
                            "test_sheet_id": {
                                "id": "test_sheet_id",
                                "name": "Test Spreadsheet",
                                "mimeType": "application/vnd.google-apps.spreadsheet",
                                "kind": "drive#file",
                                "size": "2048",
                                "createdTime": "2025-06-30T10:00:00Z",
                                "modifiedTime": "2025-06-30T10:00:00Z",
                                "owners": ["test@example.com"],
                                "trashed": False,
                                "starred": False,
                                "parents": [],
                                "permissions": [],
                            },
                            "test_pdf_id": {
                                "id": "test_pdf_id",
                                "name": "Test PDF",
                                "mimeType": "application/pdf",
                                "kind": "drive#file",
                                "size": "4096",
                                "createdTime": "2025-06-30T10:00:00Z",
                                "modifiedTime": "2025-06-30T10:00:00Z",
                                "owners": ["test@example.com"],
                                "trashed": False,
                                "starred": False,
                                "parents": [],
                                "permissions": [],
                            },
                            "untitled_file_id": {
                                "id": "untitled_file_id",
                                "name": "Untitled",
                                "mimeType": "application/octet-stream",
                                "kind": "drive#file",
                                "size": "512",
                                "createdTime": "2025-06-30T10:00:00Z",
                                "modifiedTime": "2025-06-30T10:00:00Z",
                                "owners": ["test@example.com"],
                                "trashed": False,
                                "starred": False,
                                "parents": [],
                                "permissions": [],
                            },
                            "file_without_name": {
                                "id": "file_without_name",
                                "name": "Untitled",
                                "mimeType": "text/plain",
                                "kind": "drive#file",
                                "size": "256",
                                "createdTime": "2025-06-30T10:00:00Z",
                                "modifiedTime": "2025-06-30T10:00:00Z",
                                "owners": ["test@example.com"],
                                "trashed": False,
                                "starred": False,
                                "parents": [],
                                "permissions": [],
                            },
                        },
                        "counters": {"file": 5},
                    }
                }
            }
        )
        # Ensure the user exists
        _ensure_user("me")

    # Valid input test cases
    def test_export_valid_doc_to_pdf(self):
        """Test exporting a Google Doc to PDF format."""
        result = export_google_doc("test_doc_id", "application/pdf")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], "drive#export")
        self.assertEqual(result["fileId"], "test_doc_id")
        self.assertEqual(result["mimeType"], "application/pdf")
        self.assertIsInstance(result["content"], str)
        self.assertIn("PDF export of 'Test Document'", result["content"])
        self.assertIn("application/vnd.google-apps.document", result["content"])

    def test_export_valid_doc_to_text(self):
        """Test exporting a Google Doc to text format (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'text/plain' is not supported for 'application/vnd.google-apps.spreadsheet'. Supported formats: ['application/pdf', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv', 'text/tab-separated-values', 'text/html']",
            fileId="test_sheet_id",
            mimeType="text/plain",
        )

    def test_export_valid_doc_to_docx(self):
        """Test exporting a document to Word format."""
        result = export_google_doc(
            "test_doc_id",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], "drive#export")
        self.assertEqual(result["fileId"], "test_doc_id")
        self.assertEqual(
            result["mimeType"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIsInstance(result["content"], str)
        self.assertIn("Word document export of 'Test Document'", result["content"])

    def test_export_valid_doc_to_word_mime_type(self):
        """Test exporting with a MIME type containing 'word'."""
        result = export_google_doc("test_doc_id", "application/msword")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], "drive#export")
        self.assertEqual(result["fileId"], "test_doc_id")
        self.assertEqual(result["mimeType"], "application/msword")
        self.assertIsInstance(result["content"], str)
        self.assertIn("Word document export of 'Test Document'", result["content"])

    def test_export_valid_other_mime_type(self):
        """Test exporting to a MIME type not specifically handled (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to format 'application/json' is not supported. File type 'application/pdf' is not a supported Google Workspace type for export operations.",
            fileId="test_pdf_id",
            mimeType="application/json",
        )

    def test_export_file_without_name_uses_untitled(self):
        """Test exporting a file that has no name uses 'Untitled' (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to format 'text/plain' is not supported. File type 'application/octet-stream' is not a supported Google Workspace type for export operations.",
            fileId="untitled_file_id",
            mimeType="text/plain",
        )

    def test_export_file_with_missing_name_key(self):
        """Test exporting a file where the name key is missing from file data (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to format 'application/pdf' is not supported. File type 'text/plain' is not a supported Google Workspace type for export operations.",
            fileId="file_without_name",
            mimeType="application/pdf",
        )

    # Input validation test cases - TypeError
    def test_export_invalid_fileid_type_integer(self):
        """Test export raises TypeError for integer fileId."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId=12345,
            mimeType="application/pdf",
        )

    def test_export_invalid_fileid_type_none(self):
        """Test export raises TypeError for None fileId."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId=None,
            mimeType="application/pdf",
        )

    def test_export_invalid_fileid_type_list(self):
        """Test export raises TypeError for list fileId."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId=["file_id"],
            mimeType="application/pdf",
        )

    def test_export_invalid_fileid_type_dict(self):
        """Test export raises TypeError for dict fileId."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId={"id": "file_id"},
            mimeType="application/pdf",
        )

    def test_export_invalid_mimetype_type_integer(self):
        """Test export raises TypeError for integer mimeType."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="mimeType must be a string.",
            fileId="test_doc_id",
            mimeType=12345,
        )

    def test_export_invalid_mimetype_type_none(self):
        """Test export raises TypeError for None mimeType."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="mimeType must be a string.",
            fileId="test_doc_id",
            mimeType=None,
        )

    def test_export_invalid_mimetype_type_list(self):
        """Test export raises TypeError for list mimeType."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="mimeType must be a string.",
            fileId="test_doc_id",
            mimeType=["application/pdf"],
        )

    def test_export_invalid_mimetype_type_dict(self):
        """Test export raises TypeError for dict mimeType."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=TypeError,
            expected_message="mimeType must be a string.",
            fileId="test_doc_id",
            mimeType={"type": "application/pdf"},
        )

    # Input validation test cases - ValueError
    def test_export_empty_fileid(self):
        """Test export raises ValueError for empty string fileId."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="fileId cannot be empty or contain only whitespace.",
            fileId="",
            mimeType="application/pdf",
        )

    def test_export_whitespace_only_fileid(self):
        """Test export raises ValueError for whitespace-only fileId."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="fileId cannot be empty or contain only whitespace.",
            fileId="   ",
            mimeType="application/pdf",
        )

    def test_export_tabs_and_spaces_fileid(self):
        """Test export raises ValueError for fileId with only tabs and spaces."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="fileId cannot be empty or contain only whitespace.",
            fileId="\t\n  \r",
            mimeType="application/pdf",
        )

    def test_export_empty_mimetype(self):
        """Test export raises ValueError for empty string mimeType."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="mimeType cannot be empty or contain only whitespace.",
            fileId="test_doc_id",
            mimeType="",
        )

    def test_export_whitespace_only_mimetype(self):
        """Test export raises ValueError for whitespace-only mimeType."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="mimeType cannot be empty or contain only whitespace.",
            fileId="test_doc_id",
            mimeType="   ",
        )

    def test_export_tabs_and_spaces_mimetype(self):
        """Test export raises ValueError for mimeType with only tabs and spaces."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="mimeType cannot be empty or contain only whitespace.",
            fileId="test_doc_id",
            mimeType="\t\n  \r",
        )

    # FileNotFoundError test cases
    def test_export_file_not_found(self):
        """Test export raises FileNotFoundError for non-existent file."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=FileNotFoundError,
            expected_message="File with ID 'non_existent_file' not found for user 'me'",
            fileId="non_existent_file",
            mimeType="application/pdf",
        )

    def test_export_file_not_found_valid_string(self):
        """Test export raises FileNotFoundError for valid string but non-existent file."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=FileNotFoundError,
            expected_message="File with ID 'missing_file_123' not found for user 'me'",
            fileId="missing_file_123",
            mimeType="text/plain",
        )

    # Edge cases for content generation
    def test_export_case_insensitive_mime_type_pdf(self):
        """Test export handles case-insensitive MIME type matching for PDF (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'APPLICATION/PDF' is not supported for 'application/vnd.google-apps.document'. Supported formats: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'text/plain', 'text/html']",
            fileId="test_doc_id",
            mimeType="APPLICATION/PDF",
        )

    def test_export_case_insensitive_mime_type_text(self):
        """Test export handles case-insensitive MIME type matching for text (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'TEXT/PLAIN' is not supported for 'application/vnd.google-apps.document'. Supported formats: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'text/plain', 'text/html']",
            fileId="test_doc_id",
            mimeType="TEXT/PLAIN",
        )

    def test_export_case_insensitive_mime_type_docx(self):
        """Test export handles case-insensitive MIME type matching for DOCX (should raise ValueError)."""
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'application/vnd.openxmlformats-officedocument.WORDPROCESSINGML.document' is not supported for 'application/vnd.google-apps.document'. Supported formats: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'text/plain', 'text/html']",
            fileId="test_doc_id",
            mimeType="application/vnd.openxmlformats-officedocument.WORDPROCESSINGML.document",
        )

    def test_export_partial_mime_type_matches(self):
        """Test export handles partial MIME type matching (should raise ValueError for unsupported)."""
        # Test partial PDF match (should raise ValueError)
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'custom/pdf-variant' is not supported for 'application/vnd.google-apps.document'. Supported formats: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'text/plain', 'text/html']",
            fileId="test_doc_id",
            mimeType="custom/pdf-variant",
        )
        # Test partial text match (should raise ValueError)
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'custom/text-variant' is not supported for 'application/vnd.google-apps.document'. Supported formats: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'text/plain', 'text/html']",
            fileId="test_doc_id",
            mimeType="custom/text-variant",
        )
        # Test partial word match (should raise ValueError)
        self.assert_error_behavior(
            func_to_call=export_google_doc,
            expected_exception_type=ValueError,
            expected_message="Export to 'custom/word-variant' is not supported for 'application/vnd.google-apps.document'. Supported formats: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'text/plain', 'text/html']",
            fileId="test_doc_id",
            mimeType="custom/word-variant",
        )

    def test_export_file_with_special_characters_in_name(self):
        """Test export handles files with special characters in name."""
        # Add a file with special characters in name
        DB["users"]["me"]["files"]["special_char_file"] = {
            "id": "special_char_file",
            "name": "Test File with Special Chars: @#$%^&*()",
            "mimeType": "application/vnd.google-apps.document",
            "kind": "drive#file",
            "size": "1024",
            "createdTime": "2025-06-30T10:00:00Z",
            "modifiedTime": "2025-06-30T10:00:00Z",
            "owners": ["test@example.com"],
            "trashed": False,
            "starred": False,
            "parents": [],
            "permissions": [],
        }

        result = export_google_doc("special_char_file", "application/pdf")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], "drive#export")
        self.assertEqual(result["fileId"], "special_char_file")
        self.assertEqual(result["mimeType"], "application/pdf")
        self.assertIsInstance(result["content"], str)
        self.assertIn(
            "PDF export of 'Test File with Special Chars: @#$%^&*()'",
            result["content"],
        )

    def test_export_file_with_unicode_name(self):
        """Test export handles files with Unicode characters in name."""
        # Add a file with Unicode characters in name
        DB["users"]["me"]["files"]["unicode_file"] = {
            "id": "unicode_file",
            "name": "测试文档 café naïve résumé",
            "mimeType": "application/vnd.google-apps.document",
            "kind": "drive#file",
            "size": "1024",
            "createdTime": "2025-06-30T10:00:00Z",
            "modifiedTime": "2025-06-30T10:00:00Z",
            "owners": ["test@example.com"],
            "trashed": False,
            "starred": False,
            "parents": [],
            "permissions": [],
        }

        result = export_google_doc("unicode_file", "text/plain")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["kind"], "drive#export")
        self.assertEqual(result["fileId"], "unicode_file")
        self.assertEqual(result["mimeType"], "text/plain")
        self.assertIsInstance(result["content"], str)
        # The content should include the Unicode filename properly encoded
        self.assertIn("测试文档 café naïve résumé", result["content"])


if __name__ == "__main__":
    unittest.main()
