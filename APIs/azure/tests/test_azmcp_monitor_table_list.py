import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..loganalytics import azmcp_monitor_table_list
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestAzmcpMonitorTableList(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Common setup
        self.sub_id = "test-sub-1"
        self.rg_name = "test-rg-1"
        self.ws_name = "test-ws-1"
        self.ws_empty_name = "test-ws-empty"
        self.ws_no_displayname_table_name = "test-ws-no-displayname"

        self.table1_name = "CustomTable1_CL"
        self.table1_id = f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name}/tables/{self.table1_name}"
        self.table1_schema_cols = [{"name": "TimeGenerated", "type": "datetime"}, {"name": "CustomField_s", "type": "string"}]

        self.table2_name = "AzureMetrics"
        self.table2_id = f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name}/tables/{self.table2_name}"
        self.table2_schema_cols = [{"name": "Timestamp", "type": "datetime"}, {"name": "MetricName", "type": "string"}, {"name": "Value", "type": "real"}]

        self.table3_name = "Perf"
        self.table3_id = f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name}/tables/{self.table3_name}"
        self.table3_schema_cols = [{"name": "CounterName", "type": "string"}, {"name": "InstanceName", "type": "string"}]
        
        self.table4_name_no_display = "TableNoDisplayName_CL"
        self.table4_id_no_display = f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_no_displayname_table_name}/tables/{self.table4_name_no_display}"
        self.table4_schema_cols_no_display = [{"name": "FieldA", "type": "string"}]


        DB["subscriptions"] = [
            {
                "id": "sub-guid-1",
                "subscriptionId": self.sub_id,
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}",
                        "name": self.rg_name,
                        "location": "eastus",
                        "subscription_id": self.sub_id,
                        "log_analytics_workspaces": [
                            {
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_name}",
                                "name": self.ws_name,
                                "location": "eastus",
                                "resource_group_name": self.rg_name,
                                "subscription_id": self.sub_id,
                                "available_table_types": ["CustomLog", "AzureMetrics", "Perf", "SecurityAlert"],
                                "tables": [
                                    {
                                        "id": self.table1_id,
                                        "name": self.table1_name,
                                        "timespan": "P90D",
                                        "workspace_name": self.ws_name,
                                        "schema_details": {
                                            "name": self.table1_name,
                                            "displayName": "Custom Table 1 Display Name",
                                            "columns": copy.deepcopy(self.table1_schema_cols)
                                        }
                                    },
                                    {
                                        "id": self.table2_id,
                                        "name": self.table2_name,
                                        "timespan": "P30D",
                                        "workspace_name": self.ws_name,
                                        "schema_details": {
                                            "name": self.table2_name,
                                            "displayName": "Azure Metrics Table",
                                            "columns": copy.deepcopy(self.table2_schema_cols)
                                        }
                                    },
                                    {
                                        "id": self.table3_id,
                                        "name": self.table3_name,
                                        "timespan": "P7D",
                                        "workspace_name": self.ws_name,
                                        "schema_details": {
                                            "name": self.table3_name,
                                            "displayName": "Performance Data",
                                            "columns": copy.deepcopy(self.table3_schema_cols)
                                        }
                                    }
                                ]
                            },
                            {
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_empty_name}",
                                "name": self.ws_empty_name,
                                "location": "eastus",
                                "resource_group_name": self.rg_name,
                                "subscription_id": self.sub_id,
                                "available_table_types": ["CustomLog"],
                                "tables": []
                            },
                            { 
                                "id": f"/subscriptions/{self.sub_id}/resourceGroups/{self.rg_name}/providers/Microsoft.OperationalInsights/workspaces/{self.ws_no_displayname_table_name}",
                                "name": self.ws_no_displayname_table_name,
                                "location": "eastus",
                                "resource_group_name": self.rg_name,
                                "subscription_id": self.sub_id,
                                "available_table_types": ["CustomLog"],
                                "tables": [
                                    {
                                        "id": self.table4_id_no_display,
                                        "name": self.table4_name_no_display,
                                        "timespan": "P180D",
                                        "workspace_name": self.ws_no_displayname_table_name,
                                        "schema_details": {
                                            "name": self.table4_name_no_display,
                                            "displayName": None, 
                                            "columns": copy.deepcopy(self.table4_schema_cols_no_display)
                                        }
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

    def test_list_tables_success_custom_log(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="CustomLog"
        )
        self.assertEqual(len(result), 1)
        table = result[0]
        self.assertEqual(table["name"], self.table1_name)
        self.assertEqual(table["id"], self.table1_id)
        self.assertEqual(table["timespan"], "P90D")
        self.assertEqual(table["schema"]["name"], self.table1_name)
        self.assertEqual(table["schema"]["displayName"], "Custom Table 1 Display Name")
        self.assertEqual(table["schema"]["columns"], self.table1_schema_cols)

    def test_list_tables_success_azure_metrics(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="AzureMetrics"
        )
        self.assertEqual(len(result), 1)
        table = result[0]
        self.assertEqual(table["name"], self.table2_name)
        self.assertEqual(table["id"], self.table2_id)
        self.assertEqual(table["timespan"], "P30D")
        self.assertEqual(table["schema"]["name"], self.table2_name)
        self.assertEqual(table["schema"]["displayName"], "Azure Metrics Table")
        self.assertEqual(table["schema"]["columns"], self.table2_schema_cols)

    def test_list_tables_success_perf(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="Perf"
        )
        self.assertEqual(len(result), 1)
        table = result[0]
        self.assertEqual(table["name"], self.table3_name)
        self.assertEqual(table["id"], self.table3_id)
        self.assertEqual(table["timespan"], "P7D")
        self.assertEqual(table["schema"]["name"], self.table3_name)
        self.assertEqual(table["schema"]["displayName"], "Performance Data")
        self.assertEqual(table["schema"]["columns"], self.table3_schema_cols)
        
    def test_list_tables_unknown_type_returns_empty(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="SecurityAlert" 
        )
        self.assertEqual(len(result), 0)

    def test_list_tables_empty_workspace(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_empty_name,
            table_type="CustomLog"
        )
        self.assertEqual(len(result), 0)

    def test_list_tables_schema_displayName_is_none_in_db(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_no_displayname_table_name,
            table_type="CustomLog"
        )
        self.assertEqual(len(result), 1)
        table = result[0]
        self.assertEqual(table["name"], self.table4_name_no_display)
        self.assertEqual(table["id"], self.table4_id_no_display)
        self.assertEqual(table["schema"]["name"], self.table4_name_no_display)
        self.assertEqual(table["schema"]["displayName"], self.table4_name_no_display)
        self.assertEqual(table["schema"]["columns"], self.table4_schema_cols_no_display)

    def test_list_tables_table_schema_no_columns(self):
        ws_ref = DB["subscriptions"][0]["resource_groups"][0]["log_analytics_workspaces"][0]
        original_table_cols = ws_ref["tables"][0]["schema_details"]["columns"]
        ws_ref["tables"][0]["schema_details"]["columns"] = []

        try:
            result = azmcp_monitor_table_list(
                subscription=self.sub_id,
                resource_group=self.rg_name,
                workspace=self.ws_name,
                table_type="CustomLog"
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["schema"]["columns"], [])
        finally:
            ws_ref["tables"][0]["schema_details"]["columns"] = original_table_cols

    def test_list_tables_with_all_optional_params(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="AzureMetrics",
            auth_method="credential",
            retry_delay="5",
            retry_max_delay="60",
            retry_max_retries="3",
            retry_mode="exponential",
            retry_network_timeout="100",
            tenant="test-tenant-id"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], self.table2_name)

    def test_error_subscription_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Subscription 'non-existent-sub' not found.",
            subscription="non-existent-sub",
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="CustomLog"
        )

    def test_error_resource_group_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Resource group 'non-existent-rg' not found in subscription '{self.sub_id}'.",
            subscription=self.sub_id,
            resource_group="non-existent-rg",
            workspace=self.ws_name,
            table_type="CustomLog"
        )

    def test_error_workspace_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Log Analytics workspace 'non-existent-ws' not found in resource group '{self.rg_name}' for subscription '{self.sub_id}'.",
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace="non-existent-ws",
            table_type="CustomLog"
        )
    
    def test_error_missing_subscription(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'subscription' is required and cannot be empty.",
            subscription="", 
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="CustomLog"
        )

    def test_error_missing_resource_group(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'resource_group' is required and cannot be empty.",
            subscription=self.sub_id,
            resource_group="",
            workspace=self.ws_name,
            table_type="CustomLog"
        )

    def test_error_missing_workspace(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'workspace' is required and cannot be empty.",
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace="",
            table_type="CustomLog"
        )

    def test_error_missing_table_type(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_table_list,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'table_type' is required and cannot be empty.",
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type=""
        )
        
    def test_table_type_case_sensitive_matching(self):
        result = azmcp_monitor_table_list(
            subscription=self.sub_id,
            resource_group=self.rg_name,
            workspace=self.ws_name,
            table_type="customlog" 
        )
        self.assertEqual(len(result), 0) 

    def test_workspace_exists_but_tables_list_is_none_in_db(self):
        ws_ref = DB["subscriptions"][0]["resource_groups"][0]["log_analytics_workspaces"][0]
        original_tables = ws_ref.get("tables")
        ws_ref["tables"] = None 

        try:
            result = azmcp_monitor_table_list(
                subscription=self.sub_id,
                resource_group=self.rg_name,
                workspace=self.ws_name,
                table_type="CustomLog"
            )
            self.assertEqual(len(result), 0) 
        finally:
            ws_ref["tables"] = original_tables
            
    def test_table_schema_details_is_none_in_db(self):
        ws_ref = DB["subscriptions"][0]["resource_groups"][0]["log_analytics_workspaces"][0]
        original_schema_details = ws_ref["tables"][0].get("schema_details")
        ws_ref["tables"][0]["schema_details"] = None

        try:
            result = azmcp_monitor_table_list(
                subscription=self.sub_id,
                resource_group=self.rg_name,
                workspace=self.ws_name,
                table_type="CustomLog" 
            )
            self.assertEqual(len(result), 1)
            table = result[0]
            self.assertEqual(table["name"], self.table1_name)
            self.assertEqual(table["schema"]["name"], self.table1_name)
            self.assertEqual(table["schema"]["displayName"], self.table1_name) 
            self.assertEqual(table["schema"]["columns"], []) 
        finally:
            ws_ref["tables"][0]["schema_details"] = original_schema_details

    def test_table_schema_details_columns_is_none_in_db(self):
        ws_ref = DB["subscriptions"][0]["resource_groups"][0]["log_analytics_workspaces"][0]
        original_columns = ws_ref["tables"][0]["schema_details"].get("columns")
        ws_ref["tables"][0]["schema_details"]["columns"] = None

        try:
            result = azmcp_monitor_table_list(
                subscription=self.sub_id,
                resource_group=self.rg_name,
                workspace=self.ws_name,
                table_type="CustomLog" 
            )
            self.assertEqual(len(result), 1)
            table = result[0]
            self.assertEqual(table["name"], self.table1_name)
            self.assertEqual(table["schema"]["name"], self.table1_name)
            self.assertEqual(table["schema"]["displayName"], "Custom Table 1 Display Name")
            self.assertEqual(table["schema"]["columns"], []) 
        finally:
            ws_ref["tables"][0]["schema_details"]["columns"] = original_columns

    def test_list_tables_skips_entries_with_missing_name(self):
        ws_ref = DB["subscriptions"][0]["resource_groups"][0]["log_analytics_workspaces"][0]
        original_tables = copy.deepcopy(ws_ref["tables"])
        try:
            ws_ref["tables"].append({
                "id": "/subscriptions/x/resourceGroups/y/providers/Microsoft.OperationalInsights/workspaces/w/tables/malformed",
                # name missing intentionally
                "timespan": "P1D",
                "workspace_name": self.ws_name,
                "schema_details": {"name": "malformed", "displayName": "malformed", "columns": []}
            })
            result = azmcp_monitor_table_list(
                subscription=self.sub_id,
                resource_group=self.rg_name,
                workspace=self.ws_name,
                table_type="malformed"
            )
            self.assertEqual(len(result), 0)
        finally:
            ws_ref["tables"] = original_tables

if __name__ == '__main__':
    unittest.main()