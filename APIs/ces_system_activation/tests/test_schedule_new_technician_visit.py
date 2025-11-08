import unittest
import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import schedule_new_technician_visit


class TestScheduleNewTechnicianVisit(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        
        # Add test order details to database for validation
        DB['orderDetails']['ORD-TEST-456'] = {
            "order_id": "ORD-TEST-456",
            "account_id": "ACC-TEST-123",
            "service_type": "INTERNET",
            "overall_order_status": "Pending",
            "service_name": "Test Service"
        }
        
        DB['technicianSlots'].append({
            "slotId": "SLOT-ABC-123",
            "startTime": "2023-10-28T10:00:00Z",
            "endTime": "2023-10-28T12:00:00Z",
            "technicianType": "ACTIVATION_INSTALL"
        })
        self.slot_to_schedule = copy.deepcopy(DB['technicianSlots'][0])

    def tearDown(self):
        reset_db()

    def test_schedule_new_visit_success(self):
        """Test scheduling a new technician visit successfully."""
        slot_id = self.slot_to_schedule['slotId']
        
        result = schedule_new_technician_visit(
            accountId="ACC-TEST-123",
            orderId="ORD-TEST-456",
            slotId=slot_id
        )

        self.assertIn('visitId', result)
        self.assertTrue(result['visitId'].startswith('VISIT-'))
        self.assertEqual(result['status'], 'scheduled')
        self.assertEqual(result['accountId'], "ACC-TEST-123")
        self.assertEqual(result['orderId'], "ORD-TEST-456")
        self.assertEqual(result['issueDescription'], 'New SunnyFiber Gigabit internet service installation and modem setup.')

        # Verify that the new appointment is in the DB
        new_appointment = next(
            (appt for appt in DB['appointmentDetails'] if appt['visitId'] == result['visitId']),
            None
        )
        self.assertIsNotNone(new_appointment)
        self.assertEqual(new_appointment['slotId'], slot_id)

        # Verify that the slot is removed from available slots
        slot_exists = any(slot['slotId'] == slot_id for slot in DB['technicianSlots'])
        self.assertFalse(slot_exists)

    def test_schedule_new_visit_with_issue_description(self):
        """Test scheduling a new technician visit with a custom issue description."""
        slot_id = self.slot_to_schedule['slotId']
        custom_description = "Custom issue description."
        
        result = schedule_new_technician_visit(
            accountId="ACC-TEST-123",
            orderId="ORD-TEST-456",
            slotId=slot_id,
            issueDescription=custom_description
        )

        self.assertIn('visitId', result)
        self.assertEqual(result['issueDescription'], custom_description)

        # Verify that the new appointment is in the DB with the correct description
        new_appointment = next(
            (appt for appt in DB['appointmentDetails'] if appt['visitId'] == result['visitId']),
            None
        )
        self.assertIsNotNone(new_appointment)
        self.assertEqual(new_appointment['issueDescription'], custom_description)

    def test_schedule_new_visit_slot_not_found(self):
        """Test scheduling a visit with a non-existent slot."""
        self.assert_error_behavior(
            schedule_new_technician_visit,
            custom_errors.TechnicianVisitNotFoundError,
            "No technician visit found for slotId: NON_EXISTENT_SLOT",
            None,
            accountId="ACC-TEST-123",
            orderId="ORD-TEST-456",
            slotId="NON_EXISTENT_SLOT"
        )


if __name__ == '__main__':
    unittest.main()
