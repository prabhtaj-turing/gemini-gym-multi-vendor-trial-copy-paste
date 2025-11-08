import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..keyvault import azmcp_keyvault_key_get
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestAzmcpKeyvaultKeyGet(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sub_id = "sub-test-123"
        self.rg_name = "rg-test-kv"
        self.vault_name1 = "mykeyvault1"
        self.vault_name2_empty = "mykeyvault2empty" # Vault with no keys
        
        self.key1_name = "test-key-01"
        self.key1_kid = f"https://{self.vault_name1}.vault.azure.net/keys/{self.key1_name}/abcdef1234567890"
        # Attributes as stored in DB and expected in output (matching KeyOperationAttributes structure)
        self.key1_attributes_data = {
            "enabled": True, "exp": 1700000000, "nbf": 1600000000,
            "created": 1500000000, "updated": 1550000000, "recoveryLevel": "Recoverable+Purgeable"
        }
        
        # Full key data as it might be stored in the DB (KeyVaultKey model)
        self.key1_db_data = {
            "name": self.key1_name, "kid": self.key1_kid, "kty": "RSA",
            "key_ops": ["encrypt", "decrypt", "sign", "verify"],
            "attributes": copy.deepcopy(self.key1_attributes_data),
            "vault_name": self.vault_name1, # Internal field, not part of output
            "tags": {"env": "test"}        # Internal field, not part of output
        }
        # Expected output structure for key1
        self.key1_expected_output = {
            "kid": self.key1_kid, "kty": "RSA",
            "key_ops": ["encrypt", "decrypt", "sign", "verify"],
            "attributes": copy.deepcopy(self.key1_attributes_data)
        }

        self.key2_name = "test-key-02-minimal"
        self.key2_kid = f"https://{self.vault_name1}.vault.azure.net/keys/{self.key2_name}/1234567890abcdef"
        self.key2_attributes_data = {
            "enabled": False, "exp": None, "nbf": None, # Optional attributes as None
            "created": 1510000000, "updated": 1560000000, "recoveryLevel": "Purgeable"
        }

        self.key2_db_data = {
            "name": self.key2_name, "kid": self.key2_kid, "kty": "EC",
            "key_ops": [], # Empty key_ops list
            "attributes": copy.deepcopy(self.key2_attributes_data),
            "vault_name": self.vault_name1
        }
        self.key2_expected_output = {
            "kid": self.key2_kid, "kty": "EC",
            "key_ops": [],
            "attributes": copy.deepcopy(self.key2_attributes_data)
        }

        vault1_db_data = {
            "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.KeyVault/vaults/{self.vault_name1}",
            "name": self.vault_name1, "location": "eastus", "resource_group_name": self.rg_name,
            "subscription_id": self.sub_id, "keys": [self.key1_db_data, self.key2_db_data]
        }
        vault2_empty_db_data = {
            "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.KeyVault/vaults/{self.vault_name2_empty}",
            "name": self.vault_name2_empty, "location": "westus", "resource_group_name": self.rg_name,
            "subscription_id": self.sub_id, "keys": [] # This vault has no keys
        }

        resource_group_db_data = {
            "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}",
            "name": self.rg_name, "location": "eastus", "subscription_id": self.sub_id,
            "key_vaults": [vault1_db_data, vault2_empty_db_data],
            # Ensuring other resource type lists are present as per schema, even if empty
            "app_config_stores": [], "cosmos_db_accounts": [], "log_analytics_workspaces": [],
            "monitor_health_models": [], "storage_accounts": []
        }
        
        # Adding another resource group to ensure vault lookup is specific
        other_rg_name = "rg-other-empty"
        other_rg_db_data = {
             "id": f"/subscriptions/{self.sub_id}/resourceGroups/{other_rg_name}",
            "name": other_rg_name, "location": "eastus", "subscription_id": self.sub_id,
            "key_vaults": [], "app_config_stores": [], "cosmos_db_accounts": [], 
            "log_analytics_workspaces": [], "monitor_health_models": [], "storage_accounts": []
        }

        subscription_db_data = {
            "id": f"/subscriptions/{self.sub_id}", "subscriptionId": self.sub_id,
            "displayName": "Test Subscription for Key Vault", "state": "Enabled",
            "tenantId": "tenant-for-kv-tests",
            "resource_groups": [resource_group_db_data, other_rg_db_data]
        }
        DB["subscriptions"] = [subscription_db_data]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_key_success_full_attributes(self):
        result = azmcp_keyvault_key_get(
            subscription=self.sub_id,
            vault=self.vault_name1,
            key=self.key1_name
        )
        self.assertEqual(result, self.key1_expected_output)

    def test_get_key_success_minimal_attributes_empty_ops(self):
        result = azmcp_keyvault_key_get(
            subscription=self.sub_id,
            vault=self.vault_name1,
            key=self.key2_name
        )
        self.assertEqual(result, self.key2_expected_output)

    def test_get_key_success_with_all_optional_params_passed(self):
        # This test ensures the function accepts all optional parameters.
        # The simulated backend logic might not use them, but the signature should be robust.
        result = azmcp_keyvault_key_get(
            subscription=self.sub_id,
            vault=self.vault_name1,
            key=self.key1_name,
            auth_method="credential",
            retry_delay="5",
            retry_max_delay="30",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="15",
            tenant="sample-tenant-id-for-test"
        )
        self.assertEqual(result, self.key1_expected_output)

    def test_get_key_raises_resource_not_found_for_nonexistent_subscription(self):
        nonexistent_sub = "nonexistent-subscription-guid"
        # Expected message depends on how the function or underlying utils report this.
        # If subscription is not found, the vault effectively cannot be found.
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Subscription '{nonexistent_sub}' not found.",
            subscription=nonexistent_sub,
            vault=self.vault_name1,
            key=self.key1_name
        )

    def test_get_key_raises_resource_not_found_for_nonexistent_vault(self):
        nonexistent_vault = "this-vault-does-not-exist"
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key Vault '{nonexistent_vault}' not found in subscription '{self.sub_id}'.",
            subscription=self.sub_id,
            vault=nonexistent_vault,
            key=self.key1_name
        )

    def test_get_key_raises_resource_not_found_for_nonexistent_key_in_existing_vault(self):
        nonexistent_key = "this-key-does-not-exist"
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key '{nonexistent_key}' not found in vault '{self.vault_name1}'.",
            subscription=self.sub_id,
            vault=self.vault_name1,
            key=nonexistent_key
        )

    def test_get_key_raises_resource_not_found_for_key_in_vault_with_no_keys(self):
        # self.vault_name2_empty is a vault that exists but has no keys defined in its "keys" list.
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key '{self.key1_name}' not found in vault '{self.vault_name2_empty}'.",
            subscription=self.sub_id,
            vault=self.vault_name2_empty,
            key=self.key1_name # A key name that exists in another vault, to ensure it's not found here.
        )

    def test_get_key_raises_invalid_input_for_empty_subscription(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Subscription ID/name cannot be empty.",
            subscription="",
            vault=self.vault_name1,
            key=self.key1_name
        )

    def test_get_key_raises_invalid_input_for_empty_vault_name(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Vault name cannot be empty.",
            subscription=self.sub_id,
            vault="",
            key=self.key1_name
        )

    def test_get_key_raises_invalid_input_for_empty_key_name(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_get,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Key name cannot be empty.",
            subscription=self.sub_id,
            vault=self.vault_name1,
            key=""
        )

if __name__ == '__main__':
    unittest.main()