import unittest
import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import flag_technician_visit_issue


class TestFlagTechnicianVisitIssue(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        DB['appointmentDetails'].append({
            "visitId": "VISIT-12345",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "completed",
            "scheduledStartTime": "2023-10-27T09:00:00Z",
            "scheduledEndTime": "2023-10-27T11:00:00Z",
            "technicianNotes": "Installation complete.",
            "issueDescription": "New SunnyFiber Gigabit internet service installation and modem setup."
        })
        self.visit_to_flag = copy.deepcopy(DB['appointmentDetails'][0])

    def tearDown(self):
        reset_db()

    def test_flag_visit_issue_success(self):
        """Test flagging an issue for a technician visit successfully."""
        visit_id = self.visit_to_flag['visitId']
        account_id = self.visit_to_flag['accountId']
        order_id = self.visit_to_flag['orderId']
        
        issue_summary = "Service is not working after technician left."
        follow_up_action = "Dispatch technician again."

        result = flag_technician_visit_issue(
            accountId=account_id,
            customerReportedFailure=True,
            issueSummary=issue_summary,
            orderId=order_id,
            requestedFollowUpAction=follow_up_action,
            visitId=visit_id
        )

        self.assertIn('flagId', result)
        self.assertTrue(result['flagId'].startswith('FLAG-'))
        self.assertEqual(result['status'], 'Logged for review')
        
        # Verify the flag was added to the DB
        flag_exists = any(flag['flagId'] == result['flagId'] for flag in DB['flagTechnicianVisitIssues'])
        self.assertTrue(flag_exists)

        # Verify the technician notes were updated
        updated_visit = next(
            (appt for appt in DB['appointmentDetails'] if appt['visitId'] == visit_id),
            None
        )
        self.assertIsNotNone(updated_visit)
        self.assertIn(issue_summary, updated_visit['technicianNotes'])
        self.assertIn(follow_up_action, updated_visit['technicianNotes'])

    def test_flag_visit_issue_not_found(self):
        """Test flagging an issue for a non-existent visit."""
        self.assert_error_behavior(
            flag_technician_visit_issue,
            custom_errors.VisitNotFoundError,
            "No viable visits found for account: ACC-123, order: ORD-456, visit: NON_EXISTENT_VISIT",
            None,
            accountId="ACC-123",
            customerReportedFailure=True,
            issueSummary="Test issue",
            orderId="ORD-456",
            requestedFollowUpAction="Test action",
            visitId="NON_EXISTENT_VISIT"
        )


class TestBugFixAppendTechnicianNotes(BaseTestCaseWithErrorHandler):
    """Tests for Bug Fix: flag_technician_visit_issue should append to technicianNotes, not overwrite."""
    
    def setUp(self):
        reset_db()
        DB['appointmentDetails'].append({
            "visitId": "VISIT-12345",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "completed",
            "scheduledStartTime": "2023-10-27T09:00:00Z",
            "scheduledEndTime": "2023-10-27T11:00:00Z",
            "technicianNotes": "Installation complete. Modem configured.",
            "issueDescription": "New internet service installation."
        })
    
    def tearDown(self):
        reset_db()
    
    def test_preserves_existing_technician_notes(self):
        """Test that existing technician notes are preserved when flagging an issue."""
        original_notes = "Installation complete. Modem configured."
        
        result = flag_technician_visit_issue(
            accountId="ACC-102030",
            customerReportedFailure=True,
            issueSummary="Internet not working",
            orderId="ORD-405060",
            requestedFollowUpAction="Send technician back",
            visitId="VISIT-12345"
        )
        
        # Check that the flag was created
        self.assertIn('flagId', result)
        
        # Verify original notes are still there
        updated_visit = DB['appointmentDetails'][0]
        self.assertIn(original_notes, updated_visit['technicianNotes'])
        
        # Verify new notes were appended
        self.assertIn("Internet not working", updated_visit['technicianNotes'])
        self.assertIn("Send technician back", updated_visit['technicianNotes'])
        
        # Verify separator is used
        self.assertIn(" | ", updated_visit['technicianNotes'])
    
    def test_multiple_flags_append_correctly(self):
        """Test that multiple flags append notes correctly without losing history."""
        # First flag
        flag_technician_visit_issue(
            accountId="ACC-102030",
            customerReportedFailure=True,
            issueSummary="First issue: No internet",
            orderId="ORD-405060",
            requestedFollowUpAction="Check modem",
            visitId="VISIT-12345"
        )
        
        # Second flag
        flag_technician_visit_issue(
            accountId="ACC-102030",
            customerReportedFailure=True,
            issueSummary="Second issue: Slow speeds",
            orderId="ORD-405060",
            requestedFollowUpAction="Run speed test",
            visitId="VISIT-12345"
        )
        
        # Verify all notes are present
        updated_visit = DB['appointmentDetails'][0]
        notes = updated_visit['technicianNotes']
        
        # Original notes
        self.assertIn("Installation complete", notes)
        
        # First flag
        self.assertIn("First issue: No internet", notes)
        self.assertIn("Check modem", notes)
        
        # Second flag
        self.assertIn("Second issue: Slow speeds", notes)
        self.assertIn("Run speed test", notes)
        
        # Count separators (should be 2 for 3 note entries)
        self.assertEqual(notes.count(" | "), 2)
    
    def test_first_flag_on_empty_notes(self):
        """Test that first flag works correctly when technicianNotes is empty."""
        # Create visit with empty notes
        DB['appointmentDetails'][0]['technicianNotes'] = ''
        
        result = flag_technician_visit_issue(
            accountId="ACC-102030",
            customerReportedFailure=True,
            issueSummary="Service not activated",
            orderId="ORD-405060",
            requestedFollowUpAction="Activate service",
            visitId="VISIT-12345"
        )
        
        # Verify notes were set correctly without separator
        updated_visit = DB['appointmentDetails'][0]
        self.assertEqual(updated_visit['technicianNotes'], "Service not activated Activate service")
        self.assertNotIn(" | ", updated_visit['technicianNotes'])
    
    def test_first_flag_on_missing_notes_field(self):
        """Test that first flag works when technicianNotes field doesn't exist."""
        # Remove technicianNotes field entirely
        del DB['appointmentDetails'][0]['technicianNotes']
        
        result = flag_technician_visit_issue(
            accountId="ACC-102030",
            customerReportedFailure=True,
            issueSummary="Equipment missing",
            orderId="ORD-405060",
            requestedFollowUpAction="Deliver equipment",
            visitId="VISIT-12345"
        )
        
        # Verify notes were set correctly
        updated_visit = DB['appointmentDetails'][0]
        self.assertIn('technicianNotes', updated_visit)
        self.assertEqual(updated_visit['technicianNotes'], "Equipment missing Deliver equipment")


if __name__ == '__main__':
    unittest.main()
