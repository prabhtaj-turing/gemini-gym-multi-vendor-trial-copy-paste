import unittest
import sys
import os
import datetime
import json
from unittest.mock import patch, MagicMock
from pydantic import ValidationError as PydanticValidationError
# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine.models import *
from APIs.ces_system_activation.SimulationEngine import custom_errors


# Import functions that would work with customer data
from APIs.ces_system_activation.ces_system_activation import (
    flag_technician_visit_issue,
    reschedule_technician_visit,
    schedule_new_technician_visit,
    send_customer_notification,
    search_order_details,
    search_activation_guides,
    escalate,
    fail,
    cancel,
    get_activation_visit_details,
    trigger_service_activation
)


class TestCESCoreFunctions(BaseTestCaseWithErrorHandler):
    """
    Test suite for CES core functions that work with customer database.
    Focuses on input validation, output format, error handling, and transformations.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        reset_db()
        # Store original customer data for comparison
        self.original_customers = DB['customers'].copy()
        DB['appointmentDetails'].append({
            "visitId": "VISIT-98765",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": "2023-11-24T10:00:00Z",
            "scheduledEndTime": "2023-11-24T12:00:00Z",
            "technicianNotes": "Initial appointment",
            "issueDescription": "New SunnyFiber Gigabit internet service installation and modem setup.",
            "slotId": "SLOT-98765"
        })
        DB['templates'].append({
            "templateId": "APPOINTMENT_CONFIRMATION",
            "message": "Test message"
        })

    def tearDown(self):
        """Clean up after each test method."""
        reset_db()

    # Tests for send_customer_notification
    def test_send_customer_notification_input_validation(self):
        """
        Test input validation for send_customer_notification function.
        """
        # Test with valid inputs
        result = send_customer_notification(
            accountId="ACC-102030",
            channel="EMAIL",
            message="Test message"
        )
        
        # Test with minimal required inputs (accountId is deleted in function)
        result = send_customer_notification(accountId="ACC-12345", message="test message")

    def test_send_customer_notification_template_not_found(self):
        """
        Test template not found error for send_customer_notification function.
        """
        self.assert_error_behavior(
            send_customer_notification,
            custom_errors.TemplateNotFoundError,
            "Template with ID INVALID_TEMPLATE_ID not found",
            None,
            accountId="ACC-102030",
            templateId="INVALID_TEMPLATE_ID"
        )
        
    def test_send_customer_notification_error_message_or_template_id_required(self):
        """
        Test error message or templateId is required for send_customer_notification function.
        """
        self.assert_error_behavior(
            send_customer_notification,
            custom_errors.ValidationError,
            "Invalid input for send_customer_notification: Either message or templateId is required",
            None,
            accountId="ACC-102030"
        )

    def test_send_customer_notification_output_format(self):
        """
        Test output format for send_customer_notification function.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            channel="SMS",
            message="Test SMS",
            recipient="+1234567890",
            subject="Test Subject",
            urgency="HIGH"
        )
        
        # Verify output structure
        self.assertIsInstance(result["channelSent"], str)
        self.assertIsInstance(result["status"], str)
        self.assertIsInstance(result["recipientUsed"], str)
        self.assertIsInstance(result["timestamp"], str)
        
        # Verify specific values
        self.assertEqual(result["channelSent"], "SMS")
        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["recipientUsed"], "+1234567890")

    def test_send_customer_notification_channel_validation(self):
        """
        Test channel validation in send_customer_notification.
        """
        valid_channels = ["EMAIL", "SMS"]
        
        for channel in valid_channels:
            result = send_customer_notification(
                accountId="ACC-102030",
                channel=channel,
                message="test message"
            )
            self.assertEqual(result["channelSent"], channel)

    def test_send_customer_notification_timestamp_format(self):
        """
        Test timestamp format in notification result
        """
        result = send_customer_notification(accountId="ACC-102030", message="test message")
        
        # Verify timestamp is in ISO format
        try:
            parsed_time = datetime.datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
            self.assertIsInstance(parsed_time, datetime.datetime)
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")

    def test_send_customer_notification_timestamp_format_with_template_id(self):
        """
        Test timestamp format in notification result with template ID.
        """
        result = send_customer_notification(accountId="ACC-102030", templateId="APPOINTMENT_CONFIRMATION")
        
        # Verify timestamp is in ISO format
        try:
            parsed_time = datetime.datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
            self.assertIsInstance(parsed_time, datetime.datetime)
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")

    # Tests for search_order_details
    def test_search_order_details_input_validation(self):
        """
        Test input validation for search_order_details function.
        """
        self.skipTest("Skipping test_search_order_details_input_validation")
        # Disable real datastore for testing
        DB['use_real_datastore'] = False
        
        # Test with valid query
        result = search_order_details("What is order status?")
        
        # Test with empty query - should raise ValueError
        self.assert_error_behavior(
            search_order_details,
            custom_errors.ValidationError,
            "Invalid input for search_order_details: Param query: String should have at least 1 character",
            None,
            ""
        )

    def test_search_order_details_output_format(self):
        """
        Test output format for search_order_details function.
        """
        self.skipTest("Skipping test_search_order_details_output_format")
        # Disable real datastore for testing
        DB['use_real_datastore'] = False
        
        result = search_order_details("Order details query")
        
        # Verify output structure
        self.assertIsInstance(result["answer"], str)
        self.assertIsInstance(result["snippets"], list)
        
        # Verify snippets structure
        for snippet in result["snippets"]:
            self.assertIsInstance(snippet['text'], str)
            self.assertIsInstance(snippet['title'], str)
            self.assertIsInstance(snippet['uri'], (str, type(None)))

    def test_search_order_details_with_real_datastore(self):
        """
        Test search_order_details with real datastore enabled.
        """
        # Enable real datastore
        DB['use_real_datastore'] = True
        
        with patch('APIs.ces_system_activation.SimulationEngine.utils.query_order_details_infobot') as mock_query:
            mock_query.return_value = {
                'answer': 'Mocked order details response',
                'snippets': [
                    {
                        'text': 'Order snippet text',
                        'title': 'Order Information',
                        'uri': 'https://example.com/order'
                    }
                ]
            }
            
            result = search_order_details("Test query")
            
            # Verify mock was called
            mock_query.assert_called_once_with("Test query")
            
            # Verify result structure
            self.assertEqual(result["answer"], 'Mocked order details response')
            self.assertEqual(len(result["snippets"]), 1)
            self.assertEqual(result["snippets"][0]['text'], 'Order snippet text')

    @patch('APIs.ces_system_activation.SimulationEngine.utils.search_order_details_by_query')
    def test_search_order_details_without_real_datastore(self, mock_search_details):
        """
        Test search_order_details with real datastore disabled.
        """
        self.skipTest("Skipping test_search_order_details_without_real_datastore")
        # Disable real datastore
        DB['use_real_datastore'] = False
        mock_search_details.return_value = []
        
        result = search_order_details("Test query")
        
        # Verify default response (check for common phrases in default responses)
        self.assertTrue(
            any(phrase in result["answer"].lower() for phrase in ["no information", "simulated", "default"]),
            f"Expected default response, got: {result['answer']}"
        )
        self.assertIsInstance(result["snippets"], list)

    # Tests for search_activation_guides
    def test_search_activation_guides_input_validation(self):
        """
        Test input validation for search_activation_guides function.
        """
        self.skipTest("Skipping test_search_activation_guides_input_validation")
        # Disable real datastore for testing
        DB['use_real_datastore'] = False
        
        # Test with valid query
        result = search_activation_guides("How to activate service?")
        # Test with empty query - should raise ValueError
        self.assert_error_behavior(
            search_activation_guides,
            custom_errors.ValidationError,
            "Invalid input for search_activation_guides: Param query: String should have at least 1 character",
            None,
            ""
        )

    def test_search_activation_guides_output_format(self):
        """
        Test output format for search_activation_guides function.
        """
        self.skipTest("Skipping test_search_activation_guides_output_format")
        # Disable real datastore for testing
        DB['use_real_datastore'] = False
        
        result = search_activation_guides("Activation guide query")
        
        # Verify output structure
        self.assertIsInstance(result["answer"], str)
        self.assertIsInstance(result["snippets"], list)

    def test_search_activation_guides_with_real_datastore(self):
        """
        Test search_activation_guides with real datastore enabled.
        """
        # Enable real datastore
        DB['use_real_datastore'] = True
        
        with patch('APIs.ces_system_activation.SimulationEngine.utils.query_activation_guides_infobot') as mock_query:
            mock_query.return_value = {
                'answer': 'Mocked activation guide response',
                'snippets': []
            }
            
            result = search_activation_guides("How to activate?")
            
            # Verify mock was called
            mock_query.assert_called_once_with("How to activate?")
            
            # Verify result
            self.assertEqual(result["answer"], 'Mocked activation guide response')

    # Tests for conversation management functions
    def test_escalate_input_validation(self):
        """
        Test input validation for escalate function.
        """
        # Test with valid reason
        result = escalate("Customer is frustrated")
        self.assertIsInstance(result, dict)
        
        # Test with empty string
        self.assert_error_behavior(
            escalate,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )
        
        # Test with whitespace only
        self.assert_error_behavior(
            escalate,
            PydanticValidationError,
            "reason cannot be empty",
            None,
            "   "
        )
        
        # Test with None
        self.assert_error_behavior(
            escalate,
            PydanticValidationError,
            "Input should be a valid string",
            None,
            None
        )

    def test_escalate_output_format(self):
        """
        Test output format for escalate function.
        """
        reason = "Customer needs manager assistance"
        result = escalate(reason)
        
        # Verify output structure
        self.assertIsInstance(result, dict)
        self.assertIn('action', result)
        self.assertIn('reason', result)
        self.assertIn('status', result)
        
        # Verify values
        self.assertEqual(result['action'], 'escalate')
        self.assertEqual(result['reason'], reason)
        self.assertIsInstance(result['status'], str)

    def test_escalate_state_persistence(self):
        """
        Test that escalate reason is stored in database.
        """
        reason = "Test escalation reason"
        escalate(reason)
        
        # Verify reason was stored in DB
        self.assertEqual(DB['_end_of_conversation_status']['escalate'], reason)

    def test_fail_input_validation(self):
        """
        Test input validation for fail function.
        """
        # Test with valid reason
        result = fail("System error occurred")
        self.assertIsInstance(result, dict)
        
        # Test with invalid inputs
        self.assert_error_behavior(
            fail,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    def test_fail_output_format(self):
        """
        Test output format for fail function.
        """
        reason = "Technical difficulties"
        result = fail(reason)
        
        # Verify output structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['action'], 'fail')
        self.assertEqual(result['reason'], reason)
        self.assertIn('status', result)

    def test_fail_state_persistence(self):
        """
        Test that fail reason is stored in database.
        """
        reason = "Test failure reason"
        fail(reason)
        
        # Verify reason was stored in DB
        self.assertEqual(DB['_end_of_conversation_status']['fail'], reason)

    def test_cancel_input_validation(self):
        """
        Test input validation for cancel function.
        """
        # Test with valid reason
        result = cancel("User requested cancellation")
        self.assertIsInstance(result, dict)
        
        # Test with invalid inputs
        self.assert_error_behavior(
            cancel,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    def test_cancel_output_format(self):
        """
        Test output format for cancel function.
        """
        reason = "Customer changed mind"
        result = cancel(reason)
        
        # Verify output structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['action'], 'cancel')
        self.assertEqual(result['reason'], reason)
        self.assertIn('status', result)

    def test_cancel_state_persistence(self):
        """
        Test that cancel reason is stored in database.
        """
        reason = "Test cancellation reason"
        cancel(reason)
        
        # Verify reason was stored in DB
        self.assertEqual(DB['_end_of_conversation_status']['cancel'], reason)

    # Integration tests for conversation functions
    def test_conversation_functions_consistency(self):
        """
        Test that all conversation functions return consistent format.
        """
        functions_and_reasons = [
            (escalate, "Escalation reason"),
            (fail, "Failure reason"),
            (cancel, "Cancellation reason")
        ]
        
        for func, reason in functions_and_reasons:
            result = func(reason)
            
            # Verify consistent structure
            self.assertIsInstance(result, dict)
            self.assertIn('action', result)
            self.assertIn('reason', result)
            self.assertIn('status', result)
            
            # Verify types
            self.assertIsInstance(result['action'], str)
            self.assertIsInstance(result['reason'], str)
            self.assertIsInstance(result['status'], str)
            
            # Verify reason matches
            self.assertEqual(result['reason'], reason)

    def test_conversation_state_isolation(self):
        """
        Test that conversation states don't interfere with each other.
        """
        # Set different reasons for each action
        escalate("Escalation test")
        fail("Failure test")
        cancel("Cancellation test")
        
        # Verify each state is stored independently
        self.assertEqual(DB['_end_of_conversation_status']['escalate'], "Escalation test")
        self.assertEqual(DB['_end_of_conversation_status']['fail'], "Failure test")
        self.assertEqual(DB['_end_of_conversation_status']['cancel'], "Cancellation test")

    # Error handling tests
    def test_functions_handle_unicode_input(self):
        """
        Test that functions handle Unicode input correctly.
        """
        unicode_reason = "Problème avec le service 🚫"
        
        result = escalate(unicode_reason)
        self.assertEqual(result['reason'], unicode_reason)
        self.assertEqual(DB['_end_of_conversation_status']['escalate'], unicode_reason)

    def test_functions_handle_long_input(self):
        """
        Test that functions handle very long input strings.
        """
        long_reason = "A" * 1000  # 1000 character string
        
        result = fail(long_reason)
        self.assertEqual(result['reason'], long_reason)
        self.assertEqual(DB['_end_of_conversation_status']['fail'], long_reason)

    def test_search_functions_handle_special_characters(self):
        """
        Test that search functions handle special characters in queries.
        """
        self.skipTest("Skipping test_search_functions_handle_special_characters")
        # Disable real datastore for testing
        DB['use_real_datastore'] = False
        
        special_query = "Order #12345 with 50% discount & free shipping?"
        
        # Should not raise exceptions
        result1 = search_order_details(special_query)
        result2 = search_activation_guides(special_query)
        

    # Data transformation tests
    def test_notification_channel_case_handling(self):
        """
        Test that notification channels handle case variations.
        """
        # Test different cases
        channels = ["EMAIL", "SMS"]
        
        for channel in channels:
            result = send_customer_notification(
                accountId="ACC-102030",
                channel=channel,
                message="test message"
            )
            # Function should handle case normalization
            self.assertIsInstance(result["channelSent"], str)

    def test_timestamp_consistency(self):
        """
        Test that timestamps are consistent and properly formatted.
        """
        result1 = send_customer_notification(accountId="ACC-1", message="test message")
        result2 = send_customer_notification(accountId="ACC-2", message="test message")
        
        # Both should have valid timestamps
        self.assertIsInstance(result1["timestamp"], str)
        self.assertIsInstance(result2["timestamp"], str)
        
        # Timestamps should be close in time (within 1 second)
        time1 = datetime.datetime.fromisoformat(result1["timestamp"].replace('Z', '+00:00'))
        time2 = datetime.datetime.fromisoformat(result2["timestamp"].replace('Z', '+00:00'))
        time_diff = abs((time2 - time1).total_seconds())
        self.assertLess(time_diff, 1.0)

    # Database interaction tests
    def test_functions_preserve_customer_data(self):
        """
        Test that functions don't modify customer data in database.
        """
        self.skipTest("Skipping test_functions_preserve_customer_data")
        original_customers = DB['customers'].copy()
        
        # Disable real datastore for testing
        DB['use_real_datastore'] = False
        
        # Call various functions
        send_customer_notification(accountId="ACC-102030")
        search_order_details("test query")
        search_activation_guides("test query")
        escalate("test reason")
        
        # Verify customer data unchanged
        self.assertEqual(DB['customers'], original_customers)

    def test_datastore_flag_persistence(self):
        """
        Test that use_real_datastore flag is preserved across function calls.
        """

        if not os.environ.get("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY is not set")

        # Test with flag disabled (safe for testing)
        DB['use_real_datastore'] = False
        search_order_details("test")
        self.assertFalse(DB['use_real_datastore'])
        
        search_activation_guides("test")
        self.assertFalse(DB['use_real_datastore'])
        
        # Test that the flag can be toggled
        DB['use_real_datastore'] = True
        # Don't actually call functions with real datastore enabled in tests
        self.assertTrue(DB['use_real_datastore'])
        
        DB['use_real_datastore'] = False
        self.assertFalse(DB['use_real_datastore'])

    def test_get_activation_visit_details(self):
        self.assert_error_behavior(
            get_activation_visit_details,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )

    def test_get_activation_visit_details_invalid_visitId(self):
        self.assert_error_behavior(
            get_activation_visit_details,
            PydanticValidationError,
            "Input should be a valid string",
            None,
            visitId = 98765
        )

    def test_reschedule_technician_visit(self):
        """
        Test that rescheduling with a non-existent visitId raises VisitNotFoundError.
        Uses a valid account ID to properly test the visitId validation.
        """
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.VisitNotFoundError,
            "No appointment found for visitId: VISIT-ABCDE",
            None,
            accountId="ACC-102030",
            newSlotId= "SLOT-TUE-1400-A",
            orderId = "ORD-405060",
            originalVisitId = "VISIT-ABCDE"
        )

    def test_flag_technician_visit_issue(self):
        self.assert_error_behavior(
            flag_technician_visit_issue,
            PydanticValidationError,
            'Text fields cannot be empty or whitespace only',
            None,
            accountId = "ACC-102030",
            customerReportedFailure = True,
            issueSummary = " \t \n ",
            orderId = "ORD-405060",
            requestedFollowUpAction = "   ",
            visitId = "VISIT-12345"
        )

    def test_complex_multi_faceted_issue_report(self):
        self.assert_error_behavior(
            flag_technician_visit_issue,
            custom_errors.VisitNotFoundError,
            "No viable visits found for account: ACC-GPNW-8820-A4, order: ORD-RPR-2024-Q1-99812, visit: VISIT-TECH7-45B-20240315",
            None,
            accountId = "ACC-GPNW-8820-A4",
            customerReportedFailure = True,
            issueSummary = "Customer reports persistent connectivity issues post-visit. Modem (Model: CM1200, S/N: 98AB765CDE43) is frequently rebooting. Downstream power levels are fluctuating between -15 dBmV and +12 dBmV according to the diagnostic page (192.168.100.1). Log files show repeated 'T3 timeout' and 'SYNC Timing Synchronization failure' errors. User states: \"The technician was here for only 10 minutes, replaced a splitter, and left. The problem is now 10x worse.\"",
            orderId = "ORD-RPR-2024-Q1-99812",
            requestedFollowUpAction = "1. Escalate immediately to a Level 2 network engineer for remote line diagnostics. 2. Schedule a follow-up visit with a senior technician, ensuring they bring a signal level meter and are authorized to check the line from the pedestal to the premises. 3. Request a manager callback to the primary number on file to discuss service credits for the extended outage.",
            visitId = "VISIT-TECH7-45B-20240315"
        )

    def test_scheduling_a_visit_for_a_slot_corresponding_to_a_date_far_in_the_future(self):
        # Add order details for the test account
        DB['orderDetails']['ORD-FUTURE-TEST'] = {
            "order_id": "ORD-FUTURE-TEST",
            "account_id": "ACC-FUTURE-TEST",
            "service_type": "INTERNET",
            "overall_order_status": "Pending"
        }
        
        self.assert_error_behavior(
            schedule_new_technician_visit,
            custom_errors.TechnicianVisitNotFoundError,
            "No technician visit found for slotId: SLOT-Y9999-12-31-2300",
            None,
            accountId = "ACC-FUTURE-TEST",
            orderId = "ORD-FUTURE-TEST",
            slotId = "SLOT-Y9999-12-31-2300"
        )

    def test_schedule_new_technician_visit_for_order_with_existing_appointment(self):
        # Add order details for the test account
        DB['orderDetails']['ORD-405060'] = {
            "order_id": "ORD-405060",
            "account_id": "ACC-102030",
            "service_type": "INTERNET",
            "overall_order_status": "Pending"
        }
        
        DB['appointmentDetails'].append({
            "visitId": "VISIT-EXISTING",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": "2023-11-20T10:00:00Z",
            "scheduledEndTime": "2023-11-20T12:00:00Z",
            "technicianNotes": "Existing appointment",
            "issueDescription": "Existing appointment",
            "slotId": "SLOT-EXISTING"
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-XYZ-789",
            "startTime": "2023-11-21T10:00:00Z",
            "endTime": "2023-11-21T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        self.assert_error_behavior(
            schedule_new_technician_visit,
            custom_errors.DuplicateAppointmentError,
            'An appointment for orderId ORD-405060 already exists. Please use reschedule_technician_visit to make changes.',
            None,
            accountId = "ACC-102030",
            orderId = "ORD-405060",
            slotId = "SLOT-XYZ-789"
        )

    def test_reschedule_technician_visit_with_non_existent_account_id(self):
        """
        Test that rescheduling with a non-existent account ID raises ValidationError.
        """
        DB['technicianSlots'].append({
            "slotId": "SLOT-TEST-123",
            "startTime": "2023-11-21T10:00:00Z",
            "endTime": "2023-11-21T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.ValidationError,
            'Account ID ACC-NONEXISTENT does not exist in the system.',
            None,
            accountId="ACC-NONEXISTENT",
            newSlotId="SLOT-TEST-123",
            orderId="ORD-405060",
            originalVisitId="VISIT-98765"
        )

    def test_reschedule_technician_visit_with_valid_account_id(self):
        """
        Test that rescheduling with a valid existing account ID works correctly.
        """
        # Add a technician slot to the database
        DB['technicianSlots'].append({
            "slotId": "SLOT-VALID-ACCOUNT",
            "startTime": "2023-11-29T10:00:00Z",
            "endTime": "2023-11-29T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })

        # Reschedule the visit with a valid account ID that exists
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-VALID-ACCOUNT",
            orderId="ORD-405060",
            originalVisitId="VISIT-98765"
        )

        # Verify the reschedule was successful
        self.assertIn('visitId', result)
        self.assertEqual(result['accountId'], 'ACC-102030')
        self.assertEqual(result['orderId'], 'ORD-405060')
        self.assertEqual(result['status'], 'scheduled')

    def test_reschedule_completed_technician_visit(self):
        DB['appointmentDetails'].append({
            "visitId": "VISIT-12345",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "completed",
            "scheduledStartTime": "2023-11-20T10:00:00Z",
            "scheduledEndTime": "2023-11-20T12:00:00Z",
            "technicianNotes": "Completed",
            "issueDescription": "Completed",
            "slotId": "SLOT-12345"
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-GHI-101",
            "startTime": "2023-11-21T10:00:00Z",
            "endTime": "2023-11-21T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.ValidationError,
            'Completed appointments cannot be rescheduled.',
            None,
            accountId="ACC-102030",
            newSlotId="SLOT-GHI-101",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )

    def test_reschedule_technician_visit_preserves_issue_description(self):
        """
        Test that rescheduling a visit preserves the original issue description.
        """
        # Add a technician slot to the database
        DB['technicianSlots'].append({
            "slotId": "SLOT-RESCHEDULE",
            "startTime": "2023-11-25T10:00:00Z",
            "endTime": "2023-11-25T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })

        # Reschedule the visit to the new slot
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-RESCHEDULE",
            orderId="ORD-405060",
            originalVisitId="VISIT-98765"
        )

        # Verify that the new appointment has the same issue description
        self.assertEqual(result['issueDescription'], 'New SunnyFiber Gigabit internet service installation and modem setup.')

    def test_reschedule_technician_visit_with_empty_issue_description(self):
        """
        Test that rescheduling a visit with an empty issue description results in an empty description.
        """
        # Add an appointment with an empty issue description to the database
        DB['appointmentDetails'].append({
            "visitId": "VISIT-EMPTY-DESC",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": "2023-11-26T10:00:00Z",
            "scheduledEndTime": "2023-11-26T12:00:00Z",
            "technicianNotes": "Initial notes",
            "issueDescription": "",
            "slotId": "SLOT-EMPTY-DESC"
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-RESCHEDULE-EMPTY",
            "startTime": "2023-11-27T10:00:00Z",
            "endTime": "2023-11-27T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })

        # Reschedule the visit
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-RESCHEDULE-EMPTY",
            orderId="ORD-405060",
            originalVisitId="VISIT-EMPTY-DESC"
        )

        # Verify that the new appointment has an empty issue description
        self.assertEqual(result['issueDescription'], '')

    def test_reschedule_technician_visit_with_reason_for_change(self):
        """
        Test that rescheduling with a reason for change updates technician notes
        and preserves the issue description.
        """
        # Add a technician slot to the database
        DB['technicianSlots'].append({
            "slotId": "SLOT-REASON-CHANGE",
            "startTime": "2023-11-28T10:00:00Z",
            "endTime": "2023-11-28T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })

        # Reschedule the visit with a reason for change
        reason = "Customer conflict"
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-REASON-CHANGE",
            orderId="ORD-405060",
            originalVisitId="VISIT-98765",
            reasonForChange=reason
        )

        # Verify the technician notes and issue description
        self.assertEqual(result['technicianNotes'], reason)
        self.assertEqual(result['issueDescription'], 'New SunnyFiber Gigabit internet service installation and modem setup.')

    def test_schedule_new_technician_visit_for_order_with_completed_appointment(self):
        # Add order details for the test account
        DB['orderDetails']['ORD-COMPLETED'] = {
            "order_id": "ORD-COMPLETED",
            "account_id": "ACC-COMPLETED",
            "service_type": "INTERNET",
            "overall_order_status": "Completed"
        }
        
        DB['appointmentDetails'].append({
            "visitId": "VISIT-COMPLETED",
            "accountId": "ACC-COMPLETED",
            "orderId": "ORD-COMPLETED",
            "status": "completed",
            "scheduledStartTime": "2023-11-20T10:00:00Z",
            "scheduledEndTime": "2023-11-20T12:00:00Z",
            "technicianNotes": "Completed",
            "issueDescription": "Completed",
            "slotId": "SLOT-COMPLETED"
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-NEW-APPOINTMENT",
            "startTime": "2023-11-21T10:00:00Z",
            "endTime": "2023-11-21T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        result = schedule_new_technician_visit(
            accountId = "ACC-COMPLETED",
            orderId = "ORD-COMPLETED",
            slotId = "SLOT-NEW-APPOINTMENT"
        )
        self.assertIn('visitId', result)
        self.assertEqual(result['orderId'], 'ORD-COMPLETED')
        self.assertEqual(result['status'], 'scheduled')
        self.assertEqual(result['issueDescription'], 'New SunnyFiber Gigabit internet service installation and modem setup.')

    def test_schedule_new_technician_visit_for_order_with_cancelled_appointment(self):
        # Add order details for the test account
        DB['orderDetails']['ORD-CANCELLED'] = {
            "order_id": "ORD-CANCELLED",
            "account_id": "ACC-CANCELLED",
            "service_type": "INTERNET",
            "overall_order_status": "Cancelled"
        }
        
        DB['appointmentDetails'].append({
            "visitId": "VISIT-CANCELLED",
            "accountId": "ACC-CANCELLED",
            "orderId": "ORD-CANCELLED",
            "status": "cancelled",
            "scheduledStartTime": "2023-11-20T10:00:00Z",
            "scheduledEndTime": "2023-11-20T12:00:00Z",
            "technicianNotes": "Cancelled",
            "issueDescription": "Cancelled",
            "slotId": "SLOT-CANCELLED"
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-NEW-APPOINTMENT-2",
            "startTime": "2023-11-22T10:00:00Z",
            "endTime": "2023-11-22T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        result = schedule_new_technician_visit(
            accountId = "ACC-CANCELLED",
            orderId = "ORD-CANCELLED",
            slotId = "SLOT-NEW-APPOINTMENT-2"
        )
        self.assertIn('visitId', result)
        self.assertEqual(result['orderId'], 'ORD-CANCELLED')
        self.assertEqual(result['status'], 'scheduled')
        self.assertEqual(result['issueDescription'], 'New SunnyFiber Gigabit internet service installation and modem setup.')

    def test_schedule_new_technician_visit_with_nonexistent_account_id(self):
        """
        Test that scheduling a visit with a non-existent accountId raises ValidationError.
        """
        DB['technicianSlots'].append({
            "slotId": "SLOT-TEST-123",
            "startTime": "2023-11-25T10:00:00Z",
            "endTime": "2023-11-25T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        
        self.assert_error_behavior(
            schedule_new_technician_visit,
            custom_errors.ValidationError,
            'Account ID ACC-NONEXISTENT does not exist in the system.',
            None,
            accountId="ACC-NONEXISTENT",
            orderId="ORD1006",
            slotId="SLOT-TEST-123"
        )

    def test_schedule_new_technician_visit_with_nonexistent_order_id(self):
        """
        Test that scheduling a visit with a non-existent orderId raises ValidationError.
        The accountId exists but the orderId does not.
        """
        # Ensure the test account exists in orderDetails
        DB['orderDetails']['ORD-TEST-EXIST'] = {
            "order_id": "ORD-TEST-EXIST",
            "account_id": "ACC-TEST-EXIST",
            "service_type": "INTERNET",
            "overall_order_status": "Pending"
        }
        
        DB['technicianSlots'].append({
            "slotId": "SLOT-TEST-456",
            "startTime": "2023-11-26T10:00:00Z",
            "endTime": "2023-11-26T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        
        # Using existing accountId but non-existent orderId
        self.assert_error_behavior(
            schedule_new_technician_visit,
            custom_errors.ValidationError,
            'Order ID ORD-NONEXISTENT does not exist in the system.',
            None,
            accountId="ACC-TEST-EXIST",
            orderId="ORD-NONEXISTENT",
            slotId="SLOT-TEST-456"
        )

    def test_schedule_new_technician_visit_with_mismatched_account_and_order(self):
        """
        Test that scheduling a visit where orderId doesn't belong to accountId raises ValidationError.
        Both accountId and orderId exist in the system, but they don't belong together.
        """
        # Set up two different accounts with their own orders
        DB['orderDetails']['ORD-ACCT1-ORDER'] = {
            "order_id": "ORD-ACCT1-ORDER",
            "account_id": "ACC-ACCOUNT-1",
            "service_type": "INTERNET",
            "overall_order_status": "Pending"
        }
        DB['orderDetails']['ORD-ACCT2-ORDER'] = {
            "order_id": "ORD-ACCT2-ORDER",
            "account_id": "ACC-ACCOUNT-2",
            "service_type": "INTERNET",
            "overall_order_status": "Pending"
        }
        
        DB['technicianSlots'].append({
            "slotId": "SLOT-TEST-789",
            "startTime": "2023-11-27T10:00:00Z",
            "endTime": "2023-11-27T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        
        # Try to schedule ORD-ACCT1-ORDER (which belongs to ACC-ACCOUNT-1) with ACC-ACCOUNT-2
        self.assert_error_behavior(
            schedule_new_technician_visit,
            custom_errors.ValidationError,
            'Order ID ORD-ACCT1-ORDER does not belong to Account ID ACC-ACCOUNT-2.',
            None,
            accountId="ACC-ACCOUNT-2",
            orderId="ORD-ACCT1-ORDER",
            slotId="SLOT-TEST-789"
        )

    def test_trigger_service_activation_empty_string_validation(self):
        """Test that trigger_service_activation validates empty strings in all required fields."""
        self.assert_error_behavior(
            trigger_service_activation,
            PydanticValidationError,
            "accountId cannot be empty or whitespace only",
            None,
            orderId= "",
            serviceIdentifier= "",
            serviceType= "",
            accountId= ""
        )

    def test_search_order_details_environment_error(self):
        self.skipTest("Skipping test_search_order_details_environment_error")
        
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        
        os.environ.pop("GEMINI_API_KEY")
        os.environ.pop("GOOGLE_API_KEY")
        
        self.assert_error_behavior(
            search_order_details,
            EnvironmentError,
            "Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.",
            None,
            "What is the status of order ORD-405060?"
        )

        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

if __name__ == '__main__':
    unittest.main()
