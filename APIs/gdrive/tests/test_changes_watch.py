"""
Test cases for the Changes.watch function in the Google Drive API simulation.

This module contains comprehensive tests for input validation, edge cases,
and functionality of the changes.watch method.
"""

import unittest
import warnings
from unittest.mock import patch
from .. import watch_changes
from gdrive.SimulationEngine.db import DB
from gdrive.SimulationEngine.custom_errors import ValidationError, InvalidRequestError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestChangesWatchFunction(BaseTestCaseWithErrorHandler):
    """Test cases for the Changes.watch function."""

    def setUp(self):
        """Set up test data before each test."""
        super().setUp()
        
        # Initialize test user data
        DB['users']['me']['changes'] = {
            'startPageToken': '5',
            'changes': []
        }
        DB['users']['me']['channels'] = {}

    def test_valid_minimal_request(self):
        """Test changes.watch with minimal valid parameters."""
        resource = {
            'id': 'test_channel_1',
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(pageToken='1', resource=resource)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['kind'], 'api#channel')
        self.assertEqual(result['id'], 'test_channel_1')
        self.assertEqual(result['address'], 'https://example.com/webhook')
        self.assertIn('resourceId', result)
        self.assertIn('resourceUri', result)
        self.assertIn('expiration', result)
        self.assertIn('watchConfig', result)

    def test_valid_with_all_parameters(self):
        """Test changes.watch with all valid parameters."""
        resource = {
            'id': 'test_channel_2',
            'type': 'web_hook',
            'address': 'https://example.com/webhook',
            'token': 'auth_token_123',
            'expiration': '2024-12-31T23:59:59.999Z',
            'payload': True,
            'params': {'custom': 'value'}
        }
        
        result = watch_changes(
            pageToken='1',
            resource=resource,
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
        self.assertEqual(result['kind'], 'api#channel')
        self.assertEqual(result['token'], 'auth_token_123')
        self.assertEqual(result['expiration'], '2024-12-31T23:59:59.999Z')
        self.assertIn('watchConfig', result)

    def test_auto_generated_channel_id(self):
        """Test channel ID generation when not provided."""
        resource = {
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(pageToken='1', resource=resource)
        
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertTrue(result['id'].startswith('channel_'))

    def test_none_resource_parameter(self):
        """Test with resource=None (should require address)."""
        with self.assertRaisesRegex(ValidationError, "Channel address is required"):
            watch_changes(pageToken='1', resource=None)

    def test_channel_stored_in_database(self):
        """Test that the channel is properly stored in the database."""
        resource = {
            'id': 'stored_channel',
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(pageToken='1', resource=resource)
        
        # Check channel is stored in DB
        self.assertIn('stored_channel', DB['users']['me']['channels'])
        stored_channel = DB['users']['me']['channels']['stored_channel']
        self.assertEqual(stored_channel['id'], 'stored_channel')
        self.assertEqual(stored_channel['address'], 'https://example.com/webhook')

    # Input validation tests
    def test_pagetoken_validation(self):
        """Test pageToken parameter validation."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test non-string pageToken
        with self.assertRaisesRegex(ValidationError, "pageToken must be a string"):
            watch_changes(pageToken=123, resource=resource)
        
        # Test empty pageToken - should now work by calling getStartPageToken()
        result = watch_changes(pageToken='', resource=resource)
        self.assertIsInstance(result, dict)
        self.assertIn('kind', result)
        
        # Test whitespace-only pageToken - should now work by calling getStartPageToken()
        result = watch_changes(pageToken='   ', resource=resource)
        self.assertIsInstance(result, dict)
        self.assertIn('kind', result)

    def test_resource_validation(self):
        """Test resource parameter validation."""
        # Test non-dict resource
        with self.assertRaisesRegex(ValidationError, "resource must be a dictionary"):
            watch_changes(pageToken='1', resource="not_a_dict")

    def test_channel_id_validation(self):
        """Test channel ID validation."""
        # Test empty channel ID - should auto-generate
        resource = {'id': '', 'address': 'https://example.com/webhook'}
        result = watch_changes(pageToken='1', resource=resource)
        self.assertTrue(result['id'].startswith('channel_'))
        
        # Test whitespace-only channel ID
        resource = {'id': '   ', 'address': 'https://example.com/webhook'}
        with self.assertRaisesRegex(ValidationError, "Channel ID must be a non-empty string"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test non-string channel ID
        resource = {'id': 123, 'address': 'https://example.com/webhook'}
        with self.assertRaisesRegex(ValidationError, "Channel ID must be a non-empty string"):
            watch_changes(pageToken='1', resource=resource)

    def test_channel_type_validation(self):
        """Test channel type validation."""
        # Test empty channel type
        resource = {'id': 'test', 'type': '', 'address': 'https://example.com/webhook'}
        with self.assertRaisesRegex(ValidationError, "Channel type must be a non-empty string"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test non-string channel type
        resource = {'id': 'test', 'type': 123, 'address': 'https://example.com/webhook'}
        with self.assertRaisesRegex(ValidationError, "Channel type must be a non-empty string"):
            watch_changes(pageToken='1', resource=resource)

    def test_channel_address_validation(self):
        """Test channel address validation."""
        # Test missing address
        resource = {'id': 'test'}
        with self.assertRaisesRegex(ValidationError, "Channel address is required"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test empty address
        resource = {'id': 'test', 'address': ''}
        with self.assertRaisesRegex(ValidationError, "Channel address must be a non-empty string"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test non-string address
        resource = {'id': 'test', 'address': 123}
        with self.assertRaisesRegex(ValidationError, "Channel address must be a non-empty string"):
            watch_changes(pageToken='1', resource=resource)

    def test_channel_optional_properties_validation(self):
        """Test validation of optional channel properties."""
        base_resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test non-string token
        resource = {**base_resource, 'token': 123}
        with self.assertRaisesRegex(ValidationError, "Channel token must be a string"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test non-string expiration
        resource = {**base_resource, 'expiration': 123}
        with self.assertRaisesRegex(ValidationError, "Channel expiration must be a string"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test non-boolean payload
        resource = {**base_resource, 'payload': 'true'}
        with self.assertRaisesRegex(ValidationError, "Channel payload must be a boolean"):
            watch_changes(pageToken='1', resource=resource)
        
        # Test non-dict params
        resource = {**base_resource, 'params': 'not_a_dict'}
        with self.assertRaisesRegex(ValidationError, "Channel params must be a dictionary"):
            watch_changes(pageToken='1', resource=resource)

    def test_boolean_parameters_validation(self):
        """Test validation of boolean parameters."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        boolean_params = [
            'includeCorpusRemovals', 'includeItemsFromAllDrives', 'includeRemoved',
            'includeTeamDriveItems', 'restrictToMyDrive', 'supportsAllDrives',
            'supportsTeamDrives'
        ]
        
        for param in boolean_params:
            with self.assertRaisesRegex(ValidationError, f"{param} must be a boolean"):
                kwargs = {param: "not_a_boolean"}
                watch_changes(pageToken='1', resource=resource, **kwargs)

    def test_page_size_validation(self):
        """Test pageSize parameter validation."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test non-integer pageSize
        with self.assertRaisesRegex(ValidationError, "pageSize must be an integer"):
            watch_changes(pageToken='1', resource=resource, pageSize='100')
        
        # Test pageSize too small
        with self.assertRaisesRegex(ValidationError, "pageSize must be between 1 and 1000"):
            watch_changes(pageToken='1', resource=resource, pageSize=0)
        
        # Test pageSize too large
        with self.assertRaisesRegex(ValidationError, "pageSize must be between 1 and 1000"):
            watch_changes(pageToken='1', resource=resource, pageSize=1001)

    def test_string_parameters_validation(self):
        """Test validation of string parameters."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        string_params = ['driveId', 'spaces', 'teamDriveId', 'includePermissionsForView', 'includeLabels']
        
        for param in string_params:
            with self.assertRaisesRegex(ValidationError, f"{param} must be a string"):
                kwargs = {param: 123}
                watch_changes(pageToken='1', resource=resource, **kwargs)

    def test_spaces_validation(self):
        """Test spaces parameter validation."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test invalid space
        with self.assertRaisesRegex(ValidationError, "Invalid space 'invalid'"):
            watch_changes(pageToken='1', resource=resource, spaces='drive,invalid')
        
        # Test valid spaces
        result = watch_changes(pageToken='1', resource=resource, spaces='drive,appDataFolder,photos')
        self.assertIsInstance(result, dict)

    def test_include_permissions_for_view_validation(self):
        """Test includePermissionsForView parameter validation."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test invalid value
        with self.assertRaisesRegex(ValidationError, "includePermissionsForView only supports 'published'"):
            watch_changes(pageToken='1', resource=resource, includePermissionsForView='invalid')
        
        # Test valid value
        result = watch_changes(pageToken='1', resource=resource, includePermissionsForView='published')
        self.assertIsInstance(result, dict)

    def test_drive_id_constraints(self):
        """Test driveId constraints."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test empty driveId after stripping
        with self.assertRaisesRegex(ValidationError, "driveId cannot be empty"):
            watch_changes(pageToken='1', resource=resource, driveId='   ')
        
        # Test driveId without supportsAllDrives
        with self.assertRaisesRegex(InvalidRequestError, "supportsAllDrives must be set to True"):
            watch_changes(pageToken='1', resource=resource, driveId='drive123', supportsAllDrives=False)

    def test_conflicting_parameters(self):
        """Test conflicting parameter combinations."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test restrictToMyDrive with driveId
        with self.assertRaisesRegex(InvalidRequestError, "restrictToMyDrive cannot be used together"):
            watch_changes(pageToken='1', resource=resource, restrictToMyDrive=True, driveId='drive123', supportsAllDrives=True)
        
        # Test restrictToMyDrive with teamDriveId
        with self.assertRaisesRegex(InvalidRequestError, "restrictToMyDrive cannot be used together"):
            watch_changes(pageToken='1', resource=resource, restrictToMyDrive=True, teamDriveId='drive123', supportsAllDrives=True)

    def test_deprecated_parameters_warnings(self):
        """Test that deprecated parameters generate warnings."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        
        # Test supportsTeamDrives warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            watch_changes(pageToken='1', resource=resource, supportsTeamDrives=True)
            self.assertTrue(any("supportsTeamDrives" in str(warning.message) for warning in w))
        
        # Test includeTeamDriveItems warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            watch_changes(pageToken='1', resource=resource, includeTeamDriveItems=True)
            self.assertTrue(any("includeTeamDriveItems" in str(warning.message) for warning in w))
        
        # Test teamDriveId warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            watch_changes(pageToken='1', resource=resource, teamDriveId='drive123', supportsAllDrives=True)
            self.assertTrue(any("teamDriveId" in str(warning.message) for warning in w))

    def test_conflicting_drive_ids(self):
        """Test conflicting driveId and teamDriveId values."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        with self.assertRaisesRegex(InvalidRequestError, "Conflicting drive IDs"):
            watch_changes(pageToken='1', resource=resource, driveId='drive1', teamDriveId='drive2')

    def test_invalid_page_token_format(self):
        """Test invalid page token format."""
        resource = {'id': 'test', 'address': 'https://example.com/webhook'}
        with self.assertRaisesRegex(InvalidRequestError, "Invalid page token format"):
            watch_changes(pageToken='invalid_token', resource=resource)

    def test_watch_config_creation(self):
        """Test that watch configuration is properly created."""
        resource = {
            'id': 'config_test',
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(
            pageToken='1',
            resource=resource,
            driveId='shared_drive_1',
            includeRemoved=False,
            pageSize=50,
            supportsAllDrives=True
        )
        
        self.assertIn('watchConfig', result)
        config = result['watchConfig']
        self.assertEqual(config['pageToken'], '1')
        self.assertEqual(config['driveId'], 'shared_drive_1')
        self.assertEqual(config['includeRemoved'], False)
        self.assertEqual(config['pageSize'], 50)
        self.assertEqual(config['supportsAllDrives'], True)

    def test_default_values(self):
        """Test default values are properly applied."""
        resource = {
            'id': 'defaults_test',
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(pageToken='1', resource=resource)
        
        # Test default channel type
        self.assertEqual(result['type'], 'web_hook')
        
        # Test default payload
        self.assertEqual(result['payload'], True)
        
        # Test default params
        self.assertEqual(result['params'], {})
        
        # Test that expiration is set
        self.assertIsNotNone(result['expiration'])

    def test_resource_uri_handling(self):
        """Test that resourceUri is properly handled from input or defaults to empty."""
        # Test with provided resourceUri
        resource = {
            'id': 'uri_test',
            'address': 'https://example.com/webhook',
            'resourceUri': 'https://custom.example.com/resource'
        }
        result = watch_changes(pageToken='123', resource=resource)
        self.assertEqual(result['resourceUri'], 'https://custom.example.com/resource')
        
        # Test without resourceUri (should default to empty)
        resource = {
            'id': 'uri_test2',
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(pageToken='123', resource=resource)
        self.assertEqual(result['resourceUri'], '')

    def test_return_structure(self):
        """Test the structure of the returned dictionary."""
        resource = {
            'id': 'structure_test',
            'address': 'https://example.com/webhook'
        }
        result = watch_changes(pageToken='1', resource=resource)
        
        # Check required keys
        required_keys = [
            'kind', 'id', 'resourceId', 'resourceUri', 'token', 'expiration',
            'type', 'address', 'payload', 'params', 'watchConfig'
        ]
        for key in required_keys:
            self.assertIn(key, result)
        
        # Check kind value
        self.assertEqual(result['kind'], 'api#channel')


if __name__ == '__main__':
    unittest.main() 