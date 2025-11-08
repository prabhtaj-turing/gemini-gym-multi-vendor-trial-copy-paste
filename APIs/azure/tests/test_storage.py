import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from .. import azmcp_storage_blob_container_details
from common_utils.base_case import BaseTestCaseWithErrorHandler
from datetime import datetime, timezone
from .. import azmcp_storage_account_list
from .. import azmcp_storage_blob_container_list
from .. import azmcp_storage_table_list

def get_current_utc_timestamp_iso_for_tests():
    """Helper to generate consistent ISO timestamps for tests."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class TestAzmcpStorageBlobContainerDetails(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.subscription_id1 = "sub-id-1"
        self.resource_group_name1 = "rg-test-1"
        self.account_name1 = "storageacc1"
        
        self.container_name1_full = "containerone"
        self.container_name2_minimal = "containertwo"
        self.container_name3_public_blob = "containerpublicblob"
        self.container_name4_public_container = "containerpubliccontainer"
        self.container_name5_immutable = "containerimmutable"
        self.container_name6_legal_hold = "containerlegalhold"
        self.container_name7_empty_metadata = "containeremptymeta"
        self.container_name8_malformed = "containermalformed"

        self.now_iso = get_current_utc_timestamp_iso_for_tests()

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.subscription_id1}",
                "subscriptionId": self.subscription_id1,
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-id-1",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.subscription_id1}/resourceGroups/{self.resource_group_name1}",
                        "name": self.resource_group_name1,
                        "location": "eastus",
                        "subscription_id": self.subscription_id1,
                        "storage_accounts": [
                            {
                                "id": f"/subscriptions/{self.subscription_id1}/resourceGroups/{self.resource_group_name1}/providers/Microsoft.Storage/storageAccounts/{self.account_name1}",
                                "name": self.account_name1,
                                "location": "eastus",
                                "kind": "StorageV2",
                                "sku": {"name": "Standard_LRS"},
                                "resource_group_name": self.resource_group_name1,
                                "subscription_id": self.subscription_id1,
                                "blob_containers": [
                                    {
                                        "name": self.container_name1_full,
                                        "lastModified": self.now_iso, "etag": "etag1",
                                        "leaseStatus": "locked", "leaseState": "leased",
                                        "publicAccess": "blob", "hasImmutabilityPolicy": True,
                                        "hasLegalHold": False, "metadata": {"key1": "value1", "key2": "value2"},
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name2_minimal,
                                        "lastModified": self.now_iso, "etag": "etag2",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": None, "hasImmutabilityPolicy": False,
                                        "hasLegalHold": False, "metadata": None,
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name3_public_blob,
                                        "lastModified": self.now_iso, "etag": "etag3pb",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": "blob", "hasImmutabilityPolicy": False,
                                        "hasLegalHold": False, "metadata": None,
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name4_public_container,
                                        "lastModified": self.now_iso, "etag": "etag4pc",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": "container", "hasImmutabilityPolicy": False,
                                        "hasLegalHold": False, "metadata": None,
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name5_immutable,
                                        "lastModified": self.now_iso, "etag": "etag5im",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": None, "hasImmutabilityPolicy": True,
                                        "hasLegalHold": False, "metadata": None,
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name6_legal_hold,
                                        "lastModified": self.now_iso, "etag": "etag6lh",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": None, "hasImmutabilityPolicy": False,
                                        "hasLegalHold": True, "metadata": None,
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name7_empty_metadata,
                                        "lastModified": self.now_iso, "etag": "etag7em",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": None, "hasImmutabilityPolicy": False,
                                        "hasLegalHold": False, "metadata": {},
                                        "account_name": self.account_name1, "blobs": []
                                    },
                                    {
                                        "name": self.container_name8_malformed,
                                        "lastModified": self.now_iso, "etag": "etag8mf",
                                        "leaseStatus": "unlocked", "leaseState": "available",
                                        "publicAccess": None,
                                        "hasImmutabilityPolicy": "this-is-not-a-boolean", # Invalid type
                                        "hasLegalHold": False, "metadata": None,
                                        "account_name": self.account_name1, "blobs": []
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

    def test_get_container_details_success_full_properties(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1,
            account_name=self.account_name1,
            container_name=self.container_name1_full
        )
        expected = {
            "name": self.container_name1_full, "lastModified": self.now_iso,
            "etag": "etag1", "leaseStatus": "locked", "leaseState": "leased",
            "publicAccess": "blob", "hasImmutabilityPolicy": True,
            "hasLegalHold": False, "metadata": {"key1": "value1", "key2": "value2"}
        }
        self.assertEqual(result, expected)

    def test_get_container_details_success_minimal_properties(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1,
            account_name=self.account_name1,
            container_name=self.container_name2_minimal
        )
        expected = {
            "name": self.container_name2_minimal, "lastModified": self.now_iso,
            "etag": "etag2", "leaseStatus": "unlocked", "leaseState": "available",
            "publicAccess": None, "hasImmutabilityPolicy": False,
            "hasLegalHold": False, "metadata": None
        }
        self.assertEqual(result, expected)

    def test_get_container_details_success_empty_metadata(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1,
            account_name=self.account_name1,
            container_name=self.container_name7_empty_metadata
        )
        self.assertEqual(result["metadata"], {})
        self.assertEqual(result["name"], self.container_name7_empty_metadata)


    def test_get_container_details_public_access_blob(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=self.container_name3_public_blob
        )
        self.assertEqual(result["publicAccess"], "blob")

    def test_get_container_details_public_access_container(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=self.container_name4_public_container
        )
        self.assertEqual(result["publicAccess"], "container")

    def test_get_container_details_has_immutability_policy_true(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=self.container_name5_immutable
        )
        self.assertTrue(result["hasImmutabilityPolicy"])

    def test_get_container_details_has_legal_hold_true(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=self.container_name6_legal_hold
        )
        self.assertTrue(result["hasLegalHold"])

    def test_get_container_details_with_all_optional_params_provided(self):
        result = azmcp_storage_blob_container_details(
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=self.container_name1_full, auth_method="credential",
            tenant="test-tenant", retry_max_retries="5", retry_delay="2",
            retry_max_delay="60", retry_mode="exponential", retry_network_timeout="100"
        )
        self.assertEqual(result["name"], self.container_name1_full)

    def test_get_container_details_subscription_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Storage account '{self.account_name1}' not found.",
            subscription="non-existent-sub", account_name=self.account_name1,
            container_name=self.container_name1_full
        )

    def test_get_container_details_resource_group_not_found(self):
        # Temporarily modify DB for this test to ensure RG is not found
        # This assumes DB["subscriptions"][0] exists and is the one being targeted.
        original_rgs = DB["subscriptions"][0]["resource_groups"]
        DB["subscriptions"][0]["resource_groups"] = []
        try:
            self.assert_error_behavior(
                func_to_call=azmcp_storage_blob_container_details,
                expected_exception_type=custom_errors.ResourceNotFoundError,
                expected_message=f"Storage account '{self.account_name1}' not found.",
                subscription=self.subscription_id1, account_name=self.account_name1,
                container_name=self.container_name1_full
            )
        finally:
            DB["subscriptions"][0]["resource_groups"] = original_rgs


    def test_get_container_details_account_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'non-existent-account' not found.",
            subscription=self.subscription_id1, account_name="non-existent-account",
            container_name=self.container_name1_full
        )

    def test_get_container_details_container_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Container 'non-existent-container' not found in storage account '{self.account_name1}'.",
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name="non-existent-container"
        )

    def test_get_container_details_missing_essential_fields_raises_service_error(self):
        """Covers branch that validates presence of name/lastModified/etag."""
        containers = DB["subscriptions"][0]["resource_groups"][0]["storage_accounts"][0]["blob_containers"]
        containers.append({
            "name": "missing-essentials",
            "lastModified": self.now_iso,
            # etag intentionally missing
            "account_name": self.account_name1,
            "blobs": []
        })

        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ServiceError,
            expected_message=(
                f"Incomplete data for container 'missing-essentials' in account '{self.account_name1}'. "
                "Essential properties (name, lastModified, or etag) are missing from the stored data."
            ),
            subscription=self.subscription_id1,
            account_name=self.account_name1,
            container_name="missing-essentials"
        )

    def test_get_container_details_missing_subscription_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Field required", 
            subscription=None, account_name=self.account_name1,
            container_name=self.container_name1_full
        )

    def test_get_container_details_empty_subscription_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="String should have at least 1 character",
            subscription="", account_name=self.account_name1,
            container_name=self.container_name1_full
        )

    def test_get_container_details_missing_account_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'account_name' is missing.",
            subscription=self.subscription_id1, account_name=None,
            container_name=self.container_name1_full
        )

    def test_get_container_details_empty_account_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'account_name' cannot be empty.",
            subscription=self.subscription_id1, account_name="",
            container_name=self.container_name1_full
        )

    def test_get_container_details_missing_container_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'container_name' is missing.",
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=None
        )

    def test_get_container_details_empty_container_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'container_name' cannot be empty.",
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=""
        )

    def test_get_container_details_invalid_subscription_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string",
            subscription=123, account_name=self.account_name1,
            container_name=self.container_name1_full
        )

    def test_get_container_details_invalid_account_name_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string",
            subscription=self.subscription_id1, account_name=123,
            container_name=self.container_name1_full
        )

    def test_get_container_details_invalid_container_name_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string",
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=123
        )

    def test_get_container_details_optional_retry_params_invalid_type_string_expected(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_container_details,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string",
            subscription=self.subscription_id1, account_name=self.account_name1,
            container_name=self.container_name1_full, retry_max_retries=5 
        )
    
    def test_service_error_on_malformed_db_data(self):
        """
        Tests that a ServiceError is raised if data from the DB is malformed
        and fails the Pydantic output model validation.
        """
        # We expect a ServiceError because the Pydantic output model will fail to validate
        # the malformed data (a string instead of a boolean).
        with self.assertRaises(custom_errors.ServiceError) as cm:
            azmcp_storage_blob_container_details(
                subscription=self.subscription_id1,
                account_name=self.account_name1,
                container_name=self.container_name8_malformed
            )
        
        # Verify that the error message is informative and contains the root cause.
        error_message = str(cm.exception)
        self.assertIn("Failed to serialize container properties due to invalid data", error_message)
        # Check that the message includes details from the underlying Pydantic error
        self.assertIn("hasImmutabilityPolicy", error_message)
        self.assertIn("Input should be a valid boolean", error_message)



class TestAzmcpStorageAccountList(BaseTestCaseWithErrorHandler):

    def _create_sa_dict_for_db(self, sub_id, rg_name, sa_name, location="eastus", kind="StorageV2",
                             sku_name="Standard_LRS", sku_tier="Standard", prov_state="Succeeded",
                             endpoints=None):
        sa_id_path = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Storage/storageAccounts/{sa_name}"
        if endpoints is None:
            endpoints = {
                "blob": f"https://{sa_name}.blob.core.windows.net/",
                "queue": f"https://{sa_name}.queue.core.windows.net/",
                "table": f"https://{sa_name}.table.core.windows.net/",
                "file": f"https://{sa_name}.file.core.windows.net/"
            }
        return {
            "id": sa_id_path,
            "name": sa_name,
            "location": location,
            "kind": kind,
            "sku": {"name": sku_name, "tier": sku_tier},
            "provisioningState": prov_state,
            "primaryEndpoints": endpoints,
            "resource_group_name": rg_name,
            "subscription_id": sub_id,
            "blob_containers": [],
            "tables": []
        }

    def _get_expected_sa_output(self, sa_db_dict):
        """
        Updated to match the output from the Pydantic model's .model_dump(),
        which includes all fields from the AzureSku model.
        """
        return {
            "name": sa_db_dict["name"],
            "id": sa_db_dict["id"],
            "location": sa_db_dict["location"],
            "kind": sa_db_dict["kind"],
            "sku": {
                "name": sa_db_dict["sku"]["name"],
                "tier": sa_db_dict["sku"]["tier"],
                "capacity": None,
                "family": None
            },
            "provisioningState": sa_db_dict["provisioningState"],
            "primaryEndpoints": sa_db_dict["primaryEndpoints"]
        }

    def _sort_sa_list(self, sa_list):
        return sorted(sa_list, key=lambda x: x['id'])

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sub1_id = "00000000-0000-0000-0000-000000000001"
        self.sub1_name = "Subscription One"
        self.sub2_id = "00000000-0000-0000-0000-000000000002"
        self.sub3_id = "00000000-0000-0000-0000-000000000003"
        self.sub4_id = "00000000-0000-0000-0000-000000000004"

        self.tenant1_id = "tenant-0000-0000-0001"
        self.tenant2_id = "tenant-0000-0000-0002"


        self.rg1_name = "rg-prod-eastus"
        self.rg2_name = "rg-dev-westus"
        self.rg3_name = "rg-empty-sa"

        self.sa1_sub1_rg1 = self._create_sa_dict_for_db(self.sub1_id, self.rg1_name, "sa1prod")
        self.sa2_sub1_rg1 = self._create_sa_dict_for_db(self.sub1_id, self.rg1_name, "sa2prod", location="eastus2", kind="BlobStorage")
        self.sa3_sub1_rg2 = self._create_sa_dict_for_db(self.sub1_id, self.rg2_name, "sa1dev", location="westus", sku_name="Premium_LRS", sku_tier="Premium")

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.sub1_id}",
                "subscriptionId": self.sub1_id,
                "displayName": self.sub1_name,
                "state": "Enabled",
                "tenantId": self.tenant1_id,
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub1_id}/resourceGroups/{self.rg1_name}",
                        "name": self.rg1_name,
                        "location": "eastus",
                        "subscription_id": self.sub1_id,
                        "storage_accounts": [self.sa1_sub1_rg1, self.sa2_sub1_rg1]
                    },
                    {
                        "id": f"/subscriptions/{self.sub1_id}/resourceGroups/{self.rg2_name}",
                        "name": self.rg2_name,
                        "location": "westus",
                        "subscription_id": self.sub1_id,
                        "storage_accounts": [self.sa3_sub1_rg2]
                    }
                ]
            },
            {
                "id": f"/subscriptions/{self.sub2_id}",
                "subscriptionId": self.sub2_id,
                "displayName": "Subscription Two",
                "state": "Enabled",
                "tenantId": self.tenant2_id,
                "resource_groups": [
                     {
                        "id": f"/subscriptions/{self.sub2_id}/resourceGroups/rg-for-sub2",
                        "name": "rg-for-sub2",
                        "location": "northcentralus",
                        "subscription_id": self.sub2_id,
                        "storage_accounts": []
                    }
                ]
            },
            {
                "id": f"/subscriptions/{self.sub3_id}",
                "subscriptionId": self.sub3_id,
                "displayName": "Subscription Three (RG, No SAs)",
                "state": "Enabled",
                "tenantId": self.tenant1_id,
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub3_id}/resourceGroups/{self.rg3_name}",
                        "name": self.rg3_name,
                        "location": "centralus",
                        "subscription_id": self.sub3_id,
                        "storage_accounts": []
                    }
                ]
            },
            {
                "id": f"/subscriptions/{self.sub4_id}",
                "subscriptionId": self.sub4_id,
                "displayName": "Subscription Four (No RGs)",
                "state": "Enabled",
                "tenantId": self.tenant1_id,
                "resource_groups": []
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_storage_accounts_success_multiple_rgs_multiple_sas(self):
        result = azmcp_storage_account_list(subscription=self.sub1_id)
        self.assertIsInstance(result, dict)
        self.assertIn("storage_accounts", result)

        actual_sas = self._sort_sa_list(result["storage_accounts"])
        expected_sas_db_data = [self.sa1_sub1_rg1, self.sa2_sub1_rg1, self.sa3_sub1_rg2]
        expected_sas_output = self._sort_sa_list([self._get_expected_sa_output(sa) for sa in expected_sas_db_data])

        self.assertEqual(len(actual_sas), 3)
        self.assertEqual(actual_sas, expected_sas_output)
        self.assertIn(self._get_expected_sa_output(self.sa1_sub1_rg1), actual_sas)
        self.assertIn(self._get_expected_sa_output(self.sa2_sub1_rg1), actual_sas)
        self.assertIn(self._get_expected_sa_output(self.sa3_sub1_rg2), actual_sas)

    def test_list_storage_accounts_success_by_display_name(self):
        result = azmcp_storage_account_list(subscription=self.sub1_name)
        self.assertIsInstance(result, dict)
        self.assertIn("storage_accounts", result)

        actual_sas = self._sort_sa_list(result["storage_accounts"])
        expected_sas_db_data = [self.sa1_sub1_rg1, self.sa2_sub1_rg1, self.sa3_sub1_rg2]
        expected_sas_output = self._sort_sa_list([self._get_expected_sa_output(sa) for sa in expected_sas_db_data])

        self.assertEqual(len(actual_sas), 3)
        self.assertEqual(actual_sas, expected_sas_output)

    # --- NEW TESTS FOR INCREASED COVERAGE ---

    def test_list_fails_when_subscription_id_found_in_wrong_tenant(self):
        """
        Tests that an error is raised with a specific message if the subscription
        ID exists but belongs to a different tenant than the one provided.
        """
        # self.sub1_id belongs to self.tenant1_id. We pass in self.tenant2_id.
        with self.assertRaises(custom_errors.SubscriptionNotFoundError) as cm:
            azmcp_storage_account_list(subscription=self.sub1_id, tenant=self.tenant2_id)

        expected_message = f"Subscription '{self.sub1_id}' was found, but it does not belong to the specified tenant '{self.tenant2_id}'."
        self.assertEqual(str(cm.exception), expected_message)

    def test_list_fails_when_subscription_name_found_in_wrong_tenant(self):
        """
        Tests that an error is raised with a specific message if the subscription
        display name exists but belongs to a different tenant than the one provided.
        """
        # self.sub1_name belongs to self.tenant1_id. We pass in self.tenant2_id.
        with self.assertRaises(custom_errors.SubscriptionNotFoundError) as cm:
            azmcp_storage_account_list(subscription=self.sub1_name, tenant=self.tenant2_id)

        expected_message = f"Subscription '{self.sub1_name}' was found, but it does not belong to the specified tenant '{self.tenant2_id}'."
        self.assertEqual(str(cm.exception), expected_message)

    def test_list_fails_when_subscription_and_tenant_not_found(self):
        """
        Tests that a general 'not found' error is raised if the subscription
        does not exist, even when a tenant is specified. This covers the 'else'
        block of the logic in question.
        """
        non_existent_sub = "12345-non-existent-sub-67890"
        non_existent_tenant = "non-existent-tenant"
        with self.assertRaises(custom_errors.SubscriptionNotFoundError) as cm:
            azmcp_storage_account_list(subscription=non_existent_sub, tenant=non_existent_tenant)

        # This should trigger the generic "not found" message, not the specific "wrong tenant" one.
        expected_message = f"The specified Azure subscription '{non_existent_sub}' was not found or is not accessible."
        self.assertEqual(str(cm.exception), expected_message)

    def test_list_storage_accounts_success_subscription_with_rg_but_no_sas(self):
        # sub2_id has an RG, but that RG has no storage accounts.
        # sub3_id is explicitly set up this way too. Using sub3_id for this test.
        result = azmcp_storage_account_list(subscription=self.sub3_id)
        self.assertIsInstance(result, dict)
        self.assertIn("storage_accounts", result)
        self.assertEqual(result["storage_accounts"], [])

    def test_list_storage_accounts_success_subscription_with_no_rgs(self):
        # sub4_id is set up with no resource groups.
        result = azmcp_storage_account_list(subscription=self.sub4_id)
        self.assertIsInstance(result, dict)
        self.assertIn("storage_accounts", result)
        self.assertEqual(result["storage_accounts"], [])

    def test_list_storage_accounts_success_with_all_optional_params(self):
        result = azmcp_storage_account_list(
            subscription=self.sub1_id,
            auth_method="credential",
            retry_delay="5",
            retry_max_delay="60",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="100",
            tenant=self.tenant1_id
        )
        self.assertIsInstance(result, dict)
        self.assertIn("storage_accounts", result)
        self.assertEqual(len(result["storage_accounts"]), 3)

    def test_table_list_service_error_when_subscription_missing_id(self):
        """Covers ServiceError branch when subscription data lacks subscriptionId."""
        DB["subscriptions"].append({
            "id": "/subscriptions/dummy-no-id",
            "displayName": "Sub Missing ID Field",
            "state": "Enabled",
            "tenantId": self.tenant1_id,
            "resource_groups": [
                {
                    "id": "/subscriptions/dummy-no-id/resourceGroups/rg-x",
                    "name": "rg-x",
                    "location": "eastus",
                    "storage_accounts": [self._create_sa_dict_for_db("dummy-no-id", "rg-x", "accInvalid")]
                }
            ]
        })

        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ServiceError,
            expected_message="Internal error: Subscription data for 'Sub Missing ID Field' is missing its 'subscriptionId'.",
            subscription="Sub Missing ID Field",
            account_name="accInvalid"
        )

    def test_table_list_invalid_storage_account_kind_raises_service_error(self):
        """Covers branch that validates StorageAccountKind enum conversion."""
        DB["subscriptions"][0]["resource_groups"][0]["storage_accounts"].append({
            "id": f"/subscriptions/{self.sub1_id}/resourceGroups/{self.rg1_name}/providers/Microsoft.Storage/storageAccounts/accInvalidKind",
            "name": "accInvalidKind",
            "location": "eastus",
            "kind": "NotAKind",
            "sku": {"name": "Standard_LRS"},
            "resource_group_name": self.rg1_name,
            "subscription_id": self.sub1_id,
            "blob_containers": [],
            "tables": []
        })

        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ServiceError,
            expected_message="Invalid storage account kind 'NotAKind' for account 'accInvalidKind'.",
            subscription=self.sub1_id,
            account_name="accInvalidKind"
        )

    def test_list_storage_accounts_error_subscription_not_found_by_id(self):
        non_existent_sub_id = "00000000-0000-0000-0000-000000009999"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_account_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message=f"The specified Azure subscription '{non_existent_sub_id}' was not found or is not accessible.",
            subscription=non_existent_sub_id
        )

    def test_list_storage_accounts_error_subscription_not_found_by_name(self):
        non_existent_sub_name = "NonExistentSubscriptionName"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_account_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message=f"The specified Azure subscription '{non_existent_sub_name}' was not found or is not accessible.",
            subscription=non_existent_sub_name
        )

    def test_list_storage_accounts_error_subscription_id_empty_string(self):
        # Assuming the function validates against empty subscription ID
        self.assert_error_behavior(
            func_to_call=azmcp_storage_account_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Subscription ID cannot be empty.", # Assumed specific message
            subscription=""
        )

    def test_list_storage_accounts_error_optional_param_invalid_retry_delay(self):
        # Example: retry_delay is not a valid number string
        self.assert_error_behavior(
            func_to_call=azmcp_storage_account_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid value for retry_delay: 'abc'. Must be an integer string.", # Assumed specific message
            subscription=self.sub1_id,
            retry_delay="abc"
        )

    def test_list_fails_with_invalid_retry_parameter_values(self):
        """
        Tests that a ValidationError is raised for non-integer retry parameters.
        This test method efficiently checks all similar validation blocks.
        """
        invalid_value = "not-a-number"
        retry_params = [
            "retry_delay",
            "retry_max_retries",
            "retry_max_delay",
            "retry_network_timeout"
        ]

        for param in retry_params:
            with self.subTest(param=param):
                with self.assertRaises(custom_errors.ValidationError) as cm:
                    # Pass the invalid value to the current parameter being tested
                    kwargs = {"subscription": self.sub1_id, param: invalid_value}
                    azmcp_storage_account_list(**kwargs)

                expected_message = f"Invalid value for {param}: '{invalid_value}'. Must be an integer string."
                self.assertEqual(str(cm.exception), expected_message)

    def test_list_fails_with_invalid_retry_mode(self):
        """
        Tests that a ValidationError is raised for an invalid retry_mode value.
        """
        invalid_value = "sideways"
        with self.assertRaises(custom_errors.ValidationError) as cm:
            azmcp_storage_account_list(subscription=self.sub1_id, retry_mode=invalid_value)

        allowed_modes = ['fixed', 'exponential']
        expected_message = f"Invalid retry_mode: '{invalid_value}'. Allowed values are: {', '.join(allowed_modes)}."
        self.assertEqual(str(cm.exception), expected_message)

class TestAzmcpStorageBlobContainerList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self._populate_db()

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _populate_db(self):
        DB['subscriptions'] = [{'id': '/subscriptions/00000000-0000-0000-0000-000000000001', 'subscriptionId': '00000000-0000-0000-0000-000000000001', 'displayName': 'Test Subscription 1', 'state': 'Enabled', 'tenantId': 'tenant-id-common', 'resource_groups': [{'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1', 'name': 'rg1', 'location': 'eastus', 'subscription_id': '00000000-0000-0000-0000-000000000001', 'storage_accounts': [{'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/testacc1', 'name': 'testacc1', 'location': 'eastus', 'kind': 'StorageV2', 'sku': {'name': 'Standard_LRS'}, 'resource_group_name': 'rg1', 'subscription_id': '00000000-0000-0000-0000-000000000001', 'blob_containers': [{'name': 'containerA', 'lastModified': '2023-10-26T10:00:00Z', 'etag': '0x8DABC0C1A4991E0', 'leaseStatus': 'unlocked', 'publicAccess': 'container', 'account_name': 'testacc1'}, {'name': 'containerB', 'lastModified': '2023-10-27T11:00:00Z', 'etag': '0x8DABC0C1A4991E1', 'leaseStatus': 'locked', 'publicAccess': None, 'account_name': 'testacc1'}], 'tables': []}, {'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/emptyacc', 'name': 'emptyacc', 'location': 'eastus', 'kind': 'StorageV2', 'sku': {'name': 'Standard_LRS'}, 'resource_group_name': 'rg1', 'subscription_id': '00000000-0000-0000-0000-000000000001', 'blob_containers': [], 'tables': []}], 'app_config_stores': [], 'cosmos_db_accounts': [], 'key_vaults': [], 'log_analytics_workspaces': [], 'monitor_health_models': []}, {'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2_no_accounts', 'name': 'rg2_no_accounts', 'location': 'westus', 'subscription_id': '00000000-0000-0000-0000-000000000001', 'storage_accounts': [], 'app_config_stores': [], 'cosmos_db_accounts': [], 'key_vaults': [], 'log_analytics_workspaces': [], 'monitor_health_models': []}]}, {'id': '/subscriptions/00000000-0000-0000-0000-000000000002', 'subscriptionId': '00000000-0000-0000-0000-000000000002', 'displayName': 'Empty Subscription', 'state': 'Enabled', 'tenantId': 'tenant-id-common', 'resource_groups': []}]

    def test_list_containers_success(self):
        subscription_id = '00000000-0000-0000-0000-000000000001'
        account_name = 'testacc1'
        result = azmcp_storage_blob_container_list(subscription=subscription_id, account_name=account_name)

        expected_containers = [
            {'name': 'containerA', 'lastModified': '2023-10-26T10:00:00Z', 'etag': '0x8DABC0C1A4991E0', 'leaseStatus': 'unlocked', 'publicAccess': 'container'},
            {'name': 'containerB', 'lastModified': '2023-10-27T11:00:00Z', 'etag': '0x8DABC0C1A4991E1', 'leaseStatus': 'locked'}
        ]

        self.assertEqual(len(result), 2)
        self.assertCountEqual(result, expected_containers)

    def test_list_containers_success_with_subscription_name(self):
        subscription_name = 'Test Subscription 1'
        account_name = 'testacc1'
        result = azmcp_storage_blob_container_list(subscription=subscription_name, account_name=account_name)

        expected_containers = [
            {'name': 'containerA', 'lastModified': '2023-10-26T10:00:00Z', 'etag': '0x8DABC0C1A4991E0', 'leaseStatus': 'unlocked', 'publicAccess': 'container'},
            {'name': 'containerB', 'lastModified': '2023-10-27T11:00:00Z', 'etag': '0x8DABC0C1A4991E1', 'leaseStatus': 'locked'}
        ]

        self.assertEqual(len(result), 2)
        self.assertCountEqual(result, expected_containers)

    def test_list_skips_malformed_container_data(self):
        """
        Ensures that if a container in the DB has malformed data that fails
        Pydantic validation, it is skipped and does not crash the function.
        """

        DB['subscriptions'][0]['resource_groups'][0]['storage_accounts'][0]['blob_containers'].append(
            {'name': 'malformed-container', 'lastModified': '2023-10-28T12:00:00Z', 'etag': None, 'leaseStatus': 'unlocked'}
        )

        subscription_id = '00000000-0000-0000-0000-000000000001'
        account_name = 'testacc1'
        result = azmcp_storage_blob_container_list(subscription=subscription_id, account_name=account_name)

        self.assertEqual(len(result), 2, "Function should have skipped the malformed container.")
        self.assertNotIn('malformed-container', [c['name'] for c in result])

    def test_list_containers_no_containers_in_account_success(self):
        subscription_id = '00000000-0000-0000-0000-000000000001'
        account_name = 'emptyacc'
        result = azmcp_storage_blob_container_list(subscription=subscription_id, account_name=account_name)
        self.assertEqual(len(result), 0)
        self.assertListEqual(result, [])

    def test_list_containers_storage_account_not_found(self):
        subscription_id = '00000000-0000-0000-0000-000000000001'
        non_existent_account_name = 'nonexistentacc'
        self.assert_error_behavior(func_to_call=azmcp_storage_blob_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Storage account '{non_existent_account_name}' not found in subscription '{subscription_id}'.", subscription=subscription_id, account_name=non_existent_account_name)

    def test_list_containers_account_in_different_subscription_not_found(self):
        DB['subscriptions'].append({'id': '/subscriptions/sub-id-other', 'subscriptionId': 'sub-id-other', 'displayName': 'Other Subscription', 'state': 'Enabled', 'tenantId': 'tenant-id-common', 'resource_groups': [{'name': 'rg_other', 'location': 'eastus', 'subscription_id': 'sub-id-other', 'storage_accounts': [{'name': 'acc_in_other_sub', 'location': 'eastus', 'kind': 'StorageV2', 'sku': {'name': 'Standard_LRS'}, 'resource_group_name': 'rg_other', 'subscription_id': 'sub-id-other', 'blob_containers': [], 'tables': []}], 'app_config_stores': [], 'cosmos_db_accounts': [], 'key_vaults': [], 'log_analytics_workspaces': [], 'monitor_health_models': []}]})
        target_subscription_id = '00000000-0000-0000-0000-000000000001'
        account_name_in_other_sub = 'acc_in_other_sub'
        self.assert_error_behavior(func_to_call=azmcp_storage_blob_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Storage account '{account_name_in_other_sub}' not found in subscription '{target_subscription_id}'.", subscription=target_subscription_id, account_name=account_name_in_other_sub)

    def test_list_containers_subscription_not_found_by_id(self):
        non_existent_subscription_id = '00000000-0000-0000-0000-000000000009'
        account_name = 'testacc1'
        self.assert_error_behavior(func_to_call=azmcp_storage_blob_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Subscription '{non_existent_subscription_id}' not found.", subscription=non_existent_subscription_id, account_name=account_name)

    def test_list_containers_subscription_not_found_by_name(self):
        non_existent_subscription_name = 'NonExistent Subscription Name'
        account_name = 'testacc1'
        self.assert_error_behavior(func_to_call=azmcp_storage_blob_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Subscription '{non_existent_subscription_name}' not found.", subscription=non_existent_subscription_name, account_name=account_name)

    def test_list_containers_with_all_optional_params_success(self):
        subscription_id = '00000000-0000-0000-0000-000000000001'
        account_name = 'testacc1'
        result = azmcp_storage_blob_container_list(subscription=subscription_id, account_name=account_name, auth_method='credential', tenant='tenant-id-common', retry_max_retries='3', retry_delay='5', retry_max_delay='60', retry_mode='exponential', retry_network_timeout='100')
        self.assertEqual(len(result), 2)

    def test_list_containers_empty_account_name_raises_invalid_input_error(self):
        subscription_id = '00000000-0000-0000-0000-000000000001'
        self.assert_error_behavior(func_to_call=azmcp_storage_blob_container_list, expected_exception_type=custom_errors.InvalidInputError, expected_message="Required parameter 'account-name' is missing or invalid.", subscription=subscription_id, account_name='')

    def test_list_containers_empty_subscription_id_raises_resource_not_found_error(self):
        empty_subscription_id = ''
        self.assert_error_behavior(func_to_call=azmcp_storage_blob_container_list, expected_exception_type=custom_errors.ResourceNotFoundError, expected_message=f"Subscription '{empty_subscription_id}' not found.", subscription=empty_subscription_id, account_name='testacc1')

    def test_list_containers_account_exists_in_different_rg_found_by_iteration(self):
        new_rg_name = 'rg_new_for_iteration_test'
        account_in_new_rg_name = 'acc_in_new_rg_iteration'
        new_rg = {'id': f'/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/{new_rg_name}', 'name': new_rg_name, 'location': 'westus', 'subscription_id': '00000000-0000-0000-0000-000000000001', 'storage_accounts': [{'id': f'/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/{new_rg_name}/providers/Microsoft.Storage/storageAccounts/{account_in_new_rg_name}', 'name': account_in_new_rg_name, 'location': 'westus', 'kind': 'StorageV2', 'sku': {'name': 'Standard_LRS'}, 'resource_group_name': new_rg_name, 'subscription_id': '00000000-0000-0000-0000-000000000001', 'blob_containers': [{'name': 'containerX', 'lastModified': '2023-11-01T10:00:00Z', 'etag': 'etagX', 'leaseStatus': 'unlocked', 'publicAccess': 'blob', 'account_name': account_in_new_rg_name}], 'tables': []}], 'app_config_stores': [], 'cosmos_db_accounts': [], 'key_vaults': [], 'log_analytics_workspaces': [], 'monitor_health_models': []}
        DB['subscriptions'][0]['resource_groups'].append(new_rg)
        subscription_id = '00000000-0000-0000-0000-000000000001'
        result = azmcp_storage_blob_container_list(subscription=subscription_id, account_name=account_in_new_rg_name)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'containerX')
        
if __name__ == '__main__':
    unittest.main()