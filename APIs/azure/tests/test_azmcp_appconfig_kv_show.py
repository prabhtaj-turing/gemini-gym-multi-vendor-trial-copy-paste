import copy
import unittest
from datetime import datetime, timezone

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.appconfig import azmcp_appconfig_kv_show
from common_utils.base_case import BaseTestCaseWithErrorHandler


def _get_iso_timestamp(year, month, day, hour=0, minute=0, second=0, microsecond=0):
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc).isoformat().replace(
        "+00:00", "Z")


class TestAzmcpAppconfigKvShow(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sub_id = "00000000-0000-0000-0000-000000000001"
        self.rg_name = "test-rg"
        self.store_name = "my-appconfig-store"
        self.tenant_id = "tenant-001"

        self.kv_item1_data = {
            "key": "Key1", "value": "Value1", "label": "Prod",
            "content_type": "text/plain", "etag": "etag_key1_prod",
            "last_modified": _get_iso_timestamp(2023, 1, 1, 10, 0, 0), "locked": False,
            "app_config_store_name": self.store_name
        }
        self.kv_item2_data = {
            "key": "Key2", "value": "Value2", "label": None,
            "content_type": "application/json", "etag": "etag_key2_null",
            "last_modified": _get_iso_timestamp(2023, 1, 2, 11, 0, 0), "locked": True,
            "app_config_store_name": self.store_name
        }
        self.kv_item3_data = {
            "key": "Key3", "value": "Value3", "label": "Dev",
            "content_type": None, "etag": "etag_key3_dev",
            "last_modified": _get_iso_timestamp(2023, 1, 3, 12, 0, 0), "locked": False,
            "app_config_store_name": self.store_name
        }
        self.kv_item4_data = {  # Same key as item1, different label
            "key": "Key1", "value": "Value1Dev", "label": "Dev",
            "content_type": "text/plain", "etag": "etag_key1_dev",
            "last_modified": _get_iso_timestamp(2023, 1, 4, 13, 0, 0), "locked": False,
            "app_config_store_name": self.store_name
        }
        self.kv_item5_data = {  # Empty string label
            "key": "KeyWithEmptyLabel", "value": "ValueEmptyLabel", "label": "",
            "content_type": "text/special", "etag": "etag_keyEmpty_empty",
            "last_modified": _get_iso_timestamp(2023, 1, 5, 14, 0, 0), "locked": False,
            "app_config_store_name": self.store_name
        }

        DB["subscriptions"] = [
            {
                "id": self.sub_id, "subscriptionId": self.sub_id,
                "displayName": "Test Subscription", "state": "Enabled", "tenantId": self.tenant_id,
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}",
                        "name": self.rg_name, "location": "eastus", "subscription_id": self.sub_id,
                        "app_config_stores": [
                            {
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.AppConfiguration/configurationStores/{self.store_name}",
                                "name": self.store_name, "location": "eastus",
                                "resource_group_name": self.rg_name, "subscription_id": self.sub_id,
                                "key_values": [
                                    copy.deepcopy(self.kv_item1_data), copy.deepcopy(self.kv_item2_data),
                                    copy.deepcopy(self.kv_item3_data), copy.deepcopy(self.kv_item4_data),
                                    copy.deepcopy(self.kv_item5_data),
                                ]
                            }
                        ],
                        "cosmos_db_accounts": [], "key_vaults": [],
                        "log_analytics_workspaces": [], "monitor_health_models": [], "storage_accounts": []
                    }
                ]
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_show_kv_with_specific_label_success(self):
        result = azmcp_appconfig_kv_show(
            subscription=self.sub_id, account_name=self.store_name,
            key="Key1", label="Prod"
        )
        expected = {
            "key": "Key1", "value": "Value1", "label": "Prod",
            "content_type": "text/plain", "etag": "etag_key1_prod",
            "last_modified": self.kv_item1_data["last_modified"], "locked": False
        }
        self.assertEqual(result, expected)

    def test_show_kv_with_null_label_success(self):
        result_explicit_none = azmcp_appconfig_kv_show(
            subscription=self.sub_id, account_name=self.store_name,
            key="Key2", label=None
        )
        expected = {
            "key": "Key2", "value": "Value2", "label": None,
            "content_type": "application/json", "etag": "etag_key2_null",
            "last_modified": self.kv_item2_data["last_modified"], "locked": True
        }
        self.assertEqual(result_explicit_none, expected)

        result_omitted_label = azmcp_appconfig_kv_show(
            subscription=self.sub_id, account_name=self.store_name, key="Key2"
        )
        self.assertEqual(result_omitted_label, expected)

    def test_show_kv_with_empty_string_label_success(self):
        result = azmcp_appconfig_kv_show(
            subscription=self.sub_id, account_name=self.store_name,
            key="KeyWithEmptyLabel", label=""
        )
        expected = {
            "key": "KeyWithEmptyLabel", "value": "ValueEmptyLabel", "label": "",
            "content_type": "text/special", "etag": "etag_keyEmpty_empty",
            "last_modified": self.kv_item5_data["last_modified"], "locked": False
        }
        self.assertEqual(result, expected)

    def test_show_kv_no_content_type_success(self):
        result = azmcp_appconfig_kv_show(
            subscription=self.sub_id, account_name=self.store_name,
            key="Key3", label="Dev"
        )
        expected = {
            "key": "Key3", "value": "Value3", "label": "Dev",
            "content_type": None, "etag": "etag_key3_dev",
            "last_modified": self.kv_item3_data["last_modified"], "locked": False
        }
        self.assertEqual(result, expected)

    def test_show_kv_with_all_optional_params_set_success(self):
        result = azmcp_appconfig_kv_show(
            subscription=self.sub_id, account_name=self.store_name,
            key="Key1", label="Prod", auth_method="credential",
            retry_delay="1", retry_max_delay="60", retry_max_retries="3",
            retry_mode="exponential", retry_network_timeout="30", tenant=self.tenant_id
        )
        expected = {
            "key": "Key1", "value": "Value1", "label": "Prod",
            "content_type": "text/plain", "etag": "etag_key1_prod",
            "last_modified": self.kv_item1_data["last_modified"], "locked": False
        }
        self.assertEqual(result, expected)

    def test_show_kv_subscription_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'non-existent-sub' not found.",
            subscription="non-existent-sub", account_name=self.store_name, key="Key1", label="Prod"
        )

    def test_show_kv_store_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"App Configuration store 'non-existent-store' not found in subscription '{self.sub_id}'.",
            subscription=self.sub_id, account_name="non-existent-store", key="Key1", label="Prod"
        )

    def test_show_kv_key_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key-value with key 'NonExistentKey' and default (null) label not found in App Configuration store '{self.store_name}'.",
            subscription=self.sub_id, account_name=self.store_name, key="NonExistentKey"
        )

    def test_show_kv_key_exists_label_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key-value with key 'Key1' and label 'NonExistentLabel' not found in App Configuration store '{self.store_name}'.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="NonExistentLabel"
        )

    def test_show_kv_subscription_none_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Subscription ID or name must be provided as a non-empty string.",
            subscription=None, account_name=self.store_name, key="Key1"
        )

    def test_show_kv_subscription_empty_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Subscription ID or name must be provided as a non-empty string.",
            subscription="", account_name=self.store_name, key="Key1"
        )

    def test_show_kv_account_name_none_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="App Configuration store name (account_name) must be provided as a non-empty string.",
            subscription=self.sub_id, account_name=None, key="Key1"
        )

    def test_show_kv_account_name_empty_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="App Configuration store name (account_name) must be provided as a non-empty string.",
            subscription=self.sub_id, account_name="", key="Key1"
        )

    def test_show_kv_key_none_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Key must be provided as a non-empty string.",
            subscription=self.sub_id, account_name=self.store_name, key=None
        )

    def test_show_kv_key_empty_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Key must be provided as a non-empty string.",
            subscription=self.sub_id, account_name=self.store_name, key=""
        )

    def test_show_kv_invalid_auth_method_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid auth_method: 'invalid_auth'. Allowed values are ['credential', 'key', 'connectionString'].",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod", auth_method="invalid_auth"
        )

    def test_show_kv_invalid_retry_delay_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_delay must be a valid number string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod", retry_delay="abc"
        )

    def test_show_kv_negative_retry_delay_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Value for retry_delay must be non-negative.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod", retry_delay="-5"
        )

    def test_show_kv_invalid_retry_max_delay_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_max_delay must be a valid number string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod", retry_max_delay="xyz"
        )

    def test_show_kv_invalid_retry_max_retries_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_max_retries must be a valid integer string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod", retry_max_retries="foo"
        )

    def test_show_kv_invalid_retry_mode_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_mode must be either 'fixed' or 'exponential'.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod", retry_mode="unknown_mode"
        )

    def test_show_kv_invalid_retry_network_timeout_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_network_timeout must be a valid number string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label="Prod",
            retry_network_timeout="bar"
        )

    def test_show_kv_invalid_label_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="label must be a string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", label=123
        )

    def test_show_kv_invalid_tenant_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="tenant must be a string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", tenant=456
        )

    def test_show_kv_invalid_account_name_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="App Configuration store name (account_name) can only contain letters, numbers, hyphens, and underscores.",
            subscription=self.sub_id, account_name="invalid@store", key="Key1"
        )

    def test_show_kv_invalid_auth_method_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_show,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="auth_method must be a string.",
            subscription=self.sub_id, account_name=self.store_name, key="Key1", auth_method=789
        )


if __name__ == '__main__':
    unittest.main()
