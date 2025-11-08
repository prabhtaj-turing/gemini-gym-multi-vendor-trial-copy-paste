"""
Test file for the stop_channel_watch function.

This module contains focused tests for the stop function in the Channels module.
"""
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (DB, stop_channel_watch)
from gdrive.SimulationEngine.utils import _ensure_user, _ensure_channels
from gdrive.SimulationEngine.custom_errors import ValidationError, ChannelNotFoundError


class TestChannelsStop(BaseTestCaseWithErrorHandler):
    """Test class for the stop_channel_watch function."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset DB to a clean state
        DB.clear()
        DB.update({
            'users': {
                'me': {
                    'about': {
                        'kind': 'drive#about',
                        'storageQuota': {
                            'limit': '107374182400',
                            'usageInDrive': '0',
                            'usageInDriveTrash': '0', 
                            'usage': '0'
                        },
                        'user': {
                            'displayName': 'Test User',
                            'kind': 'drive#user',
                            'me': True,
                            'permissionId': 'test-user-1234',
                            'emailAddress': 'test@example.com'
                        }
                    },
                    'files': {},
                    'drives': {},
                    'comments': {},
                    'replies': {},
                    'labels': {},
                    'accessproposals': {},
                    'apps': {},
                    'channels': {
                        'channel_1': {
                            'id': 'channel_1',
                            'resourceId': 'file_123',
                            'type': 'web_hook',
                            'address': 'https://example.com/webhook1'
                        },
                        'channel_2': {
                            'id': 'channel_2',
                            'resourceId': 'file_456',
                            'type': 'web_hook',
                            'address': 'https://example.com/webhook2'
                        }
                    },
                    'changes': {'startPageToken': '1', 'changes': []},
                    'counters': {
                        'file': 0,
                        'drive': 0,
                        'comment': 0,
                        'reply': 0,
                        'label': 0,
                        'accessproposal': 0,
                        'revision': 0,
                        'change_token': 0
                    }
                }
            }
        })
        
        # Ensure user structure is properly initialized
        _ensure_user('me')
        _ensure_channels('me')
    
    def test_stop_valid_channel(self):
        """Test stopping a valid channel."""
        # Verify channel exists before stopping
        self.assertIn('channel_1', DB['users']['me']['channels'])
        
        # Stop the channel
        stop_channel_watch({'id': 'channel_1'})
        
        # Verify channel was removed
        self.assertNotIn('channel_1', DB['users']['me']['channels'])
        # Verify other channels remain
        self.assertIn('channel_2', DB['users']['me']['channels'])
    
    def test_stop_with_none_resource(self):
        """Test stopping with None resource parameter."""
        initial_channels = dict(DB['users']['me']['channels'])
        
        # Should not raise error and not affect channels
        stop_channel_watch(None)
        
        # Verify no channels were affected
        self.assertEqual(DB['users']['me']['channels'], initial_channels)
    
    def test_stop_with_empty_dict(self):
        """Test stopping with empty dictionary."""
        initial_channels = dict(DB['users']['me']['channels'])
        
        # Should not raise error and not affect channels
        stop_channel_watch({})
        
        # Verify no channels were affected
        self.assertEqual(DB['users']['me']['channels'], initial_channels)
    
    def test_stop_with_empty_channel_id(self):
        """Test stopping with empty channel ID."""
        initial_channels = dict(DB['users']['me']['channels'])
        
        # Should not raise error and not affect channels
        stop_channel_watch({'id': ''})
        
        # Verify no channels were affected
        self.assertEqual(DB['users']['me']['channels'], initial_channels)
    
    def test_stop_nonexistent_channel(self):
        """Test stopping a channel that doesn't exist."""
        with self.assertRaises(ChannelNotFoundError) as context:
            stop_channel_watch({'id': 'nonexistent_channel'})
        
        self.assertIn("Channel 'nonexistent_channel' not found", str(context.exception))
    
    def test_stop_with_invalid_channel_id_type(self):
        """Test stopping with invalid channel ID type."""
        with self.assertRaises(ValidationError) as context:
            stop_channel_watch({'id': 123})
        
        self.assertIn("Channel validation failed", str(context.exception))
    
    def test_stop_with_invalid_data_type(self):
        """Test stopping with invalid data in resource."""
        with self.assertRaises(ValidationError) as context:
            stop_channel_watch({
                'id': 'channel_1',
                'payload': 'not_boolean'  # Should be boolean
            })
        
        self.assertIn("Channel validation failed", str(context.exception))
    
    def test_stop_with_full_resource_data(self):
        """Test stopping with complete channel resource data."""
        # Verify channel exists
        self.assertIn('channel_1', DB['users']['me']['channels'])
        
        # Stop with full resource data
        stop_channel_watch({
            'id': 'channel_1',
            'resourceId': 'file_123',
            'resourceUri': 'https://drive.googleapis.com/drive/v3/files/file_123',
            'token': 'test_token',
            'expiration': '2025-12-31T23:59:59Z',
            'type': 'web_hook',
            'address': 'https://example.com/webhook',
            'payload': True
        })
        
        # Verify channel was removed
        self.assertNotIn('channel_1', DB['users']['me']['channels'])


if __name__ == '__main__':
    unittest.main() 