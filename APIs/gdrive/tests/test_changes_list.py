"""
Test cases for the Changes.list function in the Google Drive API simulation.

This module contains comprehensive tests for input validation, edge cases,
and functionality of the changes.list method.
"""

import unittest
import warnings
from unittest.mock import patch
from .. import list_changes
from gdrive.SimulationEngine.db import DB
from gdrive.SimulationEngine.custom_errors import ValidationError, InvalidRequestError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestChangesListFunction(BaseTestCaseWithErrorHandler):
    """Test cases for the Changes.list function."""

    def setUp(self):
        """Set up test data before each test."""
        super().setUp()
        
        # Initialize test user data with sample changes
        DB['users']['me']['changes'] = {
            'startPageToken': '5',
            'changes': [
                {
                    'kind': 'drive#change',
                    'type': 'file',
                    'changeType': 'file',
                    'time': '2024-01-01T10:00:00.000Z',
                    'removed': False,
                    'fileId': 'file1',
                    'file': {
                        'id': 'file1',
                        'name': 'test1.txt',
                        'mimeType': 'text/plain',
                        'spaces': ['drive']
                    },
                    'driveId': None
                },
                {
                    'kind': 'drive#change',
                    'type': 'file',
                    'changeType': 'file',
                    'time': '2024-01-01T11:00:00.000Z',
                    'removed': True,
                    'fileId': 'file2',
                    'file': None,
                    'driveId': None
                },
                {
                    'kind': 'drive#change',
                    'type': 'file',
                    'changeType': 'file',
                    'time': '2024-01-01T12:00:00.000Z',
                    'removed': False,
                    'fileId': 'file3',
                    'file': {
                        'id': 'file3',
                        'name': 'shared.txt',
                        'mimeType': 'text/plain',
                        'spaces': ['drive']
                    },
                    'driveId': 'shared_drive_1'
                }
            ]
        }

    def test_valid_minimal_request(self):
        """Test changes.list with minimal valid parameters."""
        result = list_changes(pageToken='1')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['kind'], 'drive#changeList')
        self.assertIn('nextPageToken', result)
        self.assertIn('newStartPageToken', result)
        self.assertIn('changes', result)
        self.assertIsInstance(result['changes'], list)

    def test_valid_with_all_parameters(self):
        """Test changes.list with all valid parameters."""
        result = list_changes(
            pageToken='1',
            driveId='',
            includeCorpusRemovals=True,
            includeItemsFromAllDrives=True,
            includeRemoved=True,
            includeTeamDriveItems=False,
            pageSize=50,
            restrictToMyDrive=False,
            spaces='drive,photos',
            supportsAllDrives=True,
            supportsTeamDrives=False,
            teamDriveId='',
            includePermissionsForView='',
            includeLabels=''
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['kind'], 'drive#changeList')

    def test_pagination_functionality(self):
        """Test pagination works correctly."""
        # Test first page
        result1 = list_changes(pageToken='1', pageSize=1)
        self.assertEqual(len(result1['changes']), 1)
        self.assertIsNotNone(result1['nextPageToken'])
        
        # Test second page
        result2 = list_changes(pageToken=result1['nextPageToken'], pageSize=1)
        self.assertEqual(len(result2['changes']), 1)

    def test_include_removed_filtering(self):
        """Test includeRemoved parameter filters correctly."""
        # Include removed items
        result_with_removed = list_changes(pageToken='1', includeRemoved=True)
        removed_count_with = sum(1 for change in result_with_removed['changes'] if change.get('removed'))
        
        # Exclude removed items
        result_without_removed = list_changes(pageToken='1', includeRemoved=False)
        removed_count_without = sum(1 for change in result_without_removed['changes'] if change.get('removed'))
        
        self.assertGreater(removed_count_with, removed_count_without)

    def test_drive_id_filtering(self):
        """Test driveId parameter filters correctly."""
        result = list_changes(pageToken='1', driveId='shared_drive_1', supportsAllDrives=True)
        
        for change in result['changes']:
            if 'driveId' in change:
                self.assertEqual(change['driveId'], 'shared_drive_1')

    def test_restrict_to_my_drive(self):
        """Test restrictToMyDrive parameter works correctly."""
        result = list_changes(pageToken='1', restrictToMyDrive=True)
        
        for change in result['changes']:
            # Should not have driveId for My Drive items
            self.assertIsNone(change.get('driveId'))

    # Input validation tests
    def test_pagetoken_validation(self):
        """Test pageToken parameter validation."""
        # Test non-string pageToken
        with self.assertRaisesRegex(ValidationError, "pageToken must be a string"):
            list_changes(pageToken=123)
        
        # Test empty pageToken - should now work by calling getStartPageToken()
        result = list_changes(pageToken='')
        self.assertIsInstance(result, dict)
        self.assertIn('kind', result)
        
        # Test whitespace-only pageToken - should now work by calling getStartPageToken()
        result = list_changes(pageToken='   ')
        self.assertIsInstance(result, dict)
        self.assertIn('kind', result)

    def test_drive_id_validation(self):
        """Test driveId parameter validation."""
        with self.assertRaisesRegex(ValidationError, "driveId must be a string"):
            list_changes(pageToken='1', driveId=123)

    def test_boolean_parameters_validation(self):
        """Test validation of boolean parameters."""
        boolean_params = [
            'includeCorpusRemovals', 'includeItemsFromAllDrives', 'includeRemoved',
            'includeTeamDriveItems', 'restrictToMyDrive', 'supportsAllDrives',
            'supportsTeamDrives'
        ]
        
        for param in boolean_params:
            with self.assertRaisesRegex(ValidationError, f"{param} must be a boolean"):
                kwargs = {param: "not_a_boolean"}
                list_changes(pageToken='1', **kwargs)

    def test_page_size_validation(self):
        """Test pageSize parameter validation."""
        # Test non-integer pageSize
        with self.assertRaisesRegex(ValidationError, "pageSize must be an integer"):
            list_changes(pageToken='1', pageSize='100')
        
        # Test pageSize too small
        with self.assertRaisesRegex(ValidationError, "pageSize must be between 1 and 1000"):
            list_changes(pageToken='1', pageSize=0)
        
        # Test pageSize too large
        with self.assertRaisesRegex(ValidationError, "pageSize must be between 1 and 1000"):
            list_changes(pageToken='1', pageSize=1001)

    def test_string_parameters_validation(self):
        """Test validation of string parameters."""
        string_params = ['spaces', 'teamDriveId', 'includePermissionsForView', 'includeLabels']
        
        for param in string_params:
            with self.assertRaisesRegex(ValidationError, f"{param} must be a string"):
                kwargs = {param: 123}
                list_changes(pageToken='1', **kwargs)

    def test_spaces_validation(self):
        """Test spaces parameter validation."""
        # Test invalid space
        with self.assertRaisesRegex(ValidationError, "Invalid space 'invalid'"):
            list_changes(pageToken='1', spaces='drive,invalid')
        
        # Test valid spaces
        result = list_changes(pageToken='1', spaces='drive,appDataFolder,photos')
        self.assertIsInstance(result, dict)

    def test_include_permissions_for_view_validation(self):
        """Test includePermissionsForView parameter validation."""
        # Test invalid value
        with self.assertRaisesRegex(ValidationError, "includePermissionsForView only supports 'published'"):
            list_changes(pageToken='1', includePermissionsForView='invalid')
        
        # Test valid value
        result = list_changes(pageToken='1', includePermissionsForView='published')
        self.assertIsInstance(result, dict)

    def test_drive_id_constraints(self):
        """Test driveId constraints."""
        # Test empty driveId after stripping
        with self.assertRaisesRegex(ValidationError, "driveId cannot be empty"):
            list_changes(pageToken='1', driveId='   ')
        
        # Test driveId without supportsAllDrives
        with self.assertRaisesRegex(InvalidRequestError, "supportsAllDrives must be set to True"):
            list_changes(pageToken='1', driveId='drive123', supportsAllDrives=False)

    def test_conflicting_parameters(self):
        """Test conflicting parameter combinations."""
        # Test restrictToMyDrive with driveId
        with self.assertRaisesRegex(InvalidRequestError, "restrictToMyDrive cannot be used together"):
            list_changes(pageToken='1', restrictToMyDrive=True, driveId='drive123', supportsAllDrives=True)
        
        # Test restrictToMyDrive with teamDriveId (need to set supportsAllDrives since teamDriveId gets converted to driveId)
        with self.assertRaisesRegex(InvalidRequestError, "restrictToMyDrive cannot be used together"):
            list_changes(pageToken='1', restrictToMyDrive=True, teamDriveId='drive123', supportsAllDrives=True)

    def test_deprecated_parameters_warnings(self):
        """Test that deprecated parameters generate warnings."""
        # Test supportsTeamDrives warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            list_changes(pageToken='1', supportsTeamDrives=True)
            self.assertTrue(any("supportsTeamDrives" in str(warning.message) for warning in w))
        
        # Test includeTeamDriveItems warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            list_changes(pageToken='1', includeTeamDriveItems=True)
            self.assertTrue(any("includeTeamDriveItems" in str(warning.message) for warning in w))
        
        # Test teamDriveId warning (need to set supportsAllDrives since teamDriveId gets converted to driveId)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            list_changes(pageToken='1', teamDriveId='drive123', supportsAllDrives=True)
            self.assertTrue(any("teamDriveId" in str(warning.message) for warning in w))

    def test_conflicting_drive_ids(self):
        """Test conflicting driveId and teamDriveId values."""
        with self.assertRaisesRegex(InvalidRequestError, "Conflicting drive IDs"):
            list_changes(pageToken='1', driveId='drive1', teamDriveId='drive2')

    def test_invalid_page_token_format(self):
        """Test invalid page token format."""
        with self.assertRaisesRegex(InvalidRequestError, "Invalid page token format"):
            list_changes(pageToken='invalid_token')

    def test_new_start_page_token_generation(self):
        """Test that newStartPageToken is generated correctly."""
        result = list_changes(pageToken='1')
        
        self.assertIn('newStartPageToken', result)
        self.assertIsInstance(result['newStartPageToken'], str)
        self.assertNotEqual(result['newStartPageToken'], '1')

    def test_return_structure(self):
        """Test the structure of the returned dictionary."""
        result = list_changes(pageToken='1')
        
        # Check top-level keys
        required_keys = ['kind', 'nextPageToken', 'newStartPageToken', 'changes']
        for key in required_keys:
            self.assertIn(key, result)
        
        # Check kind value
        self.assertEqual(result['kind'], 'drive#changeList')
        
        # Check changes structure
        self.assertIsInstance(result['changes'], list)
        for change in result['changes']:
            self.assertIsInstance(change, dict)
            self.assertIn('kind', change)


if __name__ == '__main__':
    unittest.main() 