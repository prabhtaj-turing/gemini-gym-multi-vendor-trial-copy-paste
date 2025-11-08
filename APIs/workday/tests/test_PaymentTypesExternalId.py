import unittest
from workday.SimulationEngine.custom_errors import DatabaseSchemaError, NotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler
import workday
from common_utils import error_handling
error_handling.ERROR_MODE = "RAISE"

class TestPaymentTypesExternalIdAPI(BaseTestCaseWithErrorHandler):
    """
    Test suite for the PaymentTypesExternalId.delete function.
    """

    def setUp(self):
        """Set up a clean database state with sample payment types before each test."""
        workday.SimulationEngine.db.DB = {
            'payments': {
                'payment_types': [
                    {
                        "id": "1",
                        "type": "payment_types",
                        "name": "Credit Card",
                        "external_id": "ext_cc_001"
                    },
                    {
                        "id": "2",
                        "type": "payment_types",
                        "name": "Bank Transfer",
                        "external_id": "ext_bt_002"
                    },
                    {
                        "id": "3",
                        "type": "payment_types",
                        "name": "PayPal",
                        "external_id": "ext_pp_003"
                    }
                ]
            }
        }
        # Set the error mode for testing. In a real scenario, this might be
        # configured globally for the test run.


    def test_delete_success(self):
        """Test successful deletion of an existing payment type."""
        # Check initial state
        initial_count = len(workday.SimulationEngine.db.DB['payments']['payment_types'])
        self.assertEqual(initial_count, 3)

        # Perform the deletion
        result = workday.PaymentTypesExternalId.delete(external_id="ext_bt_002")

        # Assert the function returns True on success
        self.assertTrue(result)

        # Verify the item is removed from the database
        final_count = len(workday.SimulationEngine.db.DB['payments']['payment_types'])
        self.assertEqual(final_count, initial_count - 1)

        # Verify the correct item was removed
        remaining_ids = {pt.get('external_id') for pt in workday.SimulationEngine.db.DB['payments']['payment_types']}
        self.assertNotIn("ext_bt_002", remaining_ids)
        self.assertIn("ext_cc_001", remaining_ids)


    def test_delete_not_found(self):
        """Test failure when the external_id does not exist."""
        self.assert_error_behavior(
            workday.PaymentTypesExternalId.delete,
            NotFoundError,
            "Payment type with external_id 'non_existent_id' not found.",
            None,
            "non_existent_id"
        )
        # Ensure the database was not modified
        self.assertEqual(len(workday.SimulationEngine.db.DB['payments']['payment_types']), 3)


    def test_delete_invalid_id_empty(self):
        """Test failure when external_id is an empty string."""
        self.assert_error_behavior(
            workday.PaymentTypesExternalId.delete,
            ValueError,
            "external_id must be a non-empty string.",
            None,
            ""
        )


    def test_delete_invalid_id_whitespace(self):
        """Test failure when external_id is only whitespace."""
        self.assert_error_behavior(
            workday.PaymentTypesExternalId.delete,
            ValueError,
            "external_id must be a non-empty string.",
            None,
            "   "
        )


    def test_delete_invalid_id_none(self):
        """Test failure when external_id is None."""
        self.assert_error_behavior(
            workday.PaymentTypesExternalId.delete,
            ValueError,
            "external_id must be a non-empty string.",
            None,
            None
        )


    def test_delete_database_integrity_error(self):
        """Test failure when the database schema is corrupt or missing."""
        # Corrupt the database for this specific test
        del workday.SimulationEngine.db.DB['payments']['payment_types']

        self.assert_error_behavior(
            workday.PaymentTypesExternalId.delete,
            DatabaseSchemaError,
            "Database structure for payment types is corrupt or missing.",
            None,
            "ext_cc_001"
        )

if __name__ == '__main__':
    unittest.main()
