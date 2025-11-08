import unittest
import copy
from datetime import datetime, timezone
from ..SimulationEngine import custom_errors
from ..keyvault import azmcp_keyvault_key_create
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB

# Assume BaseTestCaseWithErrorHandler is globally available
# Assume DB is globally available
# Assume azmcp_keyvault_key_create is globally available

class TestAzmcpKeyvaultKeyCreate(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.subscription_id = "00000000-0000-0000-0000-000000000001"
        self.resource_group_name = "test-rg" 
        self.vault_name = "testkvault"
        self.location = "eastus"
        self.tenant_id = "00000000-0000-0000-0000-000000000000" 

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.subscription_id}",
                "subscriptionId": self.subscription_id,
                "displayName": "Test Subscription",
                "state": "Enabled",
                "tenantId": self.tenant_id,
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}",
                        "name": self.resource_group_name,
                        "location": self.location,
                        "subscription_id": self.subscription_id,
                        "key_vaults": [
                            {
                                "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.KeyVault/vaults/{self.vault_name}",
                                "name": self.vault_name,
                                "location": self.location,
                                "resource_group_name": self.resource_group_name, 
                                "subscription_id": self.subscription_id,
                                "properties": { 
                                    "sku": {"family": "A", "name": "standard"},
                                    "tenantId": self.tenant_id,
                                    "vaultUri": f"https://{self.vault_name}.vault.azure.net/",
                                    "enableSoftDelete": True,
                                    "softDeleteRetentionInDays": 90,
                                },
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

    def _get_vault_from_db(self):
        try:
            return DB["subscriptions"][0]["resource_groups"][0]["key_vaults"][0]
        except (IndexError, KeyError, TypeError): # TypeError if DB is not structured as list
            # This might happen if DB was cleared and not repopulated correctly by a faulty test
            return None


    def _get_key_from_db(self, key_name):
        vault = self._get_vault_from_db()
        if vault and "keys" in vault and isinstance(vault["keys"], list):
            for key_obj in vault["keys"]:
                if isinstance(key_obj, dict) and key_obj.get("name") == key_name:
                    return key_obj
        return None

    def test_create_rsa_key_success(self):
        key_name = "my-rsa-key"
        key_type = "RSA"
        
        start_time_sec = int(datetime.now(timezone.utc).timestamp())
        
        result = azmcp_keyvault_key_create(
            subscription=self.subscription_id,
            vault=self.vault_name,
            key=key_name,
            key_type=key_type
        )
        
        end_time_sec = int(datetime.now(timezone.utc).timestamp())

        self.assertIsInstance(result, dict)
        self.assertEqual(result["kty"], key_type)
        expected_rsa_ops = ["encrypt", "decrypt", "sign", "verify", "wrapKey", "unwrapKey"]
        self.assertListEqual(sorted(result["key_ops"]), sorted(expected_rsa_ops))

        attributes = result["attributes"]
        self.assertTrue(attributes["enabled"])
        self.assertIsNone(attributes["exp"])
        self.assertIsNone(attributes["nbf"])
        self.assertTrue(start_time_sec <= attributes["created"] <= end_time_sec + 2) # Allow 2s clock skew tolerance
        self.assertTrue(start_time_sec <= attributes["updated"] <= end_time_sec + 2)
        self.assertEqual(attributes["created"], attributes["updated"]) 
        self.assertIsInstance(attributes["recoveryLevel"], str)
        self.assertIn(attributes["recoveryLevel"], ["Purgeable", "Recoverable", "Recoverable+Purgeable", "Recoverable+ProtectedSubscription"])

        db_key = self._get_key_from_db(key_name)
        self.assertIsNotNone(db_key)
        self.assertEqual(db_key["name"], key_name)
        self.assertEqual(db_key["kty"], key_type)
        self.assertEqual(db_key["vault_name"], self.vault_name)
        self.assertTrue(db_key["kid"].startswith(f"https://{self.vault_name}.vault.azure.net/keys/{key_name}/"))
        self.assertTrue(len(db_key["kid"].split('/')[-1]) > 0) 
        self.assertEqual(db_key["attributes"]["enabled"], attributes["enabled"])
        self.assertEqual(db_key["attributes"]["created"], attributes["created"])
        self.assertEqual(db_key["attributes"]["updated"], attributes["updated"])
        self.assertEqual(db_key["attributes"]["recoveryLevel"], attributes["recoveryLevel"])
        self.assertListEqual(sorted(db_key["key_ops"]), sorted(expected_rsa_ops))
        self.assertIsNone(db_key.get("tags")) # Ensure tags are None by default

    def test_create_ec_key_success(self):
        key_name = "my-ec-key"
        key_type = "EC"

        start_time_sec = int(datetime.now(timezone.utc).timestamp())

        result = azmcp_keyvault_key_create(
            subscription=self.subscription_id,
            vault=self.vault_name,
            key=key_name,
            key_type=key_type
        )
        
        end_time_sec = int(datetime.now(timezone.utc).timestamp())

        self.assertEqual(result["kty"], key_type)
        expected_ec_ops = ["sign", "verify"]
        self.assertListEqual(sorted(result["key_ops"]), sorted(expected_ec_ops))

        attributes = result["attributes"]
        self.assertTrue(attributes["enabled"])
        self.assertTrue(start_time_sec <= attributes["created"] <= end_time_sec + 2)
        self.assertTrue(start_time_sec <= attributes["updated"] <= end_time_sec + 2)
        self.assertEqual(attributes["created"], attributes["updated"])
        self.assertIsInstance(attributes["recoveryLevel"], str)
        self.assertIn(attributes["recoveryLevel"], ["Purgeable", "Recoverable", "Recoverable+Purgeable", "Recoverable+ProtectedSubscription"])

        db_key = self._get_key_from_db(key_name)
        self.assertIsNotNone(db_key)
        self.assertEqual(db_key["name"], key_name)
        self.assertEqual(db_key["kty"], key_type)
        self.assertListEqual(sorted(db_key["key_ops"]), sorted(expected_ec_ops))

    def test_create_key_with_all_optional_params(self):
        key_name = "my-optional-key"
        key_type = "RSA"
        
        result = azmcp_keyvault_key_create(
            subscription=self.subscription_id,
            vault=self.vault_name,
            key=key_name,
            key_type=key_type,
            auth_method="credential",
            retry_delay="5",
            retry_max_delay="60",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="120",
            tenant=self.tenant_id
        )
        self.assertEqual(result["kty"], key_type)
        self.assertTrue(result["attributes"]["enabled"])
        
        db_key = self._get_key_from_db(key_name)
        self.assertIsNotNone(db_key)
        self.assertEqual(db_key["name"], key_name)

    def test_create_key_subscription_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            # Assuming the function constructs this specific message
            expected_message="Subscription 'non-existent-sub' not found or the vault is not accessible under it.",
            subscription="non-existent-sub",
            vault=self.vault_name,
            key="anykey",
            key_type="RSA"
        )

    def test_create_key_vault_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Key Vault 'non-existent-vault' not found in subscription '{self.subscription_id}'.",
            subscription=self.subscription_id,
            vault="non-existent-vault",
            key="anykey",
            key_type="RSA"
        )
    
    def test_create_key_missing_subscription_arg(self): 
        with self.assertRaisesRegex(TypeError, "required positional argument: 'subscription'"):
            azmcp_keyvault_key_create(
                vault=self.vault_name,
                key="somekey",
                key_type="RSA"
            )

    def test_create_key_missing_vault_arg(self):
        with self.assertRaisesRegex(TypeError, "required positional argument: 'vault'"):
            azmcp_keyvault_key_create(
                subscription=self.subscription_id,
                key="somekey",
                key_type="RSA"
            )

    def test_create_key_missing_key_name_arg(self):
        with self.assertRaisesRegex(TypeError, "required positional argument: 'key'"):
            azmcp_keyvault_key_create(
                subscription=self.subscription_id,
                vault=self.vault_name,
                key_type="RSA"
            )

    def test_create_key_missing_key_type_arg(self):
        with self.assertRaisesRegex(TypeError, "required positional argument: 'key_type'"):
            azmcp_keyvault_key_create(
                subscription=self.subscription_id,
                vault=self.vault_name,
                key="somekey"
            )

    def test_create_key_invalid_key_type_value(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid key_type 'INVALID_TYPE'. Allowed values are 'RSA', 'EC'.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            key="somekey",
            key_type="INVALID_TYPE"
        )

    def test_create_key_empty_string_subscription(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'subscription' cannot be an empty string.",
            subscription="",
            vault=self.vault_name,
            key="somekey",
            key_type="RSA"
        )
    
    def test_create_key_empty_string_vault_name(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'vault' cannot be an empty string.",
            subscription=self.subscription_id,
            vault="",
            key="somekey",
            key_type="RSA"
        )

    def test_create_key_empty_string_key_name(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Parameter 'key' cannot be an empty string.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            key="",
            key_type="RSA"
        )

    def test_create_key_invalid_retry_delay_format(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid format for 'retry_delay'. Must be a string representing a non-negative integer.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            key="somekey",
            key_type="RSA",
            retry_delay="not-a-number"
        )
    
    def test_create_key_invalid_retry_max_retries_format(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid format for 'retry_max_retries'. Must be a string representing a non-negative integer.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            key="somekey",
            key_type="RSA",
            retry_max_retries="not-an-integer"
        )
    
    def test_create_key_negative_retry_delay(self):
        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid format for 'retry_delay'. Must be a string representing a non-negative integer.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            key="somekey",
            key_type="RSA",
            retry_delay="-5"
        )

    def test_create_key_already_exists(self):
        key_name = "existing-key"
        key_type = "RSA"
        
        now_ts = int(datetime.now(timezone.utc).timestamp())
        existing_key_data = {
            "name": key_name,
            "kid": f"https://{self.vault_name}.vault.azure.net/keys/{key_name}/someversionid",
            "kty": key_type,
            "key_ops": ["encrypt"],
            "attributes": {
                "enabled": True, "exp": None, "nbf": None,
                "created": now_ts, "updated": now_ts, "recoveryLevel": "Purgeable"
            },
            "vault_name": self.vault_name,
            "tags": None 
        }
        vault_obj = self._get_vault_from_db()
        if vault_obj: # Defensive check
            vault_obj["keys"].append(existing_key_data)
        else:
            self.fail("Setup error: Vault object not found in DB for pre-population.")


        self.assert_error_behavior(
            func_to_call=azmcp_keyvault_key_create,
            expected_exception_type=custom_errors.ConflictError,
            expected_message=f"A key with name '{key_name}' already exists in vault '{self.vault_name}'.",
            subscription=self.subscription_id,
            vault=self.vault_name,
            key=key_name,
            key_type=key_type 
        )
        
        current_keys_in_db = self._get_vault_from_db()["keys"] if self._get_vault_from_db() else []
        self.assertEqual(len(current_keys_in_db), 1)
        if current_keys_in_db:
            self.assertEqual(current_keys_in_db[0]["name"], key_name)

if __name__ == '__main__':
    unittest.main()