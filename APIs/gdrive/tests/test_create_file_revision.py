import unittest
from unittest.mock import patch, mock_open
import os
import sys
import base64
import hashlib
from datetime import datetime, timedelta, UTC
import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import create_file_revision
from gdrive.SimulationEngine.content_manager import DriveContentManager
from gdrive.SimulationEngine.file_utils import DriveFileProcessor
from gdrive.SimulationEngine.db import DB

class TestCreateFileRevision(BaseTestCaseWithErrorHandler):
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
                            'name': 'Document.png',
                            'mimeType': 'image/png',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-26T15:00:00Z',
                            'owners': ['test_user'],
                            'size': '0',
                            'content': {
                                'data': '',
                                'encoding': 'base64',
                                'checksum': '',
                                'version': '1.0',
                                'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                            },
                            'exportFormats': {}
                        },
                        'file_with_content': {
                            'id': 'file_with_content',
                            'name': 'ContentFile.png',
                            'mimeType': 'image/png',
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
                                'application/pdf': base64.b64encode(b'cached_data').decode()
                            }
                        },
                        'file_with_content_txt': {
                            'id': 'file_with_content_txt',
                            'name': 'ContentFile.txt',
                            'mimeType': 'text/plain',
                            'createdTime': '2025-06-16T15:00:00Z',
                            'modifiedTime': '2025-06-17T11:00:00Z',
                            'owners': ['test_user'],
                            'size': '15',
                            'content': {
                                'data': 'initial content',
                                'encoding': 'text',
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

    def test_create_revision_success(self):
        result = create_file_revision(user_id='test_user', file_id='file_with_content', content='new content')
        
        self.assertEqual(result['revision_id'], 'rev-1')
        self.assertEqual(result['revision_created'], True)
        self.assertEqual(result['size'], len('new content'))
        self.assertEqual(result['checksum'], DriveFileProcessor().calculate_checksum('new content'))
    
    def test_create_revision_with_user_id_non_string_raises_value_error(self):
        self.assert_error_behavior(
            create_file_revision, ValueError, "user_id must be a string",
            user_id=123, file_id='file_with_content', content='new content'
        )
    
    def test_create_revision_with_file_id_non_string_raises_value_error(self):
        self.assert_error_behavior(
            create_file_revision, ValueError, "file_id must be a string",
            user_id='test_user', file_id=123, content='new content'
        )
    
    def test_create_revision_with_content_bytes_raises_value_error(self):
        self.assert_error_behavior(
            create_file_revision, ValueError, "content must be a string",
            user_id='test_user', file_id='file_with_content', content=b'not string'
        )
    
    def test_create_revision_with_non_existing_user_id_raises_value_error(self):
        self.assert_error_behavior(
            create_file_revision, ValueError, "User 'non_existing_user' not found",
            user_id='non_existing_user', file_id='file_with_content', content='new content'
        )
    
    def test_create_revision_with_non_existing_file_id_raises_value_error(self):
        self.assert_error_behavior(
            create_file_revision, ValueError, "File 'non_existing_file' not found for user 'test_user'",
            user_id='test_user', file_id='non_existing_file', content='new content'
        )
    
    def test_create_revision_with_non_base64_encoding(self):
        result = create_file_revision(user_id='test_user', file_id='file_with_content_txt', content='new content')
        self.assertEqual(result['revision_id'], 'rev-1')
        self.assertEqual(result['revision_created'], True)
        self.assertEqual(result['size'], len(b'new content'))
        self.assertEqual(result['checksum'], DriveFileProcessor().calculate_checksum('new content'))

    def test_create_revision_with_file_with_no_revisions(self):
        result = create_file_revision(user_id='test_user', file_id='file1', content='new content')
        self.assertEqual(result['revision_id'], 'rev-1')
        self.assertEqual(result['revision_created'], True)
        self.assertEqual(result['size'], len(b'new content'))
        self.assertEqual(result['checksum'], DriveFileProcessor().calculate_checksum('new content'))

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
