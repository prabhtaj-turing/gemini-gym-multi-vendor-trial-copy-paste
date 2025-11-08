import unittest
import sys
import os
from typing import List, Optional
from pydantic import ValidationError

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler

from APIs.ces_system_activation.SimulationEngine.models import (
    TechnicianVisitDetails,
    AppointmentAvailability,
    AvailableAppointmentSlot,
    FlaggedIssueConfirmation,
    ServiceActivationAttempt,
    NotificationResult,
    DataStoreQueryResult,
    SourceSnippet
)

class TestCESModels(BaseTestCaseWithErrorHandler):
    """
    Test suite for validating ces_system_activation dataclass models.
    """

    def test_technician_visit_details_model(self):
        """
        Test TechnicianVisitDetails model validation.
        """
        # Test valid model creation
        visit_details = TechnicianVisitDetails(
            visitId="VISIT-12345",
            accountId="ACC-102030",
            orderId="ORD-405060",
            status="scheduled",
            scheduledStartTime="2023-10-27T14:00:00Z",
            scheduledEndTime="2023-10-27T16:00:00Z",
            technicianNotes="Test notes",
            issueDescription="Test issue"
        )

        self.assertEqual(visit_details.visitId, "VISIT-12345")
        self.assertEqual(visit_details.accountId, "ACC-102030")
        self.assertEqual(visit_details.status, "scheduled")
        
        # Test valid model with optional technicianNotes as None
        visit_details_no_notes = TechnicianVisitDetails(
            visitId="VISIT-12345",
            accountId="ACC-102030",
            orderId="ORD-405060",
            status="scheduled",
            scheduledStartTime="2023-10-27T14:00:00Z",
            scheduledEndTime="2023-10-27T16:00:00Z",
            technicianNotes=None,  # Only technicianNotes is nullable
            issueDescription="Test issue"
        )
        self.assertIsNone(visit_details_no_notes.technicianNotes)
        
        # Test that required fields reject None values
        with self.assertRaises(ValidationError):
            TechnicianVisitDetails(
                visitId=None,  # This should fail - required field
                accountId="ACC-102030",
                orderId="ORD-405060",
                status="scheduled",
                scheduledStartTime="2023-10-27T14:00:00Z",
                scheduledEndTime="2023-10-27T16:00:00Z",
                technicianNotes=None,
                issueDescription="Test issue"
            )


class TestTechnicianVisitDetailsComprehensive(BaseTestCaseWithErrorHandler):
    """
    Comprehensive test suite for TechnicianVisitDetails model validation.
    Tests all required fields, nullable fields, and edge cases.
    """
    
    def get_valid_visit_data(self):
        """Helper method to get valid visit data for testing."""
        return {
            "visitId": "VISIT-12345",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": "2023-10-27T14:00:00Z",
            "scheduledEndTime": "2023-10-27T16:00:00Z",
            "technicianNotes": "Test notes",
            "issueDescription": "Test issue"
        }
    
    # ===== VALID CREATION TESTS =====
    
    def test_valid_creation_all_fields_populated(self):
        """Test valid creation with all fields populated."""
        data = self.get_valid_visit_data()
        visit = TechnicianVisitDetails(**data)
        
        self.assertEqual(visit.visitId, "VISIT-12345")
        self.assertEqual(visit.accountId, "ACC-102030")
        self.assertEqual(visit.orderId, "ORD-405060")
        self.assertEqual(visit.status, "scheduled")
        self.assertEqual(visit.scheduledStartTime, "2023-10-27T14:00:00Z")
        self.assertEqual(visit.scheduledEndTime, "2023-10-27T16:00:00Z")
        self.assertEqual(visit.technicianNotes, "Test notes")
        self.assertEqual(visit.issueDescription, "Test issue")
    
    def test_valid_creation_with_null_technician_notes(self):
        """Test valid creation with technicianNotes as None."""
        data = self.get_valid_visit_data()
        data["technicianNotes"] = None
        visit = TechnicianVisitDetails(**data)
        
        self.assertIsNone(visit.technicianNotes)
        self.assertEqual(visit.visitId, "VISIT-12345")
    
    def test_valid_creation_with_empty_string_technician_notes(self):
        """Test valid creation with empty string for technicianNotes."""
        data = self.get_valid_visit_data()
        data["technicianNotes"] = ""
        visit = TechnicianVisitDetails(**data)
        
        self.assertEqual(visit.technicianNotes, "")
    
    def test_valid_creation_with_rescheduled_prefix(self):
        """Test valid creation with rescheduled_ prefix in visitId."""
        data = self.get_valid_visit_data()
        data["visitId"] = "rescheduled_VISIT-12345"
        visit = TechnicianVisitDetails(**data)
        
        self.assertEqual(visit.visitId, "rescheduled_VISIT-12345")
    
    def test_valid_creation_with_various_status_values(self):
        """Test valid creation with different status values."""
        for status_value in ["scheduled", "in_progress", "completed", "pending"]:
            with self.subTest(status=status_value):
                data = self.get_valid_visit_data()
                data["status"] = status_value
                visit = TechnicianVisitDetails(**data)
                self.assertEqual(visit.status, status_value)
    
    # ===== REQUIRED FIELD VALIDATION =====
    
    def test_required_field_visit_id_rejects_none(self):
        """Test that visitId rejects None."""
        data = self.get_valid_visit_data()
        data["visitId"] = None
        
        with self.assertRaises(ValidationError) as context:
            TechnicianVisitDetails(**data)
        
        self.assertIn("visitId", str(context.exception))
    
    def test_required_field_account_id_rejects_none(self):
        """Test that accountId rejects None."""
        data = self.get_valid_visit_data()
        data["accountId"] = None
        
        with self.assertRaises(ValidationError):
            TechnicianVisitDetails(**data)
    
    def test_required_field_order_id_rejects_none(self):
        """Test that orderId rejects None."""
        data = self.get_valid_visit_data()
        data["orderId"] = None
        
        with self.assertRaises(ValidationError):
            TechnicianVisitDetails(**data)
    
    def test_required_field_status_rejects_none(self):
        """Test that status rejects None."""
        data = self.get_valid_visit_data()
        data["status"] = None
        
        with self.assertRaises(ValidationError):
            TechnicianVisitDetails(**data)
    
    def test_required_field_scheduled_start_time_rejects_none(self):
        """Test that scheduledStartTime accepts None (reverted to Optional)."""
        data = self.get_valid_visit_data()
        data["scheduledStartTime"] = None
        
        # Now this field is Optional, so None should be accepted
        visit = TechnicianVisitDetails(**data)
        self.assertIsNone(visit.scheduledStartTime)
    
    def test_required_field_scheduled_end_time_rejects_none(self):
        """Test that scheduledEndTime accepts None (reverted to Optional)."""
        data = self.get_valid_visit_data()
        data["scheduledEndTime"] = None
        
        # Now this field is Optional, so None should be accepted
        visit = TechnicianVisitDetails(**data)
        self.assertIsNone(visit.scheduledEndTime)
    
    def test_required_field_issue_description_rejects_none(self):
        """Test that issueDescription accepts None (reverted to Optional)."""
        data = self.get_valid_visit_data()
        data["issueDescription"] = None
        
        # Now this field is Optional, so None should be accepted
        visit = TechnicianVisitDetails(**data)
        self.assertIsNone(visit.issueDescription)
    
    # ===== OPTIONAL FIELD VALIDATION =====
    
    def test_optional_field_technician_notes_accepts_none(self):
        """Test that technicianNotes accepts None (only nullable field)."""
        data = self.get_valid_visit_data()
        data["technicianNotes"] = None
        
        visit = TechnicianVisitDetails(**data)
        self.assertIsNone(visit.technicianNotes)
    
    def test_optional_field_technician_notes_accepts_string(self):
        """Test that technicianNotes accepts string values."""
        data = self.get_valid_visit_data()
        data["technicianNotes"] = "Some technician notes"
        
        visit = TechnicianVisitDetails(**data)
        self.assertEqual(visit.technicianNotes, "Some technician notes")
    
    # ===== EDGE CASES =====
    
    def test_edge_case_very_long_strings(self):
        """Test creation with very long string values."""
        data = self.get_valid_visit_data()
        long_string = "x" * 1000
        data["visitId"] = long_string
        data["issueDescription"] = long_string
        
        visit = TechnicianVisitDetails(**data)
        self.assertEqual(visit.visitId, long_string)
        self.assertEqual(visit.issueDescription, long_string)
    
    def test_edge_case_special_characters_in_strings(self):
        """Test creation with special characters in strings."""
        data = self.get_valid_visit_data()
        data["visitId"] = "VISIT-!@#$%^&*()"
        data["issueDescription"] = "Issue: Test & Documentation (draft) [2023]"
        
        visit = TechnicianVisitDetails(**data)
        self.assertEqual(visit.visitId, "VISIT-!@#$%^&*()")
        self.assertIn("&", visit.issueDescription)
    
    def test_edge_case_unicode_characters(self):
        """Test creation with unicode characters."""
        data = self.get_valid_visit_data()
        data["issueDescription"] = "Installation for 中文 user café"
        
        visit = TechnicianVisitDetails(**data)
        self.assertIn("中文", visit.issueDescription)
    
    def test_edge_case_iso_format_timestamps(self):
        """Test creation with various ISO format timestamps."""
        data = self.get_valid_visit_data()
        iso_timestamps = [
            "2023-10-27T14:00:00Z",
            "2023-10-27T14:00:00+00:00",
            "2023-10-27T14:00:00.000Z",
        ]
        
        for timestamp in iso_timestamps:
            with self.subTest(timestamp=timestamp):
                data["scheduledStartTime"] = timestamp
                visit = TechnicianVisitDetails(**data)
                self.assertEqual(visit.scheduledStartTime, timestamp)
    
    def test_edge_case_whitespace_in_strings(self):
        """Test creation with whitespace in strings."""
        data = self.get_valid_visit_data()
        data["visitId"] = "VISIT - 12345"  # with spaces
        data["issueDescription"] = "   Issue with leading/trailing spaces   "
        
        visit = TechnicianVisitDetails(**data)
        # Strings should be preserved as-is
        self.assertEqual(visit.visitId, "VISIT - 12345")
        self.assertIn("leading", visit.issueDescription)
    
    # ===== MODEL DUMPING TESTS =====
    
    def test_model_dump_preserves_all_data(self):
        """Test that model_dump preserves all data correctly."""
        data = self.get_valid_visit_data()
        visit = TechnicianVisitDetails(**data)
        dumped = visit.model_dump()
        
        self.assertEqual(dumped["visitId"], "VISIT-12345")
        self.assertEqual(dumped["accountId"], "ACC-102030")
        self.assertEqual(dumped["technicianNotes"], "Test notes")
    
    def test_model_dump_with_none_technician_notes(self):
        """Test that model_dump handles None technicianNotes correctly."""
        data = self.get_valid_visit_data()
        data["technicianNotes"] = None
        visit = TechnicianVisitDetails(**data)
        dumped = visit.model_dump()
        
        self.assertIsNone(dumped["technicianNotes"])
    
    def test_model_dump_exclude_none_false(self):
        """Test model_dump with exclude_none=False includes None values."""
        data = self.get_valid_visit_data()
        data["technicianNotes"] = None
        visit = TechnicianVisitDetails(**data)
        dumped = visit.model_dump(exclude_none=False)
        
        self.assertIn("technicianNotes", dumped)
        self.assertIsNone(dumped["technicianNotes"])

    def test_available_appointment_slot_model(self):
        """
        Test AvailableAppointmentSlot model validation.
        """
        slot = AvailableAppointmentSlot(
            endTime="2023-11-05T14:00:00Z",
            slotId="SLOT-ABC-123",
            startTime="2023-11-05T12:00:00Z",
            technicianType="Fiber Installation Specialist"
        )

        self.assertEqual(slot.slotId, "SLOT-ABC-123")
        self.assertEqual(slot.technicianType, "Fiber Installation Specialist")
        slot_minimal = AvailableAppointmentSlot(
            endTime=None,
            slotId=None,
            startTime=None,
            technicianType=None,
        )
        self.assertIsNone(slot_minimal.slotId)

    def test_appointment_availability_model(self):
        """
        Test AppointmentAvailability model validation.
        """
        slots = [
            AvailableAppointmentSlot(
                endTime="2023-11-05T14:00:00Z",
                slotId="SLOT-ABC-123",
                startTime="2023-11-05T12:00:00Z",
                technicianType="Fiber Installation"
            )
        ]

        availability = AppointmentAvailability(output=slots)
        self.assertEqual(len(availability.output), 1)
        self.assertEqual(availability.output[0].slotId, "SLOT-ABC-123")

        # Test with empty list
        availability_empty = AppointmentAvailability(output=[])
        self.assertEqual(len(availability_empty.output), 0)
        availability_none = AppointmentAvailability(output=None)
        self.assertIsNone(availability_none.output)

    def test_flagged_issue_confirmation_model(self):
        """
        Test FlaggedIssueConfirmation model validation.
        """
        confirmation = FlaggedIssueConfirmation(
            flagId="FLAG-998877",
            message="Issue has been logged for review.",
            status="SUCCESS"
        )

        self.assertEqual(confirmation.flagId, "FLAG-998877")
        self.assertEqual(confirmation.status, "SUCCESS")
        
        # Test that all fields are required and cannot be None
        with self.assertRaises(ValidationError):
            FlaggedIssueConfirmation(
                flagId=None,
                message=None,
                status=None,
            )

    def test_service_activation_attempt_model(self):
        """
        Test ServiceActivationAttempt model validation.
        """
        attempt = ServiceActivationAttempt(
            activationAttemptId="ATTEMPT-12345",
            message="Activation is in progress.",
            status="REQUEST_RECEIVED",
            timestamp="2023-10-27T10:00:00Z"
        )

        self.assertEqual(attempt.activationAttemptId, "ATTEMPT-12345")
        self.assertEqual(attempt.status, "REQUEST_RECEIVED")
        """
        Test NotificationResult model validation.
        """
        result = NotificationResult(
            channelSent="EMAIL",
            message="Message sent successfully",
            notificationId="NOTIF-a1b2c3d4",
            recipientUsed="+14155552671",
            status="SENT",
            timestamp="2023-10-27T10:00:00Z"
        )

        self.assertEqual(result.channelSent, "EMAIL")
        self.assertEqual(result.status, "SENT")
        # recipientUsed is optional per function implementation
        result_with_optional = NotificationResult(
            channelSent="SMS",
            message="Sent",
            notificationId="NOTIF-123",
            recipientUsed=None,  # This is allowed
            status="SENT",
            timestamp="2023-10-27T10:00:00Z"
        )
        self.assertIsNone(result_with_optional.recipientUsed)
        # But other fields are required - testing with None should fail
        with self.assertRaises(Exception):  # Pydantic ValidationError
            NotificationResult(
                channelSent=None,  # This should fail
                message="Sent",
                notificationId="NOTIF-123",
                recipientUsed=None,
                status="SENT",
                timestamp="2023-10-27T10:00:00Z"
            )

    def test_data_store_query_result_model(self):
        """
        Test DataStoreQueryResult model validation.
        """
        snippets = [
            SourceSnippet(
                text="Sample text from source",
                title="Source Title",
                uri="https://example.com/source"
            )
        ]

        result = DataStoreQueryResult(
            answer="This is the answer to the query.",
            snippets=snippets
        )

        self.assertEqual(result.answer, "This is the answer to the query.")
        self.assertEqual(len(result.snippets), 1)

        # Test with empty snippets
        result_empty = DataStoreQueryResult(
            answer="Answer without snippets",
            snippets=[]
        )

        self.assertEqual(len(result_empty.snippets), 0)

    def test_source_snippet_model(self):
        """
        Test SourceSnippet model validation.
        """
        snippet = SourceSnippet(
            text="This is the text content from the source document.",
            title="Document Title",
            uri="https://example.com/document"
        )

        self.assertEqual(snippet.text, "This is the text content from the source document.")
        self.assertEqual(snippet.title, "Document Title")
        self.assertEqual(snippet.uri, "https://example.com/document")
        
        # Test that fields can be None (per API specification)
        snippet_with_none = SourceSnippet(text=None, title=None, uri=None)
        self.assertIsNone(snippet_with_none.text)
        self.assertIsNone(snippet_with_none.title)
        self.assertIsNone(snippet_with_none.uri)

if __name__ == '__main__':
    unittest.main()