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
from .. import update_file_content
from gdrive.SimulationEngine.db import DB

class TestUpdateFileContent(BaseTestCaseWithErrorHandler):
    """An extensive, state-based test suite for the DriveContentManager class."""

    def setUp(self):
        """Reset DB to a clean state before each test."""
        DB.clear()
        DB.update({
            'users': {
                'test_user': {
                    'files': {
                        'file1': {
                            'id': 'file1',
                            'name': 'Document.txt',
                            'mimeType': 'text/plain',
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
                            'name': 'ContentFile.txt',
                            'mimeType': 'application/vnd.google-apps.document',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-27T11:00:00Z',
                            'owners': ['test_user'],
                            'size': '15',
                            'content': {
                                'data': base64.b64encode(b'initial content').decode(),
                                'encoding': 'text',
                                'checksum': f"sha256:{hashlib.sha256(b'initial content').hexdigest()}",
                                'version': '1.0',
                                'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                            },
                            'revisions': [],
                            'exportFormats': {
                                'application/pdf': base64.b64encode(b'cached_data').decode()
                            }
                        },
                        'file_with_content_b64': {
                            'id': 'file_with_content_b64',
                            'name': 'ContentFileB64.png',
                            'mimeType': 'image/png',
                            'createdTime': '2025-10-01T11:00:00Z',
                            'modifiedTime': '2025-10-01T11:00:00Z',
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
                            'exportFormats': {}
                        },
                        'file_with_revs': {
                            'id': 'file_with_revs',
                            'name': 'RevisionsTest.txt',
                            'mimeType': 'text/plain',
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
                                    'originalFilename': 'RevisionsTest.txt',
                                    'size': '10',
                                    'mimeType': 'text/plain',
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
                                    'originalFilename': 'RevisionsTest.txt',
                                    'size': '12',
                                    'mimeType': 'text/plain',
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

    def test_update_file_content_success(self):
        """Test successfully updating content and creating a corresponding revision."""
        new_content = 'new content'
        result = update_file_content(user_id='test_user', file_id='file_with_revs', new_content=new_content)
        
        self.assertTrue(result['content_updated'])
        self.assertEqual(result['new_size'], len(new_content))
        
        updated_file = DB['users']['test_user']['files']['file_with_revs']
        self.assertEqual(updated_file['size'], str(len(new_content)))
        self.assertEqual(len(updated_file['revisions']), 3)
        self.assertEqual(float(updated_file['content']['version']), 1.1)

    def test_update_file_content_clears_export_cache(self):
        """Test that updating content correctly clears the file's export cache."""
        file_data = DB['users']['test_user']['files']['file_with_content']
        self.assertIn('application/pdf', file_data['exportFormats'])
        update_file_content(user_id='test_user', file_id='file_with_content', new_content='new data')
        self.assertEqual(file_data['exportFormats'], {})
    
    def test_update_file_content_with_non_existing_user_id_raises_value_error(self):
        """Test ValueError when updating content with a non-existing user ID."""
        self.assert_error_behavior(
            update_file_content, ValueError, "User 'non_existing_user' not found",
            user_id='non_existing_user', file_id='file_with_content', new_content='new data'
        )
    
    def test_update_file_content_with_non_existing_file_id_raises_value_error(self):
        """Test ValueError when updating content with a non-existing file ID."""
        self.assert_error_behavior(
            update_file_content, ValueError, "File 'non_existing_file' not found for user 'test_user'",
            user_id='test_user', file_id='non_existing_file', new_content='new data'
        )
    
    def test_update_file_content_with_non_base64_encoding(self):
        """Test that updating content with a non-base64 encoding correctly updates the content."""
        new_content = 'new content'
        result = update_file_content(user_id='test_user', file_id='file_with_content', new_content=new_content)

        self.assertTrue(result['content_updated'])
        self.assertEqual(result['new_size'], len(new_content))
        
        updated_file = DB['users']['test_user']['files']['file_with_content']
        self.assertEqual(updated_file['size'], str(len(new_content)))
        self.assertEqual(len(updated_file['revisions']), 1) # First revision created on update
        self.assertEqual(float(updated_file['content']['version']), 1.1)
    
    def test_update_file_content_with_non_string_user_id_raises_value_error(self):
        """Test ValueError when updating content with a non-string user_id."""
        self.assert_error_behavior(
            update_file_content, ValueError, "user_id must be a string",
            user_id=123, file_id='file_with_content', new_content='new data'
        )
    
    def test_update_file_content_with_non_string_file_id_raises_value_error(self):
        """Test ValueError when updating content with a non-string file_id."""
        self.assert_error_behavior(
            update_file_content, ValueError, "file_id must be a string",
            user_id='test_user', file_id=123, new_content='new data'
        )

    def test_update_file_content_with_bytes_new_content_raises_value_error(self):
        """Test ValueError when updating content with a non-string new_content."""
        self.assert_error_behavior(
            update_file_content, ValueError, "new_content must be a string",
            user_id='test_user', file_id='file_with_content', new_content=b'not string'
        )
    
    def test_update_file_content_with_base64_encoding(self):
        """Test successfully updating content and creating a corresponding revision."""
        new_content = 'new content'
        result = update_file_content(user_id='test_user', file_id='file_with_content_b64', new_content=new_content)
        
        self.assertTrue(result['content_updated'])
        self.assertEqual(result['new_size'], len(new_content))
        
        updated_file = DB['users']['test_user']['files']['file_with_content_b64']
        self.assertEqual(updated_file['size'], str(len(new_content)))
        self.assertEqual(len(updated_file['revisions']), 1)
        self.assertEqual(float(updated_file['content']['version']), 1.1)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
