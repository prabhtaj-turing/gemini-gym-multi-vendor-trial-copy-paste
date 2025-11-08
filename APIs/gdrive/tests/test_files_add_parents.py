
import pytest
import unittest
from unittest.mock import patch
import copy

from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import ResourceNotFoundError
from .. import (create_file_or_folder, update_file_metadata_or_content)

class TestFilesAddParents(unittest.TestCase):
    def setUp(self):
        """Set up a clean database before each test."""
        DB.clear()
        DB.update({
            'users': {
                'me': {
                    'files': {
                        'file-to-update': {
                            'id': 'file-to-update',
                            'name': 'Test File',
                            'parents': [],
                            'mimeType': 'text/plain'
                        },
                        'folder-parent': {
                            'id': 'folder-parent',
                            'name': 'Test Folder',
                            'parents': [],
                            'mimeType': 'application/vnd.google-apps.folder'
                        },
                        'not-a-folder': {
                            'id': 'not-a-folder',
                            'name': 'Not a Folder',
                            'parents': [],
                            'mimeType': 'text/plain'
                        }
                    },
                    'drives': {
                        'drive-parent': {
                            'id': 'drive-parent',
                            'name': 'Test Drive'
                        }
                    },
                    'counters': {'file': 0, 'drive': 0, 'comment': 0, 'reply': 0, 'label': 0, 'accessproposal': 0, 'revision': 0}
                }
            }
        })

    def test_add_parent_folder_successfully(self):
        """Tests that a valid folder can be added as a parent."""
        updated_file = update_file_metadata_or_content(fileId='file-to-update', addParents='folder-parent')
        self.assertIn('folder-parent', updated_file['parents'])

    def test_add_parent_drive_successfully(self):
        """Tests that a valid drive can be added as a parent."""
        updated_file = update_file_metadata_or_content(fileId='file-to-update', addParents='drive-parent')
        self.assertIn('drive-parent', updated_file['parents'])

    def test_add_non_existent_parent_raises_error(self):
        """Tests that adding a non-existent parent raises ResourceNotFoundError."""
        with self.assertRaises(ResourceNotFoundError):
            update_file_metadata_or_content(fileId='file-to-update', addParents='non-existent-parent')

    def test_add_non_folder_as_parent_raises_error(self):
        """Tests that adding a file that is not a folder as a parent raises ValueError."""
        with self.assertRaises(ValueError):
            update_file_metadata_or_content(fileId='file-to-update', addParents='not-a-folder')

if __name__ == '__main__':
    unittest.main()
