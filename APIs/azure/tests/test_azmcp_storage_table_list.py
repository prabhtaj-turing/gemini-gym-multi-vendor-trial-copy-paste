import copy
import unittest

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.storage import azmcp_storage_table_list
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAzmcpStorageTableList(BaseTestCaseWithErrorHandler):
    """
    Test suite for the azmcp_storage_table_list function.
    """

    def setUp(self):
        """
        Set up the test environment before each test.
        This involves saving the original state of DB, clearing DB,
        and populating DB with test-specific data.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["subscriptions"] = [
            {
                "id": "sub-guid-1",  # Internal ID, not used by func directly
                "subscriptionId": "00000000-0000-0000-0000-000000000001",
                "displayName": "Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": "rg-id-1", "name": "rg1", "location": "eastus",
                        "subscription_id": "00000000-0000-0000-0000-000000000001",
                        "storage_accounts": [
                            {
                                "id": "sa-id-1", "name": "acc1sub1rg1", "location": "eastus", "kind": "StorageV2",
                                "sku": {"name": "Standard_LRS"}, "resource_group_name": "rg1",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                "tables": [
                                    {"TableName": "tableA", "account_name": "acc1sub1rg1", "other_props": "stuff"},
                                    {"TableName": "tableB", "account_name": "acc1sub1rg1"}
                                ],
                                "blob_containers": []
                            },
                            {
                                "id": "sa-id-2", "name": "acc2sub1rg1", "location": "eastus", "kind": "StorageV2",
                                "sku": {"name": "Standard_LRS"}, "resource_group_name": "rg1",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                "tables": [],  # No tables
                                "blob_containers": []
                            },
                            {
                                "id": "sa-id-3", "name": "acc3sub1rg1", "location": "eastus", "kind": "StorageV2",
                                "sku": {"name": "Standard_LRS"}, "resource_group_name": "rg1",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                # Missing 'tables' key
                                "blob_containers": []
                            }
                        ]
                    },
                    {
                        "id": "rg-id-2", "name": "rg2", "location": "westus",
                        "subscription_id": "00000000-0000-0000-0000-000000000001",
                        "storage_accounts": [
                            {
                                "id": "sa-id-4", "name": "acc1sub1rg2", "location": "westus", "kind": "StorageV2",
                                "sku": {"name": "Standard_LRS"}, "resource_group_name": "rg2",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                "tables": [
                                    {"TableName": "tableC", "account_name": "acc1sub1rg2"}
                                ],
                                "blob_containers": []
                            }
                        ]
                    }
                ]
            },
            {
                "id": "sub-guid-2",
                "subscriptionId": "00000000-0000-0000-0000-000000000002",
                "displayName": "Subscription 2 (No RGs)",
                "state": "Enabled", "tenantId": "tenant-guid-1",
                "resource_groups": []
            },
            {
                "id": "sub-guid-3",
                "subscriptionId": "00000000-0000-0000-0000-000000000003",
                "displayName": "Subscription 3 (Missing RGs key)",
                "state": "Enabled", "tenantId": "tenant-guid-1"
                # No 'resource_groups' key
            },
            {
                "id": "sub-guid-4",
                "subscriptionId": "00000000-0000-0000-0000-000000000004",
                "displayName": "Subscription 4 (RG no SAs)",
                "state": "Enabled", "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": "rg-id-3", "name": "rg3", "location": "eastus",
                        "subscription_id": "00000000-0000-0000-0000-000000000004",
                        "storage_accounts": []  # RG exists, but no storage accounts in it
                    }
                ]
            },
            {
                "id": "sub-guid-5",
                "subscriptionId": "00000000-0000-0000-0000-000000000005",
                "displayName": "Subscription 5 (RG SA missing SAs key)",
                "state": "Enabled", "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": "rg-id-4", "name": "rg4", "location": "eastus",
                        "subscription_id": "00000000-0000-0000-0000-000000000005"
                        # RG exists, but 'storage_accounts' key is missing
                    }
                ]
            }
        ]

    def tearDown(self):
        """
        Clean up the test environment after each test.
        This involves restoring the original state of DB.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_tables_success_multiple_tables(self):
        """
        Test listing tables successfully when multiple tables exist in the account.
        """
        result = azmcp_storage_table_list(
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1"
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        # Order might not be guaranteed, so check contents
        self.assertIn({"TableName": "tableA"}, result)
        self.assertIn({"TableName": "tableB"}, result)

    def test_list_tables_success_no_tables_in_account(self):
        """
        Test listing tables successfully when the account exists but has no tables.
        """
        result = azmcp_storage_table_list(
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc2sub1rg1"
        )
        self.assertEqual(result, [])

    def test_list_tables_success_tables_key_missing_in_account_data(self):
        """
        Test listing tables successfully when the account exists but its data is missing the 'tables' key.
        """
        result = azmcp_storage_table_list(
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc3sub1rg1"
        )
        self.assertEqual(result, [])

    def test_list_tables_success_account_in_different_rg(self):
        """
        Test listing tables successfully for an account located in a different resource group within the same subscription.
        """
        result = azmcp_storage_table_list(
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg2"  # This account is in rg2
        )
        expected = [{"TableName": "tableC"}]
        self.assertEqual(result, expected)

    def test_list_tables_success_subscription_by_display_name(self):
        """
        Test listing tables successfully when identifying the subscription by its display name.
        """
        result = azmcp_storage_table_list(
            subscription="Subscription 1",  # Display name for 00000000-0000-0000-0000-000000000001
            account_name="acc1sub1rg1"
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn({"TableName": "tableA"}, result)
        self.assertIn({"TableName": "tableB"}, result)

    def test_list_tables_resource_not_found_subscription_nonexistent_guid(self):
        """
        Test ResourceNotFoundError when the specified subscription GUID does not exist.
        """
        sub_id = "nonexistent-guid-sub"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'nonexistent-guid-sub' not found or is invalid.",
            subscription=sub_id,
            account_name="acc1sub1rg1"
        )

    def test_list_tables_resource_not_found_subscription_nonexistent_display_name(self):
        """
        Test ResourceNotFoundError when the specified subscription display name does not exist.
        """
        sub_name = "NonExistent Subscription Name"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message=f"Subscription '{sub_name}' not found or is invalid.",
            subscription=sub_name,
            account_name="acc1sub1rg1"
        )

    def test_list_tables_resource_not_found_account_nonexistent_in_subscription(self):
        """
        Test ResourceNotFoundError when the storage account does not exist in the specified (valid) subscription.
        """
        account_name = "nonexistentacc"
        sub_id = "00000000-0000-0000-0000-000000000001"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'nonexistentacc' not found in subscription '00000000-0000-0000-0000-000000000001' (resolved ID: '00000000-0000-0000-0000-000000000001').",
            subscription=sub_id,
            account_name=account_name
        )

    def test_list_tables_resource_not_found_account_in_subscription_with_no_rgs(self):
        """
        Test ResourceNotFoundError when the subscription exists but has no resource groups.
        """
        sub_id = "00000000-0000-0000-0000-000000000002"  # Subscription 2 (No RGs)
        account_name = "anyacc"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'anyacc' not found in subscription '00000000-0000-0000-0000-000000000002' (resolved ID: '00000000-0000-0000-0000-000000000002').",
            subscription=sub_id,
            account_name=account_name
        )

    def test_list_tables_resource_not_found_account_in_subscription_with_missing_rgs_key(self):
        """
        Test ResourceNotFoundError when the subscription exists but is missing the 'resource_groups' key.
        """
        sub_id = "00000000-0000-0000-0000-000000000003"  # Subscription 3 (Missing RGs key)
        account_name = "anyacc"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'anyacc' not found in subscription '00000000-0000-0000-0000-000000000003' (resolved ID: '00000000-0000-0000-0000-000000000003').",
            subscription=sub_id,
            account_name=account_name
        )

    def test_list_tables_resource_not_found_account_in_rg_with_no_storage_accounts(self):
        """
        Test ResourceNotFoundError when RGs exist but none contain the storage account (or RGs have no SAs).
        """
        sub_id = "00000000-0000-0000-0000-000000000004"  # Subscription 4 (RG no SAs)
        account_name = "anyacc"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'anyacc' not found in subscription '00000000-0000-0000-0000-000000000004' (resolved ID: '00000000-0000-0000-0000-000000000004').",
            subscription=sub_id,
            account_name=account_name
        )

    def test_list_tables_resource_not_found_account_in_rg_with_missing_sa_key(self):
        """
        Test ResourceNotFoundError when RG exists but is missing the 'storage_accounts' key.
        """
        sub_id = "00000000-0000-0000-0000-000000000005"  # Subscription 5 (RG missing SAs key)
        account_name = "anyacc"
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Storage account 'anyacc' not found in subscription '00000000-0000-0000-0000-000000000005' (resolved ID: '00000000-0000-0000-0000-000000000005').",
            subscription=sub_id,
            account_name=account_name
        )

    def test_list_tables_invalid_input_empty_subscription(self):
        """
        Test InvalidInputError when subscription is an empty string.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Subscription ID or name must be provided as a non-empty string.",
            subscription="",
            account_name="acc1sub1rg1"
        )

    def test_list_tables_invalid_input_empty_account_name(self):
        """
        Test InvalidInputError when account_name is an empty string.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Storage account name must be provided as a non-empty string.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name=""
        )

    def test_list_tables_validation_error_none_subscription(self):
        """
        Test ValidationError when subscription is None.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Subscription ID or name must be provided as a non-empty string.",
            # Default or part of Pydantic message
            subscription=None,
            account_name="acc1sub1rg1"
        )

    def test_list_tables_validation_error_none_account_name(self):
        """
        Test ValidationError when account_name is None.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Storage account name must be provided as a non-empty string.",
            # Default or part of Pydantic message
            subscription="00000000-0000-0000-0000-000000000001",
            account_name=None
        )

    def test_list_tables_validation_error_invalid_auth_method(self):
        """
        Test ValidationError when auth_method is not a valid AuthMethod enum value.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid auth_method. Must be one of: credential, key, connectionString",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            auth_method="invalid_method"
        )

    def test_list_tables_validation_error_non_string_auth_method(self):
        """
        Test ValidationError when auth_method is not a string.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="auth_method must be a string.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            auth_method=123
        )

    def test_list_tables_validation_error_non_string_tenant(self):
        """
        Test ValidationError when tenant is not a string.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="tenant must be a string.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            tenant=123
        )

    def test_list_tables_validation_error_invalid_retry_max_retries(self):
        """
        Test ValidationError when retry_max_retries is not a non-negative integer.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_max_retries must be a non-negative integer.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            retry_max_retries="-1"
        )

    def test_list_tables_validation_error_invalid_retry_delay(self):
        """
        Test ValidationError when retry_delay is not a non-negative number.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_delay must be a non-negative number.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            retry_delay="-1.5"
        )

    def test_list_tables_validation_error_invalid_retry_max_delay(self):
        """
        Test ValidationError when retry_max_delay is not a non-negative number.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_max_delay must be a non-negative number.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            retry_max_delay="-1.5"
        )

    def test_list_tables_validation_error_invalid_retry_mode(self):
        """
        Test ValidationError when retry_mode is not a valid value.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Invalid retry_mode. Must be one of: fixed, exponential",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            retry_mode="invalid_mode"
        )

    def test_list_tables_validation_error_non_string_retry_mode(self):
        """
        Test ValidationError when retry_mode is not a string.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_mode must be a string.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            retry_mode=123
        )

    def test_list_tables_validation_error_invalid_retry_network_timeout(self):
        """
        Test ValidationError when retry_network_timeout is not a positive number.
        """
        self.assert_error_behavior(
            func_to_call=azmcp_storage_table_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="retry_network_timeout must be a positive number.",
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            retry_network_timeout="0"
        )

    def test_list_tables_with_all_optional_params_provided(self):
        """
        Test successful execution when all optional parameters are provided.
        Their values might not affect DB-based simulation but should be accepted.
        """
        result = azmcp_storage_table_list(
            subscription="00000000-0000-0000-0000-000000000001",
            account_name="acc1sub1rg1",
            auth_method="credential",
            tenant="tenant-guid-1",
            retry_max_retries="3",
            retry_delay="5",
            retry_max_delay="60",
            retry_mode="exponential",
            retry_network_timeout="30"
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn({"TableName": "tableA"}, result)
        self.assertIn({"TableName": "tableB"}, result)


if __name__ == '__main__':
    unittest.main()
