import copy
import unittest
from datetime import datetime, timezone

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.storage import azmcp_storage_blob_list
from common_utils.base_case import BaseTestCaseWithErrorHandler


def _get_iso_timestamp(dt_object=None):
    if dt_object is None:
        dt_object = datetime.now(timezone.utc)
    return dt_object.isoformat().replace("+00:00", "Z")


class TestAzmcpStorageBlobList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.subscription_id = "sub-001"
        self.resource_group_name = "rg-primary"
        self.account_name1 = "teststorageacc001"
        self.container_name1 = "data-container"
        self.container_name2 = "empty-logs-container"
        self.container_name_no_blobs_key = "no-blobs-key-container"

        self.blob1_name = "document.pdf"
        self.blob2_name = "image.png"
        self.blob1_ts = _get_iso_timestamp(datetime(2023, 10, 1, 10, 0, 0, tzinfo=timezone.utc))
        self.blob2_ts = _get_iso_timestamp(datetime(2023, 10, 2, 12, 30, 0, tzinfo=timezone.utc))

        DB['subscriptions'] = [
            {
                "id": self.subscription_id,
                "subscriptionId": self.subscription_id,
                "displayName": "Primary Test Subscription",
                "state": "Enabled",
                "tenantId": "tenant-001",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}",
                        "name": self.resource_group_name,
                        "location": "westus",
                        "subscription_id": self.subscription_id,
                        "storage_accounts": [
                            {
                                "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group_name}/providers/Microsoft.Storage/storageAccounts/{self.account_name1}",
                                "name": self.account_name1,
                                "location": "westus",
                                "kind": "StorageV2",
                                "sku": {"name": "Standard_GRS"},
                                "resource_group_name": self.resource_group_name,
                                "subscription_id": self.subscription_id,
                                "blob_containers": [
                                    {
                                        "name": self.container_name1,
                                        "lastModified": _get_iso_timestamp(datetime(2023, 9, 1, tzinfo=timezone.utc)),
                                        "etag": "etag_container1_v1",
                                        "account_name": self.account_name1,
                                        "blobs": [
                                            {
                                                "name": self.blob1_name,
                                                "properties": {
                                                    "lastModified": self.blob1_ts,
                                                    "etag": "etag_blob1_v2",
                                                    "contentLength": 102400,  # 100KB
                                                    "contentType": "application/pdf",
                                                    "blobType": "BlockBlob",
                                                    "leaseStatus": "unlocked",
                                                    "accessTier": "Cool"
                                                },
                                                "metadata": {"department": "finance", "confidential": "true"},
                                                "container_name": self.container_name1,
                                                "account_name": self.account_name1
                                            },
                                            {
                                                "name": self.blob2_name,
                                                "properties": {
                                                    "lastModified": self.blob2_ts,
                                                    "etag": "etag_blob2_v1",
                                                    "contentLength": 204800,  # 200KB
                                                    "contentType": "image/png",
                                                    "blobType": "BlockBlob",
                                                    "leaseStatus": "locked"  # Different lease status
                                                },
                                                # No accessTier, metadata is explicitly None in DB
                                                "metadata": None,
                                                "container_name": self.container_name1,
                                                "account_name": self.account_name1
                                            }
                                        ]
                                    },
                                    {
                                        "name": self.container_name2,
                                        "lastModified": _get_iso_timestamp(datetime(2023, 9, 5, tzinfo=timezone.utc)),
                                        "etag": "etag_container2_v1",
                                        "account_name": self.account_name1,
                                        "blobs": []  # Empty container
                                    },
                                    {
                                        "name": self.container_name_no_blobs_key,
                                        "lastModified": _get_iso_timestamp(datetime(2023, 9, 6, tzinfo=timezone.utc)),
                                        "etag": "etag_container3_v1",
                                        "account_name": self.account_name1
                                        # 'blobs' key intentionally missing
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

    # Success Scenarios
    def test_list_blobs_success_multiple_blobs(self):
        result = azmcp_storage_blob_list(
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1
        )
        self.assertEqual(len(result), 2)

        blob1_res = next((b for b in result if b['name'] == self.blob1_name), None)
        self.assertIsNotNone(blob1_res)
        self.assertEqual(blob1_res['name'], self.blob1_name)
        self.assertEqual(blob1_res['properties']['lastModified'], self.blob1_ts)
        self.assertEqual(blob1_res['properties']['etag'], "etag_blob1_v2")
        self.assertEqual(blob1_res['properties']['contentLength'], 102400)
        self.assertEqual(blob1_res['properties']['contentType'], "application/pdf")
        self.assertEqual(blob1_res['properties']['blobType'], "BlockBlob")
        self.assertEqual(blob1_res['properties']['leaseStatus'], "unlocked")
        self.assertEqual(blob1_res['properties']['accessTier'], "Cool")
        self.assertEqual(blob1_res['metadata'], {"department": "finance", "confidential": "true"})

        blob2_res = next((b for b in result if b['name'] == self.blob2_name), None)
        self.assertIsNotNone(blob2_res)
        self.assertEqual(blob2_res['name'], self.blob2_name)
        self.assertEqual(blob2_res['properties']['lastModified'], self.blob2_ts)
        self.assertEqual(blob2_res['properties']['etag'], "etag_blob2_v1")
        self.assertEqual(blob2_res['properties']['contentLength'], 204800)
        self.assertEqual(blob2_res['properties']['contentType'], "image/png")
        self.assertEqual(blob2_res['properties']['blobType'], "BlockBlob")
        self.assertEqual(blob2_res['properties']['leaseStatus'], "locked")
        self.assertIsNone(blob2_res['properties'].get('accessTier'))
        self.assertIsNone(blob2_res.get('metadata'))

    def test_list_blobs_success_empty_container(self):
        result = azmcp_storage_blob_list(
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name2
        )
        self.assertEqual(len(result), 0)

    def test_list_blobs_success_container_with_missing_blobs_key_in_db(self):
        result = azmcp_storage_blob_list(
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name_no_blobs_key
        )
        self.assertEqual(len(result), 0, "Should return empty list if 'blobs' key is missing in DB container data.")

    def test_list_blobs_success_with_all_optional_params_none(self):
        result = azmcp_storage_blob_list(
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            auth_method=None,
            retry_delay=None,
            retry_max_delay=None,
            retry_max_retries=None,
            retry_mode=None,
            retry_network_timeout=None,
            tenant=None
        )
        self.assertEqual(len(result), 2)

    def test_list_blobs_success_with_valid_optional_params(self):
        result = azmcp_storage_blob_list(
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            auth_method='credential',
            retry_delay='1.5',
            retry_max_delay='45',
            retry_max_retries='4',
            retry_mode='exponential',
            retry_network_timeout='90.0',
            tenant='tenant-001'
        )
        self.assertEqual(len(result), 2)

    # Resource Not Found Scenarios
    def test_list_blobs_subscription_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'non-existent-subscription-id' not found.",
            subscription="non-existent-subscription-id",
            account_name=self.account_name1,
            container_name=self.container_name1
        )

    def test_list_blobs_account_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'nonexistentstorageacc' not found in subscription 'sub-001'.",
            subscription=self.subscription_id,
            account_name="nonexistentstorageacc",
            container_name=self.container_name1
        )

    def test_list_blobs_container_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Container 'nonexistentcontainername' not found in storage account 'teststorageacc001' (Resource Group: 'rg-primary').",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name="nonexistentcontainername"
        )

    # Input Validation Error Scenarios
    def test_list_blobs_empty_subscription_id_raises_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,  # As per docstring for invalid required params
            expected_message="The 'subscription' argument is required and must be a string.",  # Example message
            subscription="",
            account_name=self.account_name1,
            container_name=self.container_name1
        )

    def test_list_blobs_empty_account_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'account_name' argument is required and must be a string.",
            subscription=self.subscription_id,
            account_name="",
            container_name=self.container_name1
        )

    def test_list_blobs_empty_container_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'container_name' argument is required and must be a string.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=""
        )

    def test_list_blobs_invalid_retry_delay_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_delay must be a non-negative number.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_delay="thirty-seconds"  # Not a number
        )

    def test_list_blobs_invalid_retry_max_delay_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_delay must be a non-negative number.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_max_delay="-20"  # Example: negative value if not allowed, or non-numeric
        )

    def test_list_blobs_invalid_retry_max_retries_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_retries must be a non-negative integer.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_max_retries="not_an_int"
        )

    def test_list_blobs_invalid_retry_network_timeout_format_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_network_timeout must be a positive number.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_network_timeout="zero"
        )

    def test_list_blobs_invalid_retry_mode_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid retry_mode. Must be one of: fixed, exponential",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_mode="unknown_mode"
        )

    def test_list_blobs_invalid_auth_method_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid auth_method. Must be one of: credential, key, connectionString",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            auth_method="unsupported_auth"
        )

    def test_list_blobs_optional_tenant_empty_string_raises_validation_error(self):
        # Assuming tenant, if provided as a string, must not be empty.
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'tenant' argument must be a non empty string.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            tenant=""
        )

    def test_list_blobs_non_string_subscription_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'subscription' argument is required and must be a string.",
            subscription=123,  # Non-string value
            account_name=self.account_name1,
            container_name=self.container_name1
        )

    def test_list_blobs_non_string_account_name_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'account_name' argument is required and must be a string.",
            subscription=self.subscription_id,
            account_name=456,  # Non-string value
            container_name=self.container_name1
        )

    def test_list_blobs_non_string_container_name_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'container_name' argument is required and must be a string.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=789  # Non-string value
        )

    def test_list_blobs_non_string_auth_method_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="auth_method must be a string.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            auth_method=123  # Non-string value
        )

    def test_list_blobs_non_string_retry_mode_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_mode must be a string.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_mode=456  # Non-string value
        )

    def test_list_blobs_non_string_tenant_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The 'tenant' argument must be a non empty string.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            tenant=789  # Non-string value
        )

    def test_list_blobs_negative_retry_delay_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_delay must be a non-negative number.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_delay="-1.5"  # Negative value
        )

    def test_list_blobs_negative_retry_max_delay_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_delay must be a non-negative number.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_max_delay="-30"  # Negative value
        )

    def test_list_blobs_negative_retry_max_retries_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_retries must be a non-negative integer.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_max_retries="-3"  # Negative value
        )

    def test_list_blobs_zero_retry_network_timeout_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_storage_blob_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_network_timeout must be a positive number.",
            subscription=self.subscription_id,
            account_name=self.account_name1,
            container_name=self.container_name1,
            retry_network_timeout="0"  # Zero value
        )


if __name__ == '__main__':
    unittest.main()
