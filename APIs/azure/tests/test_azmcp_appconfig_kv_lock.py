from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..appconfig import azmcp_appconfig_kv_lock
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
import copy


class TestAzmcpAppconfigKvLock(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["subscriptions"] = [
            {
                "id": "sub-1",
                "subscriptionId": "sub-1",
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-a",
                "resource_groups": [
                    {
                        "id": "/subscriptions/sub-1/resourceGroups/rg-1",
                        "name": "rg-1",
                        "location": "eastus",
                        "subscription_id": "sub-1",
                        "app_config_stores": [
                            {
                                "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.AppConfiguration/configurationStores/store-A",
                                "name": "store-A",
                                "location": "eastus",
                                "resource_group_name": "rg-1",
                                "subscription_id": "sub-1",
                                "key_values": [
                                    {
                                        "key": "KeyNoLabel", "value": "ValueNL", "label": None,
                                        "content_type": "text/plain", "etag": "etag_nl_initial",
                                        "last_modified": "2023-01-01T10:00:00Z",
                                        "locked": False, "app_config_store_name": "store-A"
                                    },
                                    {
                                        "key": "KeyWithLabel", "value": "ValueWL", "label": "Prod",
                                        "content_type": None, "etag": "etag_wl_initial",
                                        "last_modified": "2023-01-02T10:00:00Z",
                                        "locked": False, "app_config_store_name": "store-A"
                                    },
                                    {
                                        "key": "AlreadyLockedNoLabel", "value": "ValueALNL", "label": None,
                                        "content_type": "application/json", "etag": "etag_alnl_initial",
                                        "last_modified": "2023-01-03T10:00:00Z",
                                        "locked": True, "app_config_store_name": "store-A"
                                    },
                                    {
                                        "key": "AlreadyLockedWithLabel", "value": "ValueALWL", "label": "Dev",
                                        "content_type": "text/xml", "etag": "etag_alwl_initial",
                                        "last_modified": "2023-01-04T10:00:00Z",
                                        "locked": True, "app_config_store_name": "store-A"
                                    },
                                    {
                                        "key": "KeyWithLabel", "value": "ValueWL_Dev", "label": "Dev",
                                        "content_type": "text/plain", "etag": "etag_wl_dev_initial",
                                        "last_modified": "2023-01-05T10:00:00Z",
                                        "locked": False, "app_config_store_name": "store-A"
                                    }
                                ]
                            },
                            {
                                "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.AppConfiguration/configurationStores/store-B-empty-kv",
                                "name": "store-B-empty-kv",
                                "location": "eastus",
                                "resource_group_name": "rg-1",
                                "subscription_id": "sub-1",
                                "key_values": []
                            },
                             {
                                "id": "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.AppConfiguration/configurationStores/store-C-no-kv-list",
                                "name": "store-C-no-kv-list",
                                "location": "eastus",
                                "resource_group_name": "rg-1",
                                "subscription_id": "sub-1",
                                # "key_values" list is absent here
                            }
                        ]
                    }
                ]
            },
            {
                "id": "sub-2-empty",
                "subscriptionId": "sub-2-empty",
                "displayName": "Empty Subscription",
                "state": "Enabled",
                "tenantId": "tenant-b",
                "resource_groups": []
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_kv_from_db(self, subscription_id, account_name, key, label=None):
        for sub in DB.get("subscriptions", []):
            if sub.get("subscriptionId") == subscription_id:
                for rg in sub.get("resource_groups", []):
                    for store in rg.get("app_config_stores", []):
                        if store.get("name") == account_name:
                            for kv_item in store.get("key_values", []):
                                if kv_item.get("key") == key and kv_item.get("label") == label:
                                    return kv_item
        return None

    # --- Success Cases ---
    def test_lock_kv_no_label_success(self):
        subscription_id = "sub-1"
        account_name = "store-A"
        key = "KeyNoLabel"
        
        original_kv = self._get_kv_from_db(subscription_id, account_name, key, None)
        self.assertIsNotNone(original_kv, "Test setup error: KV item not found for successful test.")
        self.assertFalse(original_kv["locked"], "Test setup error: KV should be unlocked.")
        original_etag = original_kv["etag"]
        original_last_modified = original_kv["last_modified"]

        result = azmcp_appconfig_kv_lock(
            subscription=subscription_id,
            account_name=account_name,
            key=key,
            label=None
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], original_kv["value"])
        self.assertIsNone(result["label"])
        self.assertEqual(result["content_type"], original_kv["content_type"])
        self.assertTrue(result["locked"])
        self.assertNotEqual(result["etag"], original_etag)
        self.assertTrue(result["last_modified"] > original_last_modified)
        
        updated_kv_in_db = self._get_kv_from_db(subscription_id, account_name, key, None)
        self.assertIsNotNone(updated_kv_in_db)
        self.assertTrue(updated_kv_in_db["locked"])
        self.assertEqual(updated_kv_in_db["etag"], result["etag"])
        self.assertEqual(updated_kv_in_db["last_modified"], result["last_modified"])

    def test_lock_kv_with_label_success(self):
        subscription_id = "sub-1"
        account_name = "store-A"
        key = "KeyWithLabel"
        label = "Prod"

        original_kv = self._get_kv_from_db(subscription_id, account_name, key, label)
        self.assertIsNotNone(original_kv, "Test setup error: KV item not found for successful test.")
        self.assertFalse(original_kv["locked"], "Test setup error: KV should be unlocked.")
        original_etag = original_kv["etag"]
        original_last_modified = original_kv["last_modified"]

        result = azmcp_appconfig_kv_lock(
            subscription=subscription_id,
            account_name=account_name,
            key=key,
            label=label
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], key)
        self.assertEqual(result["value"], original_kv["value"])
        self.assertEqual(result["label"], label)
        self.assertEqual(result["content_type"], original_kv["content_type"])
        self.assertTrue(result["locked"])
        self.assertNotEqual(result["etag"], original_etag)
        self.assertTrue(result["last_modified"] > original_last_modified)

        updated_kv_in_db = self._get_kv_from_db(subscription_id, account_name, key, label)
        self.assertIsNotNone(updated_kv_in_db)
        self.assertTrue(updated_kv_in_db["locked"])
        self.assertEqual(updated_kv_in_db["etag"], result["etag"])
        self.assertEqual(updated_kv_in_db["last_modified"], result["last_modified"])

    # --- InvalidInputError Cases ---
    def test_lock_kv_missing_subscription_raises_invalidinput(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'subscription' is required.",
            subscription=None,
            account_name="store-A",
            key="KeyNoLabel"
        )
    
    def test_lock_kv_empty_subscription_raises_invalidinput(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'subscription' cannot be empty.",
            subscription="",
            account_name="store-A",
            key="KeyNoLabel"
        )

    def test_lock_kv_missing_account_name_raises_invalidinput(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'account_name' is required.",
            subscription="sub-1",
            account_name=None,
            key="KeyNoLabel"
        )

    def test_lock_kv_empty_account_name_raises_invalidinput(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'account_name' cannot be empty.",
            subscription="sub-1",
            account_name="",
            key="KeyNoLabel"
        )

    def test_lock_kv_missing_key_raises_invalidinput(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'key' is required.",
            subscription="sub-1",
            account_name="store-A",
            key=None
        )

    def test_lock_kv_empty_key_raises_invalidinput(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'key' cannot be empty.",
            subscription="sub-1",
            account_name="store-A",
            key=""
        )
        
    # --- ResourceNotFoundError Cases ---
    def test_lock_kv_subscription_not_found_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Subscription 'nonexistent-sub' not found.",
            subscription="nonexistent-sub",
            account_name="store-A",
            key="KeyNoLabel"
        )

    def test_lock_kv_account_name_not_found_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="App Configuration store 'nonexistent-store' not found in subscription 'sub-1'.",
            subscription="sub-1",
            account_name="nonexistent-store",
            key="KeyNoLabel"
        )

    def test_lock_kv_key_not_found_no_label_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'NonExistentKey' and label 'None' not found in App Configuration store 'store-A'.",
            subscription="sub-1",
            account_name="store-A",
            key="NonExistentKey",
            label=None
        )

    def test_lock_kv_key_not_found_with_label_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'NonExistentKey' and label 'Prod' not found in App Configuration store 'store-A'.",
            subscription="sub-1",
            account_name="store-A",
            key="NonExistentKey",
            label="Prod"
        )

    def test_lock_kv_key_exists_but_wrong_label_provided_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'KeyWithLabel' and label 'Staging' not found in App Configuration store 'store-A'.",
            subscription="sub-1",
            account_name="store-A",
            key="KeyWithLabel",
            label="Staging"
        )

    def test_lock_kv_key_exists_with_label_but_no_label_provided_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'KeyWithLabel' and label 'None' not found in App Configuration store 'store-A'.",
            subscription="sub-1",
            account_name="store-A",
            key="KeyWithLabel", 
            label=None
        )
    
    def test_lock_kv_key_exists_no_label_but_label_provided_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'KeyNoLabel' and label 'Prod' not found in App Configuration store 'store-A'.",
            subscription="sub-1",
            account_name="store-A",
            key="KeyNoLabel",
            label="Prod"
        )

    def test_lock_kv_store_with_empty_kv_list_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'AnyKey' and label 'None' not found in App Configuration store 'store-B-empty-kv'.",
            subscription="sub-1",
            account_name="store-B-empty-kv",
            key="AnyKey",
            label=None
        )

    def test_lock_kv_store_with_no_kv_list_raises_resourcenotfound(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Key-value item with key 'AnyKey' and label 'None' not found in App Configuration store 'store-C-no-kv-list'.",
            subscription="sub-1",
            account_name="store-C-no-kv-list",
            key="AnyKey",
            label=None
        )

    # --- ConflictError Cases ---
    def test_lock_kv_already_locked_no_label_raises_conflict(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ConflictError,
            expected_message="Key-value item with key 'AlreadyLockedNoLabel' and label 'None' is already locked.",
            subscription="sub-1",
            account_name="store-A",
            key="AlreadyLockedNoLabel",
            label=None
        )

    def test_lock_kv_already_locked_with_label_raises_conflict(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_kv_lock,
            expected_exception_type=custom_errors.ConflictError,
            expected_message="Key-value item with key 'AlreadyLockedWithLabel' and label 'Dev' is already locked.",
            subscription="sub-1",
            account_name="store-A",
            key="AlreadyLockedWithLabel",
            label="Dev"
        )

    # --- Optional Parameters (no specific error, just pass-through) ---
    def test_lock_kv_with_all_optional_params_success(self):
        subscription_id = "sub-1"
        account_name = "store-A"
        key_to_lock = "KeyWithLabel" 
        label_to_lock = "Dev" # This one is initially unlocked in setup
        
        original_kv = self._get_kv_from_db(subscription_id, account_name, key_to_lock, label_to_lock)
        self.assertIsNotNone(original_kv, "Test setup error: KV item not found.")
        self.assertFalse(original_kv["locked"], "Test setup error: KV should be unlocked.")

        result = azmcp_appconfig_kv_lock(
            subscription=subscription_id,
            account_name=account_name,
            key=key_to_lock,
            label=label_to_lock,
            auth_method='credential',
            tenant='tenant-a',
            retry_max_retries='3',
            retry_delay='1',
            retry_max_delay='10',
            retry_mode='exponential',
            retry_network_timeout='30'
        )
        self.assertTrue(result["locked"])
        updated_kv_in_db = self._get_kv_from_db(subscription_id, account_name, key_to_lock, label_to_lock)
        self.assertIsNotNone(updated_kv_in_db)
        self.assertTrue(updated_kv_in_db["locked"])
        self.assertEqual(updated_kv_in_db["etag"], result["etag"])
        self.assertEqual(updated_kv_in_db["last_modified"], result["last_modified"])