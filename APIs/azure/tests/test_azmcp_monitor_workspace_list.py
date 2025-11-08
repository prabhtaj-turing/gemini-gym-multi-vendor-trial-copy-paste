import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..loganalytics import azmcp_monitor_workspace_list
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestAzmcpMonitorWorkspaceList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.sub_id1 = '00000000-0000-0000-0000-000000000001'
        self.sub_id2_no_ws = '00000000-0000-0000-0000-000000000002'
        self.sub_id3_no_rgs = '00000000-0000-0000-0000-000000000003'
        self.sub_id4_empty_rgs_list = '00000000-0000-0000-0000-000000000004'
        self.sub_id5_rg_no_ws_list_key = '00000000-0000-0000-0000-000000000005'
        self.sub_id6_rg_empty_ws_list = '00000000-0000-0000-0000-000000000006'
        self.sub_id7_ws_missing_fields = '00000000-0000-0000-0000-000000000007'
        self.sub_id8_rg_ws_list_is_none = '00000000-0000-0000-0000-000000000008'
        DB['subscriptions'] = [{'id': f'/subscriptions/{self.sub_id1}', 'subscriptionId': self.sub_id1, 'displayName': 'Subscription 1', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg1', 'name': 'rg1', 'location': 'eastus', 'subscription_id': self.sub_id1, 'log_analytics_workspaces': [{'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg1/providers/Microsoft.OperationalInsights/workspaces/ws1', 'name': 'ws1', 'location': 'eastus', 'customerId': 'cust-id-ws1', 'sku': {'name': 'PerGB2018'}, 'provisioningState': 'Succeeded', 'resource_group_name': 'rg1', 'subscription_id': self.sub_id1}, {'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg1/providers/Microsoft.OperationalInsights/workspaces/ws2', 'name': 'ws2', 'location': 'westus', 'customerId': 'cust-id-ws2', 'sku': {'name': 'Standalone'}, 'provisioningState': 'Creating', 'resource_group_name': 'rg1', 'subscription_id': self.sub_id1}]}, {'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg2', 'name': 'rg2', 'location': 'centralus', 'subscription_id': self.sub_id1, 'log_analytics_workspaces': [{'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg2/providers/Microsoft.OperationalInsights/workspaces/ws3', 'name': 'ws3', 'location': 'centralus', 'customerId': 'cust-id-ws3', 'sku': {'name': 'PerGB2018'}, 'provisioningState': 'Succeeded', 'resource_group_name': 'rg2', 'subscription_id': self.sub_id1}]}, {'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg3-empty-ws', 'name': 'rg3-empty-ws', 'location': 'eastus', 'subscription_id': self.sub_id1, 'log_analytics_workspaces': []}]}, {'id': f'/subscriptions/{self.sub_id2_no_ws}', 'subscriptionId': self.sub_id2_no_ws, 'displayName': 'Subscription 2 (No Workspaces)', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id2_no_ws}/resourceGroups/rg4-empty-ws', 'name': 'rg4-empty-ws', 'location': 'eastus', 'subscription_id': self.sub_id2_no_ws, 'log_analytics_workspaces': []}]}, {'id': f'/subscriptions/{self.sub_id3_no_rgs}', 'subscriptionId': self.sub_id3_no_rgs, 'displayName': 'Subscription 3 (No RGs key)', 'state': 'Enabled', 'tenantId': 'tenant-001'}, {'id': f'/subscriptions/{self.sub_id4_empty_rgs_list}', 'subscriptionId': self.sub_id4_empty_rgs_list, 'displayName': 'Subscription 4 (Empty RGs List)', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': []}, {'id': f'/subscriptions/{self.sub_id5_rg_no_ws_list_key}', 'subscriptionId': self.sub_id5_rg_no_ws_list_key, 'displayName': 'Subscription 5 (RG no WS list key)', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id5_rg_no_ws_list_key}/resourceGroups/rg5', 'name': 'rg5', 'location': 'eastus', 'subscription_id': self.sub_id5_rg_no_ws_list_key}]}, {'id': f'/subscriptions/{self.sub_id6_rg_empty_ws_list}', 'subscriptionId': self.sub_id6_rg_empty_ws_list, 'displayName': 'Subscription 6 (RG empty WS list)', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id6_rg_empty_ws_list}/resourceGroups/rg6', 'name': 'rg6', 'location': 'eastus', 'subscription_id': self.sub_id6_rg_empty_ws_list, 'log_analytics_workspaces': []}]}, {'id': f'/subscriptions/{self.sub_id7_ws_missing_fields}', 'subscriptionId': self.sub_id7_ws_missing_fields, 'displayName': 'Subscription 7 (WS missing fields)', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id7_ws_missing_fields}/resourceGroups/rg7', 'name': 'rg7', 'location': 'eastus', 'subscription_id': self.sub_id7_ws_missing_fields, 'log_analytics_workspaces': [{'id': f'/subscriptions/{self.sub_id7_ws_missing_fields}/resourceGroups/rg7/providers/Microsoft.OperationalInsights/workspaces/ws-valid', 'name': 'ws-valid', 'location': 'eastus', 'customerId': 'cust-id-valid', 'sku': {'name': 'PerGB2018'}, 'provisioningState': 'Succeeded', 'resource_group_name': 'rg7', 'subscription_id': self.sub_id7_ws_missing_fields}, {'id': f'/subscriptions/{self.sub_id7_ws_missing_fields}/resourceGroups/rg7/providers/Microsoft.OperationalInsights/workspaces/ws-no-custid', 'name': 'ws-no-custid', 'location': 'eastus', 'customerId': None, 'sku': {'name': 'PerGB2018'}, 'provisioningState': 'Succeeded', 'resource_group_name': 'rg7', 'subscription_id': self.sub_id7_ws_missing_fields}, {'id': f'/subscriptions/{self.sub_id7_ws_missing_fields}/resourceGroups/rg7/providers/Microsoft.OperationalInsights/workspaces/ws-no-sku', 'name': 'ws-no-sku', 'location': 'eastus', 'customerId': 'cust-id-no-sku', 'sku': None, 'provisioningState': 'Succeeded', 'resource_group_name': 'rg7', 'subscription_id': self.sub_id7_ws_missing_fields}, {'id': f'/subscriptions/{self.sub_id7_ws_missing_fields}/resourceGroups/rg7/providers/Microsoft.OperationalInsights/workspaces/ws-no-provstate', 'name': 'ws-no-provstate', 'location': 'eastus', 'customerId': 'cust-id-no-provstate', 'sku': {'name': 'PerGB2018'}, 'provisioningState': None, 'resource_group_name': 'rg7', 'subscription_id': self.sub_id7_ws_missing_fields}]}]}, {'id': f'/subscriptions/{self.sub_id8_rg_ws_list_is_none}', 'subscriptionId': self.sub_id8_rg_ws_list_is_none, 'displayName': 'Subscription 8 (RG WS list is None)', 'state': 'Enabled', 'tenantId': 'tenant-001', 'resource_groups': [{'id': f'/subscriptions/{self.sub_id8_rg_ws_list_is_none}/resourceGroups/rg8', 'name': 'rg8', 'location': 'eastus', 'subscription_id': self.sub_id8_rg_ws_list_is_none, 'log_analytics_workspaces': None}]}]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_workspaces_success_multiple_rgs_multiple_ws(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id1)
        self.assertEqual(len(result), 3)
        expected_ws_data = [{'name': 'ws1', 'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg1/providers/Microsoft.OperationalInsights/workspaces/ws1', 'location': 'eastus', 'customerId': 'cust-id-ws1', 'sku': {'name': 'PerGB2018'}, 'provisioningState': 'Succeeded'}, {'name': 'ws2', 'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg1/providers/Microsoft.OperationalInsights/workspaces/ws2', 'location': 'westus', 'customerId': 'cust-id-ws2', 'sku': {'name': 'Standalone'}, 'provisioningState': 'Creating'}, {'name': 'ws3', 'id': f'/subscriptions/{self.sub_id1}/resourceGroups/rg2/providers/Microsoft.OperationalInsights/workspaces/ws3', 'location': 'centralus', 'customerId': 'cust-id-ws3', 'sku': {'name': 'PerGB2018'}, 'provisioningState': 'Succeeded'}]
        result_sorted = sorted(result, key=lambda x: x['id'])
        expected_sorted = sorted(expected_ws_data, key=lambda x: x['id'])
        for i in range(len(result_sorted)):
            self.assertDictEqual(result_sorted[i], expected_sorted[i])

    def test_list_workspaces_success_subscription_with_no_workspaces(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id2_no_ws)
        self.assertEqual(len(result), 0)

    def test_list_workspaces_success_subscription_with_no_rgs_key(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id3_no_rgs)
        self.assertEqual(len(result), 0)

    def test_list_workspaces_success_subscription_with_empty_rgs_list(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id4_empty_rgs_list)
        self.assertEqual(len(result), 0)

    def test_list_workspaces_success_rg_with_no_workspaces_list_key(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id5_rg_no_ws_list_key)
        self.assertEqual(len(result), 0)

    def test_list_workspaces_success_rg_with_empty_workspaces_list(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id6_rg_empty_ws_list)
        self.assertEqual(len(result), 0)

    def test_list_workspaces_success_rg_with_ws_list_as_none(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id8_rg_ws_list_is_none)
        self.assertEqual(len(result), 0)

    def test_list_workspaces_filters_out_items_with_missing_mandatory_fields(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id7_ws_missing_fields)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'ws-valid')
        self.assertEqual(result[0]['id'], f'/subscriptions/{self.sub_id7_ws_missing_fields}/resourceGroups/rg7/providers/Microsoft.OperationalInsights/workspaces/ws-valid')
        self.assertEqual(result[0]['location'], 'eastus')
        self.assertEqual(result[0]['customerId'], 'cust-id-valid')
        self.assertDictEqual(result[0]['sku'], {'name': 'PerGB2018'})
        self.assertEqual(result[0]['provisioningState'], 'Succeeded')

    def test_list_workspaces_subscription_not_found_raises_subscriptionnotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.SubscriptionNotFoundError, expected_message='The specified Azure subscription was not found or is not accessible.', subscription='non-existent-sub-id')

    def test_list_workspaces_empty_subscription_id_raises_InvalidInputError(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Subscription argument cannot be empty.', subscription='')

    def test_list_workspaces_with_all_optional_params_provided(self):
        result = azmcp_monitor_workspace_list(subscription=self.sub_id1, auth_method='credential', tenant='tenant-guid-example', retry_max_retries='5', retry_delay='10', retry_max_delay='60', retry_mode='exponential', retry_network_timeout='30')
        self.assertEqual(len(result), 3)

    def test_list_workspaces_invalid_retry_max_retries_raises_InvalidInputError(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Invalid format for retry_max_retries. Must be a string representing an integer.', subscription=self.sub_id1, retry_max_retries='abc')

    def test_list_workspaces_invalid_retry_delay_raises_InvalidInputError(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Invalid format for retry_delay. Must be a string representing a number.', subscription=self.sub_id1, retry_delay='xyz')

    def test_list_workspaces_invalid_retry_max_delay_raises_InvalidInputError(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Invalid format for retry_max_delay. Must be a string representing a number.', subscription=self.sub_id1, retry_max_delay='-')

    def test_list_workspaces_invalid_retry_mode_raises_InvalidInputError(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.InvalidInputError, expected_message="Invalid value for retry_mode. Allowed values are 'fixed', 'exponential'.", subscription=self.sub_id1, retry_mode='unknown_mode')

    def test_list_workspaces_invalid_retry_network_timeout_raises_InvalidInputError(self):
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.InvalidInputError, expected_message='Invalid format for retry_network_timeout. Must be a string representing a number.', subscription=self.sub_id1, retry_network_timeout='non_numeric')

    def test_list_workspaces_can_use_subscription_name(self):
        sub_idx = -1
        for i, sub in enumerate(DB['subscriptions']):
            if sub['subscriptionId'] == self.sub_id1:
                sub_idx = i
                break
        self.assertNotEqual(sub_idx, -1, 'Test setup error: sub_id1 not found.')
        original_display_name = DB['subscriptions'][sub_idx]['displayName']
        DB['subscriptions'][sub_idx]['displayName'] = 'MyUniqueSubscriptionName'
        try:
            result = azmcp_monitor_workspace_list(subscription='MyUniqueSubscriptionName')
            self.assertEqual(len(result), 3, 'Should find workspaces for the subscription matched by name.')
            ws1_found = any((ws['name'] == 'ws1' for ws in result))
            self.assertTrue(ws1_found, "Workspace 'ws1' from the named subscription should be found.")
        finally:
            DB['subscriptions'][sub_idx]['displayName'] = original_display_name

    def test_list_workspaces_db_subscriptions_key_missing(self):
        original_subs = DB.pop('subscriptions', None)
        try:
            self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.SubscriptionNotFoundError, expected_message='The specified Azure subscription was not found or is not accessible.', subscription=self.sub_id1)
        finally:
            if original_subs is not None:
                DB['subscriptions'] = original_subs

    def test_list_workspaces_db_subscriptions_list_empty(self):
        DB['subscriptions'] = []
        self.assert_error_behavior(func_to_call=azmcp_monitor_workspace_list, expected_exception_type=custom_errors.SubscriptionNotFoundError, expected_message='The specified Azure subscription was not found or is not accessible.', subscription=self.sub_id1)
if __name__ == '__main__':
    unittest.main()