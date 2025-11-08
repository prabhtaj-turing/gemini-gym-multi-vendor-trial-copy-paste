import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..management import azmcp_subscription_list

class TestAzmcpSubscriptionList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['subscriptions'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_subscription_to_db(self, sub_guid: str, display_name: str, state: str, tenant_id: str):
        DB['subscriptions'].append({'id': f'/subscriptions/{sub_guid}', 'subscriptionId': sub_guid, 'displayName': display_name, 'state': state, 'tenantId': tenant_id, 'resource_groups': []})

    def _get_expected_subscription_dict(self, sub_guid: str, display_name: str, state: str, tenant_id: str) -> dict:
        return {'id': sub_guid, 'subscriptionId': sub_guid, 'displayName': display_name, 'state': state, 'tenantId': tenant_id}

    def test_list_subscriptions_empty_db(self):
        result = azmcp_subscription_list()
        self.assertEqual(result, [])

    def test_list_subscriptions_single_subscription(self):
        self._add_subscription_to_db('sub-guid-1', 'Subscription One', 'Enabled', 'tenant-A')
        expected_output = [self._get_expected_subscription_dict('sub-guid-1', 'Subscription One', 'Enabled', 'tenant-A')]
        result = azmcp_subscription_list()
        self.assertEqual(result, expected_output)

    def test_list_subscriptions_multiple_subscriptions(self):
        self._add_subscription_to_db('sub-guid-1', 'Subscription One', 'Enabled', 'tenant-A')
        self._add_subscription_to_db('sub-guid-2', 'Subscription Two', 'Disabled', 'tenant-B')
        self._add_subscription_to_db('sub-guid-3', 'Subscription Three', 'Warned', 'tenant-A')
        expected_output = [self._get_expected_subscription_dict('sub-guid-1', 'Subscription One', 'Enabled', 'tenant-A'), self._get_expected_subscription_dict('sub-guid-2', 'Subscription Two', 'Disabled', 'tenant-B'), self._get_expected_subscription_dict('sub-guid-3', 'Subscription Three', 'Warned', 'tenant-A')]
        result = azmcp_subscription_list()
        self.assertCountEqual(result, expected_output)

    def test_list_subscriptions_with_tenant_filter_success(self):
        self._add_subscription_to_db('sub-guid-1', 'Alpha Sub', 'Enabled', 'tenant-alpha')
        self._add_subscription_to_db('sub-guid-2', 'Beta Sub', 'Enabled', 'tenant-beta')
        self._add_subscription_to_db('sub-guid-3', 'Gamma Sub', 'Enabled', 'tenant-alpha')
        expected_output = [self._get_expected_subscription_dict('sub-guid-1', 'Alpha Sub', 'Enabled', 'tenant-alpha'), self._get_expected_subscription_dict('sub-guid-3', 'Gamma Sub', 'Enabled', 'tenant-alpha')]
        result = azmcp_subscription_list(tenant='tenant-alpha')
        self.assertCountEqual(result, expected_output)

    def test_list_subscriptions_with_nonexistent_tenant_raises_tenantnotfounderror(self):
        self._add_subscription_to_db('sub-guid-1', 'Alpha Sub', 'Enabled', 'tenant-alpha')
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.TenantNotFoundError,
            expected_message='The specified Azure tenant was not found or is inaccessible.',
            tenant='non-existent-tenant-id')

    def test_list_subscriptions_empty_db_with_tenant_filter_raises_tenantnotfounderror(self):
        self.assertTrue(not DB['subscriptions'])
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.TenantNotFoundError, expected_message='The specified Azure tenant was not found or is inaccessible.', tenant='any-tenant-id')

    def test_list_subscriptions_tenant_filter_is_case_sensitive(self):
        self._add_subscription_to_db('sub-case-1', 'Case Sub Upper', 'Enabled', 'Tenant-Alpha')
        expected_match = [self._get_expected_subscription_dict('sub-case-1', 'Case Sub Upper', 'Enabled', 'Tenant-Alpha')]
        result_match = azmcp_subscription_list(tenant='Tenant-Alpha')
        self.assertCountEqual(result_match, expected_match)
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.TenantNotFoundError, expected_message='The specified Azure tenant was not found or is inaccessible.', tenant='tenant-alpha')
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.TenantNotFoundError, expected_message='The specified Azure tenant was not found or is inaccessible.', tenant='TENANT-ALPHA')

    def test_list_subscriptions_with_valid_auth_methods(self):
        self._add_subscription_to_db('sub-guid-1', 'Test Sub', 'Enabled', 'tenant-default')
        expected_output = [self._get_expected_subscription_dict('sub-guid-1', 'Test Sub', 'Enabled', 'tenant-default')]
        for auth_method in ['credential', 'key', 'connectionString']:
            with self.subTest(auth_method=auth_method):
                result = azmcp_subscription_list(auth_method=auth_method)
                self.assertEqual(result, expected_output)

    def test_list_subscriptions_with_none_auth_method(self):
        self._add_subscription_to_db('sub-guid-1', 'Test Sub', 'Enabled', 'tenant-default')
        expected_output = [self._get_expected_subscription_dict('sub-guid-1', 'Test Sub', 'Enabled', 'tenant-default')]
        result = azmcp_subscription_list(auth_method=None)
        self.assertEqual(result, expected_output)

    def test_list_subscriptions_with_invalid_auth_method_raises_validationerror(self):
        expected_msg = "Invalid auth_method: 'invalid_auth'. Allowed values are: credential, key, connectionString."
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.ValidationError, expected_message=expected_msg, auth_method='invalid_auth')

    def test_list_subscriptions_with_valid_retry_parameters(self):
        self._add_subscription_to_db('sub-guid-1', 'Retry Sub', 'Enabled', 'tenant-retry')
        expected_output = [self._get_expected_subscription_dict('sub-guid-1', 'Retry Sub', 'Enabled', 'tenant-retry')]
        retry_params = {'retry_max_retries': '5', 'retry_delay': '2', 'retry_max_delay': '120', 'retry_mode': 'exponential', 'retry_network_timeout': '60'}
        result = azmcp_subscription_list(**retry_params)
        self.assertEqual(result, expected_output)
        retry_params_fixed = {**retry_params, 'retry_mode': 'fixed'}
        result_fixed = azmcp_subscription_list(**retry_params_fixed)
        self.assertEqual(result_fixed, expected_output)
        result_none_retry = azmcp_subscription_list(retry_max_retries=None, retry_delay=None, retry_max_delay=None, retry_mode=None, retry_network_timeout=None)
        self.assertEqual(result_none_retry, expected_output)

    def test_list_subscriptions_with_invalid_retry_max_retries_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'retry_max_retries' ('not-a-number') is not a valid string representation of an integer.",
            retry_max_retries='not-a-number')

    def test_list_subscriptions_with_invalid_retry_delay_raises_validationerror(self):
        expected_msg = "Parameter 'retry_delay' ('abc') is not a valid string representation of a number."
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.ValidationError, expected_message=expected_msg, retry_delay='abc')

    def test_list_subscriptions_with_invalid_retry_max_delay_raises_validationerror(self):
        expected_msg = "Parameter 'retry_max_delay' ('xyz') is not a valid string representation of a number."
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.ValidationError, expected_message=expected_msg, retry_max_delay='xyz')

    def test_list_subscriptions_with_invalid_retry_mode_raises_validationerror(self):
        expected_msg = "Invalid retry_mode: 'unsupported_mode'. Allowed values are: fixed, exponential."
        self.assert_error_behavior(func_to_call=azmcp_subscription_list, expected_exception_type=custom_errors.ValidationError, expected_message=expected_msg, retry_mode='unsupported_mode')

    def test_list_subscriptions_with_invalid_retry_network_timeout_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'retry_network_timeout' ('foo') is not a valid string representation of a number.",
            retry_network_timeout='foo')

    def test_list_subscriptions_id_field_is_guid(self):
        sub_guid = '00000000-0000-0000-0000-000000000001'
        self._add_subscription_to_db(sub_guid, 'GUID Test Sub', 'Enabled', 'tenant-guid-test')
        result = azmcp_subscription_list()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], sub_guid)
        self.assertEqual(result[0]['subscriptionId'], sub_guid)
        self.assertEqual(result[0]['displayName'], 'GUID Test Sub')
        self.assertEqual(result[0]['state'], 'Enabled')
        self.assertEqual(result[0]['tenantId'], 'tenant-guid-test')

    def test_list_subscriptions_various_states(self):
        self._add_subscription_to_db('sub-s1', 'State Sub 1', 'Enabled', 'tenant-state')
        self._add_subscription_to_db('sub-s2', 'State Sub 2', 'Warned', 'tenant-state')
        self._add_subscription_to_db('sub-s3', 'State Sub 3', 'PastDue', 'tenant-state')
        self._add_subscription_to_db('sub-s4', 'State Sub 4', 'Disabled', 'tenant-state')
        expected = [self._get_expected_subscription_dict('sub-s1', 'State Sub 1', 'Enabled', 'tenant-state'), self._get_expected_subscription_dict('sub-s2', 'State Sub 2', 'Warned', 'tenant-state'), self._get_expected_subscription_dict('sub-s3', 'State Sub 3', 'PastDue', 'tenant-state'), self._get_expected_subscription_dict('sub-s4', 'State Sub 4', 'Disabled', 'tenant-state')]
        result = azmcp_subscription_list()
        self.assertCountEqual(result, expected)
    
    def test_list_subscriptions_with_negative_retry_max_retries_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'retry_max_retries' must be 0 or greater, but received '-1' (evaluates to -1).",
            retry_max_retries='-1')

    def test_list_subscriptions_with_negative_retry_delay_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'retry_delay' must be 0 or greater, but received '-1' (evaluates to -1.0).",
            retry_delay='-1')
    
    def test_list_subscriptions_with_negative_retry_max_delay_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'retry_max_delay' must be 0 or greater, but received '-1' (evaluates to -1.0).",
            retry_max_delay='-1')
    
    def test_list_subscriptions_with_negative_retry_network_timeout_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'retry_network_timeout' must be 0 or greater, but received '-1' (evaluates to -1.0).",
            retry_network_timeout='-1')
    
    def test_list_subscriptions_with_retry_max_delay_less_than_retry_delay_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_subscription_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_max_delay ('1') cannot be less than retry_delay ('2').",
            retry_max_delay='1',
            retry_delay='2')
            

if __name__ == '__main__':
    unittest.main()