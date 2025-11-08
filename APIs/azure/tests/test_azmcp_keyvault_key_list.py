import unittest
import copy
from datetime import datetime, timezone
from ..SimulationEngine import custom_errors
from ..keyvault import azmcp_keyvault_key_list
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import models

class TestAzmcpKeyvaultKeyList(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.subscription_id = "00000000-0000-0000-0000-000000000000"
        self.resource_group_name = "rg-test"
        self.vault_name = "test-vault"
        self.vault_name_empty = "empty-vault"
        
        self.now_ts = int(datetime.now(timezone.utc).timestamp())
        self.created_ts_key1 = self.now_ts - 7200
        self.updated_ts_key1 = self.now_ts - 3600
        self.exp_ts_key1 = self.now_ts + 86400 * 7
        self.nbf_ts_key1 = self.now_ts - 600

        self.created_ts_key2 = self.now_ts - 10000
        self.updated_ts_key2 = self.now_ts - 5000

        self.created_ts_key3 = self.now_ts - 15000
        self.updated_ts_key3 = self.now_ts - 7500


        DB["subscriptions"] = [
            {
                "id": f"sub-{self.subscription_id}",
                "subscriptionId": self.subscription_id,
                "displayName": "Test Subscription",
                "state": "Enabled",
                "tenantId": "tenant-abc",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}",
                        "name": self.resource_group_name,
                        "location": "eastus",
                        "subscription_id": self.subscription_id,
                        "key_vaults": [
                            {
                                "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.KeyVault/vaults/{self.vault_name}",
                                "name": self.vault_name,
                                "location": "eastus",
                                "resource_group_name": self.resource_group_name,
                                "subscription_id": self.subscription_id,
                                "keys": [
                                    { # Key 1 - Full features
                                        "name": "key1-active-with-expiry",
                                        "kid": f"https://{self.vault_name}.vault.azure.net/keys/key1-active-with-expiry/v1",
                                        "kty": "RSA",
                                        "key_ops": ["encrypt", "decrypt", "sign", "verify", "wrapKey", "unwrapKey"],
                                        "attributes": {
                                            "enabled": True,
                                            "exp": self.exp_ts_key1,
                                            "nbf": self.nbf_ts_key1,
                                            "created": self.created_ts_key1,
                                            "updated": self.updated_ts_key1,
                                            "recoveryLevel": "Recoverable+Purgeable"
                                        },
                                        "tags": {"purpose": "general-encryption", "env": "prod"},
                                        "vault_name": self.vault_name
                                    },
                                    { # Key 2 - Disabled, no expiry/nbf, no tags
                                        "name": "key2-disabled-no-tags",
                                        "kid": f"https://{self.vault_name}.vault.azure.net/keys/key2-disabled-no-tags/v1",
                                        "kty": "EC",
                                        "key_ops": ["sign", "verify"],
                                        "attributes": {
                                            "enabled": False,
                                            "created": self.created_ts_key2,
                                            "updated": self.updated_ts_key2,
                                            "recoveryLevel": "Recoverable"
                                        },
                                        "tags": None,
                                        "vault_name": self.vault_name
                                    },
                                    { # Key 3 - Minimal, enabled, no optional attributes, implicit no tags
                                        "name": "key3-minimal-active",
                                        "kid": f"https://{self.vault_name}.vault.azure.net/keys/key3-minimal-active/v1",
                                        "kty": "oct",
                                        "key_ops": [],
                                        "attributes": {
                                            "enabled": True,
                                            "created": self.created_ts_key3,
                                            "updated": self.updated_ts_key3,
                                            "recoveryLevel": "CustomizedRecoverable+Purgeable" 
                                        },
                                        # "tags" field omitted, should be treated as None
                                        "vault_name": self.vault_name
                                    }
                                ]
                            },
                            { # Vault with no keys
                                "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.KeyVault/vaults/{self.vault_name_empty}",
                                "name": self.vault_name_empty,
                                "location": "eastus",
                                "resource_group_name": self.resource_group_name,
                                "subscription_id": self.subscription_id,
                                "keys": [] 
                            }
                        ]
                    }
                ]
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Success Cases ---
    def test_list_keys_success_multiple_keys(self):
        keys_list = azmcp_keyvault_key_list(
            subscription=self.subscription_id,
            vault=self.vault_name
        )
        self.assertEqual(len(keys_list), 3)
        self.assertIsInstance(keys_list, list)

        # Assuming order is preserved from DB setup
        # Key 1: key1-active-with-expiry
        key1_data = keys_list[0]
        self.assertIsInstance(key1_data, dict)
        self.assertIn("attributes", key1_data)
        self.assertIn("tags", key1_data)
        
        key1_attrs = key1_data["attributes"]
        self.assertEqual(key1_attrs["enabled"], True)
        self.assertEqual(key1_attrs["exp"], self.exp_ts_key1)
        self.assertEqual(key1_attrs["nbf"], self.nbf_ts_key1)
        self.assertEqual(key1_attrs["created"], self.created_ts_key1)
        self.assertEqual(key1_attrs["updated"], self.updated_ts_key1)
        self.assertNotIn("recoveryLevel", key1_attrs) 

        self.assertEqual(key1_data["tags"], {"purpose": "general-encryption", "env": "prod"})

        # Key 2: key2-disabled-no-tags
        key2_data = keys_list[1]
        self.assertIsInstance(key2_data, dict)
        key2_attrs = key2_data["attributes"]
        self.assertEqual(key2_attrs["enabled"], False)
        self.assertIsNone(key2_attrs.get("exp"))
        self.assertIsNone(key2_attrs.get("nbf"))
        self.assertEqual(key2_attrs["created"], self.created_ts_key2)
        self.assertEqual(key2_attrs["updated"], self.updated_ts_key2)
        self.assertNotIn("recoveryLevel", key2_attrs)
        self.assertIsNone(key2_data["tags"])

        # Key 3: key3-minimal-active
        key3_data = keys_list[2]
        self.assertIsInstance(key3_data, dict)
        key3_attrs = key3_data["attributes"]
        self.assertEqual(key3_attrs["enabled"], True)
        self.assertIsNone(key3_attrs.get("exp"))
        self.assertIsNone(key3_attrs.get("nbf"))
        self.assertEqual(key3_attrs["created"], self.created_ts_key3)
        self.assertEqual(key3_attrs["updated"], self.updated_ts_key3)
        self.assertNotIn("recoveryLevel", key3_attrs)
        self.assertIsNone(key3_data["tags"]) 

    def test_list_keys_empty_vault_returns_empty_list(self):
        keys_list = azmcp_keyvault_key_list(
            subscription=self.subscription_id,
            vault=self.vault_name_empty
        )
        self.assertEqual(len(keys_list), 0)
        self.assertIsInstance(keys_list, list)

    def test_list_keys_include_managed_true_no_effect_on_current_schema(self):
        keys_list = azmcp_keyvault_key_list(
            subscription=self.subscription_id,
            vault=self.vault_name,
            include_managed="true"
        )
        self.assertEqual(len(keys_list), 3) 

    def test_list_keys_include_managed_false_default_behavior(self):
        keys_list = azmcp_keyvault_key_list(
            subscription=self.subscription_id,
            vault=self.vault_name,
            include_managed="false"
        )
        self.assertEqual(len(keys_list), 3)

    def test_list_keys_with_all_optional_params_valid(self):
        keys_list = azmcp_keyvault_key_list(
            subscription=self.subscription_id,
            vault=self.vault_name,
            auth_method="credential",
            include_managed="true",
            retry_delay="10",
            retry_max_delay="120",
            retry_max_retries="5",
            retry_mode="fixed",
            retry_network_timeout="60",
            tenant="tenant-abc"
        )
        self.assertEqual(len(keys_list), 3)

    # --- Error Cases - InvalidInputError ---
    def test_list_keys_missing_subscription_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'subscription' is required.",
            subscription=None,
            vault=self.vault_name
        )

    def test_list_keys_missing_vault_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'vault' is required.",
            subscription=self.subscription_id,
            vault=None
        )

    def test_list_keys_empty_subscription_string_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'subscription' cannot be an empty string.",
            subscription="",
            vault=self.vault_name
        )

    def test_list_keys_empty_vault_name_string_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'vault' cannot be an empty string.",
            subscription=self.subscription_id,
            vault=""
        )

    def test_list_keys_invalid_value_for_include_managed_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'include_managed' must be 'true' or 'false' if provided.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            include_managed="maybe"
        )
    
    def test_list_keys_invalid_format_for_retry_max_retries_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'retry_max_retries' must be a string representing a valid integer.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            retry_max_retries="three" 
        )

    # --- Error Cases - ResourceNotFoundError ---
    def test_list_keys_subscription_not_found_raises_resource_not_found_error(self):
        non_existent_sub_id = "11111111-0000-0000-0000-000000000000"
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Subscription with ID '{non_existent_sub_id}' not found.",
            subscription=non_existent_sub_id,
            vault=self.vault_name
        )

    def test_list_keys_vault_not_found_in_subscription_raises_resource_not_found_error(self):
        non_existent_vault_name = "phantom-vault"
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key Vault '{non_existent_vault_name}' not found in subscription '{self.subscription_id}'.",
            subscription=self.subscription_id,
            vault=non_existent_vault_name
        )
    
    def test_list_keys_auth_method_not_allowed_raises_invalid_input_error(self):
        not_allowed_auth_method = "not-a-valid-auth-method"
        allowed_str = ", ".join([f"'{v.value}'" for v in models.AuthMethod])
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Parameter 'auth-method' has an invalid value '{not_allowed_auth_method}'. Allowed values are {allowed_str}.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            auth_method=not_allowed_auth_method
        )
    
    def test_list_keys_retry_mode_not_allowed_raises_invalid_input_error(self):
        not_allowed_retry_mode = "not-a-valid-retry-mode"
        allowed_str = ", ".join([f"'{v.value}'" for v in models.RetryMode])
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Parameter 'retry-mode' has an invalid value '{not_allowed_retry_mode}'. Allowed values are {allowed_str}.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            retry_mode=not_allowed_retry_mode
        )

    def test_list_keys_vault_exists_but_in_different_subscription(self):
        other_sub_id = "99999999-9999-9999-9999-999999999999"
        vault_name_in_other_sub = "shared-name-vault"
        
        original_subs_backup = copy.deepcopy(DB.get("subscriptions", []))
        
        DB.setdefault("subscriptions", []).append({
            "id": f"sub-{other_sub_id}", "subscriptionId": other_sub_id, "displayName": "Other Sub", 
            "state": "Enabled", "tenantId": "tenant-other",
            "resource_groups": [{
                "id": f"/subscriptions/{other_sub_id}/resourceGroups/rg-other", "name": "rg-other", 
                "location": "westus", "subscription_id": other_sub_id,
                "key_vaults": [{
                    "id": f"/subscriptions/{other_sub_id}/resourceGroups/rg-other/providers/Microsoft.KeyVault/vaults/{vault_name_in_other_sub}",
                    "name": vault_name_in_other_sub, "location": "westus", 
                    "resource_group_name": "rg-other", "subscription_id": other_sub_id, "keys": []
                }]
            }]
        })

        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key Vault '{vault_name_in_other_sub}' not found in subscription '{self.subscription_id}'.",
            subscription=self.subscription_id, 
            vault=vault_name_in_other_sub 
        )
        
        DB["subscriptions"] = original_subs_backup

    def test_list_keys_invalid_tenant_type_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'tenant' must be a string.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            tenant=123
        )

if __name__ == '__main__':
    unittest.main()