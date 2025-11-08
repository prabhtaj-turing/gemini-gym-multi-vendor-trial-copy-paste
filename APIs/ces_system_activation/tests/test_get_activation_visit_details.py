import unittest
import sys
import os
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.SimulationEngine import custom_errors
from APIs.ces_system_activation.ces_system_activation import get_activation_visit_details


class TestGetActivationVisitDetails(BaseTestCaseWithErrorHandler):
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

    def tearDown(self):
        reset_db()

    def test_get_visit_details_success(self):
        """Test retrieving activation visit details successfully."""
        visit_id = DB['appointmentDetails'][0]['visitId']
        result = get_activation_visit_details(visitId=visit_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['visitId'], visit_id)
        self.assertEqual(result['accountId'], DB['appointmentDetails'][0]['accountId'])
        self.assertIn('status', result)

    def test_get_visit_details_not_found(self):
        """Test retrieving details for a non-existent visit."""
        self.assert_error_behavior(
            get_activation_visit_details,
            custom_errors.AppointmentNotFoundError,
            "No appointment found for visitId: NON_EXISTENT_ID",
            None,
            "NON_EXISTENT_ID"
        )

    def test_get_visit_details_missing_optional_fields(self):
        """Test retrieving details for a visit with missing optional fields."""
        DB['appointmentDetails'].append({
            "visitId": "VISIT-54321",
            "accountId": "ACC-030201",
            "orderId": "ORD-060504",
            "status": "scheduled",
            "scheduledStartTime": "2023-11-01T10:00:00Z",
            "scheduledEndTime": "2023-11-01T12:00:00Z",
            "technicianNotes": None,
            "issueDescription": None
        })
        visit_id = "VISIT-54321"
        result = get_activation_visit_details(visitId=visit_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['visitId'], visit_id)
        self.assertIsNone(result['technicianNotes'])
        self.assertIsNone(result['issueDescription'])

    def test_input_validation_empty_visit_id(self):
        """Test input validation for an empty visitId."""
        self.assert_error_behavior(
            get_activation_visit_details,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            ""
        )


if __name__ == '__main__':
    unittest.main()
