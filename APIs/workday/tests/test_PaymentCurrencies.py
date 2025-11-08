from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine import db
from workday.SimulationEngine import custom_errors
import workday as WorkdayStrategicSourcingAPI
import copy


SAMPLE_DB_STATE = {
    'payments': {
        'payment_currencies': [
            {'id': 'USD', 'alpha': 'USD', 'numeric': '840'},
            {'id': 'EUR', 'alpha': 'EUR', 'numeric': '978'}
        ],
        'payment_terms': []
    },
    'events': {}
    # ... other necessary keys can be added here
}


class TestPaymentCurrenciesAPI(BaseTestCaseWithErrorHandler):
    """
    Test suite for the PaymentCurrencies.get() function.
    """

    def setUp(self):
        """
        Set up a clean, predictable database state before each test.
        """
        db.DB = copy.deepcopy(SAMPLE_DB_STATE)

    def test_get_payment_currencies_success(self):
        """
        Tests successful retrieval of all payment currencies.
        """
        currencies = WorkdayStrategicSourcingAPI.PaymentCurrencies.get()
        self.assertIsInstance(currencies, list)
        self.assertEqual(len(currencies), 2)
        self.assertEqual(currencies[0]['id'], 'USD')

    def test_get_payment_currencies_when_empty(self):
        """
        Tests retrieval when the list of payment currencies is empty.
        """
        # Set the currencies list to empty for this specific test
        db.DB['payments']['payment_currencies'] = []
        
        currencies = WorkdayStrategicSourcingAPI.PaymentCurrencies.get()
        self.assertIsInstance(currencies, list)
        self.assertEqual(len(currencies), 0)

    def test_get_fails_if_payments_key_is_missing(self):
        """
        Tests that NotFoundError is raised if the top-level 'payments' key is missing.
        """
        # Remove the 'payments' key to simulate a corrupted DB structure
        del db.DB['payments']

        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.PaymentCurrencies.get,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Database integrity error: Missing expected key 'payments' in data structure."
        )

    def test_get_fails_if_payment_currencies_key_is_missing(self):
        """
        Tests that NotFoundError is raised if the nested 'payment_currencies' key is missing.
        """
        # Remove the 'payment_currencies' key to simulate a corrupted DB structure
        del db.DB['payments']['payment_currencies']

        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.PaymentCurrencies.get,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Database integrity error: Missing expected key 'payment_currencies' in data structure."
        )
