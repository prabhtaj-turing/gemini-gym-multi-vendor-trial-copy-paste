import copy
import unittest
from datetime import datetime

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.appconfig import azmcp_appconfig_kv_unlock
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAzmcpAppConfigKvUnlock(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.subscription_id = "00000000-0000-0000-0000-000000000001"
        self.resource_group_name = "rg1"
        self.account_name = "appconfig1"
        self.tenant_id = "tenant-id-1"

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.subscription_id}",
                "subscriptionId": self.subscription_id,
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": self.tenant_id,
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}",
                        "name": self.resource_group_name,
                        "location": "eastus",
                        "subscription_id": self.subscription_id,
                        "app_config_stores": [
                            {
                                "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.AppConfiguration/configurationStores/{self.account_name}",
                                "name": self.account_name,
                                "location": "eastus",
                                "resource_group_name": self.resource_group_name,
                                "subscription_id": self.subscription_id,
                                "key_values": []
                            }
                        ]
                    }
                ]
            }
        ]
        # Helper to add KV items for tests
        self.initial_locked_kv_no_label = {
            "key": "LockedKeyNoLabel",
            "value": "InitialValue1",
            "label": None,
            "content_type": "text/plain",
            "etag": "etag-original-1",
            "last_modified": "2023-01-01T00:00:00Z",
            "locked": True,
            "app_config_store_name": self.account_name
        }
        self.initial_locked_kv_with_label = {
            "key": "LockedKeyWithLabel",
            "value": "InitialValue2",
            "label": "Prod",
            "content_type": "application/json",
            "etag": "etag-original-2",
            "last_modified": "2023-01-02T00:00:00Z",
            "locked": True,
            "app_config_store_name": self.account_name
        }
        self.initial_unlocked_kv_no_label = {
            "key": "UnlockedKeyNoLabel",
            "value": "InitialValue3",
            "label": None,
            "content_type": "text/plain",
            "etag": "etag-original-3",
            "last_modified": "2023-01-03T00:00:00Z",
            "locked": False,
            "app_config_store_name": self.account_name
        }
        self.initial_unlocked_kv_with_label = {
            "key": "UnlockedKeyWithLabel",
            "value": "InitialValue4",
            "label": "Dev",
            "content_type": "application/json",
            "etag": "etag-original-4",
            "last_modified": "2023-01-04T00:00:00Z",
            "locked": False,
            "app_config_store_name": self.account_name
        }
        self.kv_for_label_mismatch_test = {
            "key": "KeyForLabelMismatch",
            "value": "ValueMismatch",
            "label": "ExistingLabel",
            "content_type": "text/plain",
            "etag": "etag-original-5",
            "last_modified": "2023-01-05T00:00:00Z",
            "locked": True,
            "app_config_store_name": self.account_name
        }

        self._add_kv_item(copy.deepcopy(self.initial_locked_kv_no_label))
        self._add_kv_item(copy.deepcopy(self.initial_locked_kv_with_label))
        self._add_kv_item(copy.deepcopy(self.initial_unlocked_kv_no_label))
        self._add_kv_item(copy.deepcopy(self.initial_unlocked_kv_with_label))
        self._add_kv_item(copy.deepcopy(self.kv_for_label_mismatch_test))

    def _get_store_ref(self):
        # Helper to get a reference to the app_config_store's key_values list in DB
        # This is for test setup/verification, not for the function under test
        for sub in DB.get("subscriptions", []):
            if sub["subscriptionId"] == self.subscription_id:
                for rg in sub.get("resource_groups", []):
                    if rg["name"] == self.resource_group_name:
                        for store in rg.get("app_config_stores", []):
                            if store["name"] == self.account_name:
                                return store
        return None

    def _add_kv_item(self, kv_item_data):
        store_ref = self._get_store_ref()
        if store_ref:
            store_ref.setdefault("key_values", []).append(kv_item_data)

    def _get_kv_item_from_db(self, key, label=None):
        store_ref = self._get_store_ref()
        if store_ref:
            for kv in store_ref.get("key_values", []):
                if kv["key"] == key and kv["label"] == label:
                    return kv
        return None

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_unlock_kv_no_label_success(self):
        key_to_unlock = self.initial_locked_kv_no_label["key"]

        result = azmcp_appconfig_kv_unlock(
            account_name=self.account_name,
            key=key_to_unlock,
            subscription=self.subscription_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], key_to_unlock)
        self.assertEqual(result["value"], self.initial_locked_kv_no_label["value"])
        self.assertIsNone(result["label"])
        self.assertEqual(result["content_type"], self.initial_locked_kv_no_label["content_type"])
        self.assertFalse(result["locked"])
        self.assertNotEqual(result["etag"], self.initial_locked_kv_no_label["etag"])
        self.assertNotEqual(result["last_modified"], self.initial_locked_kv_no_label["last_modified"])

        # Verify timestamp format
        try:
            datetime.fromisoformat(result["last_modified"].replace("Z", "+00:00"))
        except ValueError:
            self.fail("last_modified is not a valid ISO 8601 timestamp")

        # Verify DB state
        db_item = self._get_kv_item_from_db(key_to_unlock, None)
        self.assertIsNotNone(db_item)
        self.assertFalse(db_item["locked"])
        self.assertEqual(db_item["etag"], result["etag"])
        self.assertEqual(db_item["last_modified"], result["last_modified"])

    def test_unlock_kv_with_label_success(self):
        key_to_unlock = self.initial_locked_kv_with_label["key"]
        label_to_unlock = self.initial_locked_kv_with_label["label"]

        result = azmcp_appconfig_kv_unlock(
            account_name=self.account_name,
            key=key_to_unlock,
            label=label_to_unlock,
            subscription=self.subscription_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], key_to_unlock)
        self.assertEqual(result["value"], self.initial_locked_kv_with_label["value"])
        self.assertEqual(result["label"], label_to_unlock)
        self.assertEqual(result["content_type"], self.initial_locked_kv_with_label["content_type"])
        self.assertFalse(result["locked"])
        self.assertNotEqual(result["etag"], self.initial_locked_kv_with_label["etag"])
        self.assertNotEqual(result["last_modified"], self.initial_locked_kv_with_label["last_modified"])

        datetime.fromisoformat(result["last_modified"].replace("Z", "+00:00"))  # Check format

        db_item = self._get_kv_item_from_db(key_to_unlock, label_to_unlock)
        self.assertIsNotNone(db_item)
        self.assertFalse(db_item["locked"])
        self.assertEqual(db_item["etag"], result["etag"])
        self.assertEqual(db_item["last_modified"], result["last_modified"])

    def test_unlock_kv_all_optional_params_provided(self):
        key_to_unlock = self.initial_locked_kv_no_label["key"]

        result = azmcp_appconfig_kv_unlock(
            account_name=self.account_name,
            key=key_to_unlock,
            subscription=self.subscription_id,
            auth_method="credential",
            label=None,  # Explicitly None
            retry_delay="5",
            retry_max_delay="60",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="30",
            tenant=self.tenant_id
        )
        self.assertFalse(result["locked"])
        db_item = self._get_kv_item_from_db(key_to_unlock, None)
        self.assertFalse(db_item["locked"])

    def test_unlock_kv_subscription_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'invalid-sub' not found.",
            account_name=self.account_name,
            key="anykey",
            subscription="invalid-sub"
        )

    def test_unlock_kv_resource_group_not_found(self):
        # Create a subscription without the target RG for this test
        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.subscription_id}",
                "subscriptionId": self.subscription_id,
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": self.tenant_id,
                "resource_groups": []  # No RGs
            }
        ]
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="App Configuration store 'appconfig1' not found in subscription '00000000-0000-0000-0000-000000000001'.",
            account_name=self.account_name,
            key="anykey",
            subscription=self.subscription_id
        )

    def test_unlock_kv_app_config_store_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="App Configuration store 'nonexistent-store' not found in subscription '00000000-0000-0000-0000-000000000001'.",
            account_name="nonexistent-store",
            key="anykey",
            subscription=self.subscription_id
        )

    def test_unlock_kv_key_not_found_no_label(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value with key 'NonExistentKey' and label (none) not found in App Configuration store 'appconfig1'.",
            account_name=self.account_name,
            key="NonExistentKey",
            subscription=self.subscription_id
        )

    def test_unlock_kv_key_not_found_with_label(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value with key 'NonExistentKey' and label 'Prod' not found in App Configuration store 'appconfig1'.",
            account_name=self.account_name,
            key="NonExistentKey",
            label="Prod",
            subscription=self.subscription_id
        )

    def test_unlock_kv_key_exists_but_label_mismatch(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value with key 'KeyForLabelMismatch' and label 'MissingLabel' not found in App Configuration store 'appconfig1'.",
            account_name=self.account_name,
            key=self.kv_for_label_mismatch_test["key"],
            label="MissingLabel",
            subscription=self.subscription_id
        )
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value with key 'KeyForLabelMismatch' and label (none) not found in App Configuration store 'appconfig1'.",
            account_name=self.account_name,
            key=self.kv_for_label_mismatch_test["key"],
            label=None,  # Explicitly None
            subscription=self.subscription_id
        )

    def test_unlock_kv_missing_account_name(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,  # Or ValidationError based on implementation
            expected_message="App Configuration store name ('account_name') must be a non-empty string.",
            account_name="",  # Empty string
            key="anykey",
            subscription=self.subscription_id
        )

    def test_unlock_kv_missing_key(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Key name ('key') must be a non-empty string.",
            account_name=self.account_name,
            key="",  # Empty string
            subscription=self.subscription_id
        )

    def test_unlock_kv_missing_subscription(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Subscription ID or name ('subscription') must be a non-empty string.",
            account_name=self.account_name,
            key="anykey",
            subscription=""  # Empty string
        )

    def test_unlock_kv_malformed_retry_delay(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_delay must be a valid number",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            retry_delay="not-a-number"
        )

    def test_unlock_kv_malformed_retry_max_retries(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_retries must be a valid integer",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            retry_max_retries="false"
        )

    def test_unlock_kv_invalid_retry_mode(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_mode must be either 'fixed' or 'exponential'",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            retry_mode="invalid_mode"
        )

    def test_unlock_kv_invalid_auth_method(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="auth_method must be one of: 'credential', 'key', 'connectionString'",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            auth_method="invalid_auth"
        )

    def test_unlock_kv_invalid_label_type(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="label must be a string",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            label=123  # Non-string value
        )

    def test_unlock_kv_invalid_retry_max_delay(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_delay must be a valid number",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            retry_max_delay="not-a-number"
        )

    def test_unlock_kv_invalid_retry_network_timeout(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_network_timeout must be a valid number",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            retry_network_timeout="invalid-timeout"
        )

    def test_unlock_kv_invalid_tenant(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="tenant must be a non-empty string",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id,
            tenant=""  # Empty string
        )

    def test_unlock_kv_non_string_account_name(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="App Configuration store name ('account_name') must be a non-empty string.",
            account_name=123,  # Non-string value
            key=self.initial_locked_kv_no_label["key"],
            subscription=self.subscription_id
        )

    def test_unlock_kv_non_string_key(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Key name ('key') must be a non-empty string.",
            account_name=self.account_name,
            key=456,  # Non-string value
            subscription=self.subscription_id
        )

    def test_unlock_kv_non_string_subscription(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Subscription ID or name ('subscription') must be a non-empty string.",
            account_name=self.account_name,
            key=self.initial_locked_kv_no_label["key"],
            subscription=789  # Non-string value
        )

    def test_unlock_kv_already_unlocked_no_label(self):
        key_to_unlock = self.initial_unlocked_kv_no_label["key"]
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ConflictError,
            expected_message="Key-value 'UnlockedKeyNoLabel' with label (none) in store 'appconfig1' is already unlocked.",
            account_name=self.account_name,
            key=key_to_unlock,
            subscription=self.subscription_id
        )

    def test_unlock_kv_already_unlocked_with_label(self):
        key_to_unlock = self.initial_unlocked_kv_with_label["key"]
        label_to_unlock = self.initial_unlocked_kv_with_label["label"]
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_unlock,
            expected_exception_type=custom_errors.ConflictError,
            expected_message="Key-value 'UnlockedKeyWithLabel' with label 'Dev' in store 'appconfig1' is already unlocked.",
            account_name=self.account_name,
            key=key_to_unlock,
            label=label_to_unlock,
            subscription=self.subscription_id
        )


if __name__ == '__main__':
    unittest.main()
