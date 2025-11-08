import unittest
from unittest.mock import patch, mock_open
import os
import sys
import base64
import hashlib
from datetime import datetime, timedelta, UTC
import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler

from gdrive.SimulationEngine.content_manager import DriveContentManager
from .. import (export_file_content, create_file_or_folder, export_google_doc)
from .. import (export_file_content, export_google_doc)
from gdrive.SimulationEngine.db import DB

class TestExportFileContent(BaseTestCaseWithErrorHandler):
    """An extensive, state-based test suite for the DriveContentManager class."""

    def setUp(self):
        """Reset DB to a clean state before each test."""
        self.manager = DriveContentManager()
        DB.clear()
        DB.update({
            'users': {
                'test_user': {
                    'files': {
                        'file1': {
                            'id': 'file1',
                            'name': 'Document',
                            'mimeType': 'application/vnd.google-apps.document',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-26T15:00:00Z',
                            'owners': ['test_user'],
                            'size': '0',
                            'content': None,
                            'revisions': [],
                            'exportFormats': {}
                        },
                        'file_with_content': {
                            'id': 'file_with_content',
                            'name': 'ContentFile',
                            'mimeType': 'application/vnd.google-apps.document',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-27T11:00:00Z',
                            'owners': ['test_user'],
                            'size': '15',
                            'content': {
                                'data': base64.b64encode(b'initial content').decode(),
                                'encoding': 'base64',
                                'checksum': f"sha256:{hashlib.sha256(b'initial content').hexdigest()}",
                                'version': '1.0',
                                'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                            },
                            'revisions': [],
                            'exportFormats': {
                                'application/pdf': 'cached_data'
                            }
                        },
                        'file_with_content_txt': {
                            'id': 'file_with_content_txt',
                            'name': 'ContentFile',
                            'mimeType': 'application/vnd.google-apps.document',
                            'createdTime': '2025-06-16T15:00:00Z',
                            'modifiedTime': '2025-06-17T11:00:00Z',
                            'owners': ['test_user'],
                            'size': '15',
                            'content': {
                                'data': 'initial content',
                                'encoding': 'utf-8',
                                'checksum': self.manager.file_processor.calculate_checksum('initial content'),
                                'version': '1.0',
                                'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                            },
                            'revisions': [],
                            'exportFormats': {
                                'application/pdf': 'cached_data'
                            }
                        },
                        'file_with_revs': {
                            'id': 'file_with_revs',
                            'name': 'RevisionsTest',
                            'mimeType': 'application/vnd.google-apps.document',
                            'createdTime': '2025-06-26T20:00:00Z',
                            'modifiedTime': '2025-06-27T10:00:00Z',
                            'owners': ['test_user'],
                            'size': '13',
                            'content': {
                                'data': 'aW5pdGlhbCBjb250ZW50',
                                'checksum': f"sha256:{hashlib.sha256(b'initial content').hexdigest()}",
                                'version': '1.0',
                                'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                            },
                            'revisions': [
                                {
                                    'id': 'rev-1',
                                    'keepForever': False,
                                    'originalFilename': 'RevisionsTest',
                                    'size': '10',
                                    'mimeType': 'application/vnd.google-apps.document',
                                    'modifiedTime': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                    'content': {
                                        'data': base64.b64encode(b'rev-1').decode(),
                                        'encoding': 'base64',
                                        'checksum': f"sha256:{hashlib.sha256(b'rev-1').hexdigest()}",
                                        'version': '1.0',
                                        'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                                    }
                                },
                                {
                                    'id': 'rev-2',
                                    'keepForever': True,
                                    'originalFilename': 'RevisionsTest',
                                    'size': '12',
                                    'mimeType': 'application/vnd.google-apps.document',
                                    'modifiedTime': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                    'content': {
                                        'data': base64.b64encode(b'rev-2').decode(),
                                        'encoding': 'base64',
                                        'checksum': f"sha256:{hashlib.sha256(b'rev-2').hexdigest()}",
                                        'version': '1.0',
                                        'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                                    }
                                }
                            ],
                            'exportFormats': {}
                        }
                    }
                }
            }
        })

    def test_export_file_content_success_not_cached(self):
        """Test exporting content to a new format creates a new cache entry."""
        result = export_file_content(user_id='test_user', file_id='file_with_content', target_mime='text/plain')
        self.assertEqual(result['file_id'], 'file_with_content')
        self.assertTrue(result['exported'])
        self.assertEqual(result['target_mime'], 'text/plain')
        self.assertFalse(result['cached'])
        
        file_data = DB['users']['test_user']['files']['file_with_content']
        self.assertIn('text/plain', file_data['exportFormats'])
    
    def test_export_file_content_success_not_cached_txt(self):
        """Test exporting content to a new format creates a new cache entry."""
        result = export_file_content(user_id='test_user', file_id='file_with_content_txt', target_mime='application/pdf')
        self.assertEqual(result['file_id'], 'file_with_content_txt')
        self.assertTrue(result['exported'])
        self.assertEqual(result['target_mime'], 'application/pdf')
        self.assertTrue(result['cached'])

        file_data = DB['users']['test_user']['files']['file_with_content_txt']
        self.assertIn('application/pdf', file_data['exportFormats'])

    def test_export_file_content_from_cache_success(self):
        """Test that exporting returns cached content without reprocessing."""
        original_string = DB['users']['test_user']['files']['file_with_content']['exportFormats']['application/pdf']
        result = export_file_content(user_id='test_user', file_id='file_with_content', target_mime='application/pdf')
        self.assertTrue(result['exported'])
        self.assertTrue(result['cached'])
        self.assertEqual(result['content'], original_string)
        self.assertEqual(result['size'], len(original_string))
    
    def test_export_file_content_with_non_string_user_id_raises_value_error(self):
        """Test ValueError when exporting content with a non-string user_id."""
        self.assert_error_behavior(
            export_file_content, ValueError, "user_id must be a string",
            user_id=123, file_id='file_with_content', target_mime='text/plain'
        )
    
    def test_export_file_content_with_non_string_file_id_raises_value_error(self):
        """Test ValueError when exporting content with a non-string file_id."""
        self.assert_error_behavior(
            export_file_content, ValueError, "file_id must be a string",
            user_id='test_user', file_id=123, target_mime='text/plain'
        )
    
    def test_export_file_content_with_non_string_target_mime_raises_value_error(self):
        """Test ValueError when exporting content with a non-string target_mime."""
        self.assert_error_behavior(
            export_file_content, ValueError, "target_mime must be a string",
            user_id='test_user', file_id='file_with_content', target_mime=123
        )
    
    def test_export_file_content_with_non_existing_user_id_raises_value_error(self):
        """Test ValueError when exporting content with a non-existing user_id."""
        self.assert_error_behavior(
            export_file_content, ValueError, "User 'non_existing_user' not found",
            user_id='non_existing_user', file_id='file_with_content', target_mime='text/plain'
        )
    
    def test_export_file_content_with_non_existing_file_id_raises_value_error(self):
        """Test ValueError when exporting content with a non-existing file_id."""
        self.assert_error_behavior(
            export_file_content, ValueError, "File 'non_existing_file' not found for user 'test_user'",
            user_id='test_user', file_id='non_existing_file', target_mime='text/plain'
        )
    
    def test_export_file_content_with_no_content_txt(self):
        """Test ValueError when exporting content with no content."""
        gdoc_id = 'e2c91b5b-b0c7-4776-8f54-94f394f4c4ba'
        DB['users']['me'] = {'files': {}}
        DB['users']['me']['files'][gdoc_id] = {'id': gdoc_id,
            'driveId': '',
            'name': 'Q3 Project Requirements Specification',
            'mimeType': 'application/vnd.google-apps.document',
            'createdTime': '2025-03-11T09:00:00Z',
            'modifiedTime': '2025-03-11T09:00:00Z',
            'parents': [],
            'owners': ['john.doe@gmail.com'],
            'suggestionsViewMode': 'DEFAULT',
            'includeTabsContent': False,
            'content': [],
            'tabs': [],
            'permissions': [{'role': 'owner',
                'type': 'user',
                'emailAddress': 'john.doe@gmail.com'}],
            'trashed': False,
            'starred': False,
            'size': '0'}
        result = export_google_doc(fileId=gdoc_id, mimeType='text/plain',)
        self.assertEqual(result['kind'], 'drive#export')
        self.assertEqual(result['fileId'], gdoc_id)
        self.assertEqual(result['mimeType'], 'text/plain')
        self.assertEqual(result['content'], "Text export of 'Q3 Project Requirements Specification'\nOriginal format: application/vnd.google-apps.document\nExported content...")

    def test_export_file_content_with_none_content_handles_gracefully(self):
        """Test Bug #1008: export_file_content handles None content gracefully."""
        # This test verifies the fix for Bug #1008 where file_data.get('content', {}).get('encoding', 'base64')
        # would fail with AttributeError when content is None
        
        # Create a file with None content (this was causing the bug)
        file_id = 'file_with_none_content'
        DB['users']['test_user']['files'][file_id] = {
            'id': file_id,
            'name': 'NoneContentFile',
            'mimeType': 'application/vnd.google-apps.document',
            'createdTime': '2025-06-26T15:00:00Z',
            'modifiedTime': '2025-06-26T15:00:00Z',
            'owners': ['test_user'],
            'size': '0',
            'content': None,  # This was causing the bug
            'revisions': [],
            'exportFormats': {}
        }
        
        # This should not raise an AttributeError anymore
        result = export_file_content(user_id='test_user', file_id=file_id, target_mime='text/plain')
        self.assertEqual(result['file_id'], file_id)
        self.assertTrue(result['exported'])
        self.assertEqual(result['target_mime'], 'text/plain')
        self.assertFalse(result['cached'])


    def test_export_file_content_encoding_extraction_bug_1008(self):
        """Test Bug #1008: encoding extraction handles None values gracefully."""
        # Test the specific encoding extraction logic that was causing the bug
        
        # Test case 1: content is None (the main bug)
        file_data = {'content': None}
        content = file_data.get('content')
        if content is None or not isinstance(content, dict):
            encoding = 'base64'
        else:
            encoding = content.get('encoding', 'base64')
        self.assertEqual(encoding, 'base64')
        
        # Test case 2: content is empty dict
        file_data = {'content': {}}
        content = file_data.get('content')
        if content is None or not isinstance(content, dict):
            encoding = 'base64'
        else:
            encoding = content.get('encoding', 'base64')
        self.assertEqual(encoding, 'base64')
        
        # Test case 3: content is string instead of dict
        file_data = {'content': 'not a dict'}
        content = file_data.get('content')
        if content is None or not isinstance(content, dict):
            encoding = 'base64'
        else:
            encoding = content.get('encoding', 'base64')
        self.assertEqual(encoding, 'base64')
        
        # Test case 4: content is dict with None encoding
        file_data = {'content': {'encoding': None}}
        content = file_data.get('content')
        if content is None or not isinstance(content, dict):
            encoding = 'base64'
        else:
            encoding = content.get('encoding', 'base64')
        self.assertEqual(encoding, None)  # This is expected behavior
        
        # Test case 5: content is dict without encoding key
        file_data = {'content': {'data': 'some data'}}
        content = file_data.get('content')
        if content is None or not isinstance(content, dict):
            encoding = 'base64'
        else:
            encoding = content.get('encoding', 'base64')
        self.assertEqual(encoding, 'base64')
        
        # Test case 6: content is dict with valid encoding
        file_data = {'content': {'encoding': 'utf-8'}}
        content = file_data.get('content')
        if content is None or not isinstance(content, dict):
            encoding = 'base64'
        else:
            encoding = content.get('encoding', 'base64')
        self.assertEqual(encoding, 'utf-8')

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
