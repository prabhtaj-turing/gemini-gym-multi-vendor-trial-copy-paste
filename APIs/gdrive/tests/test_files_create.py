import unittest
import os
import tempfile
import base64
import json
from datetime import datetime, UTC
from common_utils.base_case import BaseTestCaseWithErrorHandler
from gdrive.SimulationEngine.db import DB, save_state, load_state
from pydantic import ValidationError
from gdrive.SimulationEngine.custom_errors import QuotaExceededError, UserNotFoundError
from common_utils.datetime_utils import InvalidDateTimeFormatError
from .. import (create_file_or_folder, get_file_metadata_or_content)

class TestFilesCreate(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset DB to a clean state with proper quota settings."""
        # Clear and initialize DB with proper structure
        DB.clear()
        DB.update({
            'users': {
                'me': {
                    'about': {
                        'kind': 'drive#about',
                        'storageQuota': {
                            'limit': str(1024 * 1024 * 1024),  # 1GB
                            'usageInDrive': '0',
                            'usageInDriveTrash': '0',
                            'usage': '0'
                        },
                        'driveThemes': False,
                        'canCreateDrives': False,
                        'importFormats': {},
                        'exportFormats': {},
                        'appInstalled': False,
                        'user': {
                            'displayName': 'Test User',
                            'kind': 'drive#user',
                            'me': True,
                            'permissionId': 'perm_1',
                            'emailAddress': 'test@example.com'
                        },
                        'folderColorPalette': "",
                        'maxImportSizes': {},
                        'maxUploadSize': str(50 * 1024 * 1024)  # 50MB
                    },
                    'files': {},
                    'drives': {},
                    'comments': {},
                    'replies': {},
                    'labels': {},
                    'accessproposals': {},
                    'counters': {
                        'file': 0,
                        'drive': 0,
                        'comment': 0,
                        'reply': 0,
                        'label': 0,
                        'accessproposal': 0,
                        'revision': 0
                    }
                }
            }
        })

    def test_create_metadata_only(self):
        """Test creating a file with metadata only (no content upload)."""
        body = {
            'name': 'test_file.txt',
            'mimeType': 'text/plain',
            'size': '0',
            'parents': [],
        }
        
        # Verify there are no files in the DB
        self.assertEqual(len(DB['users']['me']['files']), 0)
        
        # Create file
        result = create_file_or_folder(body=body)
        
        # Verify returned result
        self.assertEqual(result['name'], 'test_file.txt')
        self.assertEqual(result['mimeType'], 'text/plain')
        self.assertEqual(result['size'], '0')

        self.assertIsNone(result.get('content'))
        self.assertNotIn('revisions', result)

        # Verify file exists in DB using get()
        file_id = result['id']
        file_from_db = get_file_metadata_or_content(file_id)
        self.assertEqual(file_from_db['name'], 'test_file.txt')
        self.assertEqual(file_from_db['mimeType'], 'text/plain')
        self.assertEqual(file_from_db['size'], '0')
        self.assertIsNone(file_from_db.get('content'))
        self.assertNotIn('revisions', file_from_db)

    def test_create_with_content_upload(self):
        """Test creating a file with content upload and verify DB storage."""
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write('hello world')
            tmp.flush()
            file_path = tmp.name
            
        try:
            body = {
                'name': 'file_with_content.txt',
                'mimeType': 'text/plain',
                'parents': []
            }
            media_body = {'filePath': file_path}
            
            # Create file with content
            result = create_file_or_folder(body=body, media_body=media_body)
            
            # Verify returned result
            self.assertEqual(result['name'], 'file_with_content.txt')
            self.assertEqual(result['mimeType'], 'text/plain')
            self.assertIn('content', result)
            self.assertIn('revisions', result)
            self.assertEqual(len(result['revisions']), 1)
            
            # Verify main content structure - should have all 5 fields
            content = result['content']
            self.assertIn('data', content)
            self.assertIn('encoding', content)
            self.assertIn('checksum', content)
            self.assertIn('version', content)
            self.assertIn('lastContentUpdate', content)
            self.assertEqual(content['encoding'], 'base64')
            self.assertEqual(content['version'], '1.0')
            
            # Verify content data is valid base64
            self.assertIsInstance(content['data'], str)
            self.assertTrue(len(content['data']) > 0)
            
            # Verify checksum format
            self.assertTrue(content['checksum'].startswith('sha256:'))
            self.assertEqual(len(content['checksum']), 71)  # sha256: + 64 hex chars
            
            # Verify timestamp format
            self.assertIsInstance(content['lastContentUpdate'], str)
            self.assertTrue(content['lastContentUpdate'].endswith('Z'))
            
            # Verify revision structure
            revision = result['revisions'][0]
            self.assertEqual(revision['id'], 'rev-1')
            self.assertEqual(revision['mimeType'], 'text/plain')
            self.assertEqual(revision['originalFilename'], 'file_with_content.txt')
            self.assertIn('content', revision)
            self.assertIn('modifiedTime', revision)
            self.assertIn('keepForever', revision)
            self.assertIn('size', revision)
            
            # Verify revision content - should have only 3 fields (no version/lastContentUpdate)
            rev_content = revision['content']
            self.assertIn('data', rev_content)
            self.assertIn('encoding', rev_content)
            self.assertIn('checksum', rev_content)
            self.assertNotIn('version', rev_content)
            self.assertNotIn('lastContentUpdate', rev_content)
            
            # Verify revision content data matches main content
            self.assertEqual(rev_content['data'], content['data'])
            self.assertEqual(rev_content['encoding'], content['encoding'])
            self.assertEqual(rev_content['checksum'], content['checksum'])
            
            # Verify file exists in DB using get()
            file_id = result['id']
            file_from_db = get_file_metadata_or_content(file_id)
            self.assertEqual(file_from_db['name'], 'file_with_content.txt')
            self.assertIn('content', file_from_db)
            self.assertIn('revisions', file_from_db)
            self.assertEqual(len(file_from_db['revisions']), 1)
            
            # Verify content in DB matches exactly
            db_content = file_from_db['content']
            self.assertEqual(db_content['data'], content['data'])
            self.assertEqual(db_content['encoding'], content['encoding'])
            self.assertEqual(db_content['checksum'], content['checksum'])
            self.assertEqual(db_content['version'], content['version'])
            self.assertEqual(db_content['lastContentUpdate'], content['lastContentUpdate'])
            
            # Verify revision in DB matches exactly
            db_revision = file_from_db['revisions'][0]
            self.assertEqual(db_revision['id'], revision['id'])
            self.assertEqual(db_revision['mimeType'], revision['mimeType'])
            self.assertEqual(db_revision['originalFilename'], revision['originalFilename'])
            self.assertEqual(db_revision['size'], revision['size'])
            self.assertEqual(db_revision['keepForever'], revision['keepForever'])
            
            # Verify revision content in DB matches exactly
            db_rev_content = db_revision['content']
            self.assertEqual(db_rev_content['data'], rev_content['data'])
            self.assertEqual(db_rev_content['encoding'], rev_content['encoding'])
            self.assertEqual(db_rev_content['checksum'], rev_content['checksum'])
            self.assertNotIn('version', db_rev_content)
            self.assertNotIn('lastContentUpdate', db_rev_content)
            
        finally:
            # Clean up temporary file
            os.remove(file_path)

    def test_create_with_all_parameters(self):
        """Test creating a file with all parameters and content upload."""
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write('test content with params')
            tmp.flush()
            file_path = tmp.name
            
        try:
            body = {
                'name': 'full_params.txt',
                'mimeType': 'text/plain',
                'parents': ['parent1']
            }
            media_body = {'filePath': file_path}
            
            # Create file with all parameters
            result = create_file_or_folder(
                body=body,
                media_body=media_body,
                enforceSingleParent=True,
                ignoreDefaultVisibility=True,
                keepRevisionForever=True,
                ocrLanguage='en',
                supportsAllDrives=True,
                supportsTeamDrives=True,
                useContentAsIndexableText=True,
                includePermissionsForView='anyone',
                includeLabels='test,label'
            )
            
            # Verify returned result
            self.assertEqual(result['name'], 'full_params.txt')
            self.assertTrue(result['enforceSingleParent'])
            self.assertTrue(result['ignoreDefaultVisibility'])
            self.assertTrue(result['keepRevisionForever'])
            self.assertEqual(result['ocrLanguage'], 'en')
            self.assertTrue(result['supportsAllDrives'])
            self.assertTrue(result['supportsTeamDrives'])
            self.assertTrue(result['useContentAsIndexableText'])
            self.assertEqual(result['includePermissionsForView'], 'anyone')
            self.assertEqual(result['includeLabels'], 'test,label')
            self.assertIn('labels', result)
            self.assertEqual(result['labels'], ['test', 'label'])
            self.assertIn('content', result)
            self.assertIn('revisions', result)
            
            # Verify file exists in DB using get()
            file_id = result['id']
            file_from_db = get_file_metadata_or_content(file_id)
            self.assertEqual(file_from_db['name'], 'full_params.txt')
            self.assertTrue(file_from_db['enforceSingleParent'])
            self.assertTrue(file_from_db['keepRevisionForever'])
            self.assertEqual(file_from_db['ocrLanguage'], 'en')
            self.assertEqual(file_from_db['labels'], ['test', 'label'])
            self.assertIn('content', file_from_db)
            
        finally:
            # Clean up temporary file
            os.remove(file_path)

    def test_create_google_workspace_document(self):
        """Test creating a Google Workspace document (metadata only)."""
        body = {
            'name': 'test_document',
            'mimeType': 'application/vnd.google-apps.document',
            'parents': []
        }
        
        # Create Google Workspace document
        result = create_file_or_folder(body=body)
        
        # Verify returned result
        self.assertEqual(result['name'], 'test_document')
        self.assertEqual(result['mimeType'], 'application/vnd.google-apps.document')
        self.assertIn('content', result)  # Google Workspace docs have empty content array
        self.assertIn('tabs', result)
        self.assertEqual(result['suggestionsViewMode'], 'DEFAULT')
        self.assertFalse(result['includeTabsContent'])
        
        # Verify file exists in DB using get()
        file_id = result['id']
        file_from_db = get_file_metadata_or_content(file_id)
        self.assertEqual(file_from_db['name'], 'test_document')
        self.assertEqual(file_from_db['mimeType'], 'application/vnd.google-apps.document')
        self.assertIn('content', file_from_db)
        self.assertIn('tabs', file_from_db)

    def test_create_spreadsheet(self):
        """Test creating a Google Sheets document."""
        body = {
            'name': 'test_spreadsheet',
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': []
        }
        
        # Create spreadsheet
        result = create_file_or_folder(body=body)
        
        # Verify returned result
        self.assertEqual(result['name'], 'test_spreadsheet')
        self.assertEqual(result['mimeType'], 'application/vnd.google-apps.spreadsheet')
        self.assertIn('sheets', result)
        self.assertIn('data', result)
        self.assertEqual(len(result['sheets']), 1)
        self.assertEqual(result['sheets'][0]['properties']['title'], 'Sheet1')
        
        # Verify file exists in DB using get()
        file_id = result['id']
        file_from_db = get_file_metadata_or_content(file_id)
        self.assertEqual(file_from_db['name'], 'test_spreadsheet')
        self.assertIn('sheets', file_from_db)
        self.assertIn('data', file_from_db)

    def test_create_invalid_body_type(self):
        """Test error handling for invalid body type."""
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=TypeError,
            expected_message="Argument 'body' must be a dictionary or None, got str",
            body='not_a_dict'
        )

    def test_create_invalid_media_body_type(self):
        """Test error handling for invalid media_body type."""
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=TypeError,
            expected_message="Argument 'media_body' must be a dictionary or None, got str",
            media_body='not_a_dict'
        )

    def test_create_invalid_bool_param(self):
        """Test error handling for invalid boolean parameter."""
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=TypeError,
            expected_message="Argument 'enforceSingleParent' must be a boolean, got str",
            enforceSingleParent='not_bool'
        )

    def test_create_invalid_str_param(self):
        """Test error handling for invalid string parameter."""
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=TypeError,
            expected_message="Argument 'ocrLanguage' must be a string, got int",
            ocrLanguage=123
        )

    def test_create_invalid_body_schema(self):
        """Test error handling for invalid body schema."""
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for FileBodyModel",
            body={'name': 123, 'mimeType': 'text/plain'}
        )

    def test_create_invalid_media_body_schema(self):
        """Test error handling for invalid media_body schema."""
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for MediaBodyModel",
            media_body={'filePath': 123}
        )

    def test_create_quota_exceeded(self):
        """Test error handling when quota is exceeded."""
        # Set quota to 1 byte
        DB['users']['me']['about']['storageQuota']['limit'] = '1'
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write('abc')
            tmp.flush()
            file_path = tmp.name
            
        try:
            body = {'name': 'bigfile.txt', 'mimeType': 'text/plain'}
            media_body = {'filePath': file_path}
            
            self.assert_error_behavior(
                func_to_call=create_file_or_folder,
                expected_exception_type=QuotaExceededError,
                expected_message="Quota exceeded. Cannot create the file.",
                body=body,
                media_body=media_body
            )
        finally:
            os.remove(file_path)

    def test_create_file_not_found(self):
        """Test error handling when file path doesn't exist."""
        body = {'name': 'nofile.txt', 'mimeType': 'text/plain'}
        media_body = {'filePath': '/nonexistent/path.txt'}
        
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=FileNotFoundError,
            expected_message="File not found: /nonexistent/path.txt",
            body=body,
            media_body=media_body
        )

    def test_create_with_enforce_single_parent(self):
        """Test enforceSingleParent parameter behavior."""
        body = {
            'name': 'test_file.txt',
            'mimeType': 'text/plain',
            'parents': ['parent1', 'parent2', 'parent3']
        }
        
        # Test with enforceSingleParent=True
        result = create_file_or_folder(body=body, enforceSingleParent=True)
        self.assertTrue(result['enforceSingleParent'])
        self.assertEqual(result['parents'], ['parent3'])  # Should keep only the last parent
        
        # Verify in DB
        file_id = result['id']
        file_from_db = get_file_metadata_or_content(file_id)
        self.assertEqual(file_from_db['parents'], ['parent3'])

    def test_create_with_ignore_default_visibility(self):
        """Test ignoreDefaultVisibility parameter behavior."""
        body = {
            'name': 'test_file.txt',
            'mimeType': 'text/plain',
            'parents': []
        }
        
        # Test with ignoreDefaultVisibility=True
        result = create_file_or_folder(body=body, ignoreDefaultVisibility=True)
        self.assertTrue(result['ignoreDefaultVisibility'])
        
        # Should have owner permission added
        self.assertIn('permissions', result)
        owner_perms = [p for p in result['permissions'] if p['role'] == 'owner']
        self.assertEqual(len(owner_perms), 1)
        self.assertEqual(owner_perms[0]['emailAddress'], 'test@example.com')

    def test_content_structure_matches_db_schema(self):
        """Test that content structure exactly matches the GdriveDefaultDB.json schema."""
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write('test content for schema validation')
            tmp.flush()
            file_path = tmp.name
            
        try:
            body = {
                'name': 'schema_test.txt',
                'mimeType': 'text/plain',
                'parents': []
            }
            media_body = {'filePath': file_path}
            
            # Create file with content
            result = create_file_or_folder(body=body, media_body=media_body)
            
            # Verify main content structure matches GdriveDefaultDB.json schema
            content = result['content']
            expected_content_keys = {'data', 'encoding', 'checksum', 'version', 'lastContentUpdate'}
            actual_content_keys = set(content.keys())
            self.assertEqual(actual_content_keys, expected_content_keys, 
                           f"Main content keys mismatch. Expected: {expected_content_keys}, Got: {actual_content_keys}")
            
            # Verify each field has correct type and format
            self.assertIsInstance(content['data'], str)
            self.assertIsInstance(content['encoding'], str)
            self.assertIsInstance(content['checksum'], str)
            self.assertIsInstance(content['version'], str)
            self.assertIsInstance(content['lastContentUpdate'], str)
            
            # Verify specific format requirements
            self.assertEqual(content['encoding'], 'base64')
            self.assertEqual(content['version'], '1.0')
            self.assertTrue(content['checksum'].startswith('sha256:'))
            self.assertTrue(content['lastContentUpdate'].endswith('Z'))
            
            # Verify revision structure matches GdriveDefaultDB.json schema
            self.assertEqual(len(result['revisions']), 1)
            revision = result['revisions'][0]
            
            # Verify revision top-level keys
            expected_revision_keys = {'id', 'mimeType', 'modifiedTime', 'keepForever', 'originalFilename', 'size', 'content'}
            actual_revision_keys = set(revision.keys())
            self.assertEqual(actual_revision_keys, expected_revision_keys,
                           f"Revision keys mismatch. Expected: {expected_revision_keys}, Got: {actual_revision_keys}")
            
            # Verify revision content structure (should have only 3 fields)
            rev_content = revision['content']
            expected_rev_content_keys = {'data', 'encoding', 'checksum'}
            actual_rev_content_keys = set(rev_content.keys())
            self.assertEqual(actual_rev_content_keys, expected_rev_content_keys,
                           f"Revision content keys mismatch. Expected: {expected_rev_content_keys}, Got: {actual_rev_content_keys}")
            
            # Verify revision content data matches main content exactly
            self.assertEqual(rev_content['data'], content['data'])
            self.assertEqual(rev_content['encoding'], content['encoding'])
            self.assertEqual(rev_content['checksum'], content['checksum'])
            
            # Verify through get() that DB storage maintains exact structure
            file_id = result['id']
            file_from_db = get_file_metadata_or_content(file_id)
            
            # Verify main content in DB has exact same structure
            db_content = file_from_db['content']
            db_content_keys = set(db_content.keys())
            self.assertEqual(db_content_keys, expected_content_keys,
                           f"DB main content keys mismatch. Expected: {expected_content_keys}, Got: {db_content_keys}")
            
            # Verify revision content in DB has exact same structure
            db_revision = file_from_db['revisions'][0]
            db_rev_content = db_revision['content']
            db_rev_content_keys = set(db_rev_content.keys())
            self.assertEqual(db_rev_content_keys, expected_rev_content_keys,
                           f"DB revision content keys mismatch. Expected: {expected_rev_content_keys}, Got: {db_rev_content_keys}")
            
            # Verify all values are preserved exactly in DB
            for key in expected_content_keys:
                self.assertEqual(db_content[key], content[key], f"DB content field '{key}' mismatch")
            
            for key in expected_rev_content_keys:
                self.assertEqual(db_rev_content[key], rev_content[key], f"DB revision content field '{key}' mismatch")
                
        finally:
            # Clean up temporary file
            os.remove(file_path)

    def test_db_persistence(self):
        """Test that created files persist in the database across operations."""
        # Create first file
        body1 = {'name': 'file1.txt', 'mimeType': 'text/plain'}
        result1 = create_file_or_folder(body=body1)
        file_id1 = result1['id']
        
        # Create second file
        body2 = {'name': 'file2.txt', 'mimeType': 'text/plain'}
        result2 = create_file_or_folder(body=body2)
        file_id2 = result2['id']
        
        # Verify both files exist in DB
        file1_from_db = get_file_metadata_or_content(file_id1)
        file2_from_db = get_file_metadata_or_content(file_id2)
        
        self.assertEqual(file1_from_db['name'], 'file1.txt')
        self.assertEqual(file2_from_db['name'], 'file2.txt')
        
        # Verify they have different IDs
        self.assertNotEqual(file_id1, file_id2)

    def test_create_file_with_modified_time(self):
        """Test that the modified time is included in the response."""
        file_metadata = {
            'name': 'Test File Name',
            'mimeType': 'application/vnd.google-apps.document',
            'modifiedTime': '2024-05-01T00:00:00Z',
        }
        result = create_file_or_folder(body=file_metadata)
        self.assertIn('modifiedTime', result)
        self.assertIsInstance(result['modifiedTime'], str)
        self.assertEqual(result['modifiedTime'], '2024-05-01T00:00:00Z')
    
    def test_create_file_with_modified_time_and_includeLabels(self):
        """Test that the modified time is included in the response and includeLabels is included."""
        file_metadata = {
            'name': 'Test File Name',
            'mimeType': 'application/vnd.google-apps.document',
            'modifiedTime': '2024-05-01T00:00:00Z',
        }
        result = create_file_or_folder(body=file_metadata, includeLabels='Archived')
        self.assertIn('modifiedTime', result)
        self.assertIsInstance(result['modifiedTime'], str)
        self.assertEqual(result['modifiedTime'], '2024-05-01T00:00:00Z')
        self.assertIn('labels', result)
        self.assertEqual(result['labels'], ['Archived'])

    def test_create_file_with_invalid_modified_time_format(self):
        """Test that invalid modifiedTime format raises appropriate error."""
        file_metadata = {
            'name': 'Test File Name',
            'mimeType': 'application/vnd.google-apps.document',
            'modifiedTime': 'invalid-date-format',
        }
        
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=InvalidDateTimeFormatError,
            expected_message="Invalid modifiedTime datetime format: Invalid Google Drive datetime format: invalid-date-format. Expected RFC3339/ISO 8601 format with Z suffix (e.g., YYYY-MM-DDTHH:MM:SSZ).",
            body=file_metadata
        )

    def test_create_file_with_empty_modified_time(self):
        """Test that empty modifiedTime raises appropriate error."""
        file_metadata = {
            'name': 'Test File Name',
            'mimeType': 'application/vnd.google-apps.document',
            'modifiedTime': '',
        }
        
        self.assert_error_behavior(
            func_to_call=create_file_or_folder,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for FileBodyModel",
            body=file_metadata
        )

    def test_create_file_with_valid_modified_time_formats(self):
        """Test that various valid RFC3339 formats work correctly."""
        valid_formats = [
            '2024-05-01T00:00:00Z',
            '2024-05-01T12:30:45.123Z',
            '2024-05-01T12:30:45+00:00',
            '2024-05-01T12:30:45-05:00'
        ]
        
        for date_format in valid_formats:
            with self.subTest(date_format=date_format):
                file_metadata = {
                    'name': f'Test File {date_format}',
                    'mimeType': 'application/vnd.google-apps.document',
                    'modifiedTime': date_format,
                }
                result = create_file_or_folder(body=file_metadata)
                self.assertIn('modifiedTime', result)
                self.assertEqual(result['modifiedTime'], date_format)

    def test_get_file_readonly_operation_prevents_user_creation(self):
        """Test that get (read-only operation) does not create users - fixes Bug #798."""
        
        # Clear the DB to ensure no users exist
        DB.clear()
        
        # This should raise a UserNotFoundError, not create a new user (read-only operation should not modify data)
        self.assert_error_behavior(
            func_to_call=get_file_metadata_or_content,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID 'me' not found. Cannot perform read operation for non-existent user.",
            fileId="some-file-id"
        )
        
        # Verify the user was NOT created (critical for read-only operations)
        self.assertNotIn("users", DB)

    def test_invalid_fields_in_body_raises_validation_error(self):
        """Test that invalid fields in body dictionary raise ValidationError."""
        # Test with integer field
        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'invalidField': 123  # Integer field should be rejected
            })
        self.assertIn("Extra inputs are not permitted", str(exc_info.exception))
        
        # Test with boolean field
        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'anotherInvalidField': True  # Boolean field should be rejected
            })
        self.assertIn("Extra inputs are not permitted", str(exc_info.exception))

    def test_malformed_comma_separated_strings_in_include_labels(self):
        """Test that malformed comma-separated strings in includeLabels raise ValueError."""
        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder(
                body={'name': 'test.txt', 'mimeType': 'text/plain'},
                includeLabels='label1,,label2'
            )
        self.assertIn("includeLabels cannot contain consecutive commas", str(exc_info.exception))

        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder(
                body={'name': 'test.txt', 'mimeType': 'text/plain'},
                includeLabels=',label1'
            )
        self.assertIn("includeLabels cannot start or end with comma", str(exc_info.exception))

        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder(
                body={'name': 'test.txt', 'mimeType': 'text/plain'},
                includeLabels='label1,'
            )
        self.assertIn("includeLabels cannot start or end with comma", str(exc_info.exception))

        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder(
                body={'name': 'test.txt', 'mimeType': 'text/plain'},
                includeLabels='label with space'
            )
        self.assertIn("Invalid label format: 'label with space'", str(exc_info.exception))

    def test_negative_file_size_validation(self):
        """Test that negative file sizes are rejected."""
        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'size': '-100'
            })
        self.assertIn("File size cannot be negative", str(exc_info.exception))

    def test_invalid_file_size_format_validation(self):
        """Test that invalid file size formats are rejected."""
        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'size': 'abc'
            })
        self.assertIn("File size must be a valid integer string", str(exc_info.exception))

    def test_path_traversal_validation_in_name(self):
        """Test that path traversal sequences in the name parameter are rejected."""
        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': '../sensitive_file.txt',
                'mimeType': 'text/plain'
            })
        self.assertIn("File name contains path traversal sequences", str(exc_info.exception))

        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': 'folder/..\\file.txt',
                'mimeType': 'text/plain'
            })
        self.assertIn("File name contains path traversal sequences", str(exc_info.exception))

    def test_invalid_parent_folder_id_validation(self):
        """Test that invalid parent folder IDs are rejected."""
        # Test with non-existent parent folder
        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'parents': ['non_existent_folder_id']
            })
        self.assertIn("Parent folder with ID 'non_existent_folder_id' does not exist", str(exc_info.exception))
    
        # Test with empty parent folder ID
        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'parents': ['']
            })
        self.assertIn("Parent folder ID must be a non-empty string", str(exc_info.exception))
    
        # Test with non-string parent folder ID
        with self.assertRaises(ValidationError) as exc_info:  # Pydantic catches this first
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'parents': [123]  # Integer instead of string
            })
        self.assertIn("Input should be a valid string", str(exc_info.exception))

    def test_valid_parent_folder_id_acceptance(self):
        """Test that valid parent folder IDs are accepted."""
        # Create a valid parent folder for testing
        valid_folder_id = "valid_folder_123"
        DB['users']['me']['files'][valid_folder_id] = {
            'id': valid_folder_id,
            'name': 'Valid Parent Folder',
            'mimeType': 'application/vnd.google-apps.folder',
            'owners': ['test@example.com'],
            'permissions': [{'id': 'perm1', 'role': 'owner', 'type': 'user', 'emailAddress': 'test@example.com'}]
        }
        
        file = create_file_or_folder({
            'name': 'test.txt',
            'mimeType': 'text/plain',
            'parents': [valid_folder_id]
        })
        self.assertEqual(file['parents'], [valid_folder_id])

    def test_google_workspace_document_as_parent(self):
        """Test that Google Workspace documents can be used as parent folders."""
        doc_result = create_file_or_folder({
            'name': 'test_doc',
            'mimeType': 'application/vnd.google-apps.document'
        })
        doc_id = doc_result['id']

        file = create_file_or_folder({
            'name': 'test_in_google_doc.txt',
            'mimeType': 'text/plain',
            'parents': [doc_id]
        })
        self.assertEqual(file['parents'], [doc_id])

    def test_multiple_parent_validation(self):
        """Test with multiple valid and invalid parent folder IDs."""
        # Test with one valid and one non-existent
        valid_folder_id = "valid_folder_456"
        DB['users']['me']['files'][valid_folder_id] = {
            'id': valid_folder_id,
            'name': 'Valid Parent Folder',
            'mimeType': 'application/vnd.google-apps.folder',
            'owners': ['test@example.com'],
            'permissions': [{'id': 'perm2', 'role': 'owner', 'type': 'user', 'emailAddress': 'test@example.com'}]
        }
        
        with self.assertRaises(ValueError) as exc_info:
            create_file_or_folder({
                'name': 'test.txt',
                'mimeType': 'text/plain',
                'parents': [valid_folder_id, 'another_non_existent']
            })
        self.assertIn("Parent folder with ID 'another_non_existent' does not exist", str(exc_info.exception))

        # Test with multiple valid parents
        doc_result = create_file_or_folder({
            'name': 'test_doc_2',
            'mimeType': 'application/vnd.google-apps.document'
        })
        doc_id_2 = doc_result['id']

        file = create_file_or_folder({
            'name': 'test.txt',
            'mimeType': 'text/plain',
            'parents': [valid_folder_id, doc_id_2]
        })
        self.assertEqual(file['parents'], [valid_folder_id, doc_id_2])

    def test_combined_validation_errors(self):
        """Test that multiple validation errors are caught."""
        with self.assertRaises(ValidationError) as exc_info:
            create_file_or_folder({
                'name': '../malicious.txt',
                'mimeType': 'text/plain',
                'size': '-50',
                'invalid_key': 'value'
            })
        error_message = str(exc_info.exception)
        self.assertIn("Extra inputs are not permitted", error_message)
        self.assertIn("File size cannot be negative", error_message)
        self.assertIn("File name contains path traversal sequences", error_message)

    def test_valid_file_creation_still_works(self):
        """Test that a valid file creation still works."""
        valid_folder_id = "valid_folder_789"
        DB['users']['me']['files'][valid_folder_id] = {
            'id': valid_folder_id,
            'name': 'Valid Parent Folder',
            'mimeType': 'application/vnd.google-apps.folder',
            'owners': ['test@example.com'],
            'permissions': [{'id': 'perm3', 'role': 'owner', 'type': 'user', 'emailAddress': 'test@example.com'}]
        }
        
        file = create_file_or_folder({
            'name': 'valid_file.txt',
            'mimeType': 'text/plain',
            'size': '1024',
            'parents': [valid_folder_id]
        })
        self.assertEqual(file['name'], 'valid_file.txt')
        self.assertEqual(file['mimeType'], 'text/plain')
        self.assertEqual(file['size'], '1024')
        self.assertEqual(file['parents'], [valid_folder_id])
        self.assertIn(file['id'], DB['users']['me']['files'])

    def test_empty_include_labels_handled_gracefully(self):
        """Test that empty includeLabels string is handled gracefully."""
        result = create_file_or_folder(
            body={'name': 'test.txt', 'mimeType': 'text/plain'},
            includeLabels=''
        )
        self.assertEqual(result['labels'], [])

    def test_none_include_labels_handled_gracefully(self):
        """Test that None includeLabels is handled gracefully."""
        result = create_file_or_folder(
            body={'name': 'test.txt', 'mimeType': 'text/plain'},
            includeLabels=None
        )
        self.assertEqual(result['labels'], [])

if __name__ == '__main__':
    unittest.main() 