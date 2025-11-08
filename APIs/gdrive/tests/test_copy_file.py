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
from .. import copy_file
from gdrive.SimulationEngine.db import DB
from pydantic import ValidationError

class TestDriveContentManager(BaseTestCaseWithErrorHandler):
    """An extensive, state-based test suite for the DriveContentManager class."""

    def setUp(self):
        """Reset DB to a clean state before each test."""
        self.manager = DriveContentManager()
        DB.clear()
        DB.update({
            'users': {
                'me': {
                    'files': {
                        'file1': {
                            'id': 'file1',
                            'name': 'Document.png',
                            'mimeType': 'image/png',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-26T15:00:00Z',
                            'owners': ['me'],
                            'size': '0',
                            'content': None,
                            'revisions': [],
                            'exportFormats': {}
                        },
                        'file_no_revisions': {
                            'id': 'file_no_revisions',
                            'name': 'Document.png',
                            'mimeType': 'image/png',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-26T15:00:00Z',
                            'owners': ['me'],
                            'size': '0',
                            'content': None,
                            'exportFormats': {}
                        },
                        'file_with_content': {
                            'id': 'file_with_content',
                            'name': 'ContentFile.png',
                            'mimeType': 'image/png',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-27T11:00:00Z',
                            'owners': ['me'],
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
                            'owners': ['me'],
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
                        },
                        'file_with_permissions': {
                            'id': 'file_with_permissions',
                            'name': 'Document.png',
                            'mimeType': 'image/png',
                            'createdTime': '2025-06-26T15:00:00Z',
                            'modifiedTime': '2025-06-26T15:00:00Z',
                            'owners': ['me'],
                            'size': '0',
                            'content': None,
                            'revisions': [],
                            'exportFormats': {},
                            'permissions': [
                                {
                                    'id': 'permission_file_with_permissions_1',
                                    'role': 'owner',
                                    'type': 'user',
                                    'emailAddress': 'john.doe@gmail.com'
                                }
                            ]
                        }
                    },
                    'about': {
                        'storageQuota': {
                            'limit': '1000000000',
                            'usage': '0'
                        }
                    },
                    "counters": {
                        "file": 0,
                        "drive": 0,
                        "comment": 0,
                        "reply": 0,
                        "label": 0,
                        "accessproposal": 0,
                        "revision": 0,
                        "change_token": 0,
                    }
                }
            }
        })

    def test_copy_file_success(self):
        """Test copying a file returns correct data."""
        result = copy_file(fileId='file_with_content')
        self.assertIn('content', result)
        self.assertEqual(result['content']['data'], base64.b64encode('initial content'.encode('utf-8')).decode())
    
    def test_copy_file_non_existing_file_id_raises_value_error(self):
        """Test ValueError when copying a file from a non-existing file."""
        self.assert_error_behavior(
            copy_file, ValueError, "File not found. If you want to check in shared drives, pass supportsAllDrives=True or supportsTeamDrives=True.",
            fileId='non_existing_file'
        )
    
    def test_copy_file_copies_only_keepForever_revisions(self):
        result = copy_file(fileId='file_with_revs')
        self.assertEqual(len(result['revisions']), 1)
        self.assertEqual(result['revisions'][0]['id'], 'rev-2')
    
    def test_copy_file_does_not_allow_permissions_in_body(self):
        """Test that copying a file with permissions in body raises a ValidationError."""
        expected_message="""1 validation error for FileCopyBodyModel
permissions
  Extra inputs are not permitted [type=extra_forbidden, input_value=[{'id': 'permission-1', '...: 'john.doe@gmail.com'}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden"""

        self.assert_error_behavior(
            func_to_call=copy_file,
            expected_exception_type=ValidationError,
            expected_message=expected_message,
            fileId='file_with_permissions',
            body={'permissions': [{"id": "permission-1", "role": "owner", "type": "user", "emailAddress": "john.doe@gmail.com"}]}
        )
    
    def test_copy_file_copies_permissions(self):
        """Test that copying a file copies the permissions."""
        file_to_copy = DB['users']['me']['files']['file_with_permissions']
        copied_file = copy_file(fileId=file_to_copy['id'])
        self.assertIn('permissions', copied_file)
        self.assertIn('permissions', file_to_copy)
        self.assertEqual(copied_file['permissions'], file_to_copy['permissions'])

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
