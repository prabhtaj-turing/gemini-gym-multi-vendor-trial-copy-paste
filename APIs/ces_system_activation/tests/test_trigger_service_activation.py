import unittest
import sys
import os
import datetime
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import trigger_service_activation


class TestTriggerServiceActivation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        DB['orderDetails']['ORD-405060'] = {
            "order_id": "ORD-405060",
            "account_id": "ACC-102030",
            "service_type": "INTERNET",
            "service_identifier_for_activation": "AA:BB:CC:11:22:33",
            "service_activation_status": "PENDING_SELF_ACTIVATION"
        }
        DB['serviceTypes'] = ['MOBILE', 'INTERNET', 'IOT_DEVICE', 'VOIP']
        # Find an order that is pending self-activation for testing
        self.test_order = next(
            (order for order in DB['orderDetails'].values() if order['service_activation_status'] == 'PENDING_SELF_ACTIVATION'),
            None
        )
        if not self.test_order:
            raise Exception("No suitable test order found in DB for PENDING_SELF_ACTIVATION status.")

    def tearDown(self):
        reset_db()

    def test_trigger_activation_success(self):
        """Test triggering service activation successfully."""
        order_id = self.test_order['order_id']
        service_identifier = self.test_order['service_identifier_for_activation']
        service_type = self.test_order['service_type']

        result = trigger_service_activation(
            orderId=order_id,
            serviceIdentifier=service_identifier,
            serviceType=service_type
        )

        self.assertIn('activationAttemptId', result)
        self.assertEqual(result['activationAttemptId'], service_identifier)
        self.assertEqual(result['status'], 'IN_PROGRESS')
        self.assertIn('timestamp', result)

        # Verify that the order status was updated in the DB
        updated_order = next((order for order in DB['orderDetails'].values() if order['order_id'] == order_id), None)
        self.assertIsNotNone(updated_order)
        self.assertEqual(updated_order['service_activation_status'], 'IN_PROGRESS')

    def test_trigger_activation_invalid_service_type(self):
        """Test triggering activation with an invalid service type."""
        self.assert_error_behavior(
            trigger_service_activation,
            PydanticValidationError,
            "Input should be 'MOBILE', 'INTERNET', 'IOT_DEVICE' or 'VOIP'",
            None,
            orderId=self.test_order['order_id'],
            serviceIdentifier=self.test_order['service_identifier_for_activation'],
            serviceType="INVALID_TYPE"
        )

    def test_trigger_activation_order_not_found(self):
        """Test triggering activation for a non-existent order."""
        self.assert_error_behavior(
            trigger_service_activation,
            ValueError,
            "No viable order found for order: NON_EXISTENT_ORDER, serviceIdentifier: AA:BB:CC:11:22:33,serviceType: INTERNET",
            None,
            orderId="NON_EXISTENT_ORDER",
            serviceIdentifier=self.test_order['service_identifier_for_activation'],
            serviceType=self.test_order['service_type']
        )

    def test_trigger_activation_wrong_status(self):
        """Test triggering activation for an order not in a pending self-activation state."""
        # Manually change the status of the test order
        self.test_order['service_activation_status'] = 'COMPLETED'
        
        with self.assertRaises(ValueError) as context:
            trigger_service_activation(
                orderId=self.test_order['order_id'],
                serviceIdentifier=self.test_order['service_identifier_for_activation'],
                serviceType=self.test_order['service_type']
            )
        self.assertIn('is not in a pending self-activation state', str(context.exception))


if __name__ == '__main__':
    unittest.main()