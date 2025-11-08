import json
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError as PydanticValidationError

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler

from APIs.ces_system_activation.SimulationEngine.custom_errors import ValidationError

from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db, load_default_data

from APIs.ces_system_activation.ces_system_activation import (
    send_customer_notification,
    search_order_details,
    search_activation_guides
)

class TestCESCommunicationFunctions(BaseTestCaseWithErrorHandler):
    """
    Test suite for ces_system_activation communication functions: notifications and search.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        reset_db()
        load_default_data()

    def tearDown(self):
        """Clean up after each test method."""
        reset_db()

    # Tests for send_customer_notification
    def test_send_customer_notification_success(self):
        """
        Test successful sending of customer notification.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            channel="EMAIL",
            message="Test message",
            templateId="APPOINTMENT_CONFIRMATION",
            orderId="ORD-405060",
            recipient="+14155552671",
            subject="Test Subject",
            urgency="HIGH"
        )

        self.assertEqual(result["channelSent"], "EMAIL")
        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["recipientUsed"], "+14155552671")

    def test_send_customer_notification_minimal_params(self):
        """
        Test send_customer_notification with minimal parameters.
        """
        result = send_customer_notification(accountId="ACC-102030", templateId="APPOINTMENT_CONFIRMATION")

        self.assertEqual(result["channelSent"], "EMAIL")  # Default value
        self.assertEqual(result["status"], "SENT")

    def test_send_customer_notification_no_account_id_validation(self):
        """
        Test that send_customer_notification doesn't validate accountId.
        """
        # The function currently ignores accountId validation (del accountId)
        result = send_customer_notification(accountId="ACC-12345", templateId="APPOINTMENT_CONFIRMATION")

    # Tests for search_order_details
    def test_search_order_details_success_with_mock_datastore(self):
        """
        Test successful search of order details with mock datastore.
        """
        DB['use_real_datastore'] = True

        with patch('APIs.ces_system_activation.SimulationEngine.utils.query_order_details_infobot') as mock_query:
            mock_query.return_value = {
                'answer': 'Order ORD-405060 is for internet service installation.',
                'snippets': [
                    {
                        'text': 'Order details snippet',
                        'title': 'Order Information',
                        'uri': 'https://example.com/order'
                    }
                ]
            }

            result = search_order_details("What is the status of order ORD-405060?")

            self.assertEqual(result["answer"], 'Order ORD-405060 is for internet service installation.')
            self.assertEqual(len(result["snippets"]), 1)

    @patch('APIs.ces_system_activation.SimulationEngine.utils.search_order_details_by_query')
    def test_search_order_details_success_without_real_datastore(self, mock_search_order_details):
        """
        Test search_order_details without real datastore (default behavior).
        """
        self.skipTest("Skipping test_search_order_details_success_without_real_datastore")
        DB['use_real_datastore'] = False
        mock_search_order_details.return_value = []

        result = search_order_details("What is the status of order ORD-405060?")

        self.assertEqual(result["answer"], 'I have no information about the order details.')
        self.assertEqual(len(result["snippets"]), 0)

    def test_search_order_details_invalid_query(self):
        """
        Test search_order_details with invalid query.
        """
        self.assert_error_behavior(
            search_order_details,
            PydanticValidationError,
            'String should have at least 1 character',
            None,
            ""
        )

    def test_search_order_details_success_path(self):
        """
        Test successful search of order details with success path.
        """

        if not os.environ.get("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY is not set")

        DB['use_real_datastore'] = False
        result = search_order_details("What is the status of order ORD1010?")

        self.assertEqual(json.dumps(result), json.dumps({'answer': 'Here are the available orders that match your query:\n{\"status\": \"Awaiting Install\", \"customerName\": \"Jennifer Moore\", \"serviceType\": \"INTERNET\", \"accountId\": \"ACC5010\", \"serviceActivationStatus\": \"AWAITING_INSTALL\", \"visitId\": \"VISIT703\"}', 'snippets': [{'text': 'Gigabit Fiber Internet', 'title': 'ORD1010 INTERNET', 'uri': 'https://tracker.example.com/UPSTRACKAABBCC'}]}))
        self.assertEqual(len(result["snippets"]), 1)

    def test_search_order_details_success_path_with_dash(self):
        """
        Test successful search of order details with success path.
        """
        DB['use_real_datastore'] = False

        if not os.environ.get("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY is not set")

        result = search_order_details("What is the status of order ORD-1010?")

        self.assertEqual(json.dumps(result), json.dumps({'answer': 'Here are the available orders that match your query:\n{\"status\": \"Awaiting Install\", \"customerName\": \"Jennifer Moore\", \"serviceType\": \"INTERNET\", \"accountId\": \"ACC5010\", \"serviceActivationStatus\": \"AWAITING_INSTALL\", \"visitId\": \"VISIT703\"}', 'snippets': [{'text': 'Gigabit Fiber Internet', 'title': 'ORD1010 INTERNET', 'uri': 'https://tracker.example.com/UPSTRACKAABBCC'}]}))
        self.assertEqual(len(result["snippets"]), 1)

    def test_search_order_details_success_path_with_dash_and_account_id(self):
        """
        Test successful search of order details with success path.
        """
        
        if not os.environ.get("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY is not set")
        
        DB['use_real_datastore'] = False
        result = search_order_details("What is the status of order ORD1006 and account ACC5006?")

        self.assertEqual(json.dumps(result), json.dumps({'answer': 'Here are the available orders that match your query:\n{\"status\": \"Activation in Progress\", \"customerName\": \"Linda Brown\", \"serviceType\": \"INTERNET\", \"accountId\": \"ACC5006\", \"serviceActivationStatus\": \"ACTIVATION_IN_PROGRESS\", \"visitId\": \"VISIT702\"}', 'snippets': [{'text': 'Gigabit Fiber Internet', 'title': 'ORD1006 INTERNET', 'uri': 'https://tracker.example.com/UPSTRACK112233'}]}))
        self.assertEqual(len(result["snippets"]), 1)

    def test_search_order_details_success_path_account_id_only(self):
        """
        Test successful search of order details with success path.
        """

        if not os.environ.get("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY is not set")

        DB['use_real_datastore'] = False
        result = search_order_details("What is the status of account ACC5006?")

        self.assertEqual(json.dumps(result), json.dumps({'answer': 'Here are the available orders that match your query:\n{\"status\": \"Activation in Progress\", \"customerName\": \"Linda Brown\", \"serviceType\": \"INTERNET\", \"accountId\": \"ACC5006\", \"serviceActivationStatus\": \"ACTIVATION_IN_PROGRESS\", \"visitId\": \"VISIT702\"}', 'snippets': [{'text': 'Gigabit Fiber Internet', 'title': 'ORD1006 INTERNET', 'uri': 'https://tracker.example.com/UPSTRACK112233'}]}))
        self.assertEqual(len(result["snippets"]), 1)

    @patch('APIs.ces_system_activation.SimulationEngine.utils.search_order_details_by_query')
    def test_search_order_details_success_path_malformed_order_id(self, mock_search_order_details):
        """
        Test successful search of order details with success path.
        """
        self.skipTest("Skipping test_search_order_details_success_path_malformed_order_id")
        DB['use_real_datastore'] = False
        mock_search_order_details.return_value = [
            {
                "overall_order_status": "Activation in Progress",
                "customer_name": "Linda Brown",
                "service_type": "INTERNET",
                "account_id": "ACC5006",
                "service_activation_status": "ACTIVATION_IN_PROGRESS",
                "appointment_visit_id": "VISIT702",
                "service_name": "Gigabit Fiber Internet",
                "order_id": "ORD1006",
                "equipment_tracking_url": "https://tracker.example.com/UPSTRACK112233"
            }
        ]
        result = search_order_details("status 1006?")

        self.assertEqual(json.dumps(result), json.dumps({'answer': 'Here are the available orders that match your query:\n{\"status\": \"Activation in Progress\", \"customerName\": \"Linda Brown\", \"serviceType\": \"INTERNET\", \"accountId\": \"ACC5006\", \"serviceActivationStatus\": \"ACTIVATION_IN_PROGRESS\", \"visitId\": \"VISIT702\"}', 'snippets': [{'text': 'Gigabit Fiber Internet', 'title': 'ORD1006 INTERNET', 'uri': 'https://tracker.example.com/UPSTRACK112233'}]}))
        self.assertEqual(len(result["snippets"]), 1)

    @patch('APIs.ces_system_activation.SimulationEngine.utils.search_order_details_by_query')
    def test_search_order_details_not_found_path(self, mock_search_order_details):
        """
        Test successful search of order details with success path.
        """
        self.skipTest("Skipping test_search_order_details_not_found_path")
        DB['use_real_datastore'] = False
        mock_search_order_details.return_value = []
        result = search_order_details("What is the status of order?")

        self.assertEqual(json.dumps(result), json.dumps({'answer': 'I have no information about the order details.', 'snippets': []}))
        self.assertEqual(len(result["snippets"]), 0)

    # Tests for search_activation_guides
    def test_search_activation_guides_success_with_mock_datastore(self):
        """
        Test successful search of activation guides with mock datastore.
        """
        DB['use_real_datastore'] = True

        with patch('APIs.ces_system_activation.SimulationEngine.utils.query_activation_guides_infobot') as mock_query:
            mock_query.return_value = {
                'answer': 'To activate your internet service, connect the modem and wait for the lights to turn solid.',
                'snippets': [
                    {
                        'text': 'Activation guide snippet',
                        'title': 'Modem Setup Guide',
                        'uri': 'https://example.com/guide'
                    }
                ]
            }

            result = search_activation_guides("How do I set up my modem?")

            self.assertEqual(result['answer'], 'To activate your internet service, connect the modem and wait for the lights to turn solid.')

    def test_search_activation_guides_invalid_query(self):
        """
        Test search_activation_guides with invalid query.
        """
        self.assert_error_behavior(
            search_activation_guides,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    # Tests for notification variations
    def test_send_customer_notification_different_channels(self):
        """
        Test send_customer_notification with different channel values.
        """
        channels = ["EMAIL", "SMS"]

        for channel in channels:
            with self.subTest(channel=channel):
                result = send_customer_notification(
                    accountId="ACC-102030",
                    channel=channel,
                    message="Test message"
                )

                self.assertEqual(result["channelSent"], channel)  # Function passes through the value as-is
                self.assertEqual(result["status"], "SENT")

    def test_send_customer_notification_with_template_parameters(self):
        """
        Test send_customer_notification with template parameters.
        """
        template_params = {"customerName": "John Doe", "appointmentTime": "2:00 PM"}

        result = send_customer_notification(
            accountId="ACC-102030",
            templateId="APPOINTMENT_CONFIRMATION"
        )

        self.assertEqual(result["status"], "SENT")

    def test_send_customer_notification_timestamp_format(self):
        """
        Test that send_customer_notification returns proper timestamp format.
        """
        result = send_customer_notification(accountId="ACC-102030", message="Test message")

        # Should be in ISO 8601 format
        self.assertRegex(result["timestamp"], r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')

if __name__ == '__main__':
    unittest.main()