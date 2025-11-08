import copy
import unittest

from azure.SimulationEngine import custom_errors
from azure.SimulationEngine.db import DB
from azure.loganalytics import azmcp_monitor_table_type_list
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAzmcpMonitorTableTypeList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sub_id1 = "00000000-0000-0000-0000-000000000001"
        self.rg_name1 = "Default-RG"
        self.ws_name1 = "MyWorkspace1"
        self.ws_id1 = f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name1}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name1}"
        self.table_types1 = ["AzureDiagnostics", "CustomLogs", "Syslog"]

        self.ws_name2 = "MyWorkspace2-EmptyTypes"
        self.ws_id2 = f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name1}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name2}"
        self.table_types2 = []

        self.ws_name3 = "MyWorkspace3-NoTypesKey"
        self.ws_id3 = f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name1}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name3}"

        self.rg_name2 = "Another-RG"
        self.ws_name_other_rg = "WorkspaceInAnotherRG"
        self.ws_id_other_rg = f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name2}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name_other_rg}"
        self.table_types_other_rg = ["Heartbeat"]

        self.sub_id_nonexistent = "00000000-0000-0000-0000-000000000000"
        self.ws_name_nonexistent = "NonExistentWorkspace"

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.sub_id1}",
                "subscriptionId": self.sub_id1,
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-001",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name1}",
                        "name": self.rg_name1,
                        "location": "eastus",
                        "subscription_id": self.sub_id1,
                        "log_analytics_workspaces": [
                            {
                                "id": self.ws_id1, "name": self.ws_name1, "location": "eastus",
                                "resource_group_name": self.rg_name1, "subscription_id": self.sub_id1,
                                "available_table_types": copy.deepcopy(self.table_types1),
                                "customerId": "cust1", "sku": {"name": "PerGB2018"}, "provisioningState": "Succeeded",
                                "tables": []
                            },
                            {
                                "id": self.ws_id2, "name": self.ws_name2, "location": "eastus",
                                "resource_group_name": self.rg_name1, "subscription_id": self.sub_id1,
                                "available_table_types": copy.deepcopy(self.table_types2),
                                "customerId": "cust2", "sku": {"name": "Standalone"}, "provisioningState": "Succeeded",
                                "tables": []
                            },
                            {
                                "id": self.ws_id3, "name": self.ws_name3, "location": "eastus",
                                "resource_group_name": self.rg_name1, "subscription_id": self.sub_id1,
                                "customerId": "cust3", "sku": {"name": "PerGB2018"}, "provisioningState": "Succeeded",
                                "tables": []
                            }
                        ],
                        "app_config_stores": [], "cosmos_db_accounts": [], "key_vaults": [],
                        "monitor_health_models": [], "storage_accounts": []
                    },
                    {
                        "id": f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name2}",
                        "name": self.rg_name2,
                        "location": "westus",
                        "subscription_id": self.sub_id1,
                        "log_analytics_workspaces": [
                            {
                                "id": self.ws_id_other_rg, "name": self.ws_name_other_rg, "location": "westus",
                                "resource_group_name": self.rg_name2, "subscription_id": self.sub_id1,
                                "available_table_types": copy.deepcopy(self.table_types_other_rg),
                                "customerId": "cust4", "sku": {"name": "PerGB2018"}, "provisioningState": "Succeeded",
                                "tables": []
                            }
                        ],
                        "app_config_stores": [], "cosmos_db_accounts": [], "key_vaults": [],
                        "monitor_health_models": [], "storage_accounts": []
                    }
                ],
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Success Cases ---
    def test_list_table_types_success_by_name(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_name1
        )
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, self.table_types1)

    def test_list_table_types_success_by_name_other_rg(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_name_other_rg
        )
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, self.table_types_other_rg)

    def test_list_table_types_success_by_arm_id(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_id1
        )
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, self.table_types1)

    def test_list_table_types_success_by_arm_id_other_rg(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_id_other_rg
        )
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, self.table_types_other_rg)

    def test_list_table_types_success_empty_list(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_name2
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_list_table_types_success_workspace_missing_available_table_types_key(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_name3
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    # --- Error Cases: ResourceNotFoundError ---
    def test_list_table_types_subscription_not_found(self):
        expected_msg = f"Subscription '{self.sub_id_nonexistent}' not found."
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message=expected_msg,
            subscription=self.sub_id_nonexistent,
            workspace=self.ws_name1
        )

    def test_list_table_types_workspace_not_found_by_name(self):
        expected_msg = f"Log Analytics workspace '{self.ws_name_nonexistent}' not found in subscription '{self.sub_id1}'."
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=expected_msg,
            subscription=self.sub_id1,
            workspace=self.ws_name_nonexistent
        )

    def test_list_table_types_workspace_not_found_by_id(self):
        non_existent_ws_id = f"/subscriptions/{self.sub_id1}/resourceGroups/{self.rg_name1}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name_nonexistent}"
        expected_msg = f"Log Analytics workspace '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/Default-RG/providers/Microsoft.OperationalInsights/workspaces/NonExistentWorkspace' not found in subscription '00000000-0000-0000-0000-000000000001'."
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=expected_msg,
            subscription=self.sub_id1,
            workspace=non_existent_ws_id
        )

    def test_list_table_types_workspace_id_subscription_mismatch(self):
        mismatched_sub_id = "mismatched-sub-000000000000"
        ws_id_with_mismatched_sub = f"/subscriptions/{mismatched_sub_id}/resourceGroups/{self.rg_name1}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name1}"
        expected_msg = "Log Analytics workspace '/subscriptions/mismatched-sub-000000000000/resourceGroups/Default-RG/providers/Microsoft.OperationalInsights/workspaces/MyWorkspace1' not found in subscription '00000000-0000-0000-0000-000000000001'."

        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=expected_msg,
            subscription=self.sub_id1,
            workspace=ws_id_with_mismatched_sub
        )

    # --- Error Cases: InvalidInputError / ValidationError / TypeError ---
    def test_list_table_types_typeerror_missing_subscription(self):
        with self.assertRaises(TypeError):
            azmcp_monitor_table_type_list(workspace=self.ws_name1)

    def test_list_table_types_typeerror_missing_workspace(self):
        with self.assertRaises(TypeError):
            azmcp_monitor_table_type_list(subscription=self.sub_id1)

    def test_list_table_types_empty_subscription(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,  # Based on InvalidInputError description
            expected_message="The subscription ID or name cannot be empty.",
            subscription="",
            workspace=self.ws_name1
        )

    def test_list_table_types_empty_workspace(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,  # Based on docstring for missing workspace_name
            expected_message="The Log Analytics workspace ID or name cannot be empty.",
            subscription=self.sub_id1,
            workspace=""
        )

    def test_list_table_types_invalid_retry_max_retries_format(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_retries must be a non-negative integer.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_max_retries="abc"
        )

    def test_list_table_types_invalid_retry_delay_format(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_delay must be a positive number.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_delay="abc"
        )

    def test_list_table_types_invalid_retry_max_delay_format(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_delay must be a positive number.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_max_delay="abc"
        )

    def test_list_table_types_invalid_retry_mode(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid retry_mode. Must be one of: fixed, exponential",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_mode="invalid"
        )

    def test_list_table_types_invalid_retry_network_timeout_format(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_network_timeout must be a positive number.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_network_timeout="abc"
        )

    def test_list_table_types_invalid_auth_method(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid auth_method. Must be one of: credential, key, connectionString",
            subscription=self.sub_id1, workspace=self.ws_name1, auth_method="invalid"
        )

    def test_list_table_types_empty_tenant(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="The tenant ID or name cannot be empty if provided.",
            subscription=self.sub_id1, workspace=self.ws_name1, tenant="   "
        )

    def test_list_table_types_negative_retry_max_retries(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_retries must be a non-negative integer.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_max_retries="-1"
        )

    def test_list_table_types_negative_retry_delay(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_delay must be a positive number.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_delay="-1.0"
        )

    def test_list_table_types_negative_retry_max_delay(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_max_delay must be a positive number.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_max_delay="-1.0"
        )

    def test_list_table_types_negative_retry_network_timeout(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_type_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="retry_network_timeout must be a positive number.",
            subscription=self.sub_id1, workspace=self.ws_name1, retry_network_timeout="-1.0"
        )

    # --- Test with all optional parameters valid ---
    def test_list_table_types_with_all_valid_optional_params(self):
        result = azmcp_monitor_table_type_list(
            subscription=self.sub_id1,
            workspace=self.ws_name1,
            auth_method="credential",
            tenant="tenant-001",
            retry_max_retries="5",
            retry_delay="1.0",
            retry_max_delay="60.5",
            retry_mode="exponential",
            retry_network_timeout="30.0"
        )
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, self.table_types1)


if __name__ == '__main__':
    unittest.main()
