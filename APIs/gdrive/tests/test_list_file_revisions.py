import unittest
from unittest.mock import patch, mock_open
import os
import sys
import base64
import hashlib
from datetime import datetime, timedelta, UTC
import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import list_file_revisions
from gdrive.SimulationEngine.content_manager import DriveContentManager
from gdrive.SimulationEngine.db import DB

class TestListFileRevisions(BaseTestCaseWithErrorHandler):
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
                                'application/pdf': base64.b64encode(b'cached_data').decode()
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

    def test_list_file_revisions_with_data(self):
        """Test getting the list of revisions from a file that has them."""
        revisions = list_file_revisions('file_with_revs', 'test_user')
        self.assertIsInstance(revisions, list)
        self.assertEqual(len(revisions), 2)
        self.assertEqual(revisions[0]['id'], 'rev-1')

    def test_list_file_revisions_empty(self):
        """Test getting revisions from a file with no revision history."""
        revisions = list_file_revisions('file_with_content', 'test_user')
        self.assertIsInstance(revisions, list)
        self.assertEqual(len(revisions), 0)
    
    def test_list_file_revisions_without_user_id(self):
        """Test getting revisions without providing user_id parameter (uses default 'me')."""
        # Add 'me' user to the database for this test
        DB['users']['me'] = {
            'files': {
                'file_with_revs': {
                    'id': 'file_with_revs',
                    'name': 'RevisionsTest',
                    'mimeType': 'application/vnd.google-apps.document',
                    'createdTime': '2025-06-26T20:00:00Z',
                    'modifiedTime': '2025-06-27T10:00:00Z',
                    'owners': ['me'],
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
                        }
                    ],
                    'exportFormats': {}
                }
            }
        }
        
        # Test calling without user_id parameter
        revisions = list_file_revisions('file_with_revs')
        self.assertIsInstance(revisions, list)
        self.assertEqual(len(revisions), 1)
        self.assertEqual(revisions[0]['id'], 'rev-1')
    
    def test_list_file_revisions_with_non_string_user_id_raises_value_error(self):
        """Test ValueError when listing revisions with a non-string user_id."""
        self.assert_error_behavior(
            list_file_revisions, ValueError, "user_id must be a string",
            user_id=123, file_id='file_with_revs'
        )
    
    def test_list_file_revisions_with_non_string_file_id_raises_value_error(self):
        """Test ValueError when listing revisions with a non-string file_id."""
        self.assert_error_behavior(
            list_file_revisions, ValueError, "file_id must be a string",
            user_id='test_user', file_id=123
        )
    
    def test_list_file_revisions_with_non_existing_user_id_raises_value_error(self):
        """Test ValueError when listing revisions with a non-existing user_id."""
        self.assert_error_behavior(
            list_file_revisions, ValueError, "User 'non_existing_user' not found",
            user_id='non_existing_user', file_id='file_with_revs'
        )
    
    def test_list_file_revisions_with_non_existing_file_id_raises_value_error(self):
        """Test ValueError when listing revisions with a non-existing file_id."""
        self.assert_error_behavior(
            list_file_revisions, ValueError, "File 'non_existing_file' not found for user 'test_user'",
            user_id='test_user', file_id='non_existing_file'
        )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
