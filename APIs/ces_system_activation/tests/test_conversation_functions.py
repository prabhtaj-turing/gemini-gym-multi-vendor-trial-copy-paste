import unittest
import sys
import os
import json
from pydantic import ValidationError as PydanticValidationError

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler

from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db

from APIs.ces_system_activation.SimulationEngine.custom_errors import ValidationError

from APIs.ces_system_activation.ces_system_activation import (
    escalate,
    fail,
    cancel
)

class TestCESConversationFunctions(BaseTestCaseWithErrorHandler):
    """
    Test suite for ces_system_activation conversation management functions: escalate, fail, cancel.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        reset_db()

    def tearDown(self):
        """Clean up after each test method."""
        reset_db()

    # Tests for escalate
    def test_escalate_success(self):
        """
        Test successful escalation of conversation.
        """
        result = escalate("User is frustrated and requests to speak to a manager")

        self.assertIsInstance(result, dict)
        self.assertEqual(result['action'], 'escalate')
        self.assertEqual(result['reason'], 'User is frustrated and requests to speak to a manager')
        self.assertEqual(result['status'], 'You will be connected to a human agent shortly.')

        # Check that the reason was stored in DB
        self.assertEqual(DB['_end_of_conversation_status']['escalate'],
                        'User is frustrated and requests to speak to a manager')

    def test_escalate_invalid_reason_empty_string(self):
        """
        Test escalate with empty reason string.
        """
        self.assert_error_behavior(
            escalate,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    def test_escalate_invalid_reason_whitespace_only(self):
        """
        Test escalate with whitespace-only reason.
        """
        self.assert_error_behavior(
            escalate,
            PydanticValidationError,
            "reason cannot be empty",
            None,
            "   \n\t  "
        )

    def test_escalate_invalid_reason_none(self):
        """
        Test escalate with None reason.
        """
        self.assert_error_behavior(
            escalate,
            PydanticValidationError,
            "Input should be a valid string",
            None,
            None
        )

    def test_escalate_reason_stored_in_db(self):
        """
        Test that escalate reason is properly stored in database.
        """
        test_reason = "Complex technical issue requiring human expertise"
        escalate(test_reason)

        self.assertIn('_end_of_conversation_status', DB)
        self.assertEqual(DB['_end_of_conversation_status']['escalate'], test_reason)

    # Tests for fail
    def test_fail_success(self):
        """
        Test successful failure of conversation.
        """
        result = fail("Unable to understand user request after multiple attempts")

        self.assertIsInstance(result, dict)
        self.assertEqual(result['action'], 'fail')
        self.assertEqual(result['reason'], 'Unable to understand user request after multiple attempts')
        self.assertEqual(result['status'],
                        "I'm sorry, I'm unable to help with that at the moment. Please try again later.")

        # Check that the reason was stored in DB
        self.assertEqual(DB['_end_of_conversation_status']['fail'],
                        'Unable to understand user request after multiple attempts')

    def test_fail_invalid_reason_empty_string(self):
        """
        Test fail with empty reason string.
        """
        self.assert_error_behavior(
            fail,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    def test_fail_invalid_reason_whitespace_only(self):
        """
        Test fail with whitespace-only reason.
        """
        self.assert_error_behavior(
            fail,
            PydanticValidationError,
            "reason cannot be empty",
            None,
            "   \n\t  "
        )

    def test_fail_invalid_reason_none(self):
        """
        Test fail with None reason.
        """
        self.assert_error_behavior(
            fail,
            PydanticValidationError,
            "Input should be a valid string",
            None,
            None
        )

    def test_fail_reason_stored_in_db(self):
        """
        Test that fail reason is properly stored in database.
        """
        test_reason = "User request is outside the scope of available functions"
        fail(test_reason)

        self.assertIn('_end_of_conversation_status', DB)
        self.assertEqual(DB['_end_of_conversation_status']['fail'], test_reason)

    # Tests for cancel
    def test_cancel_success(self):
        """
        Test successful cancellation of conversation.
        """
        result = cancel("User decided they don't want to proceed with the request")

        self.assertIsInstance(result, dict)
        self.assertEqual(result['action'], 'cancel')
        self.assertEqual(result['reason'], "User decided they don't want to proceed with the request")
        self.assertEqual(result['status'], 'Okay, I have canceled this request.')

        # Check that the reason was stored in DB
        self.assertEqual(DB['_end_of_conversation_status']['cancel'],
                        "User decided they don't want to proceed with the request")

    def test_cancel_invalid_reason_empty_string(self):
        """
        Test cancel with empty reason string.
        """
        self.assert_error_behavior(
            cancel,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    def test_cancel_invalid_reason_whitespace_only(self):
        """
        Test cancel with whitespace-only reason.
        """
        self.assert_error_behavior(
            cancel,
            PydanticValidationError,
            "reason cannot be empty",
            None,
            "   \n\t  "
        )

    def test_cancel_invalid_reason_none(self):
        """
        Test cancel with None reason.
        """
        self.assert_error_behavior(
            cancel,
            PydanticValidationError,
            "Input should be a valid string",
            None,
            None
        )

    def test_cancel_reason_stored_in_db(self):
        """
        Test that cancel reason is properly stored in database.
        """
        test_reason = "User changed their mind about the service request"
        cancel(test_reason)

        self.assertIn('_end_of_conversation_status', DB)
        self.assertEqual(DB['_end_of_conversation_status']['cancel'], test_reason)

    # Tests for conversation state management
    def test_conversation_state_isolation(self):
        """
        Test that different conversation actions don't interfere with each other.
        """
        # Test that escalate, fail, and cancel can be called independently
        escalate("Test escalate reason")
        fail("Test fail reason")
        cancel("Test cancel reason")

        self.assertEqual(DB['_end_of_conversation_status']['escalate'], "Test escalate reason")
        self.assertEqual(DB['_end_of_conversation_status']['fail'], "Test fail reason")
        self.assertEqual(DB['_end_of_conversation_status']['cancel'], "Test cancel reason")

    def test_conversation_state_persistence(self):
        """
        Test that conversation state persists across function calls.
        """
        escalate("First escalate reason")

        # Call escalate again with different reason
        escalate("Second escalate reason")

        # Should store the latest reason
        self.assertEqual(DB['_end_of_conversation_status']['escalate'], "Second escalate reason")

    def test_conversation_functions_return_consistent_format(self):
        """
        Test that all conversation functions return the same dictionary format.
        """
        functions_and_reasons = [
            (escalate, "escalate", "Test escalate"),
            (fail, "fail", "Test fail"),
            (cancel, "cancel", "Test cancel")
        ]

        for func, expected_action, reason in functions_and_reasons:
            with self.subTest(function=func.__name__):
                result = func(reason)

                self.assertIsInstance(result, dict)
                self.assertIn('action', result)
                self.assertIn('reason', result)
                self.assertIn('status', result)
                self.assertEqual(result['action'], expected_action)
                self.assertEqual(result['reason'], reason)

if __name__ == '__main__':
    unittest.main()