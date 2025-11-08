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
from APIs.ces_system_activation.ces_system_activation import find_available_technician_appointment_slots


class TestFindAvailableTechnicianAppointmentSlots(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        DB['technicianSlots'].extend([
            {
                "slotId": "SLOT-94105-MON-0900-A",
                "startTime": "2025-10-27T09:00:00Z",
                "endTime": "2025-10-27T11:00:00Z",
                "technicianType": "ACTIVATION_INSTALL"
            },
            {
                "slotId": "SLOT-94105-TUE-1000-B",
                "startTime": "2025-10-28T10:00:00Z",
                "endTime": "2025-10-28T12:00:00Z",
                "technicianType": "ACTIVATION_INSTALL"
            },
            {
                "slotId": "SLOT-12345-WED-1100-C",
                "startTime": "2025-10-29T11:00:00Z",
                "endTime": "2025-10-29T13:00:00Z",
                "technicianType": "ACTIVATION_INSTALL"
            }
        ])

    def tearDown(self):
        reset_db()

    def test_find_available_slots_success(self):
        """Test finding available slots successfully."""
        result = find_available_technician_appointment_slots(
            startDate="2025-10-26"
        )
        self.assertIn('output', result)
        self.assertIsInstance(result['output'], list)
        self.assertEqual(len(result['output']), 3)
        for slot in result['output']:
            self.assertIn('slotId', slot)
            self.assertIn('startTime', slot)
            self.assertIn('endTime', slot)
            self.assertIn('technicianType', slot)

    def test_find_available_slots_with_postal_code_filter(self):
        """Test finding available slots with a specific postal code."""
        result = find_available_technician_appointment_slots(
            postalCode="94105",
            startDate="2025-10-26"
        )
        self.assertIn('output', result)
        self.assertIsInstance(result['output'], list)
        self.assertEqual(len(result['output']), 2)
        for slot in result['output']:
            self.assertTrue(slot['slotId'].startswith("SLOT-94105"))

    def test_find_available_slots_with_wrong_postal_code_filter(self):
        """Test that no slots are returned for a non-existent postal code."""
        result = find_available_technician_appointment_slots(
            postalCode="00000",
            startDate="2025-10-26"
        )
        self.assertIn('output', result)
        self.assertIsInstance(result['output'], list)
        self.assertEqual(len(result['output']), 0)

    def test_find_available_slots_with_daysToSearch(self):
        """Test finding available slots with a specific number of days to search."""
        result = find_available_technician_appointment_slots(
            startDate="2025-10-26",
            daysToSearch=3
        )
        self.assertIn('output', result)
        self.assertIsInstance(result['output'], list)
        self.assertEqual(len(result['output']), 3)
        start_date = datetime.date.fromisoformat("2025-10-26")
        end_date = start_date + datetime.timedelta(days=3)
        for slot in result['output']:
            slot_date = datetime.date.fromisoformat(slot['startTime'][:10])
            self.assertTrue(start_date <= slot_date <= end_date)

    def test_find_available_slots_invalid_date_format(self):
        """Test behavior with an invalid startDate format."""
        with self.assertRaises(ValueError) as context:
            find_available_technician_appointment_slots(
                postalCode="94105",
                startDate="2025/10/26"
            )
        self.assertIn('Invalid start date format', str(context.exception))

    def test_find_available_slots_no_availability(self):
        """Test scenario with no available slots in the given date range."""
        result = find_available_technician_appointment_slots(
            postalCode="94105",
            startDate="2025-01-01",
            daysToSearch=1
        )
        self.assertIn('output', result)
        self.assertIsInstance(result['output'], list)
        self.assertEqual(len(result['output']), 0)

    def test_input_validation_missing_postal_code(self):
        """Test input validation for missing postalCode."""
        result = find_available_technician_appointment_slots(
            startDate="2025-10-26"
        )
        self.assertIn('output', result)
        self.assertIsInstance(result['output'], list)
        self.assertTrue(len(result['output']) > 0)

    def test_input_validation_empty_startDate(self):
        """Test input validation for empty startDate."""
        with self.assertRaises(TypeError):
            find_available_technician_appointment_slots(
                postalCode="94105"
            )

    def test_input_validation_empty_postal_code(self):
        """Test input validation for empty or whitespace postal code."""
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            startDate="2025-10-26",
            postalCode=""
        )
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "postalCode cannot be empty or whitespace only",
            None,
            startDate="2025-10-26",
            postalCode="   "
        )

    def test_input_validation_invalid_days_to_search(self):
        """Test input validation for invalid daysToSearch values."""
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "Input should be greater than 0",
            None,
            startDate="2025-10-26",
            daysToSearch=0
        )
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "Input should be less than or equal to 365",
            None,
            startDate="2025-10-26",
            daysToSearch=366
        )

    def test_input_validation_whitespace_start_date(self):
        """Test input validation for whitespace-only startDate."""
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "startDate cannot be empty or whitespace only",
            None,
            startDate="   "
        )



    def test_input_validation_empty_postal_code(self):
        """Test input validation for empty or whitespace postal code."""
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "String should have at least 1 character",
            None,
            startDate="2025-10-26",
            postalCode=""
        )
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "postalCode cannot be empty or whitespace only",
            None,
            startDate="2025-10-26",
            postalCode="   "
        )

    def test_input_validation_invalid_days_to_search(self):
        """Test input validation for invalid daysToSearch values."""
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "Input should be greater than 0",
            None,
            startDate="2025-10-26",
            daysToSearch=0
        )
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "Input should be less than or equal to 365",
            None,
            startDate="2025-10-26",
            daysToSearch=366
        )

    def test_input_validation_whitespace_start_date(self):
        """Test input validation for whitespace-only startDate."""
        self.assert_error_behavior(
            find_available_technician_appointment_slots,
            PydanticValidationError,
            "startDate cannot be empty or whitespace only",
            None,
            startDate="   "
        )


if __name__ == '__main__':
    unittest.main()