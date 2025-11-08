import copy
import unittest

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.appconfig import azmcp_appconfig_kv_set
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAzmcpAppconfigKvSet(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.subscription_id = "sub-test-alpha"
        self.resource_group_name = "rg-test-bravo"
        self.account_name_valid = "appconfig-store-charlie"

        self.tenant_id = "tenant-delta"

        DB["subscriptions"] = [
            {
                "id": self.subscription_id,
                "subscriptionId": self.subscription_id,
                "displayName": "Test Subscription Alpha",
                "state": "Enabled",
                "tenantId": self.tenant_id,
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}",
                        "name": self.resource_group_name,
                        "location": "westus",
                        "subscription_id": self.subscription_id,
                        "app_config_stores": [
                            {
                                "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.AppConfiguration/configurationStores/{self.account_name_valid}",
                                "name": self.account_name_valid,
                                "location": "westus",
                                "resource_group_name": self.resource_group_name,
                                "subscription_id": self.subscription_id,
                                "key_values": [
                                    {
                                        "key": "ExistingKey1",
                                        "value": "InitialValue1",
                                        "label": None,
                                        "content_type": "text/plain",
                                        "etag": "initial-etag-1",
                                        "last_modified": "2023-10-01T10:00:00Z",
                                        "locked": False,
                                        "app_config_store_name": self.account_name_valid
                                    },
                                    {
                                        "key": "ExistingKey2",
                                        "value": "InitialValue2",
                                        "label": "Prod",
                                        "content_type": "application/json",
                                        "etag": "initial-etag-2",
                                        "last_modified": "2023-10-02T11:00:00Z",
                                        "locked": False,
                                        "app_config_store_name": self.account_name_valid
                                    },
                                    {
                                        "key": "LockedKey1",
                                        "value": "ValueForLockedKey1",
                                        "label": None,
                                        "content_type": "text/xml",
                                        "etag": "initial-etag-3",
                                        "last_modified": "2023-10-03T12:00:00Z",
                                        "locked": True,
                                        "app_config_store_name": self.account_name_valid
                                    },
                                    {
                                        "key": "LockedKey2",
                                        "value": "ValueForLockedKey2",
                                        "label": "Feature",
                                        "content_type": "text/plain",
                                        "etag": "initial-etag-4",
                                        "last_modified": "2023-10-04T13:00:00Z",
                                        "locked": True,
                                        "app_config_store_name": self.account_name_valid
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_kv_from_db(self, account_name, key, label=None):
        subs = DB.get("subscriptions", [])
        for sub in subs:
            if sub["subscriptionId"] == self.subscription_id:
                for rg in sub.get("resource_groups", []):
                    if rg["name"] == self.resource_group_name:
                        for store in rg.get("app_config_stores", []):
                            if store["name"] == account_name:
                                for kv_item in store.get("key_values", []):
                                    db_label = kv_item.get("label")
                                    input_label = label if label else None
                                    if kv_item["key"] == key and db_label == input_label:
                                        return kv_item
        return None

    # --- Success Cases ---
    def test_set_new_key_value_no_label_success(self):
        key = "NewKeyNoLabel"
        value = "NewValueForNoLabel"

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=value
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], value)
        self.assertIsNone(result["label"])
        self.assertIsNone(result.get("content_type"))
        self.assertTrue(result["etag"])
        self.assertTrue(result["last_modified"])
        self.assertFalse(result["locked"])

        db_item = self._get_kv_from_db(self.account_name_valid, key, None)
        self.assertIsNotNone(db_item)
        self.assertEqual(db_item["value"], value)
        self.assertEqual(db_item["etag"], result["etag"])
        self.assertEqual(db_item["last_modified"], result["last_modified"])
        self.assertIsNone(db_item.get("content_type"))
        self.assertFalse(db_item.get("locked", False))

    def test_set_new_key_value_with_label_success(self):
        key = "NewKeyWithLabel"
        value = "NewValueForWithLabel"
        label = "Beta"

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=value,
            label=label
        )

        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], value)
        self.assertEqual(result["label"], label)
        self.assertIsNone(result.get("content_type"))
        self.assertTrue(result["etag"])
        self.assertTrue(result["last_modified"])
        self.assertFalse(result["locked"])

        db_item = self._get_kv_from_db(self.account_name_valid, key, label)
        self.assertIsNotNone(db_item)
        self.assertEqual(db_item["value"], value)
        self.assertEqual(db_item["label"], label)

    def test_set_new_key_value_with_empty_string_label_treats_as_no_label(self):
        key = "NewKeyEmptyLabel"
        value = "ValueForEmptyLabel"

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=value,
            label=""
        )

        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], value)
        self.assertEqual(result["label"], "")

        db_item_none_label = self._get_kv_from_db(self.account_name_valid, key, None)
        self.assertIsNone(db_item_none_label)

        db_item_empty_string_label = self._get_kv_from_db(self.account_name_valid, key, "")
        self.assertIsNone(db_item_empty_string_label)

    def test_update_existing_key_value_no_label_success(self):
        key = "ExistingKey1"
        new_value = "UpdatedValue1"

        original_item = self._get_kv_from_db(self.account_name_valid, key, None)
        self.assertIsNotNone(original_item)
        original_etag = original_item["etag"]
        original_last_modified = original_item["last_modified"]
        original_content_type = original_item["content_type"]
        original_locked_status = original_item["locked"]

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=new_value
        )

        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], new_value)
        self.assertIsNone(result["label"])
        self.assertEqual(result["content_type"], original_content_type)
        self.assertNotEqual(result["etag"], original_etag)
        self.assertGreater(result["last_modified"], original_last_modified)
        self.assertEqual(result["locked"], original_locked_status)

        db_item = self._get_kv_from_db(self.account_name_valid, key, None)
        self.assertEqual(db_item["value"], new_value)
        self.assertEqual(db_item["etag"], result["etag"])
        self.assertEqual(db_item["content_type"], original_content_type)
        self.assertEqual(db_item["locked"], original_locked_status)

    def test_update_existing_key_value_with_label_success(self):
        key = "ExistingKey2"
        label = "Prod"
        new_value = "UpdatedValue2WithLabel"

        original_item = self._get_kv_from_db(self.account_name_valid, key, label)
        self.assertIsNotNone(original_item)
        original_etag = original_item["etag"]
        original_last_modified = original_item["last_modified"]
        original_content_type = original_item["content_type"]
        original_locked_status = original_item["locked"]

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=new_value,
            label=label
        )

        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], new_value)
        self.assertEqual(result["label"], label)
        self.assertEqual(result["content_type"], original_content_type)
        self.assertNotEqual(result["etag"], original_etag)
        self.assertGreater(result["last_modified"], original_last_modified)
        self.assertEqual(result["locked"], original_locked_status)

        db_item = self._get_kv_from_db(self.account_name_valid, key, label)
        self.assertEqual(db_item["value"], new_value)
        self.assertEqual(db_item["label"], label)

    def test_set_key_value_all_optional_params_provided_success(self):
        key = "OptionalParamsKey"
        value = "OptionalParamsValue"

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=value,
            auth_method="credential",
            label="Temp",
            retry_delay="1",
            retry_max_delay="10",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="5",
            tenant=self.tenant_id
        )
        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], value)
        self.assertEqual(result["label"], "Temp")
        self.assertTrue(result["etag"])  # Ensure basic fields are still there

    def test_set_key_value_with_empty_value_success(self):
        key = "KeyWithEmptyValue"
        value = ""

        result = azmcp_appconfig_kv_set(
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value=value
        )
        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], "")
        db_item = self._get_kv_from_db(self.account_name_valid, key, None)
        self.assertIsNotNone(db_item)
        self.assertEqual(db_item["value"], "")

    # --- Error Cases: InvalidInputError ---
    def test_set_key_value_empty_subscription_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Subscription ID or name must be provided as a non-empty string.',
            subscription="",
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_empty_account_name_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='App Configuration store name (account_name) must be provided as a non-empty string.',
            subscription=self.subscription_id,
            account_name="",
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_empty_key_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Configuration key must be provided as a non-empty string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="",
            value="TestValue"
        )

    # --- Error Cases: ResourceNotFoundError ---
    def test_set_key_value_non_existent_subscription_raises_resourcenotfounderror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Subscription 'non-existent-sub' not found.",
            subscription="non-existent-sub",
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_non_existent_account_name_raises_resourcenotfounderror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="App Configuration store 'non-existent-store' not found in subscription 'sub-test-alpha'.",
            subscription=self.subscription_id,
            account_name="non-existent-store",
            key="TestKey",
            value="TestValue"
        )

    # --- Error Cases: ConflictError ---
    def test_set_key_value_on_locked_key_no_label_raises_conflicterror(self):
        key = "LockedKey1"
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.ConflictError,
            expected_message="The key-value 'LockedKey1' with label (No Label) is locked and cannot be modified.",
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value="AttemptToUpdateLockedValue"
        )

    def test_set_key_value_on_locked_key_with_label_raises_conflicterror(self):
        key = "LockedKey2"
        label = "Feature"
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.ConflictError,
            expected_message="The key-value 'LockedKey2' with label 'Feature' is locked and cannot be modified.",
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=key,
            value="AttemptToUpdateLockedValueWithLabel",
            label=label
        )

    # --- Error Cases: custom_errors.InvalidInputError ---
    def test_set_key_value_invalid_auth_method_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Invalid auth_method. Must be one of: credential, key, connectionString',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            auth_method="invalid_auth"
        )

    def test_set_key_value_invalid_retry_mode_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_mode must be one of: fixed, exponential',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_mode="invalid_mode"
        )

    def test_set_key_value_non_numeric_retry_delay_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_delay must be a valid number string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_delay="abc"
        )

    def test_set_key_value_non_numeric_retry_max_retries_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_max_retries must be a valid integer string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_max_retries="xyz"
        )

    def test_set_key_value_non_numeric_retry_max_delay_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_max_delay must be a valid number string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_max_delay="def"
        )

    def test_set_key_value_non_numeric_retry_network_timeout_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_network_timeout must be a valid number string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_network_timeout="ghi"
        )

    # --- TypeError for missing required arguments (Python level) ---
    def test_set_key_value_missing_required_arg_subscription_raises_typeerror(self):
        with self.assertRaises(TypeError):
            azmcp_appconfig_kv_set(
                account_name=self.account_name_valid, key="k", value="v"
            )

    def test_set_key_value_missing_required_arg_account_name_raises_typeerror(self):
        with self.assertRaises(TypeError):
            azmcp_appconfig_kv_set(
                subscription=self.subscription_id, key="k", value="v"
            )

    def test_set_key_value_missing_required_arg_key_raises_typeerror(self):
        with self.assertRaises(TypeError):
            azmcp_appconfig_kv_set(
                subscription=self.subscription_id, account_name=self.account_name_valid, value="v"
            )

    def test_set_key_value_missing_required_arg_value_raises_typeerror(self):
        with self.assertRaises(TypeError):
            azmcp_appconfig_kv_set(
                subscription=self.subscription_id, account_name=self.account_name_valid, key="k"
            )

    def test_set_key_value_non_string_subscription_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Subscription ID or name must be provided as a non-empty string.',
            subscription=123,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_non_string_account_name_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='App Configuration store name (account_name) must be provided as a non-empty string.',
            subscription=self.subscription_id,
            account_name=456,  # Non-string value
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_non_string_key_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Configuration key must be provided as a non-empty string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key=789,  # Non-string value
            value="TestValue"
        )

    def test_set_key_value_non_string_value_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Configuration value must be provided as a string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value=123  # Non-string value
        )

    def test_set_key_value_whitespace_only_subscription_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Subscription ID or name must be provided as a non-empty string.',
            subscription="   ",
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_whitespace_only_account_name_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='App Configuration store name (account_name) must be provided as a non-empty string.',
            subscription=self.subscription_id,
            account_name="   ",
            key="TestKey",
            value="TestValue"
        )

    def test_set_key_value_whitespace_only_key_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Configuration key must be provided as a non-empty string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="   ",
            value="TestValue"
        )

    def test_set_key_value_non_string_label_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='label must be a string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            label=123  # Non-string value
        )

    def test_set_key_value_non_string_tenant_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='tenant must be a string.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            tenant=456  # Non-string value
        )

    def test_set_key_value_negative_retry_delay_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_delay must be greater than 0.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_delay="-1"
        )

    def test_set_key_value_negative_retry_max_delay_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_max_delay must be a positive number.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_max_delay="-1"
        )

    def test_set_key_value_negative_retry_max_retries_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_max_retries must be at least 1.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_max_retries="-1"
        )

    def test_set_key_value_negative_retry_network_timeout_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_set,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='retry_network_timeout must be a positive number.',
            subscription=self.subscription_id,
            account_name=self.account_name_valid,
            key="TestKey",
            value="TestValue",
            retry_network_timeout="-1"
        )


if __name__ == '__main__':
    unittest.main()
