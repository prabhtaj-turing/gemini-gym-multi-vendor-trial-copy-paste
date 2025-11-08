import unittest
import sys
import os
import datetime
from unittest.mock import patch
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import get_service_activation_status


class TestGetServiceActivationStatus(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        DB['orderDetails']['ORD-405060'] = {
            "order_id": "ORD-405060",
            "account_id": "ACC-102030",
            "service_type": "INTERNET",
            "service_identifier_for_activation": "AA:BB:CC:11:22:33",
            "service_activation_status": "PENDING_SELF_ACTIVATION"
        }

    def tearDown(self):
        reset_db()

    def test_get_status_success(self):
        """Test retrieving activation status successfully."""
        service_identifier = DB['orderDetails']['ORD-405060']['service_identifier_for_activation']
        result = get_service_activation_status(service_identifier)

        self.assertIn('activationAttemptId', result)
        self.assertEqual(result['activationAttemptId'], service_identifier)
        self.assertIn('status', result)
        self.assertEqual(result['status'], DB['orderDetails']['ORD-405060']['service_activation_status'])
        self.assertIn('timestamp', result)

    def test_get_status_not_found(self):
        """Test retrieving status for a non-existent activation attempt."""
        self.assert_error_behavior(
            get_service_activation_status,
            custom_errors.ActivationAttemptNotFoundError,
            "No activation attempt found for activationAttemptIdOrServiceIdentifier: NON_EXISTENT_ID",
            None,
            "NON_EXISTENT_ID"
        )

    def test_input_validation_empty_identifier(self):
        """Test input validation for an empty identifier."""
        self.assert_error_behavior(
            get_service_activation_status,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )
    
    def test_timestamp_format_in_status_check(self):
        """Test that the timestamp in the status check result is in the correct ISO format."""
        service_identifier = DB['orderDetails']['ORD-405060']['service_identifier_for_activation']
        result = get_service_activation_status(service_identifier)

        self.assertIn('timestamp', result)
        try:
            datetime.datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            self.fail("Timestamp is not in a valid ISO 8601 format.")


if __name__ == '__main__':
    unittest.main()