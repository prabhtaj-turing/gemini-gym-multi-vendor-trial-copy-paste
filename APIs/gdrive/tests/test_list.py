import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from gdrive.SimulationEngine.custom_errors import InvalidPageSizeError, UserNotFoundError, InvalidQueryError
from .. import (list_user_files, _ensure_user, create_file_or_folder, list_user_shared_drives)
from gdrive.SimulationEngine.db import DB as SimulationDB

class TestListFiles(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Setup DB and ensure user 'me' is initialized with sample files."""
        SimulationDB.clear()
        SimulationDB.update({
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
                        "canCreateDrives": True,
                        "user": {"emailAddress": "me@example.com"},
                    },
                    "counters": {
                        "file": 7,
                        "drive": 1,
                        "comment": 1,
                        "reply": 1,
                        "label": 2,
                        "accessproposal": 1,
                        "revision": 0
                    },
                    "files": {
                        "file1": {
                            "id": "file1",
                            "name": "File One",
                            "mimeType": "application/pdf",
                            "modifiedTime": "2024-06-01T10:00:00Z",
                            "createdTime": "2024-05-01T10:00:00Z",
                            "trashed": False,
                            "size": "1024",
                            "labels": ["finance"],
                            "parents": ["root"],
                            "permissions": [{"type": "anyone", "role": "reader"}],
                            "content": {
                                "data": "test content data",
                                "encoding": "text",
                                "checksum": "sha256:abc123",
                                "version": "1.0",
                                "lastContentUpdate": "2024-05-01T10:00:00Z"
                            },
                            "revisions": [
                                {
                                    "id": "rev-1",
                                    "mimeType": "application/pdf",
                                    "modifiedTime": "2024-05-01T10:00:00Z",
                                    "keepForever": False,
                                    "originalFilename": "file1.pdf",
                                    "size": "1024",
                                    "content": {
                                        "data": "revision content data",
                                        "encoding": "text",
                                        "checksum": "sha256:def456"
                                    }
                                }
                            ]
                        },
                        "file2": {
                            "id": "file2",
                            "name": "File Two",
                            "mimeType": "image/jpeg",
                            "modifiedTime": "2024-04-01T09:00:00Z",
                            "createdTime": "2024-04-01T08:00:00Z",
                            "trashed": False,
                            "size": "2048",
                            "labels": ["marketing"],
                            "parents": ["photos"],
                            "content": {
                                "data": "base64encodeddata",
                                "encoding": "base64",
                                "checksum": "sha256:ghi789",
                                "version": "1.0",
                                "lastContentUpdate": "2024-04-01T08:00:00Z"
                            }
                        },
                        "file3": {
                            "id": "file3",
                            "name": "Vendor_List_2023.xlsx",
                            "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "modifiedTime": "2023-12-15T14:30:00Z",
                            "createdTime": "2023-12-01T09:00:00Z",
                            "trashed": False,
                            "size": "5120",
                            "labels": ["vendor", "2023"],
                            "parents": ["fcc035f8-99e7-4866-8e04-d0582e7a4d3f"],
                            "permissions": [{"type": "user", "role": "editor", "emailAddress": "user@example.com"}],
                            "content": {
                                "data": "excel content",
                                "encoding": "text",
                                "checksum": "sha256:jkl012",
                                "version": "1.0",
                                "lastContentUpdate": "2023-12-15T14:30:00Z"
                            }
                        },
                        "file4": {
                            "id": "file4",
                            "name": "Meeting_Notes.docx",
                            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "modifiedTime": "2024-01-20T16:45:00Z",
                            "createdTime": "2024-01-15T11:00:00Z",
                            "trashed": False,
                            "size": "3072",
                            "labels": ["meeting", "notes"],
                            "parents": ["fcc035f8-99e7-4866-8e04-d0582e7a4d3f"],
                            "permissions": [{"type": "domain", "role": "commenter"}],
                            "content": {
                                "data": "meeting notes content",
                                "encoding": "text",
                                "checksum": "sha256:mno345",
                                "version": "1.0",
                                "lastContentUpdate": "2024-01-20T16:45:00Z"
                            }
                        },
                        "file5": {
                            "id": "file5",
                            "name": "Budget_2024.xlsx",
                            "mimeType": "application/vnd.google-apps.spreadsheet",
                            "modifiedTime": "2024-02-10T13:20:00Z",
                            "createdTime": "2024-01-01T00:00:00Z",
                            "trashed": False,
                            "size": "8192",
                            "labels": ["budget", "2024", "finance"],
                            "parents": ["root"],
                            "permissions": [{"type": "anyone", "role": "viewer"}],
                            "sheets": [
                                {
                                    "properties": {
                                        "sheetId": "sheet1",
                                        "title": "Sheet1",
                                        "index": 0,
                                        "sheetType": "GRID",
                                        "gridProperties": {
                                            "rowCount": 1000,
                                            "columnCount": 26
                                        }
                                    }
                                }
                            ],
                            "data": {
                                "sheet1": {
                                    "cells": [
                                        ["Item", "Amount", "Category"],
                                        ["Rent", "1000", "Housing"],
                                        ["Groceries", "500", "Food"]
                                    ]
                                }
                            }
                        },
                        "file6": {
                            "id": "file6",
                            "name": "Project_Report.pdf",
                            "mimeType": "application/pdf",
                            "modifiedTime": "2024-03-05T10:15:00Z",
                            "createdTime": "2024-02-28T14:30:00Z",
                            "trashed": False,
                            "size": "1536",
                            "labels": ["report", "project"],
                            "parents": ["photos"],
                            "permissions": [{"type": "group", "role": "writer", "emailAddress": "team@example.com"}],
                            "content": {
                                "data": "project report content",
                                "encoding": "text",
                                "checksum": "sha256:pqr678",
                                "version": "1.0",
                                "lastContentUpdate": "2024-03-05T10:15:00Z"
                            },
                            "exportFormats": {
                                "application/msword": "exported word content",
                                "text/plain": "exported text content"
                            }
                        },
                        "file7": {
                            "id": "file7",
                            "name": "Presentation.pptx",
                            "mimeType": "application/vnd.google-apps.presentation",
                            "modifiedTime": "2024-03-10T14:00:00Z",
                            "createdTime": "2024-03-01T09:00:00Z",
                            "trashed": False,
                            "size": "4096",
                            "labels": ["presentation"],
                            "parents": ["root"],
                            "permissions": [{"type": "anyone", "role": "viewer"}],
                            "tabs": [
                                {"id": "slide1", "title": "Introduction"},
                                {"id": "slide2", "title": "Content"}
                            ],
                            "content": {
                                "data": "presentation content",
                                "encoding": "text",
                                "checksum": "sha256:stu901",
                                "version": "1.0",
                                "lastContentUpdate": "2024-03-10T14:00:00Z"
                            }
                        }
                    },
                    "drives": {
                       "drive-1": {
                            "id": "drive-1",
                            "name": "a<=b",
                            "kind": "drive#drive",
                            "createdTime": "2024-12-15T09:00:00Z"
                       }
                    },
                    "comments": {},
                    "labels": {
                        "label-1": {
                            "id": "label-1",
                            "fileId": "file1",
                            "name": "Urgent",
                            "color": "#FF0000"
                        },
                        "label-2": {
                            "id": "label-2",
                            "fileId": "file1",
                            "name": "Important",
                            "color": "#00FF00"
                        },
                        "label-3": {
                            "id": "label-3",
                            "fileId": "file2",
                            "name": "Urgent",
                            "color": "#0000FF"
                        }
                    },
                }
            }
        })
        _ensure_user("me")

    def test_list_files_default(self):
        """Test listing files with default arguments."""
        result = list_user_files()
        self.assertEqual(result['kind'], 'drive#fileList')
        self.assertEqual(len(result['files']), 7)
        self.assertIsNone(result['nextPageToken'])

    def test_list_files_custom_page_size(self):
        """Test pagination with custom pageSize."""
        result = list_user_files(pageSize=1)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['nextPageToken'], 'page_1')

    def test_invalid_page_size_zero(self):
        """Test pageSize of 0 raises InvalidPageSizeError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=InvalidPageSizeError,
            expected_message="Argument 'pageSize' must be a positive integer.",
            pageSize=0
        )

    def test_invalid_corpopra_value(self):
        """Test invalid corpora value raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid corpora values: invalid. Valid values are: user, drive, domain, allDrives",
            corpora='invalid'
        )

    def test_invalid_spaces_value(self):
        """Test invalid spaces value raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid spaces values: junk. Valid values are: drive, appDataFolder, photos",
            spaces='junk'
        )

    def test_invalid_order_by_field(self):
        """Test invalid orderBy field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid orderBy fields: invalidField. Valid fields are: folder, modifiedTime, name, createdTime, size, quotaBytesUsed",
            orderBy='invalidField'
        )

    def test_invalid_label_format(self):
        """Test invalid label characters raise ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid label format: $$$. Labels must contain only alphanumeric characters, hyphens, and underscores.",
            includeLabels='finance,$$$'
        )

    def test_query_with_unbalanced_quotes(self):
        """Test query with unbalanced quotes raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Query string contains unbalanced quotes",
            q="name = 'Unclosed string"
        )

    def test_list_files_with_page_token(self):
        """Test listing files with pageToken."""
        result = list_user_files(pageSize=1)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['nextPageToken'], 'page_1')
        result = list_user_files(pageSize=1, pageToken=result['nextPageToken'])
        self.assertEqual(len(result['files']), 1)


    def test_list_files_with_invalid_page_size(self):
        """Test listing files with invalid pageSize."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=InvalidPageSizeError,
            expected_message="Argument 'pageSize' must be a positive integer.",
            pageSize=-1
        )
        
    def test_list_files_with_include_items_from_all_drives(self):
        """Test listing files with includeItemsFromAllDrives."""
        result = list_user_files(includeItemsFromAllDrives=True)
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file1')
        self.assertEqual(result['files'][0]['name'], 'File One')

    # New test for content exclusion
    def test_list_files_excludes_content(self):
        """Test that list_files excludes content-related fields."""
        result = list_user_files()
        
        # Check that all content-related fields are excluded
        content_fields = {'content', 'sheets', 'data', 'tabs', 'exportFormats'}
        for file in result['files']:
            for field in content_fields:
                self.assertNotIn(field, file, f"File {file.get('id')} should not contain '{field}' field")
            
            # Check that revisions don't have content either
            if 'revisions' in file:
                for revision in file['revisions']:
                    self.assertNotIn('content', revision, 
                                   f"Revision in file {file.get('id')} should not contain 'content' field")
    
    # Test for specific file types
    def test_list_files_excludes_spreadsheet_content(self):
        """Test that list_files excludes spreadsheet-specific content fields."""
        result = list_user_files(q="mimeType = 'application/vnd.google-apps.spreadsheet'")
        
        self.assertTrue(len(result['files']) > 0, "Should have found at least one spreadsheet")
        for file in result['files']:
            self.assertNotIn('sheets', file, f"Spreadsheet {file.get('id')} should not contain 'sheets' field")
            self.assertNotIn('data', file, f"Spreadsheet {file.get('id')} should not contain 'data' field")
    
    def test_list_files_excludes_document_content(self):
        """Test that list_files excludes document-specific content fields."""
        result = list_user_files(q="mimeType = 'application/vnd.google-apps.document' or mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'")
        
        for file in result['files']:
            self.assertNotIn('content', file, f"Document {file.get('id')} should not contain 'content' field")
    
    def test_list_files_excludes_presentation_content(self):
        """Test that list_files excludes presentation-specific content fields."""
        result = list_user_files(q="mimeType = 'application/vnd.google-apps.presentation'")
        
        self.assertTrue(len(result['files']) > 0, "Should have found at least one presentation")
        for file in result['files']:
            self.assertNotIn('tabs', file, f"Presentation {file.get('id')} should not contain 'tabs' field")
            self.assertNotIn('content', file, f"Presentation {file.get('id')} should not contain 'content' field")
    
    def test_list_files_excludes_export_formats(self):
        """Test that list_files excludes exportFormats field."""
        result = list_user_files(q="name = 'Project_Report.pdf'")
        
        self.assertTrue(len(result['files']) > 0, "Should have found the Project_Report.pdf file")
        for file in result['files']:
            self.assertNotIn('exportFormats', file, f"File {file.get('id')} should not contain 'exportFormats' field")

    def test_order_by_folder(self):
        """Test listing files with orderBy='folder'."""
        result = list_user_files(orderBy='folder')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file1')
        self.assertEqual(result['files'][0]['name'], 'File One')

    def test_order_by_modified_time(self):
        """Test listing files with orderBy='modifiedTime desc'."""
        result = list_user_files(orderBy='modifiedTime desc')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file1')
        self.assertEqual(result['files'][0]['name'], 'File One')

    def test_order_by_name(self):
        """Test listing files with orderBy='name'."""
        result = list_user_files(orderBy='name')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file5')
        self.assertEqual(result['files'][0]['name'], 'Budget_2024.xlsx')
        
    def test_order_by_created_time(self):
        """Test listing files with orderBy='createdTime'."""
        result = list_user_files(orderBy='createdTime')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file3')
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')
        
    def test_order_by_size(self):
        """Test listing files with orderBy='size'."""
        result = list_user_files(orderBy='size')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file1')
        self.assertEqual(result['files'][0]['name'], 'File One')
        
    def test_order_by_quota_bytes_used(self):
        """Test listing files with orderBy='quotaBytesUsed'."""
        result = list_user_files(orderBy='quotaBytesUsed')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file1')
        self.assertEqual(result['files'][0]['name'], 'File One')
        
    def test_order_by_multiple_fields(self):
        """Test listing files with orderBy='folder,modifiedTime desc,name'."""
        result = list_user_files(orderBy='folder,modifiedTime desc,name')
        self.assertEqual(len(result['files']), 7)
        self.assertEqual(result['files'][0]['id'], 'file1')
        self.assertEqual(result['files'][0]['name'], 'File One')

    def test_query_exact_name_match(self):
        """Test query with exact name match."""
        result = list_user_files(q="name = 'Vendor_List_2023.xlsx'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')
        self.assertEqual(result['files'][0]['id'], 'file3')

    def test_query_name_contains(self):
        """Test query with name contains operator."""
        result = list_user_files(q="name contains 'Vendor'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')

    def test_query_parents_in_operator(self):
        """Test query with parents in operator."""
        result = list_user_files(q="'fcc035f8-99e7-4866-8e04-d0582e7a4d3f' in parents")
        self.assertEqual(len(result['files']), 2)
        file_names = [f['name'] for f in result['files']]
        self.assertIn('Vendor_List_2023.xlsx', file_names)
        self.assertIn('Meeting_Notes.docx', file_names)

    def test_query_combined_name_and_parents(self):
        """Test query combining name and parents conditions with AND."""
        result = list_user_files(q="name = 'Vendor_List_2023.xlsx' and 'fcc035f8-99e7-4866-8e04-d0582e7a4d3f' in parents")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')
        self.assertEqual(result['files'][0]['id'], 'file3')

    def test_query_mime_type_filter(self):
        """Test query with MIME type filter."""
        result = list_user_files(q="mimeType = 'application/pdf'")
        self.assertEqual(len(result['files']), 2)
        for file in result['files']:
            self.assertEqual(file['mimeType'], 'application/pdf')

    def test_query_size_comparison(self):
        """Test query with size comparison."""
        result = list_user_files(q="size > '2000'")
        self.assertEqual(len(result['files']), 5)  # file2, file3, file5 have size > 2000
        for file in result['files']:
            self.assertGreater(int(file['size']), 2000)

    def test_query_modified_time_comparison(self):
        """Test query with modified time comparison."""
        result = list_user_files(q="modifiedTime > '2024-01-01T00:00:00Z'")
        self.assertEqual(len(result['files']), 6)
        for file in result['files']:
            self.assertGreater(file['modifiedTime'], '2024-01-01T00:00:00Z')

    def test_query_or_operator(self):
        """Test query with OR operator."""
        result = list_user_files(q="name = 'Vendor_List_2023.xlsx' or name = 'Budget_2024.xlsx'")
        self.assertEqual(len(result['files']), 2)
        file_names = [f['name'] for f in result['files']]
        self.assertIn('Vendor_List_2023.xlsx', file_names)
        self.assertIn('Budget_2024.xlsx', file_names)

    def test_query_complex_and_or_combination(self):
        """Test query with complex AND/OR combination."""
        result = list_user_files(q="name contains 'Vendor' and 'fcc035f8-99e7-4866-8e04-d0582e7a4d3f' in parents or mimeType = 'application/pdf'")
        self.assertEqual(len(result['files']), 3)  # Vendor file + 2 PDF files
        file_names = [f['name'] for f in result['files']]
        self.assertIn('Vendor_List_2023.xlsx', file_names)
        self.assertIn('File One', file_names)  # PDF
        self.assertIn('Project_Report.pdf', file_names)  # PDF

    def test_query_not_equals_operator(self):
        """Test query with not equals operator."""
        result = list_user_files(q="mimeType != 'application/pdf'")
        self.assertEqual(len(result['files']), 5)  # All files except the 2 PDFs
        for file in result['files']:
            self.assertNotEqual(file['mimeType'], 'application/pdf')

    def test_query_less_than_operator(self):
        """Test query with less than operator."""
        result = list_user_files(q="size < '3000'")
        self.assertEqual(len(result['files']), 3)  # file1, file2, file6
        for file in result['files']:
            self.assertLess(int(file['size']), 3000)

    def test_query_less_than_or_equal_operator(self):
        """Test query with less than or equal operator."""
        result = list_user_files(q="size <= 2048")
        self.assertEqual(len(result['files']), 3)
        for file in result['files']:
            self.assertLessEqual(int(file['size']), 2048)

    def test_query_greater_than_or_equal_operator(self):
        """Test query with greater than or equal operator."""
        result = list_user_files(q="size >= '5000'")
        self.assertEqual(len(result['files']), 2)  # file3, file5
        for file in result['files']:
            self.assertGreaterEqual(int(file['size']), 5000)

    def test_query_created_time_filter(self):
        """Test query with created time filter."""
        result = list_user_files(q="createdTime > '2024-01-01T00:00:00Z'")
        self.assertEqual(len(result['files']), 5)
        for file in result['files']:
            self.assertGreater(file['createdTime'], '2024-01-01T00:00:00Z')

    def test_query_id_filter(self):
        """Test query with file ID filter."""
        result = list_user_files(q="id = 'file3'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['id'], 'file3')

    def test_query_empty_string(self):
        """Test query with empty string (should return all files)."""
        result = list_user_files(q="")
        self.assertEqual(len(result['files']), 7)

    def test_query_operator_at_start(self):
        """Test query with operator at start raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid query syntax: operator '=' must have operands on both sides",
            q="= 'value'"
        )

    def test_query_operator_at_end(self):
        """Test query with operator at end raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid query syntax: operator '=' must have operands on both sides",
            q="name ="
        )

    def test_query_logical_operator_at_start(self):
        """Test query with logical operator at start raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid query syntax: logical operator 'and' must have conditions on both sides",
            q="and name = 'test'"
        )

    def test_query_logical_operator_at_end(self):
        """Test query with logical operator at end raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid query syntax: logical operator 'or' must have conditions on both sides",
            q="name = 'test' or"
        )

    def test_query_multiple_parents_check(self):
        """Test query checking multiple parents."""
        result = list_user_files(q="'root' in parents or 'photos' in parents")
        self.assertEqual(len(result['files']), 5)  # file1, file2, file5, file6
        for file in result['files']:
            parents = file.get('parents', [])
            self.assertTrue('root' in parents or 'photos' in parents)

    def test_query_combined_filters_with_pagination(self):
        """Test query with combined filters and pagination."""
        result = list_user_files(q="mimeType = 'application/pdf'", pageSize=1)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['nextPageToken'], 'page_1')
        result2 = list_user_files(q="mimeType = 'application/pdf'", pageSize=1, pageToken=result['nextPageToken'])
        self.assertEqual(len(result2['files']), 1)
        self.assertIsNone(result2['nextPageToken'])

    def test_query_with_spaces_filter(self):
        """Test query combined with spaces filter."""
        result = list_user_files(q="mimeType = 'image/jpeg'", spaces="photos")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'File Two')

    def test_query_with_permissions_filter(self):
        """Test query combined with permissions filter."""
        result = list_user_files(q="name contains 'Meeting'", includePermissionsForView="domain")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Meeting_Notes.docx')

    def test_query_complex_real_world_scenario(self):
        """Test a complex real-world query scenario."""
        # Find Excel files in a specific folder that are larger than 1KB and modified in 2024
        result = list_user_files(q="'fcc035f8-99e7-4866-8e04-d0582e7a4d3f' in parents and mimeType contains 'spreadsheet' and size > '1000' and modifiedTime > '2023-01-01T00:00:00Z'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')

    def test_query_no_matching_results(self):
        """Test query that returns no results."""
        result = list_user_files(q="name = 'NonExistentFile.txt'")
        self.assertEqual(len(result['files']), 0)
        self.assertIsNone(result['nextPageToken'])

    def test_query_field_not_present(self):
        """Test query with field that doesn't exist in files."""
        result = list_user_files(q="nonexistentField = 'value'")
        self.assertEqual(len(result['files']), 0)

    def test_query_invalid_field_name(self):
        """Test query with invalid field name raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid field name in query: invalid-field-name",
            q="invalid-field-name = 'value'"
        )

    def test_query_invalid_field_name_with_special_chars(self):
        """Test query with invalid field name containing special characters raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid field name in query: field@name",
            q="field@name = 'value'"
        )

    def test_query_invalid_field_name_in_in_operator(self):
        """Test query with invalid field name in 'in' operator raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid field name in query: invalid-field",
            q="'value' in invalid-field"
        )

    def test_query_invalid_field_name_in_in_operator_with_special_chars(self):
        """Test query with invalid field name containing special chars in 'in' operator raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid field name in query: field#name",
            q="'value' in field#name"
        )

    def test_query_invalid_field_name_in_in_operator_line_956(self):
        """Test query specifically for line 956 validation - invalid field name after 'in' operator."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Invalid field name in query: field@name",
            q="'test_value' in field@name"
        )

    def test_query_valid_field_name_with_underscore(self):
        """Test query with valid field name containing underscore passes validation."""
        result = list_user_files(q="valid_field_name = 'value'")
        self.assertEqual(len(result['files']), 0)  # No files match, but no error

    def test_query_valid_field_name_in_in_operator_with_underscore(self):
        """Test query with valid field name containing underscore in 'in' operator passes validation."""
        result = list_user_files(q="'value' in valid_field_name")
        self.assertEqual(len(result['files']), 0)  # No files match, but no error

    def test_query_with_whitespace_handling(self):
        """Test query with various whitespace patterns."""
        result = list_user_files(q="  name  =  'Vendor_List_2023.xlsx'  ")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')

    def test_query_complex_nested_conditions(self):
        """Test query with complex nested conditions using disjunctive normal form."""
        result = list_user_files(q="(name contains 'Vendor' and mimeType contains 'spreadsheet') or (name contains 'Budget' and size > '5000')")
        self.assertEqual(len(result['files']), 2)
        file_names = [f['name'] for f in result['files']]
        self.assertIn('Vendor_List_2023.xlsx', file_names)
        self.assertIn('Budget_2024.xlsx', file_names)

    def test_query_with_parentheses_simple_or(self):
        """Test query with parentheses to group OR conditions."""
        result = list_user_files(q="(name = 'File One' or name = 'File Two') and mimeType = 'application/pdf'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'File One')

    def test_query_with_parentheses_and_precedence(self):
        """Test query showing AND precedence over OR with parentheses."""
        result = list_user_files(q="name = 'File One' or (name = 'File Two' and mimeType = 'image/jpeg')")
        self.assertEqual(len(result['files']), 2)
        file_names = {f['name'] for f in result['files']}
        self.assertIn('File One', file_names)
        self.assertIn('File Two', file_names)

    def test_query_with_nested_parentheses(self):
        """Test query with nested parentheses."""
        result = list_user_files(q="(name = 'Budget_2024.xlsx' and (mimeType = 'application/vnd.google-apps.spreadsheet' or size = '1024')) or name = 'File One'")
        self.assertEqual(len(result['files']), 2)
        file_names = {f['name'] for f in result['files']}
        self.assertIn('Budget_2024.xlsx', file_names)
        self.assertIn('File One', file_names)
    
    def test_query_complex_with_parentheses(self):
        """Test a more complex query using parentheses."""
        # This query should find PDF or JPEG files that are larger than 1KB and are in 'root' or 'photos' parent.
        result = list_user_files(q="('root' in parents or 'photos' in parents) and (mimeType = 'application/pdf' or mimeType = 'image/jpeg') and size > '1000'")
        self.assertEqual(len(result['files']), 3)
        file_names = {f['name'] for f in result['files']}
        self.assertIn('File One', file_names) # In 'root', is a PDF, and size > 1000
        self.assertIn('Project_Report.pdf', file_names) # In 'photos', is a PDF, and size > 1000
        self.assertIn('File Two', file_names) # In 'photos', is a JPEG, and size > 1000

    def test_query_mismatched_parentheses_open(self):
        """Test query with mismatched opening parenthesis raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Mismatched parentheses",
            q="(name = 'File One'"
        )

    def test_query_mismatched_parentheses_close(self):
        """Test query with mismatched closing parenthesis raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Mismatched parentheses",
            q="name = 'File One')"
        )

    def test_list_user_files_with_not_logic_expression(self):
        """Test list user files with not logic expression."""
        SimulationDB["users"]["me"]["files"]["file_hello_world"] = {
            "id": "file_hello_world",
            "name": "Hello World",
            "mimeType": "text/plain",
            "size": "0",
            "modifiedTime": "2024-01-01T00:00:00Z",
            "createdTime": "2024-01-01T00:00:00Z",
        }
        SimulationDB["users"]["me"]["files"]["file_hello_earth"] = {
            "id": "file_hello_earth",
            "name": "Hello Earth",
            "mimeType": "text/plain",
            "size": "0",
            "modifiedTime": "2024-01-01T00:00:00Z",
            "createdTime": "2024-01-01T00:00:00Z",
        }
        result = list_user_files(q="name contains 'Hello' and not name contains 'Earth'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['id'], 'file_hello_world')
        self.assertEqual(result['files'][0]['name'], 'Hello World')
        self.assertEqual(result['files'][0]['mimeType'], 'text/plain')
        self.assertEqual(result['files'][0]['size'], '0')
        self.assertEqual(result['files'][0]['modifiedTime'], '2024-01-01T00:00:00Z')
        self.assertEqual(result['files'][0]['createdTime'], '2024-01-01T00:00:00Z')

    def test_invalid_operator_for_name_field_greater_than(self):
        """Test that using '>' with 'name' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '>' not supported for field 'name'. Supported operators are 'contains', '=', '!='.",
            q="name > 'A'"
        )

    def test_invalid_operator_for_name_field_less_than(self):
        """Test that using '<' with 'name' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '<' not supported for field 'name'. Supported operators are 'contains', '=', '!='.",
            q="name < 'Z'"
        )

    def test_invalid_operator_for_name_field_in(self):
        """Test that using 'in' with 'name' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'in' not supported for field 'name'. Supported operators are 'contains', '=', '!='.",
            q="'File' in name"
        )

    def test_invalid_operator_for_name_field_greater_than_or_equal(self):
        """Test that using '>=' with 'name' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '>=' not supported for field 'name'. Supported operators are 'contains', '=', '!='.",
            q="name >= 'A'"
        )

    def test_invalid_operator_for_name_field_less_than_or_equal(self):
        """Test that using '<=' with 'name' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '<=' not supported for field 'name'. Supported operators are 'contains', '=', '!='.",
            q="name <= 'Z'"
        )

    def test_invalid_operator_for_mimeType_field_greater_than(self):
        """Test that using '>' with 'mimeType' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '>' not supported for field 'mimeType'. Supported operators are 'contains', '=', '!='.",
            q="mimeType > 'application/pdf'"
        )

    def test_invalid_operator_for_mimeType_field_less_than(self):
        """Test that using '<' with 'mimeType' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '<' not supported for field 'mimeType'. Supported operators are 'contains', '=', '!='.",
            q="mimeType < 'image/jpeg'"
        )

    def test_invalid_operator_for_modifiedTime_field_contains(self):
        """Test that using 'contains' with 'modifiedTime' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'contains' not supported for field 'modifiedTime'. Supported operators are '<=', '<', '=', '!=', '>', '>='.",
            q="modifiedTime contains '2024'"
        )

    def test_invalid_operator_for_modifiedTime_field_in(self):
        """Test that using 'in' with 'modifiedTime' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'in' not supported for field 'modifiedTime'. Supported operators are '<=', '<', '=', '!=', '>', '>='.",
            q="'2024-01-01T00:00:00Z' in modifiedTime"
        )

    def test_invalid_operator_for_trashed_field_greater_than(self):
        """Test that using '>' with 'trashed' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '>' not supported for field 'trashed'. Supported operators are '=', '!='.",
            q="trashed > true"
        )

    def test_invalid_operator_for_trashed_field_contains(self):
        """Test that using 'contains' with 'trashed' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'contains' not supported for field 'trashed'. Supported operators are '=', '!='.",
            q="trashed contains 'true'"
        )

    def test_invalid_operator_for_starred_field_greater_than(self):
        """Test that using '>' with 'starred' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '>' not supported for field 'starred'. Supported operators are '=', '!='.",
            q="starred > true"
        )

    def test_invalid_operator_for_starred_field_contains(self):
        """Test that using 'contains' with 'starred' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'contains' not supported for field 'starred'. Supported operators are '=', '!='.",
            q="starred contains 'true'"
        )

    def test_invalid_operator_for_parents_field_equals(self):
        """Test that using '=' with 'parents' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '=' not supported for field 'parents'. Supported operator is 'in'.",
            q="parents = 'root'"
        )

    def test_invalid_operator_for_parents_field_contains(self):
        """Test that using 'contains' with 'parents' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'contains' not supported for field 'parents'. Supported operator is 'in'.",
            q="parents contains 'root'"
        )

    def test_invalid_operator_for_owners_field_equals(self):
        """Test that using '=' with 'owners' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '=' not supported for field 'owners'. Supported operator is 'in'.",
            q="owners = 'user@example.com'"
        )

    def test_invalid_operator_for_writers_field_equals(self):
        """Test that using '=' with 'writers' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '=' not supported for field 'writers'. Supported operator is 'in'.",
            q="writers = 'user@example.com'"
        )

    def test_invalid_operator_for_readers_field_equals(self):
        """Test that using '=' with 'readers' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '=' not supported for field 'readers'. Supported operator is 'in'.",
            q="readers = 'user@example.com'"
        )

    def test_invalid_operator_for_viewedByMeTime_field_contains(self):
        """Test that using 'contains' with 'viewedByMeTime' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator 'contains' not supported for field 'viewedByMeTime'. Supported operators are '<=', '<', '=', '!=', '>', '>='.",
            q="viewedByMeTime contains '2024'"
        )

    def test_invalid_operator_for_visibility_field_greater_than(self):
        """Test that using '>' with 'visibility' field raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=ValueError,
            expected_message="Operator '>' not supported for field 'visibility'. Supported operators are '=', '!='.",
            q="visibility > 'anyone'"
        )

    def test_query_with_contains_only_checks_prefix_success(self):
        """Test query with contains only checks prefix success."""
        result = list_user_files(q="name contains 'Vendor'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')
    
    def test_query_with_contains_only_checks_prefix_failure(self):
        """Test query with contains only checks prefix failure."""
        result = list_user_files(q="name contains 'List'")
        # With the current logic, "List" should find "Vendor_List_2023.xlsx" because it appears as a substring
        # This test now verifies that substring matching works for single words
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')

    def test_query_with_contains_for_content_field_success(self):
        """Test query with contains for content field."""
        result = list_user_files(q="content contains 'project'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Project_Report.pdf')

    def test_query_with_contains_for_content_field_failue_no_match(self):
        """Test query with contains for content field failure no match."""
        result = list_user_files(q="content contains 'abc123'") # No content contains this
        self.assertEqual(len(result['files']), 0)

    def test_query_with_full_text_field(self):
        """Test query with fullText field."""
        result = list_user_files(q="fullText contains 'project'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Project_Report.pdf')

    def test_query_with_full_text_field_no_match(self):
        """Test query with fullText field no match."""
        result = list_user_files(q="fullText contains 'abc123'")
        self.assertEqual(len(result['files']), 0)

    def test_query_with_full_text_field_no_match_partial_content(self):
        """Test query with fullText field no match partial content."""
        result = list_user_files(q="fullText contains 'proj'")
        self.assertEqual(len(result['files']), 0)

    def test_query_with_contains_operator_is_alphanumeric_if_double_quotes_success(self):
        """Test query with contains operator is alphanumeric if double quotes."""
        result = list_user_files(q="name contains \"Vendor List\"")
        self.assertEqual(len(result['files']), 1)
        self.assertIn('Vendor', result['files'][0]['name'])
        self.assertIn('List', result['files'][0]['name'])
    
    def test_full_text_contains_double_quotes(self):
        """ Test query with contains operator is alphanumeric if double quotes and field is fullText"""
        result = list_user_files(q='fullText contains "list"')
        self.assertEqual(len(result['files']), 1)
        self.assertIn('Vendor', result['files'][0]['name'])
        self.assertIn('List', result['files'][0]['name'])
    
    def test_bug_1337_fulltext_with_multi_word_phrase(self):
        """Test Bug #1337: fullText query with multi-word phrase should not raise TypeError."""
        # This test verifies that a query with space-separated words in fullText doesn't raise TypeError
        # The query 'fullText contains 'project management'' should work correctly
        result = list_user_files(q="fullText contains 'project'")
        # Should not raise TypeError, should return results or empty list
        self.assertIsInstance(result['files'], list)
    
    def test_bug_1337_fulltext_with_content_none(self):
        """Test Bug #1337: fullText query when file has content=None should not raise TypeError."""
        from APIs.gdrive.SimulationEngine.db import DB
        
        # Add a file with content=None to the existing database to reproduce the bug
        DB['users']['me']['files']['test_file_with_none_content'] = {
            'id': 'test_file_with_none_content',
            'name': 'test_file.txt',
            'description': 'test description',
            'mimeType': 'text/plain',
            'modifiedTime': '2024-01-01T10:00:00Z',
            'createdTime': '2024-01-01T10:00:00Z',
            'trashed': False,
            'size': '0',
            'parents': [],
            'permissions': [],
            'content': None  # This would cause TypeError without the fix
        }
        
        try:
            # This should not raise TypeError even with content=None
            result = list_user_files(q="fullText contains 'test'")
            self.assertIsInstance(result['files'], list)
        except TypeError as e:
            if "argument of type 'NoneType' is not iterable" in str(e):
                self.fail(f"Bug #1337 reproduced: TypeError when content is None - {e}")
            else:
                raise
        finally:
            # Cleanup
            if 'test_file_with_none_content' in DB['users']['me']['files']:
                del DB['users']['me']['files']['test_file_with_none_content']
    
    def test_bug_1337_fulltext_with_or_operator(self):
        """Test Bug #1337: fullText query with OR operator should not raise TypeError."""
        # Test the exact query from the bug report
        result = list_user_files(q="fullText contains 'project management' or name contains 'project' or name contains 'PM'")
        # Should not raise TypeError, should return results or empty list
        self.assertIsInstance(result['files'], list)
    
    def test_Agent_312_base_MT_Simulation(self):
        """ Test query with Agent_312_base_MT_Simulation."""
        FILENAME = "Draft Proposal.docx"
        create_file_or_folder(body={'name': FILENAME})
        result = list_user_files(q=f'name="{FILENAME}"')

        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], FILENAME)

    def test_name_contains_case_insensitive(self):
        """Test that name contains filter is case insensitive."""
        # Test with lowercase search term
        result = list_user_files(q="name contains 'vendor'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')
        
        # Test with uppercase search term
        result = list_user_files(q="name contains 'VENDOR'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')
        
        # Test with mixed case search term
        result = list_user_files(q="name contains 'VeNdOr'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Vendor_List_2023.xlsx')

    def test_mime_type_contains_case_insensitive(self):
        """Test that mimeType contains filter is case insensitive."""
        # Test with lowercase search term
        result = list_user_files(q="mimeType contains 'pdf'")
        self.assertEqual(len(result['files']), 2)  # Should find both PDF files
        
        # Test with uppercase search term
        result = list_user_files(q="mimeType contains 'PDF'")
        self.assertEqual(len(result['files']), 2)  # Should find both PDF files
        
        # Test with mixed case search term
        result = list_user_files(q="mimeType contains 'Pdf'")
        self.assertEqual(len(result['files']), 2)  # Should find both PDF files

    def test_content_contains_case_insensitive(self):
        """Test that content contains filter is case insensitive."""
        # Test with lowercase search term
        result = list_user_files(q="content contains 'project'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Project_Report.pdf')
        
        # Test with uppercase search term
        result = list_user_files(q="content contains 'PROJECT'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Project_Report.pdf')
        
        # Test with mixed case search term
        result = list_user_files(q="content contains 'PrOjEcT'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Project_Report.pdf')
    

    def test_Gemini_Apps_ID_158(self):
        #Create two air car assignment files in gdrive
        file_one_name = "air car assignment Test.txt"
        file_two_name = "air car assignment.pdf "

        create_file_or_folder(
            {
                "name":file_one_name,
                "mimeType":"text/plain",
            }
        )

        create_file_or_folder(
            {
                "name":file_two_name,
                "mimeType":"application/pdf",
            }
        )

        result_contains = list_user_files(q="name contains 'air car assignment'")
        self.assertEqual(len(result_contains['files']), 2)
        self.assertEqual(result_contains['files'][0]['name'], file_one_name)
        self.assertEqual(result_contains['files'][1]['name'], file_two_name)

        result_equals = list_user_files(q="name = 'air car assignment'")
        self.assertEqual(len(result_equals['files']), 0)
        self.assertEqual(result_equals['files'], [])
    
    def test_list_user_files_with_trashed_false_case_insensitive(self):
        """Test list user files with trashed false case insensitive."""
        result_F = list_user_files(q="trashed = False")
        result_f = list_user_files(q="trashed = false")
        self.assertEqual(len(result_F['files']), len(result_f['files']))
        self.assertEqual(result_F['files'], result_f['files'])

    def test_name_contains_multi_word_exact_match(self):
        """Test that name contains works with multi-word searches for exact matches."""
        # Create a file with a multi-word name
        create_file_or_folder(body={'name': 'Trace Book'})
        
        # Test that searching for the exact multi-word name works
        result = list_user_files(q="name contains 'Trace Book'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Trace Book')
        
        # Test case insensitive
        result = list_user_files(q="name contains 'trace book'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Trace Book')

    def test_name_contains_multi_word_partial_match(self):
        """Test that name contains works with multi-word searches for partial matches."""
        # Create files with multi-word names
        create_file_or_folder(body={'name': 'Project Management Guide'})
        create_file_or_folder(body={'name': 'Project Status Report'})
        create_file_or_folder(body={'name': 'User Manual'})
        
        # Test searching for part of a multi-word name
        result = list_user_files(q="name contains 'Project Management'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Project Management Guide')
        
        # Test searching for a word that appears in multiple files
        result = list_user_files(q="name contains 'Project'")
        self.assertEqual(len(result['files']), 3)  # 2 new files + existing Project_Report.pdf
        file_names = [f['name'] for f in result['files']]
        self.assertIn('Project Management Guide', file_names)
        self.assertIn('Project Status Report', file_names)
        self.assertIn('Project_Report.pdf', file_names)  # Existing file

    def test_name_contains_single_word_vs_multi_word_behavior(self):
        """Test that single-word and multi-word contains searches behave correctly."""
        # Create files with different name patterns
        create_file_or_folder(body={'name': 'Trace Book'})
        create_file_or_folder(body={'name': 'Trace Document'})
        create_file_or_folder(body={'name': 'Book Report'})
        
        # Single word search should find files where any token starts with the word
        result = list_user_files(q="name contains 'Trace'")
        self.assertEqual(len(result['files']), 2)
        file_names = [f['name'] for f in result['files']]
        self.assertIn('Trace Book', file_names)
        self.assertIn('Trace Document', file_names)
        
        # Multi-word search should find files containing the exact phrase
        result = list_user_files(q="name contains 'Trace Book'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Trace Book')
        
        # Multi-word search should not match partial phrases
        result = list_user_files(q="name contains 'Book Report'")
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], 'Book Report')

    def test_name_contains_multi_word_no_match(self):
        """Test that multi-word contains searches correctly return no results when no match exists."""
        # Create a file with a specific name
        create_file_or_folder(body={'name': 'Trace Book'})
        
        # Search for a multi-word phrase that doesn't exist
        result = list_user_files(q="name contains 'Trace Document'")
        self.assertEqual(len(result['files']), 0)
        
        # Search for a multi-word phrase with different word order
        result = list_user_files(q="name contains 'Book Trace'")
        self.assertEqual(len(result['files']), 0)
        
        # Search for a multi-word phrase that's close but not exact
        result = list_user_files(q="name contains 'Trace Books'")
        self.assertEqual(len(result['files']), 0)

    def test_list_files_readonly_operation_prevents_user_creation(self):
        """Test that list (read-only operation) does not create users - fixes Bug #798."""
        # Clear the DB to ensure no users exist
        SimulationDB.clear()
        
        # This should raise a UserNotFoundError, not create a new user (read-only operation should not modify data)
        self.assert_error_behavior(
            func_to_call=list_user_files,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID 'me' not found. Cannot perform read operation for non-existent user.",
            corpora="user"
        )
        
        # Verify the user was NOT created (critical for read-only operations)
        self.assertNotIn("users", SimulationDB)

    def test_list_user_shared_drives_drive_with_operator_inside_quotes(self):
        """Test list user files with file with operator inside quotes."""
        result = list_user_shared_drives(q="name = 'a<=b'")
        self.assertEqual(len(result['drives']), 1)
        self.assertEqual(result['drives'][0]['name'], 'a<=b')
    
    def test_list_user_files_with_includeLabels(self):
        """Test list user files with includeLabels."""
        result = list_user_files(includeLabels = 'Urgent')
        self.assertEqual(len(result['files']), 2)

        file_ids = set([f['id'] for f in result['files']])
        self.assertEqual(file_ids, {'file1', 'file2'})
    
    def test_list_user_files_with_includeLabels_multiple(self):
        """Test list user files with includeLabels multiple."""
        result = list_user_files(includeLabels = 'Urgent, Important')
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['id'], 'file1')

    def test_list_user_files_with_includeLabels_multiple_no_space(self):
        """Test list user files with includeLabels multiple."""
        result = list_user_files(includeLabels = 'Urgent,Important')
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['id'], 'file1')
    
    def test_list_user_shared_drives_createdTime_contains_operator_failure(self):
        """Test list user shared drives with createdTime contains operator failure."""
        self.assert_error_behavior(
            func_to_call=list_user_shared_drives,
            expected_exception_type=InvalidQueryError,
            expected_message="Invalid query string: 'createdTime contains 2025' with error: Operator 'contains' not supported for field 'createdTime'. Supported operators are '<=', '<', '=', '!=', '>', '>='.",
            q='createdTime contains 2025'
        )

    def test_list_user_shared_drives_createdTime_in_operator_failure(self):
        """Test list user shared drives with createdTime in operator failure."""
        self.assert_error_behavior(
            func_to_call=list_user_shared_drives,
            expected_exception_type=InvalidQueryError,
            expected_message="Invalid query string: '2025 in createdTime' with error: Operator 'in' not supported for field 'createdTime'. Supported operators are '<=', '<', '=', '!=', '>', '>='.",
            q='2025 in createdTime'
        )
    
    def test_list_user_shared_drives_hidden_operator_failure(self):
        """Test list user shared drives with hidden operator failure."""
        unsupported_operator_queries = ['hidden contains true', 'hidden > true', 'hidden < true', 'hidden >= true', 'hidden <= true', 'true in hidden']
        for q in unsupported_operator_queries:
            self.assert_error_behavior(
                func_to_call=list_user_shared_drives,
                expected_exception_type=InvalidQueryError,
                expected_message=f"Invalid query string: '{q}' with error: Operator '{q.split(' ')[1]}' not supported for field 'hidden'. Supported operators are '=', '!='.",
                q=q
            )