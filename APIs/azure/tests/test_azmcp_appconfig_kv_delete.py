import unittest
import copy
from datetime import datetime, timezone
from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..appconfig import azmcp_appconfig_kv_delete
from ..SimulationEngine.db import DB

class TestAzmcpAppconfigKvDelete(BaseTestCaseWithErrorHandler):
    SUB_ID = '00000000-0000-0000-0000-000000000001'
    RG_NAME = 'TestRg'
    STORE_NAME = 'TestAppConfigStore'
    EMPTY_STORE_NAME = 'EmptyAppConfigStore'
    KEY_1 = 'TestKey1'
    KEY_2 = 'TestKey2'
    LABEL_PROD = 'Prod'
    LABEL_DEV = 'Dev'

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.now_iso = datetime.now(timezone.utc).isoformat()
        self.kv_key1_default = {'key': self.KEY_1, 'value': 'v1_default', 'label': None, 'content_type': 'text/plain', 'locked': False, 'etag': 'etag1_default', 'last_modified': self.now_iso, 'app_config_store_name': self.STORE_NAME}
        self.kv_key1_prod = {'key': self.KEY_1, 'value': 'v1_prod', 'label': self.LABEL_PROD, 'content_type': 'application/json', 'locked': True, 'etag': 'etag1_prod', 'last_modified': self.now_iso, 'app_config_store_name': self.STORE_NAME}
        self.kv_key2_dev = {'key': self.KEY_2, 'value': 'v2_dev', 'label': self.LABEL_DEV, 'content_type': 'text/xml', 'locked': False, 'etag': 'etag2_dev', 'last_modified': self.now_iso, 'app_config_store_name': self.STORE_NAME}
        DB['subscriptions'] = [{'id': f'/subscriptions/{self.SUB_ID}', 'subscriptionId': self.SUB_ID, 'displayName': 'Test Subscription', 'state': 'Enabled', 'tenantId': 'tenant-id-example', 'resource_groups': [{'id': f'/subscriptions/{self.SUB_ID}/resourceGroups/{self.RG_NAME}', 'name': self.RG_NAME, 'location': 'eastus', 'subscription_id': self.SUB_ID, 'app_config_stores': [{'id': f'/subscriptions/{self.SUB_ID}/resourceGroups/{self.RG_NAME}/providers/Microsoft.AppConfiguration/configurationStores/{self.STORE_NAME}', 'name': self.STORE_NAME, 'location': 'eastus', 'resource_group_name': self.RG_NAME, 'subscription_id': self.SUB_ID, 'key_values': [copy.deepcopy(self.kv_key1_default), copy.deepcopy(self.kv_key1_prod), copy.deepcopy(self.kv_key2_dev)]}, {'id': f'/subscriptions/{self.SUB_ID}/resourceGroups/{self.RG_NAME}/providers/Microsoft.AppConfiguration/configurationStores/{self.EMPTY_STORE_NAME}', 'name': self.EMPTY_STORE_NAME, 'location': 'eastus', 'resource_group_name': self.RG_NAME, 'subscription_id': self.SUB_ID, 'key_values': []}]}]}]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_store_kvs_ref(self, sub_id, rg_name, store_name):
        for sub in DB.get('subscriptions', []):
            if sub['subscriptionId'] == sub_id:
                for rg in sub.get('resource_groups', []):
                    if rg['name'] == rg_name:
                        for store in rg.get('app_config_stores', []):
                            if store['name'] == store_name:
                                return store.get('key_values')
        return None

    def _find_kv_in_list(self, kv_list, key, label):
        for kv_item in kv_list:
            if kv_item['key'] == key and kv_item['label'] == label:
                return kv_item
        return None

    def test_delete_kv_with_default_label_success(self):
        result = azmcp_appconfig_kv_delete(subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_1)
        self.assertEqual(result, {})
        store_kvs = self._get_store_kvs_ref(self.SUB_ID, self.RG_NAME, self.STORE_NAME)
        self.assertIsNotNone(store_kvs)
        self.assertEqual(len(store_kvs), 2)
        self.assertIsNone(self._find_kv_in_list(store_kvs, self.KEY_1, None))
        self.assertIsNotNone(self._find_kv_in_list(store_kvs, self.KEY_1, self.LABEL_PROD))
        self.assertIsNotNone(self._find_kv_in_list(store_kvs, self.KEY_2, self.LABEL_DEV))

    def test_delete_kv_with_specific_label_success(self):
        result = azmcp_appconfig_kv_delete(subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_1, label=self.LABEL_PROD)
        self.assertEqual(result, {})
        store_kvs = self._get_store_kvs_ref(self.SUB_ID, self.RG_NAME, self.STORE_NAME)
        self.assertIsNotNone(store_kvs)
        self.assertEqual(len(store_kvs), 2)
        self.assertIsNone(self._find_kv_in_list(store_kvs, self.KEY_1, self.LABEL_PROD))
        self.assertIsNotNone(self._find_kv_in_list(store_kvs, self.KEY_1, None))
        self.assertIsNotNone(self._find_kv_in_list(store_kvs, self.KEY_2, self.LABEL_DEV))

    def test_delete_last_kv_for_key_success(self):
        azmcp_appconfig_kv_delete(subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_1, label=self.LABEL_PROD)
        result = azmcp_appconfig_kv_delete(subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_1)
        self.assertEqual(result, {})
        store_kvs = self._get_store_kvs_ref(self.SUB_ID, self.RG_NAME, self.STORE_NAME)
        self.assertIsNotNone(store_kvs)
        self.assertEqual(len(store_kvs), 1)
        self.assertIsNone(self._find_kv_in_list(store_kvs, self.KEY_1, None))
        self.assertIsNone(self._find_kv_in_list(store_kvs, self.KEY_1, self.LABEL_PROD))
        self.assertIsNotNone(self._find_kv_in_list(store_kvs, self.KEY_2, self.LABEL_DEV))

    def test_delete_kv_with_all_optional_params_provided_success(self):
        result = azmcp_appconfig_kv_delete(subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_2, label=self.LABEL_DEV, auth_method='credential', retry_delay='1', retry_max_delay='10', retry_max_retries='3', retry_mode='exponential', retry_network_timeout='30', tenant='some-tenant-id')
        self.assertEqual(result, {})
        store_kvs = self._get_store_kvs_ref(self.SUB_ID, self.RG_NAME, self.STORE_NAME)
        self.assertIsNotNone(store_kvs)
        self.assertEqual(len(store_kvs), 2)
        self.assertIsNone(self._find_kv_in_list(store_kvs, self.KEY_2, self.LABEL_DEV))

    def test_delete_kv_missing_subscription_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_delete,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Subscription is required.',
            subscription=None,
            account_name=self.STORE_NAME,
            key=self.KEY_1)

    def test_delete_kv_missing_account_name_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_delete,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Account name is required.',
            subscription=self.SUB_ID,
            account_name=None,
            key=self.KEY_1)

    def test_delete_kv_missing_key_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_delete,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Key is required.',
            subscription=self.SUB_ID,
            account_name=self.STORE_NAME,
            key=None)

    def test_delete_kv_empty_subscription_raises_invalidinputerror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.InvalidInputError, expected_message='Subscription cannot be empty.', subscription='', account_name=self.STORE_NAME, key=self.KEY_1)

    def test_delete_kv_empty_account_name_raises_invalidinputerror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.InvalidInputError, expected_message='Account name cannot be empty.', subscription=self.SUB_ID, account_name='', key=self.KEY_1)

    def test_delete_kv_empty_key_raises_invalidinputerror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.InvalidInputError, expected_message='Key cannot be empty.', subscription=self.SUB_ID, account_name=self.STORE_NAME, key='')

    def test_delete_kv_subscription_not_found_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Subscription 'nonexistentsub' not found.", subscription='nonexistentsub', account_name=self.STORE_NAME, key=self.KEY_1)

    def test_delete_kv_resource_group_not_found_raises_resourcenotfounderror(self):
        DB['subscriptions'][0]['resource_groups'] = []
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"App Configuration store '{self.STORE_NAME}' not found in subscription '{self.SUB_ID}'.", subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_1)

    def test_delete_kv_store_not_found_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"App Configuration store 'nonexistentstore' not found in subscription '{self.SUB_ID}'.", subscription=self.SUB_ID, account_name='nonexistentstore', key=self.KEY_1)

    def test_delete_kv_key_not_found_default_label_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Key-value with key 'NonExistentKey' and default label not found in store '{self.STORE_NAME}'.", subscription=self.SUB_ID, account_name=self.STORE_NAME, key='NonExistentKey')

    def test_delete_kv_key_not_found_specific_label_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Key-value with key 'NonExistentKey' and label '{self.LABEL_PROD}' not found in store '{self.STORE_NAME}'.", subscription=self.SUB_ID, account_name=self.STORE_NAME, key='NonExistentKey', label=self.LABEL_PROD)

    def test_delete_kv_key_exists_but_label_mismatch_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Key-value with key '{self.KEY_1}' and label '{self.LABEL_DEV}' not found in store '{self.STORE_NAME}'.", subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_1, label=self.LABEL_DEV)

    def test_delete_kv_key_exists_with_label_but_no_default_when_none_specified_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Key-value with key '{self.KEY_2}' and default label not found in store '{self.STORE_NAME}'.", subscription=self.SUB_ID, account_name=self.STORE_NAME, key=self.KEY_2)

    def test_delete_kv_from_empty_store_raises_resourcenotfounderror(self):
        self.assert_error_behavior(func_to_call=azmcp_appconfig_kv_delete, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Key-value with key '{self.KEY_1}' and default label not found in store '{self.EMPTY_STORE_NAME}'.", subscription=self.SUB_ID, account_name=self.EMPTY_STORE_NAME, key=self.KEY_1)
if __name__ == '__main__':
    unittest.main()