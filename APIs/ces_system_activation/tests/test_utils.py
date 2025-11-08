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
    get_infobot_config,
    get_conversation_end_status
)
from APIs.ces_system_activation.SimulationEngine.db import DB


class TestCESUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for CES system identification utility functions.
    Tests shared helper functions for formatting, parsing, and error handling.
    
    Note: These tests have been superseded by test_infobot_config_integration.py
    but are kept for backward compatibility.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset configuration before each test
        reset_infobot_config()

    def tearDown(self):
        """Clean up after each test method."""
        # Reset configuration after each test
        reset_infobot_config()

    # Tests for _get_token
    def test_get_token_missing_service_account_info(self):
        """
        Test _get_token raises error when service account info is not set.
        """
        # Config is reset in setUp, service_account_info is empty by default
        
        self.assert_error_behavior(
            utils._get_token,
            ValueError,
            'Service account info must be set before uploading the image.'
        )

    @patch('APIs.ces_system_activation.SimulationEngine.utils.service_account')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.Session')
    def test_get_token_success(self, mock_session_class, mock_service_account):
        """
        Test _get_token successfully returns token with valid service account.
        """
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
        """
        Test _get_token handles invalid base64 encoding gracefully.
        """
        update_infobot_config(service_account_info='invalid-base64!')
        
        self.assert_error_behavior(
            utils._get_token,
            Exception,
            "Invalid base64-encoded string: number of data characters (13) cannot be 1 more than a multiple of 4"
        )

    def test_get_token_invalid_json(self):
        """
        Test _get_token handles invalid JSON in service account info.
        """
        invalid_json = base64.b64encode(b'invalid-json').decode('utf-8')
        update_infobot_config(service_account_info=invalid_json)
        
        self.assert_error_behavior(
            utils._get_token,
            json.JSONDecodeError,
            "Expecting value: line 1 column 1 (char 0)"
        )

    # Tests for _query_infobot
    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.post')
    def test_query_infobot_success(self, mock_post, mock_get_token):
        """
        Test _query_infobot successfully queries the service.
        """
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
        expected_response = {
            'answer': 'Test response',
            'snippets': []
        }
        self.assertEqual(result, expected_response)
        
        # Verify API call
        config = get_infobot_config()
        tool_id = config.tool_resources['activation_guides']
        expected_url = f'{config.full_api_endpoint}:executeTool'
        expected_headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
        }
        expected_data = json.dumps({
            'args': {'query': 'test query'},
            'tool': f'{config.parent_resource}/tools/{tool_id}'
        })
        
        mock_post.assert_called_once_with(
            expected_url,
            headers=expected_headers,
            data=expected_data,
            verify=config.ca_bundle
        )

    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.requests.post')
    def test_query_infobot_http_error(self, mock_post, mock_get_token):
        """
        Test _query_infobot handles HTTP errors gracefully.
        """
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
        """
        Test _query_infobot handles connection errors gracefully.
        """
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
        """
        Test query_activation_guides_infobot calls _query_infobot with correct tool name.
        """
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
        """
        Test query_order_details_infobot calls _query_infobot with correct tool name.
        """
        expected_response = {'answer': 'Order details response'}
        mock_query_infobot.return_value = expected_response
        
        result = utils.query_order_details_infobot('What is order status?')
        
        self.assertEqual(result, expected_response)
        mock_query_infobot.assert_called_once_with(
            'What is order status?',
            'order_details'
        )

    # Deterministic behavior tests
    def test_query_functions_deterministic(self):
        """
        Test that query functions are deterministic - same input gives same behavior.
        """
        with patch('APIs.ces_system_activation.SimulationEngine.utils._query_infobot') as mock_query:
            mock_query.return_value = {'answer': 'consistent response'}
            
            # Test activation guides
            result1 = utils.query_activation_guides_infobot('test query')
            result2 = utils.query_activation_guides_infobot('test query')
            self.assertEqual(result1, result2)
            
            # Test order details
            result3 = utils.query_order_details_infobot('test query')
            result4 = utils.query_order_details_infobot('test query')
            self.assertEqual(result3, result4)

    # Constants validation tests
    def test_constants_are_strings(self):
        """
        Test that all configuration values are properly defined as strings.
        """
        config = get_infobot_config()
        self.assertIsInstance(config.gcp_project, str)
        self.assertIsInstance(config.location, str)
        self.assertIsInstance(config.app_id, str)
        self.assertIsInstance(config.api_version, str)
        self.assertIsInstance(config.api_endpoint, str)
        self.assertIsInstance(config.ca_bundle, str)
        self.assertIsInstance(config.tool_resources, dict)

    def test_constants_not_empty(self):
        """
        Test that all configuration values are not empty.
        """
        config = get_infobot_config()
        self.assertTrue(config.gcp_project.strip())
        self.assertTrue(config.location.strip())
        self.assertTrue(config.app_id.strip())
        self.assertTrue(config.api_version.strip())
        self.assertTrue(config.api_endpoint.strip())
        self.assertTrue(config.ca_bundle.strip())
        # Tool resources should have default values
        self.assertIn('activation_guides', config.tool_resources)
        self.assertIn('order_details', config.tool_resources)

    def test_parent_resource_format(self):
        """
        Test that parent_resource is formatted correctly.
        """
        config = get_infobot_config()
        expected_format = f'projects/{config.gcp_project}/locations/{config.location}/apps/{config.app_id}'
        self.assertEqual(config.parent_resource, expected_format)

    def test_api_endpoint_format(self):
        """
        Test that full_api_endpoint is formatted correctly.
        """
        config = get_infobot_config()
        expected_format = f'{config.api_endpoint}/{config.api_version}/{config.parent_resource}'
        self.assertEqual(config.full_api_endpoint, expected_format)
    
    def test_get_conversation_end_status_all(self):
        """Test get_conversation_end_status returns all statuses when no function_name provided."""
        # Set up test data
        test_statuses = {
            "escalate": "test escalation reason",
            "fail": "test failure reason",
            "cancel": "test cancel reason"
        }
        original = DB.get("_end_of_conversation_status", {})
        DB["_end_of_conversation_status"] = test_statuses
        
        result = get_conversation_end_status()
        self.assertEqual(result, test_statuses)
        self.assertEqual(result["escalate"], "test escalation reason")
        self.assertEqual(result["fail"], "test failure reason")
        self.assertEqual(result["cancel"], "test cancel reason")
        
        # Clean up
        DB["_end_of_conversation_status"] = original
    
    def test_get_conversation_end_status_specific_function(self):
        """Test get_conversation_end_status returns specific function status."""
        # Set up test data
        original = DB.get("_end_of_conversation_status", {})
        DB["_end_of_conversation_status"] = {
            "escalate": "escalation reason",
            "fail": "failure reason",
            "cancel": None
        }
        
        # Test getting specific function statuses
        self.assertEqual(get_conversation_end_status("escalate"), "escalation reason")
        self.assertEqual(get_conversation_end_status("fail"), "failure reason")
        self.assertIsNone(get_conversation_end_status("cancel"))
        
        # Clean up
        DB["_end_of_conversation_status"] = original
    
    def test_get_conversation_end_status_missing_key(self):
        """Test get_conversation_end_status when DB key doesn't exist."""
        # Remove the key temporarily
        original = DB.pop("_end_of_conversation_status", None)
        
        result = get_conversation_end_status()
        self.assertIsNone(result)
        
        # Restore
        if original:
            DB["_end_of_conversation_status"] = original


if __name__ == '__main__':
    unittest.main()
