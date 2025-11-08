"""
Test suite for CES System Activation Infobot Configuration Integration

Tests the integration of the new configuration system with ces_system_activation service.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import json
import base64
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine import utils
from APIs.ces_system_activation.SimulationEngine.utils import (
    update_infobot_config,
    reset_infobot_config,
    get_infobot_config
)


class TestInfobotConfigIntegration(BaseTestCaseWithErrorHandler):
    """Test suite for Infobot configuration integration with utils"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset configuration to defaults before each test
        reset_infobot_config()

    def tearDown(self):
        """Clean up after each test method."""
        # Reset configuration to defaults after each test
        reset_infobot_config()

    # Tests for _get_token with new config system
    def test_get_token_missing_service_account_info(self):
        """Test _get_token raises error when service account info is not set."""
        # Config is already reset in setUp, service_account_info is empty by default
        
        self.assert_error_behavior(
            utils._get_token,
            ValueError,
            'Service account info must be set before uploading the image.'
        )

    @patch('APIs.ces_system_activation.SimulationEngine.utils.service_account')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.Session')
    def test_get_token_success_with_config(self, mock_session_class, mock_service_account):
        """Test _get_token successfully returns token with configured service account."""
        # Setup mock service account info
        service_account_info = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        # Encode and set in config
        encoded_info = base64.b64encode(
            json.dumps(service_account_info).encode('utf-8')
        ).decode('utf-8')
        update_infobot_config(service_account_info=encoded_info)
        
        # Mock credentials and session
        mock_credentials = MagicMock()
        mock_credentials.token = 'test-token-123'
        mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Test the function
        result = utils._get_token()
        
        # Verify results
        self.assertEqual(result, 'test-token-123')
        config = get_infobot_config()
        mock_service_account.Credentials.from_service_account_info.assert_called_once_with(
            service_account_info, scopes=config.scopes
        )
        mock_credentials.refresh.assert_called_once()
        mock_session_class.assert_called_once()

    def test_get_token_invalid_base64(self):
        """Test _get_token handles invalid base64 encoding gracefully."""
        update_infobot_config(service_account_info='invalid-base64!')
        
        self.assert_error_behavior(
            utils._get_token,
            Exception,
            "Invalid base64-encoded string: number of data characters (13) cannot be 1 more than a multiple of 4"
        )

    def test_get_token_invalid_json(self):
        """Test _get_token handles invalid JSON in service account info."""
        invalid_json = base64.b64encode(b'invalid-json').decode('utf-8')
        update_infobot_config(service_account_info=invalid_json)
        
        self.assert_error_behavior(
            utils._get_token,
            json.JSONDecodeError,
            "Expecting value: line 1 column 1 (char 0)"
        )

    # Tests for _query_infobot with new config system
    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.post')
    def test_query_infobot_success(self, mock_post, mock_get_token):
        """Test _query_infobot successfully queries the service."""
        # Setup mocks
        mock_get_token.return_value = 'test-token'
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': {
                'answer': 'Test response',
                'snippets': []
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test the function with a configured tool
        result = utils._query_infobot('test query', 'activation_guides')
        
        # Verify results
        self.assertEqual(result, {'answer': 'Test response', 'snippets': []})
        mock_get_token.assert_called_once()
        mock_post.assert_called_once()

    def test_query_infobot_missing_tool_resource(self):
        """Test _query_infobot raises error for unconfigured tool."""
        with self.assertRaises(ValueError) as context:
            utils._query_infobot('test query', 'nonexistent_tool')
        
        self.assertIn("Tool resource 'nonexistent_tool' not configured", str(context.exception))

    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.post')
    def test_query_infobot_http_error(self, mock_post, mock_get_token):
        """Test _query_infobot handles HTTP errors gracefully."""
        # Setup mocks
        mock_get_token.return_value = 'test-token'
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('404 Not Found')
        mock_post.return_value = mock_response
        
        # Test the function
        self.assert_error_behavior(
            utils._query_infobot,
            requests.exceptions.HTTPError,
            "404 Not Found",
            None,
            'test query',
            'activation_guides'
        )

    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.post')
    def test_query_infobot_connection_error(self, mock_post, mock_get_token):
        """Test _query_infobot handles connection errors gracefully."""
        # Setup mocks
        mock_get_token.return_value = 'test-token'
        mock_post.side_effect = requests.exceptions.ConnectionError('Connection failed')
        
        # Test the function
        self.assert_error_behavior(
            utils._query_infobot,
            requests.exceptions.ConnectionError,
            "Connection failed",
            None,
            'test query',
            'activation_guides'
        )

    # Tests for query_activation_guides_infobot
    @patch('APIs.ces_system_activation.SimulationEngine.utils._query_infobot')
    def test_query_activation_guides_infobot(self, mock_query_infobot):
        """Test query_activation_guides_infobot calls _query_infobot with correct tool name."""
        expected_response = {'answer': 'Activation guide response'}
        mock_query_infobot.return_value = expected_response
        
        result = utils.query_activation_guides_infobot('How to activate service?')
        
        self.assertEqual(result, expected_response)
        mock_query_infobot.assert_called_once_with(
            'How to activate service?',
            'activation_guides'
        )

    # Tests for query_order_details_infobot
    @patch('APIs.ces_system_activation.SimulationEngine.utils._query_infobot')
    def test_query_order_details_infobot(self, mock_query_infobot):
        """Test query_order_details_infobot calls _query_infobot with correct tool name."""
        expected_response = {'answer': 'Order details response'}
        mock_query_infobot.return_value = expected_response
        
        result = utils.query_order_details_infobot('What is order status?')
        
        self.assertEqual(result, expected_response)
        mock_query_infobot.assert_called_once_with(
            'What is order status?',
            'order_details'
        )

    # Tests for configuration properties
    def test_config_properties_used_in_query(self):
        """Test that configuration properties are correctly used in queries."""
        config = get_infobot_config()
        
        # Verify default config values
        self.assertEqual(config.gcp_project, 'gbot-experimentation')
        self.assertEqual(config.location, 'us-east1')
        self.assertIn('activation_guides', config.tool_resources)
        self.assertIn('order_details', config.tool_resources)
        
        # Verify computed properties
        self.assertIn('projects/', config.parent_resource)
        self.assertIn('locations/', config.parent_resource)
        self.assertIn('apps/', config.parent_resource)
        self.assertIn(config.api_version, config.full_api_endpoint)

    def test_config_update_affects_queries(self):
        """Test that updating configuration affects query behavior."""
        # Update configuration
        update_infobot_config(
            gcp_project='custom-project',
            location='custom-location'
        )
        
        config = get_infobot_config()
        
        # Verify updates
        self.assertEqual(config.gcp_project, 'custom-project')
        self.assertEqual(config.location, 'custom-location')
        
        # Verify computed properties reflect changes
        self.assertIn('custom-project', config.parent_resource)
        self.assertIn('custom-location', config.parent_resource)

    def test_tool_resources_customization(self):
        """Test that tool resources can be customized."""
        # Update tool resources
        custom_tools = {
            'activation_guides': 'custom-activation-id',
            'order_details': 'custom-order-id',
            'new_tool': 'new-tool-id'
        }
        update_infobot_config(tool_resources=custom_tools)
        
        config = get_infobot_config()
        
        # Verify custom tools
        self.assertEqual(config.tool_resources, custom_tools)
        self.assertEqual(config.tool_resources['activation_guides'], 'custom-activation-id')
        self.assertEqual(config.tool_resources['new_tool'], 'new-tool-id')


class TestInfobotConfigDefaults(unittest.TestCase):
    """Test that default configuration values are correct for ces_system_activation"""

    def setUp(self):
        """Set up test fixtures."""
        # Reset to defaults before each test
        reset_infobot_config()

    def tearDown(self):
        """Clean up after test."""
        reset_infobot_config()

    def test_default_tool_resources(self):
        """Test that default tool resources are correctly set."""
        config = get_infobot_config()
        
        self.assertIn('activation_guides', config.tool_resources)
        self.assertIn('order_details', config.tool_resources)
        self.assertEqual(config.tool_resources['activation_guides'], '46f527f8-0509-4e28-9563-db5666e0790b')
        self.assertEqual(config.tool_resources['order_details'], 'c90c11bb-6868-4631-8bf0-7f8b5fe4b92c')

    def test_default_gcp_settings(self):
        """Test that default GCP settings are correct."""
        config = get_infobot_config()
        
        self.assertEqual(config.gcp_project, 'gbot-experimentation')
        self.assertEqual(config.location, 'us-east1')
        self.assertEqual(config.app_id, '78151603-8f03-4385-9c2a-42a2431f04e0')
        self.assertEqual(config.api_version, 'v1beta')
        self.assertEqual(config.api_endpoint, 'https://autopush-ces-googleapis.sandbox.google.com')


if __name__ == '__main__':
    unittest.main()

