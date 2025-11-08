import unittest
import sys
import os
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import send_customer_notification


class TestSendCustomerNotificationErrors(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()

    def tearDown(self):
        reset_db()

    def test_send_notification_missing_account_id(self):
        """Test sending a notification with a missing accountId."""
        # Pydantic validation is done on the model, so we can't easily use assert_error_behavior
        # as it is not catching the PydanticValidationError directly from the function call
        with self.assertRaises(TypeError):
            send_customer_notification(message="Test message")

if __name__ == '__main__':
    unittest.main()

