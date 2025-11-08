import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler # Adjust path to your base_case
from ..SimulationEngine import db, custom_errors
import workday
import os

class TestPaymentCurrenciesAPI(BaseTestCaseWithErrorHandler):
    """
    Test suite for the Payment Currencies API, focusing on the delete function.
    """
    
    TEST_DB_FILE = "test_db_currencies.json"

    @classmethod
    def setUpClass(cls):
        """Set up the test database file once before all tests in this class run."""
        initial_db_state = {
            'payments': {
                'payment_currencies': [
                    {'id': 1, 'name': 'US Dollar', 'external_id': 'usd_01'},
                    {'id': 2, 'name': 'Euro', 'external_id': 'eur_02'},
                    {'id': 3, 'name': 'British Pound', 'external_id': 'gbp_03'}
                ]
            },
            'attachments': {}, 'awards': {}, 'contracts': {}, 'events': {}, 'fields': {},
            'projects': {}, 'reports': {}, 'scim': {}, 'spend_categories': {}, 'suppliers': {}
        }
        cls.initial_db_state = initial_db_state
        db.DB = initial_db_state
        db.save_state(cls.TEST_DB_FILE)

    @classmethod
    def tearDownClass(cls):
        """Remove the test database file once after all tests in this class have run."""
        if os.path.exists(cls.TEST_DB_FILE):
            os.remove(cls.TEST_DB_FILE)

    def setUp(self):
        """Reset the in-memory database to a clean state before each test."""
        db.DB = self.initial_db_state.copy()

    def test_delete_by_external_id_success(self):
        """Test deleting an existing currency by its external ID."""
        currency_count_before = len(db.DB['payments']['payment_currencies'])
        result = workday.PaymentCurrenciesExternalId.delete(external_id='eur_02')
        currency_count_after = len(db.DB['payments']['payment_currencies'])
        self.assertTrue(result)
        self.assertEqual(currency_count_after, currency_count_before - 1)
        remaining_ids = [c.get('external_id') for c in db.DB['payments']['payment_currencies']]
        self.assertNotIn('eur_02', remaining_ids)

    def test_delete_by_external_id_not_found(self):
        """Test that deleting a non-existent currency completes successfully."""
        currency_count_before = len(db.DB['payments']['payment_currencies'])
        result = workday.PaymentCurrenciesExternalId.delete(external_id='non_existent_id')
        currency_count_after = len(db.DB['payments']['payment_currencies'])
        self.assertTrue(result)
        self.assertEqual(currency_count_after, currency_count_before)

    def test_delete_invalid_id_empty_string(self):
        """Test that deleting with an empty string raises a ValueError."""
        self.assert_error_behavior(
            workday.PaymentCurrenciesExternalId.delete,
            expected_exception_type=ValueError,
            expected_message="external_id must be a non-empty string.",
            # FIX: Pass argument as a keyword
            external_id=""
        )

    def test_delete_invalid_id_whitespace(self):
        """Test that deleting with a whitespace string raises a ValueError."""
        self.assert_error_behavior(
            workday.PaymentCurrenciesExternalId.delete,
            expected_exception_type=ValueError,
            expected_message="external_id must be a non-empty string.",
            # FIX: Pass argument as a keyword
            external_id="   "
        )

    def test_delete_invalid_id_type(self):
        """Test that deleting with a non-string ID raises a ValueError."""
        self.assert_error_behavior(
            workday.PaymentCurrenciesExternalId.delete,
            expected_exception_type=ValueError,
            expected_message="external_id must be a non-empty string.",
            # FIX: Pass argument as a keyword
            external_id=123
        )

    def test_delete_with_corrupted_db_schema(self):
        """Test that a corrupted DB schema raises a DatabaseSchemaError."""
        del db.DB['payments']['payment_currencies']
        self.assert_error_behavior(
            workday.PaymentCurrenciesExternalId.delete,
            expected_exception_type=custom_errors.DatabaseSchemaError,
            expected_message="Failed to access payment currencies due to an invalid database schema.",
            # FIX: Pass argument as a keyword
            external_id='usd_01'
        )

if __name__ == '__main__':
    unittest.main()