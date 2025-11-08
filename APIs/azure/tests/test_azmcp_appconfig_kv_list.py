import copy
import unittest

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.appconfig import azmcp_appconfig_kv_list
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAzmcpAppconfigKvList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sub_id = "test-sub-id-1"
        self.rg_name = "test-rg-1"
        self.store_name1 = "my-appconfig-1"
        self.store_name_empty = "my-appconfig-empty"
        self.store_name_no_kv_list = "my-appconfig-no-kv-list"
        self.non_existent_store_name = "my-appconfig-nonexistent"
        self.non_existent_sub_id = "non-existent-sub-id"

        self.ts1 = "2023-01-01T10:00:00Z"
        self.ts2 = "2023-01-02T12:30:00Z"
        self.ts3 = "2023-01-03T15:45:00Z"

        self.etag1 = "etag_val_1"
        self.etag2 = "etag_val_2"
        self.etag3 = "etag_val_3"
        self.etag4 = "etag_val_4"
        self.etag5 = "etag_val_5"
        self.etag6 = "etag_val_6"
        self.etag7 = "etag_val_7"

        self.resp_kv_item1 = {"key": "App.Setting.Color", "value": "Blue", "label": "Prod",
                              "content_type": "text/plain", "etag": self.etag1, "last_modified": self.ts1,
                              "locked": False}
        self.resp_kv_item2 = {"key": "App.Setting.Version", "value": "1.0", "label": "Prod",
                              "content_type": "application/json", "etag": self.etag2, "last_modified": self.ts2,
                              "locked": True}
        self.resp_kv_item3 = {"key": "App.Feature.Beta", "value": "true", "label": "Dev",
                              "content_type": "application/vnd.microsoft.appconfig.featureflag+json",
                              "etag": self.etag3, "last_modified": self.ts3, "locked": False}
        self.resp_kv_item4 = {"key": "App.Setting.Endpoint", "value": "http://localhost", "label": None,
                              "content_type": "text/uri-list", "etag": self.etag4, "last_modified": self.ts1,
                              "locked": False}
        self.resp_kv_item5 = {"key": "App.Setting.Size", "value": "Large", "label": "Prod",
                              "content_type": "text/plain", "etag": self.etag5, "last_modified": self.ts2,
                              "locked": False}
        self.resp_kv_item6 = {"key": "App.Setting.EmptyLabel", "value": "empty", "label": "",
                              "content_type": "text/plain", "etag": self.etag6, "last_modified": self.ts3,
                              "locked": False}
        self.resp_kv_item7 = {"key": "App.Setting.CaseTest", "value": "case_value", "label": "prod",
                              "content_type": "text/plain", "etag": self.etag7, "last_modified": self.ts3,
                              "locked": False}

        db_kv_item1 = {**self.resp_kv_item1, "app_config_store_name": self.store_name1}
        db_kv_item2 = {**self.resp_kv_item2, "app_config_store_name": self.store_name1}
        db_kv_item3 = {**self.resp_kv_item3, "app_config_store_name": self.store_name1}
        db_kv_item4 = {**self.resp_kv_item4, "app_config_store_name": self.store_name1}
        db_kv_item5 = {**self.resp_kv_item5, "app_config_store_name": self.store_name1}
        db_kv_item6 = {**self.resp_kv_item6, "app_config_store_name": self.store_name1}
        db_kv_item7 = {**self.resp_kv_item7, "app_config_store_name": self.store_name1}

        self.all_kv_items_store1_resp = [
            self.resp_kv_item1, self.resp_kv_item2, self.resp_kv_item3,
            self.resp_kv_item4, self.resp_kv_item5, self.resp_kv_item6, self.resp_kv_item7
        ]

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.sub_id}",
                "subscriptionId": self.sub_id,
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": "test-tenant-id",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}",
                        "name": self.rg_name,
                        "location": "eastus",
                        "subscription_id": self.sub_id,
                        "app_config_stores": [
                            {
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.AppConfiguration/configurationStores/{self.store_name1}",
                                "name": self.store_name1, "location": "eastus", "resource_group_name": self.rg_name,
                                "subscription_id": self.sub_id,
                                "key_values": [
                                    copy.deepcopy(db_kv_item1), copy.deepcopy(db_kv_item2),
                                    copy.deepcopy(db_kv_item3), copy.deepcopy(db_kv_item4),
                                    copy.deepcopy(db_kv_item5), copy.deepcopy(db_kv_item6),
                                    copy.deepcopy(db_kv_item7),
                                ]
                            },
                            {
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.AppConfiguration/configurationStores/{self.store_name_empty}",
                                "name": self.store_name_empty, "location": "eastus",
                                "resource_group_name": self.rg_name, "subscription_id": self.sub_id,
                                "key_values": []
                            },
                            {
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.AppConfiguration/configurationStores/{self.store_name_no_kv_list}",
                                "name": self.store_name_no_kv_list, "location": "eastus",
                                "resource_group_name": self.rg_name, "subscription_id": self.sub_id,
                            }
                        ]
                    }
                ]
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def assert_kv_lists_equal_unordered(self, list1, list2, msg=None):
        self.assertEqual(len(list1), len(list2), msg=f"Lists have different lengths. {msg or ''}")
        key_func = lambda x: (x.get('key'), x.get('label', '_NONE_LABEL_SORT_KEY_'))

        sorted_list1 = sorted(list1, key=key_func)
        sorted_list2 = sorted(list2, key=key_func)

        for item1, item2 in zip(sorted_list1, sorted_list2):
            self.assertDictEqual(item1, item2, msg=f"Items not equal: {item1} vs {item2}. {msg or ''}")

    def test_list_all_key_values_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1)
        self.assert_kv_lists_equal_unordered(result['key_value_items'], self.all_kv_items_store1_resp)

    def test_list_key_values_empty_store_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name_empty)
        self.assertEqual(result['key_value_items'], [])

    def test_list_key_values_store_with_no_kv_list_attr_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name_no_kv_list)
        self.assertEqual(result['key_value_items'], [])

    def test_list_key_filter_exact_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1,
                                         key="App.Setting.Color")
        self.assert_kv_lists_equal_unordered(result['key_value_items'], [self.resp_kv_item1])

    def test_list_key_filter_wildcard_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, key="App.Setting.*")
        expected = [self.resp_kv_item1, self.resp_kv_item2, self.resp_kv_item4, self.resp_kv_item5, self.resp_kv_item6,
                    self.resp_kv_item7]
        self.assert_kv_lists_equal_unordered(result['key_value_items'], expected)

    def test_list_key_filter_no_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, key="NonExistentKey")
        self.assertEqual(result['key_value_items'], [])

    def test_list_label_filter_exact_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label="Prod")
        expected = [self.resp_kv_item1, self.resp_kv_item2, self.resp_kv_item5]
        self.assert_kv_lists_equal_unordered(result['key_value_items'], expected)

    def test_list_label_filter_wildcard_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label="Pr*")
        expected = [self.resp_kv_item1, self.resp_kv_item2, self.resp_kv_item5]
        self.assert_kv_lists_equal_unordered(result['key_value_items'], expected)

    def test_list_label_filter_null_label_explicit_success(self):
        # Assuming the function translates r'\0' to filter for None labels, as per common AppConfig CLI behavior
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label=r'\0')
        self.assert_kv_lists_equal_unordered(result['key_value_items'], [self.resp_kv_item4])

    def test_list_label_filter_empty_string_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label="")
        self.assert_kv_lists_equal_unordered(result['key_value_items'], [self.resp_kv_item6])

    def test_list_label_filter_no_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1,
                                         label="NonExistentLabel")
        self.assertEqual(result['key_value_items'], [])

    def test_list_label_filter_case_sensitive_prod_lowercase_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label="prod")
        self.assert_kv_lists_equal_unordered(result['key_value_items'], [self.resp_kv_item7])

    def test_list_label_filter_case_sensitive_prod_uppercase_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label="Prod")
        expected = [self.resp_kv_item1, self.resp_kv_item2, self.resp_kv_item5]
        self.assert_kv_lists_equal_unordered(result['key_value_items'], expected)

    def test_list_key_and_label_filter_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, key="App.Setting.*",
                                         label="Prod")
        expected = [self.resp_kv_item1, self.resp_kv_item2, self.resp_kv_item5]
        self.assert_kv_lists_equal_unordered(result['key_value_items'], expected)

    def test_list_key_and_label_filter_no_match_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, key="App.Setting.*",
                                         label="Dev")
        self.assertEqual(result['key_value_items'], [])  # App.Setting.* does not have Dev label

    def test_list_key_filter_all_wildcard_success(self):
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, key="*")
        self.assert_kv_lists_equal_unordered(result['key_value_items'], self.all_kv_items_store1_resp)

    def test_list_label_filter_all_wildcard_success(self):
        # '*' label filter should match all items, including those with null or empty string labels
        result = azmcp_appconfig_kv_list(subscription=self.sub_id, account_name=self.store_name1, label="*")
        self.assert_kv_lists_equal_unordered(result['key_value_items'], self.all_kv_items_store1_resp)

    def test_list_kv_with_all_optional_params_set_success(self):
        result = azmcp_appconfig_kv_list(
            subscription=self.sub_id,
            account_name=self.store_name1,
            auth_method='credential',
            key=None,
            label=None,
            retry_delay="1",
            retry_max_delay="60",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="30",
            tenant="test-tenant-id"
        )
        self.assert_kv_lists_equal_unordered(result['key_value_items'], self.all_kv_items_store1_resp)

    def test_list_kv_subscription_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'non-existent-sub-id' not found.",
            subscription=self.non_existent_sub_id,
            account_name=self.store_name1
        )

    def test_list_kv_store_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"App Configuration store '{self.non_existent_store_name}' not found in subscription '{self.sub_id}'.",
            subscription=self.sub_id,
            account_name=self.non_existent_store_name
        )

    def test_list_kv_missing_subscription_validation_error(self):
        with self.assertRaisesRegex(TypeError, "required positional argument: 'subscription'"):
            azmcp_appconfig_kv_list(account_name=self.store_name1)

    def test_list_kv_missing_account_name_validation_error(self):
        with self.assertRaisesRegex(TypeError, "required positional argument: 'account_name'"):
            azmcp_appconfig_kv_list(subscription=self.sub_id)

    def test_list_kv_invalid_auth_method_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="auth_method must be one of: 'credential', 'key', or 'connectionString'",
            subscription=self.sub_id,
            account_name=self.store_name1,
            auth_method='invalid_method'
        )

    def test_list_kv_invalid_retry_delay_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_delay must be a positive number",
            subscription=self.sub_id,
            account_name=self.store_name1,
            retry_delay="-1"
        )

    def test_list_kv_invalid_retry_max_delay_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_delay must be a positive number",
            subscription=self.sub_id,
            account_name=self.store_name1,
            retry_max_delay="0"
        )

    def test_list_kv_invalid_retry_max_retries_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_retries must be a non-negative integer",
            subscription=self.sub_id,
            account_name=self.store_name1,
            retry_max_retries="-1"
        )

    def test_list_kv_invalid_retry_mode_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_mode must be either 'fixed' or 'exponential'",
            subscription=self.sub_id,
            account_name=self.store_name1,
            retry_mode='invalid_mode'
        )

    def test_list_kv_invalid_retry_network_timeout_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_network_timeout must be a positive number",
            subscription=self.sub_id,
            account_name=self.store_name1,
            retry_network_timeout="0"
        )

    def test_list_kv_invalid_key_type_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="key must be a string",
            subscription=self.sub_id,
            account_name=self.store_name1,
            key=123
        )

    def test_list_kv_invalid_label_type_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="label must be a string",
            subscription=self.sub_id,
            account_name=self.store_name1,
            label=456
        )

    def test_list_kv_invalid_tenant_type_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="tenant must be a string",
            subscription=self.sub_id,
            account_name=self.store_name1,
            tenant=789
        )


if __name__ == '__main__':
    unittest.main()
