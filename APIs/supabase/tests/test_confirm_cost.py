import unittest
import copy

from supabase import confirm_cost

from ..SimulationEngine.db import DB

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors

class TestConfirmCost(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({'organizations': [], 'projects': [], 'tables': {}, 'extensions': {}, 'migrations': {}, 'edge_functions': {}, 'branches': {}, 'costs': {}, 'unconfirmed_costs': {}, 'project_urls': {}, 'project_anon_keys': {}, 'project_ts_types': {}, 'logs': {}})
        self._unconfirmed_quote_id_counter = 0

    def _add_unconfirmed_cost(self, type_str: str, recurrence_str: str, amount_float: float, currency_str: str='USD', description_str: str='Test cost description') -> str:
        quote_id = f'temp_quote_{self._unconfirmed_quote_id_counter}'
        self._unconfirmed_quote_id_counter += 1
        DB['unconfirmed_costs'][quote_id] = {'type': type_str, 'recurrence': recurrence_str, 'amount': amount_float, 'currency': currency_str, 'description': description_str, 'confirmation_id': None}
        return quote_id

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_successful_confirmation_project_hourly(self):
        unconfirmed_quote_key = self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=10.0, currency_str='EUR', description_str='Project hourly cost')
        initial_unconfirmed_costs_count = len(DB['unconfirmed_costs'])
        initial_confirmed_costs_count = len(DB['costs'])
        result = confirm_cost(type='project', recurrence='hourly', amount=10.0)
        self.assertIsInstance(result, dict)
        self.assertIn('confirmation_id', result)
        confirmation_id = result['confirmation_id']
        self.assertIsInstance(confirmation_id, str)
        self.assertTrue(len(confirmation_id) > 0, 'Confirmation ID should not be empty')
        self.assertEqual(len(DB['costs']), initial_confirmed_costs_count + 1)
        self.assertIn(confirmation_id, DB['costs'])
        confirmed_cost_details = DB['costs'][confirmation_id]
        self.assertEqual(confirmed_cost_details['type'], 'project')
        self.assertEqual(confirmed_cost_details['recurrence'], 'hourly')
        self.assertEqual(confirmed_cost_details['amount'], 10.0)
        self.assertEqual(confirmed_cost_details['currency'], 'EUR')
        self.assertEqual(confirmed_cost_details['description'], 'Project hourly cost')
        self.assertEqual(confirmed_cost_details['confirmation_id'], confirmation_id)
        self.assertEqual(len(DB['unconfirmed_costs']), initial_unconfirmed_costs_count - 1)
        self.assertNotIn(unconfirmed_quote_key, DB['unconfirmed_costs'])

    def test_successful_confirmation_branch_monthly(self):
        unconfirmed_quote_key = self._add_unconfirmed_cost(type_str='branch', recurrence_str='monthly', amount_float=5.5)
        initial_unconfirmed_costs_count = len(DB['unconfirmed_costs'])
        result = confirm_cost(type='branch', recurrence='monthly', amount=5.5)
        self.assertIsInstance(result, dict)
        self.assertIn('confirmation_id', result)
        confirmation_id = result['confirmation_id']
        self.assertIn(confirmation_id, DB['costs'])
        confirmed_cost_details = DB['costs'][confirmation_id]
        self.assertEqual(confirmed_cost_details['type'], 'branch')
        self.assertEqual(confirmed_cost_details['recurrence'], 'monthly')
        self.assertEqual(confirmed_cost_details['amount'], 5.5)
        self.assertEqual(confirmed_cost_details['currency'], 'USD')
        self.assertEqual(confirmed_cost_details['description'], 'Test cost description')
        self.assertEqual(confirmed_cost_details['confirmation_id'], confirmation_id)
        self.assertEqual(len(DB['unconfirmed_costs']), initial_unconfirmed_costs_count - 1)
        self.assertNotIn(unconfirmed_quote_key, DB['unconfirmed_costs'])

    def test_successful_confirmation_picks_first_match_and_removes_it(self):
        quote_key1 = self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=20.0, description_str='First quote')
        quote_key2 = self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=20.0, description_str='Second quote identical details')
        self._add_unconfirmed_cost(type_str='branch', recurrence_str='monthly', amount_float=15.0, description_str='Different quote')
        initial_unconfirmed_costs_count = len(DB['unconfirmed_costs'])
        initial_costs_count = len(DB['costs'])
        result = confirm_cost(type='project', recurrence='hourly', amount=20.0)
        confirmation_id = result['confirmation_id']
        self.assertEqual(len(DB['costs']), initial_costs_count + 1)
        self.assertIn(confirmation_id, DB['costs'])
        self.assertEqual(len(DB['unconfirmed_costs']), initial_unconfirmed_costs_count - 1)
        self.assertNotIn(quote_key1, DB['unconfirmed_costs'])
        self.assertIn(quote_key2, DB['unconfirmed_costs'])
        self.assertEqual(DB['costs'][confirmation_id]['description'], 'First quote')

    def test_invalid_input_error_no_matching_unconfirmed_cost_type_mismatch(self):
        self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=10.0)
        initial_unconfirmed_costs = copy.deepcopy(DB['unconfirmed_costs'])
        initial_costs = copy.deepcopy(DB['costs'])
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='No matching unconfirmed cost quote found for the provided details.', type='branch', recurrence='hourly', amount=10.0)
        self.assertEqual(DB['unconfirmed_costs'], initial_unconfirmed_costs)
        self.assertEqual(DB['costs'], initial_costs)

    def test_invalid_input_error_no_matching_unconfirmed_cost_recurrence_mismatch(self):
        self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=10.0)
        initial_unconfirmed_costs = copy.deepcopy(DB['unconfirmed_costs'])
        initial_costs = copy.deepcopy(DB['costs'])
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='No matching unconfirmed cost quote found for the provided details.', type='project', recurrence='monthly', amount=10.0)
        self.assertEqual(DB['unconfirmed_costs'], initial_unconfirmed_costs)
        self.assertEqual(DB['costs'], initial_costs)

    def test_invalid_input_error_no_matching_unconfirmed_cost_amount_mismatch(self):
        self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=10.0)
        initial_unconfirmed_costs = copy.deepcopy(DB['unconfirmed_costs'])
        initial_costs = copy.deepcopy(DB['costs'])
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='No matching unconfirmed cost quote found for the provided details.', type='project', recurrence='hourly', amount=10.01)
        self.assertEqual(DB['unconfirmed_costs'], initial_unconfirmed_costs)
        self.assertEqual(DB['costs'], initial_costs)

    def test_invalid_input_error_unconfirmed_costs_is_empty(self):
        initial_costs = copy.deepcopy(DB['costs'])
        self.assertTrue(not DB['unconfirmed_costs'])
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='No matching unconfirmed cost quote found for the provided details.', type='project', recurrence='hourly', amount=10.0)
        self.assertEqual(DB['costs'], initial_costs)
        self.assertTrue(not DB['unconfirmed_costs'])

    def test_invalid_input_error_amount_is_negative(self):
        self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=10.0)
        initial_unconfirmed_costs = copy.deepcopy(DB['unconfirmed_costs'])
        initial_costs = copy.deepcopy(DB['costs'])
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='Cost amount must be positive.', type='project', recurrence='hourly', amount=-10.0)
        self.assertEqual(DB['unconfirmed_costs'], initial_unconfirmed_costs)
        self.assertEqual(DB['costs'], initial_costs)

    def test_invalid_input_error_amount_is_zero(self):
        self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=10.0)
        initial_unconfirmed_costs = copy.deepcopy(DB['unconfirmed_costs'])
        initial_costs = copy.deepcopy(DB['costs'])
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='Cost amount must be positive.', type='project', recurrence='hourly', amount=0.0)
        self.assertEqual(DB['unconfirmed_costs'], initial_unconfirmed_costs)
        self.assertEqual(DB['costs'], initial_costs)

    def test_validation_error_invalid_type_parameter_value(self):
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='Input validation failed', type='invalid_type_value', recurrence='hourly', amount=10.0)

    def test_validation_error_invalid_recurrence_parameter_value(self):
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='Input validation failed', type='project', recurrence='invalid_recurrence_value', amount=10.0)

    def test_validation_error_amount_not_a_float(self):
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='Input validation failed', type='project', recurrence='hourly', amount='not_a_float_value')

    def test_successful_confirmation_with_float_amount_precision(self):
        amount_val = 10.123456789
        unconfirmed_quote_key = self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=amount_val)
        result = confirm_cost(type='project', recurrence='hourly', amount=amount_val)
        self.assertIn('confirmation_id', result)
        confirmation_id = result['confirmation_id']
        self.assertEqual(DB['costs'][confirmation_id]['amount'], amount_val)
        self.assertNotIn(unconfirmed_quote_key, DB['unconfirmed_costs'])
        different_close_amount = 10.123456788
        self._add_unconfirmed_cost(type_str='project', recurrence_str='hourly', amount_float=different_close_amount, description_str='Slightly different amount quote')
        self.assert_error_behavior(func_to_call=confirm_cost, expected_exception_type=custom_errors.InvalidInputError, expected_message='No matching unconfirmed cost quote found for the provided details.', type='project', recurrence='hourly', amount=10.123)

    def test_multiple_successful_confirmations_managed_correctly(self):
        quote_key_project_hourly = self._add_unconfirmed_cost('project', 'hourly', 25.0)
        quote_key_branch_monthly = self._add_unconfirmed_cost('branch', 'monthly', 7.5)
        quote_key_project_monthly = self._add_unconfirmed_cost('project', 'monthly', 50.0)
        initial_unconfirmed_count = len(DB['unconfirmed_costs'])
        initial_confirmed_count = len(DB['costs'])
        result1 = confirm_cost(type='project', recurrence='hourly', amount=25.0)
        conf_id1 = result1['confirmation_id']
        self.assertIn(conf_id1, DB['costs'])
        self.assertEqual(DB['costs'][conf_id1]['amount'], 25.0)
        self.assertEqual(len(DB['unconfirmed_costs']), initial_unconfirmed_count - 1)
        self.assertNotIn(quote_key_project_hourly, DB['unconfirmed_costs'])
        self.assertEqual(len(DB['costs']), initial_confirmed_count + 1)
        result2 = confirm_cost(type='branch', recurrence='monthly', amount=7.5)
        conf_id2 = result2['confirmation_id']
        self.assertIn(conf_id2, DB['costs'])
        self.assertEqual(DB['costs'][conf_id2]['amount'], 7.5)
        self.assertEqual(len(DB['unconfirmed_costs']), initial_unconfirmed_count - 2)
        self.assertNotIn(quote_key_branch_monthly, DB['unconfirmed_costs'])
        self.assertEqual(len(DB['costs']), initial_confirmed_count + 2)
        self.assertNotEqual(conf_id1, conf_id2)
        self.assertIn(quote_key_project_monthly, DB['unconfirmed_costs'])
        self.assertEqual(DB['unconfirmed_costs'][quote_key_project_monthly]['amount'], 50.0)

    def test_malformed_quote_data_handling(self):
        # Add a quote with missing required fields
        quote_id = 'malformed_quote'
        DB['unconfirmed_costs'][quote_id] = {
            'type': 'project',
            # Missing recurrence
            'amount': 10.0,
            'currency': 'USD',
            'description': 'Malformed quote'
        }
        
        # Add a valid quote that should be matched
        valid_quote_id = self._add_unconfirmed_cost('project', 'hourly', 10.0)
        
        # Should still work with the valid quote
        result = confirm_cost(type='project', recurrence='hourly', amount=10.0)
        self.assertIn('confirmation_id', result)
        
        # The malformed quote should still be in unconfirmed_costs since it was skipped
        self.assertIn(quote_id, DB['unconfirmed_costs'])
        # The valid quote should be removed
        self.assertNotIn(valid_quote_id, DB['unconfirmed_costs'])
        
        # Verify the malformed quote wasn't modified
        self.assertEqual(DB['unconfirmed_costs'][quote_id]['type'], 'project')
        self.assertEqual(DB['unconfirmed_costs'][quote_id]['amount'], 10.0)
        self.assertEqual(DB['unconfirmed_costs'][quote_id]['currency'], 'USD')
        self.assertEqual(DB['unconfirmed_costs'][quote_id]['description'], 'Malformed quote')
        self.assertNotIn('recurrence', DB['unconfirmed_costs'][quote_id])

    def test_float_comparison_with_epsilon(self):
        # Test with very close float values
        amount = 10.123456789
        unconfirmed_quote_key = self._add_unconfirmed_cost('project', 'hourly', amount)
        
        # Should match with slightly different float representation
        result = confirm_cost(type='project', recurrence='hourly', amount=10.123456789)
        self.assertIn('confirmation_id', result)
        self.assertNotIn(unconfirmed_quote_key, DB['unconfirmed_costs'])

    def test_missing_field_in_confirmed_cost_entry(self):
        # Add a quote with missing currency field
        quote_id = 'incomplete_quote'
        DB['unconfirmed_costs'][quote_id] = {
            'type': 'project',
            'recurrence': 'hourly',
            'amount': 10.0,
            # Missing currency
            'description': 'Incomplete quote'
        }
        
        # Should raise InvalidInputError when trying to create confirmed cost entry
        self.assert_error_behavior(
            func_to_call=confirm_cost,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Matched quote is malformed and cannot be confirmed. Missing field: 'currency'",
            type='project',
            recurrence='hourly',
            amount=10.0
        )
    
    def test_unconfirmed_cost_removal_edge_cases(self):
        # Test when unconfirmed_costs is not in DB
        DB.clear()
        DB.update({
            'organizations': [], 
            'projects': [], 
            'tables': {}, 
            'extensions': {}, 
            'migrations': {}, 
            'edge_functions': {}, 
            'branches': {}, 
            'costs': {}, 
            'unconfirmed_costs': {},  # Initialize unconfirmed_costs
            'project_urls': {}, 
            'project_anon_keys': {}, 
            'project_ts_types': {}, 
            'logs': {}
        })
        
        # Add a quote
        quote_id = self._add_unconfirmed_cost('project', 'hourly', 10.0)
        
        # Should still work and remove the quote
        result = confirm_cost(type='project', recurrence='hourly', amount=10.0)
        self.assertIn('confirmation_id', result)
        self.assertNotIn(quote_id, DB.get('unconfirmed_costs', {}))

    def test_costs_dictionary_initialization(self):
        # Clear DB and initialize without costs dictionary
        DB.clear()
        DB.update({
            'organizations': [], 
            'projects': [], 
            'tables': {}, 
            'extensions': {}, 
            'migrations': {}, 
            'edge_functions': {}, 
            'branches': {}, 
            'unconfirmed_costs': {}, 
            'project_urls': {}, 
            'project_anon_keys': {}, 
            'project_ts_types': {}, 
            'logs': {}
        })
        
        # Add a quote
        quote_id = self._add_unconfirmed_cost('project', 'hourly', 10.0)
        
        # Confirm the cost
        result = confirm_cost(type='project', recurrence='hourly', amount=10.0)
        
        # Verify costs dictionary was created and contains the confirmed cost
        self.assertIn('costs', DB)
        self.assertIsInstance(DB['costs'], dict)
        self.assertIn(result['confirmation_id'], DB['costs'])
        confirmed_cost = DB['costs'][result['confirmation_id']]
        self.assertEqual(confirmed_cost['type'], 'project')
        self.assertEqual(confirmed_cost['recurrence'], 'hourly')
        self.assertEqual(confirmed_cost['amount'], 10.0)

if __name__ == '__main__':
    unittest.main()