import unittest
import copy
from workday.SimulationEngine.custom_errors import PaymentTypeNotFoundError, InvalidInputError
from common_utils.base_case import BaseTestCaseWithErrorHandler
import workday

class TestPaymentTypesIdAPI(BaseTestCaseWithErrorHandler):
    """
    Test suite for the PaymentTypesId.delete function, ensuring correct behavior
    for successful deletions, invalid inputs, and non-existent records.
    """

    def setUp(self):
        """
        Set up a clean, predictable database state before each test.
        This ensures that tests are isolated and results are consistent.
        """
        # Initialize the in-memory database with sample payment types
        workday.SimulationEngine.db.DB = {
            'payments': {
                'payment_types': [
                    {"id": 1, "name": "Credit Card", "external_id": "ext_cc"},
                    {"id": 2, "name": "ACH", "external_id": "ext_ach"},
                    {"id": 3, "name": "Wire Transfer", "external_id": "ext_wire"}
                ]
            }
        }

    def test_delete_success(self):
        """
        Test the successful deletion of an existing payment type.
        Verifies that the function returns True and the item is removed from the database.
        """
        # Call the delete function with a valid, existing ID
        result = workday.PaymentTypesId.delete(id=2)

        # Assert that the operation was successful
        self.assertTrue(result)

        # Verify that the payment type was actually removed
        payment_types = workday.SimulationEngine.db.DB['payments']['payment_types']
        self.assertEqual(len(payment_types), 2)

        # Verify that the correct item was removed and others remain
        remaining_ids = {pt['id'] for pt in payment_types}
        self.assertNotIn(2, remaining_ids)
        self.assertIn(1, remaining_ids)
        self.assertIn(3, remaining_ids)

    def test_delete_id_not_found(self):
        """
        Test that deleting a non-existent payment type ID raises a PaymentTypeNotFoundError.
        """
        self.assert_error_behavior(
            workday.PaymentTypesId.delete,
            PaymentTypeNotFoundError,
            "Payment type with id '99' not found.",
            None,
            id=99
        )
        # Ensure the database was not modified
        self.assertEqual(len(workday.SimulationEngine.db.DB['payments']['payment_types']), 3)

    # --- Edge Cases and Invalid Input Tests ---

    def test_delete_invalid_id_zero(self):
        """
        Test that providing an ID of 0 raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.PaymentTypesId.delete,
            InvalidInputError,
            "Payment type 'id' must be a positive integer.",
            None,
            id=0
        )

    def test_delete_invalid_id_negative(self):
        """
        Test that providing a negative ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.PaymentTypesId.delete,
            InvalidInputError,
            "Payment type 'id' must be a positive integer.",
            None,
            id=-10
        )

    def test_delete_invalid_id_string(self):
        """
        Test that providing a string ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.PaymentTypesId.delete,
            InvalidInputError,
            "Payment type 'id' must be a positive integer.",
            None,
            id="not-an-int"
        )

    def test_delete_invalid_id_none(self):
        """
        Test that providing None as the ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.PaymentTypesId.delete,
            InvalidInputError,
            "Payment type 'id' must be a positive integer.",
            None,
            id=None
        )

    def test_delete_from_empty_list(self):
        """
        Test that attempting to delete from an empty list of payment types
        correctly raises a PaymentTypeNotFoundError.
        """
        # Set up the database with an empty list
        workday.SimulationEngine.db.DB['payments']['payment_types'] = []

        self.assert_error_behavior(
            workday.PaymentTypesId.delete,
            PaymentTypeNotFoundError,
            "Payment type with id '1' not found.",
            None,
            id=1
        )

if __name__ == '__main__':
    unittest.main()