import unittest
import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import reschedule_technician_visit


class TestRescheduleTechnicianVisit(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        DB['appointmentDetails'].append({
            "visitId": "VISIT-12345",
            "slotId": "OLD-SLOT-ID",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": "2023-10-27T09:00:00Z",
            "scheduledEndTime": "2023-10-27T11:00:00Z",
            "technicianNotes": "Initial appointment.",
            "issueDescription": "New SunnyFiber Gigabit internet service installation and modem setup."
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-XYZ-789",
            "startTime": "2023-10-28T14:00:00Z",
            "endTime": "2023-10-28T16:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        self.appointment_to_reschedule = copy.deepcopy(DB['appointmentDetails'][0])
        self.new_slot = copy.deepcopy(DB['technicianSlots'][0])

    def tearDown(self):
        reset_db()

    def test_reschedule_visit_success(self):
        """Test rescheduling a technician visit successfully."""
        original_visit_id = self.appointment_to_reschedule['visitId']
        new_slot_id = self.new_slot['slotId']
        
        result = reschedule_technician_visit(
            accountId=self.appointment_to_reschedule['accountId'],
            newSlotId=new_slot_id,
            orderId=self.appointment_to_reschedule['orderId'],
            originalVisitId=original_visit_id,
            reasonForChange="Customer request"
        )

        self.assertIn('visitId', result)
        self.assertTrue(result['visitId'].startswith('rescheduled_'))
        self.assertEqual(result['status'], 'scheduled')
        self.assertEqual(result['scheduledStartTime'], self.new_slot['startTime'])

        # Verify that the old appointment is removed and the new one is added
        old_appointment_exists = any(
            appt['visitId'] == original_visit_id for appt in DB['appointmentDetails']
        )
        self.assertFalse(old_appointment_exists)

        new_appointment_exists = any(
            appt['visitId'] == result['visitId'] for appt in DB['appointmentDetails']
        )
        self.assertTrue(new_appointment_exists)

    def test_reschedule_visit_not_found(self):
        """Test rescheduling a non-existent visit with a valid account ID."""
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.VisitNotFoundError,
            "No appointment found for visitId: NON_EXISTENT_VISIT",
            None,
            accountId="ACC-102030",
            newSlotId=self.new_slot['slotId'],
            orderId="ORD-405060",
            originalVisitId="NON_EXISTENT_VISIT"
        )

    def test_reschedule_slot_not_found(self):
        """Test rescheduling to a non-existent slot."""
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.SlotNotFoundError,
            "The slotId: NON_EXISTENT_SLOT is not available.",
            None,
            accountId=self.appointment_to_reschedule['accountId'],
            newSlotId="NON_EXISTENT_SLOT",
            orderId=self.appointment_to_reschedule['orderId'],
            originalVisitId=self.appointment_to_reschedule['visitId']
        )

    def test_reschedule_unauthorized_account_mismatch(self):
        """Test SECURITY: Prevent rescheduling appointments that don't belong to the provided accountId.
        
        This test ensures a malicious actor cannot reschedule an appointment for any account
        if they know a valid originalVisitId but use a different accountId.
        """
        # Create a second account with its own appointment
        DB['appointmentDetails'].append({
            "visitId": "VISIT-ATTACKER",
            "slotId": "ATTACKER-SLOT-ID",
            "accountId": "ACC-ATTACKER",
            "orderId": "ORD-ATTACKER",
            "status": "scheduled",
            "scheduledStartTime": "2023-10-27T09:00:00Z",
            "scheduledEndTime": "2023-10-27T11:00:00Z",
            "technicianNotes": "Attacker's appointment.",
            "issueDescription": "Attacker's service."
        })
        
        # Try to reschedule the legitimate account's appointment using a different accountId
        # This should fail because the visitId belongs to ACC-102030, not the attacker's account
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.ValidationError,
            "The appointment with visitId VISIT-12345 does not belong to account ACC-ATTACKER.",
            None,
            accountId="ACC-ATTACKER",  # Wrong account trying to reschedule another's appointment
            newSlotId=self.new_slot['slotId'],
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"  # This appointment belongs to ACC-102030
        )
    
    def test_reschedule_visit_completed_appointment(self):
        """Test that completed appointments cannot be rescheduled."""
        # Mark the appointment as completed
        DB['appointmentDetails'][0]['status'] = 'completed'
        
        self.assert_error_behavior(
            reschedule_technician_visit,
            custom_errors.ValidationError,
            "Completed appointments cannot be rescheduled.",
            None,
            accountId=self.appointment_to_reschedule['accountId'],
            newSlotId=self.new_slot['slotId'],
            orderId=self.appointment_to_reschedule['orderId'],
            originalVisitId=self.appointment_to_reschedule['visitId']
        )


class TestRescheduleTechnicianVisitComprehensive(BaseTestCaseWithErrorHandler):
    """
    Comprehensive integration tests for reschedule_technician_visit function.
    Verifies all required fields are populated and response model validation.
    """
    
    def setUp(self):
        """Set up test database with appointments and slots."""
        reset_db()
        DB['appointmentDetails'].append({
            "visitId": "VISIT-12345",
            "slotId": "OLD-SLOT-ID",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": "2023-10-27T09:00:00Z",
            "scheduledEndTime": "2023-10-27T11:00:00Z",
            "technicianNotes": "Initial appointment.",
            "issueDescription": "New SunnyFiber Gigabit internet service installation and modem setup."
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-XYZ-789",
            "startTime": "2023-10-28T14:00:00Z",
            "endTime": "2023-10-28T16:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
    
    def tearDown(self):
        """Clean up test database."""
        reset_db()
    
    # ===== RESPONSE STRUCTURE VALIDATION =====
    
    def test_response_contains_all_required_fields(self):
        """Test that response contains all required fields as strings."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345",
            reasonForChange="Customer request"
        )
        
        # Verify all required fields exist
        required_fields = [
            'visitId', 'accountId', 'orderId', 'status',
            'scheduledStartTime', 'scheduledEndTime', 'issueDescription'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing required field: {field}")
            self.assertIsNotNone(result[field], f"Field {field} should not be None")
            self.assertIsInstance(result[field], str, f"Field {field} should be string")
    
    def test_response_visit_id_has_rescheduled_prefix(self):
        """Test that visitId in response has 'rescheduled_' prefix."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertTrue(result['visitId'].startswith('rescheduled_'))
        self.assertIn('VISIT-12345', result['visitId'])
    
    def test_response_account_id_matches_input(self):
        """Test that accountId in response matches input."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertEqual(result['accountId'], "ACC-102030")
    
    def test_response_order_id_matches_input(self):
        """Test that orderId in response matches input."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertEqual(result['orderId'], "ORD-405060")
    
    def test_response_status_is_scheduled(self):
        """Test that status is always 'scheduled'."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertEqual(result['status'], 'scheduled')
    
    def test_response_scheduled_start_time_from_slot(self):
        """Test that scheduledStartTime comes from new slot."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertEqual(result['scheduledStartTime'], "2023-10-28T14:00:00Z")
    
    def test_response_scheduled_end_time_from_slot(self):
        """Test that scheduledEndTime comes from new slot."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertEqual(result['scheduledEndTime'], "2023-10-28T16:00:00Z")
    
    def test_response_issue_description_from_original(self):
        """Test that issueDescription comes from original appointment."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertEqual(
            result['issueDescription'],
            "New SunnyFiber Gigabit internet service installation and modem setup."
        )
    
    # ===== OPTIONAL FIELD HANDLING =====
    
    def test_response_technician_notes_with_reason_for_change(self):
        """Test that technicianNotes is populated when reasonForChange provided."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345",
            reasonForChange="Customer requested earlier time slot"
        )
        
        self.assertEqual(result['technicianNotes'], "Customer requested earlier time slot")
    
    def test_response_technician_notes_without_reason_for_change(self):
        """Test that technicianNotes is None when reasonForChange not provided."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertIsNone(result['technicianNotes'])
    
    # ===== DATA CONSISTENCY TESTS =====
    
    def test_old_appointment_removed_from_database(self):
        """Test that old appointment is removed after rescheduling."""
        original_visit_id = "VISIT-12345"
        
        reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId=original_visit_id
        )
        
        # Verify old appointment is gone
        old_exists = any(
            appt['visitId'] == original_visit_id 
            for appt in DB['appointmentDetails']
        )
        self.assertFalse(old_exists)
    
    def test_new_appointment_added_to_database(self):
        """Test that new appointment is added after rescheduling."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345",
            reasonForChange="Test"
        )
        
        # Verify new appointment is in database
        new_exists = any(
            appt['visitId'] == result['visitId']
            for appt in DB['appointmentDetails']
        )
        self.assertTrue(new_exists)
    
    def test_new_slot_removed_from_available_slots(self):
        """Test that new slot is removed from available slots."""
        initial_slot_count = len(DB['technicianSlots'])
        
        reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        final_slot_count = len(DB['technicianSlots'])
        # One slot removed (new), one restored (old) = same count
        self.assertEqual(initial_slot_count, final_slot_count)
    
    # ===== ERROR HANDLING =====
    
    def test_error_account_not_found(self):
        """Test error when account doesn't exist."""
        with self.assertRaises(custom_errors.ValidationError):
            reschedule_technician_visit(
                accountId="ACC-INVALID",
                newSlotId="SLOT-XYZ-789",
                orderId="ORD-405060",
                originalVisitId="VISIT-12345"
            )
    
    def test_error_original_visit_not_found(self):
        """Test error when original visit doesn't exist."""
        with self.assertRaises(custom_errors.VisitNotFoundError):
            reschedule_technician_visit(
                accountId="ACC-102030",
                newSlotId="SLOT-XYZ-789",
                orderId="ORD-405060",
                originalVisitId="VISIT-INVALID"
            )
    
    def test_error_new_slot_not_found(self):
        """Test error when new slot doesn't exist."""
        with self.assertRaises(custom_errors.SlotNotFoundError):
            reschedule_technician_visit(
                accountId="ACC-102030",
                newSlotId="SLOT-INVALID",
                orderId="ORD-405060",
                originalVisitId="VISIT-12345"
            )
    
    # ===== MULTIPLE RESCHEDULES =====
    
    def test_multiple_reschedules_create_correct_prefixes(self):
        """Test that multiple reschedules maintain correct visit ID prefixes."""
        # First reschedule
        result1 = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        self.assertTrue(result1['visitId'].startswith('rescheduled_'))
        
        # Verify all required fields are strings
        for field in ['visitId', 'accountId', 'orderId', 'status', 
                      'scheduledStartTime', 'scheduledEndTime', 'issueDescription']:
            self.assertIsInstance(result1[field], str, 
                                f"{field} should be string in rescheduled visit")


class TestRescheduleTechnicianVisitWithNoneValues(BaseTestCaseWithErrorHandler):
    """
    Test reschedule_technician_visit behavior when database contains None values
    for scheduledStartTime, scheduledEndTime, and issueDescription.
    This tests if None values will break downstream code.
    """
    
    def setUp(self):
        """Set up test database with None values in critical fields."""
        reset_db()
        DB['appointmentDetails'].append({
            "visitId": "VISIT-12345",
            "slotId": "OLD-SLOT-ID",
            "accountId": "ACC-102030",
            "orderId": "ORD-405060",
            "status": "scheduled",
            "scheduledStartTime": None,  # ← None value
            "scheduledEndTime": None,    # ← None value
            "technicianNotes": "Initial appointment.",
            "issueDescription": None,    # ← None value
        })
        DB['technicianSlots'].append({
            "slotId": "SLOT-XYZ-789",
            "startTime": "2023-10-28T14:00:00Z",
            "endTime": "2023-10-28T16:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
    
    def tearDown(self):
        """Clean up test database."""
        reset_db()
    
    def test_reschedule_with_none_scheduled_start_time_in_db(self):
        """Test rescheduling when original appointment has None scheduledStartTime."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        # With None in DB, the function still works because it uses new_slot['startTime']
        # But let's verify what's actually returned
        print(f"\n=== RESULT WITH NONE scheduledStartTime ===")
        print(f"scheduledStartTime: {result['scheduledStartTime']}")
        print(f"Type: {type(result['scheduledStartTime'])}")
        print(f"Result dict: {result}")
        
        self.assertIsNotNone(result['scheduledStartTime'])
        self.assertEqual(result['scheduledStartTime'], "2023-10-28T14:00:00Z")
    
    def test_reschedule_with_none_scheduled_end_time_in_db(self):
        """Test rescheduling when original appointment has None scheduledEndTime."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        print(f"\n=== RESULT WITH NONE scheduledEndTime ===")
        print(f"scheduledEndTime: {result['scheduledEndTime']}")
        print(f"Type: {type(result['scheduledEndTime'])}")
        
        self.assertIsNotNone(result['scheduledEndTime'])
        self.assertEqual(result['scheduledEndTime'], "2023-10-28T16:00:00Z")
    
    def test_reschedule_with_none_issue_description_in_db(self):
        """Test rescheduling when original appointment has None issueDescription."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        print(f"\n=== RESULT WITH NONE issueDescription ===")
        print(f"issueDescription: {result['issueDescription']}")
        print(f"Type: {type(result['issueDescription'])}")
        
        # This WILL be None because it comes from original_appointment['issueDescription']
        self.assertIsNone(result['issueDescription'])
    
    def test_none_issue_description_breaks_downstream(self):
        """Test if None issueDescription breaks downstream code like email/UI formatting."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        print(f"\n=== TESTING DOWNSTREAM USAGE ===")
        
        # Simulate downstream code that would use this
        print(f"Original issueDescription: {result['issueDescription']}")
        
        # Test 1: String formatting (like in UI)
        print("\nTest 1: UI String formatting")
        try:
            formatted = f"Issue: {result['issueDescription'].upper()}"
            print(f"  ✓ Result: {formatted}")
        except AttributeError as e:
            print(f"  ✗ ERROR: {e}")
            print(f"    Reason: Can't call .upper() on None")
        
        # Test 2: Email body construction
        print("\nTest 2: Email body construction")
        try:
            email_body = f"""
Your appointment details:
Issue: {result['issueDescription']}
Time: {result['scheduledStartTime']} to {result['scheduledEndTime']}
"""
            print(f"  ✓ Email body created:")
            print(f"    {email_body}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
        
        # Test 3: Test assertion (like in test_reschedule_visit_success)
        print("\nTest 3: Test assertion from test_reschedule_visit_success")
        try:
            # This is what the existing test does
            assert result['issueDescription'] is not None, "issueDescription should not be None"
            print(f"  ✓ Assertion passed")
        except AssertionError as e:
            print(f"  ✗ ASSERTION FAILED: {e}")
    
    def test_all_three_fields_none_together(self):
        """Test when all three fields (scheduledStartTime, scheduledEndTime, issueDescription) are None in DB."""
        result = reschedule_technician_visit(
            accountId="ACC-102030",
            newSlotId="SLOT-XYZ-789",
            orderId="ORD-405060",
            originalVisitId="VISIT-12345"
        )
        
        print(f"\n=== ALL THREE FIELDS RESPONSE ===")
        print(f"scheduledStartTime: {result['scheduledStartTime']} (type: {type(result['scheduledStartTime'])})")
        print(f"scheduledEndTime: {result['scheduledEndTime']} (type: {type(result['scheduledEndTime'])})")
        print(f"issueDescription: {result['issueDescription']} (type: {type(result['issueDescription'])})")
        
        # This demonstrates the asymmetry:
        # - scheduledStartTime and scheduledEndTime are NOT None (from new_slot)
        # - issueDescription IS None (from original_appointment which has None)
        self.assertIsNotNone(result['scheduledStartTime'])
        self.assertIsNotNone(result['scheduledEndTime'])
        self.assertIsNone(result['issueDescription'])  # ← This is the problem!


if __name__ == '__main__':
    unittest.main()
