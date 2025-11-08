import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..appconfig import azmcp_appconfig_account_list

class TestAzmcpAppconfigAccountList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["subscriptions"] = [
            {
                "id": "/subscriptions/00000000-0000-0000-0000-000000000001",
                "subscriptionId": "00000000-0000-0000-0000-000000000001",
                "displayName": "My Test Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1",
                        "name": "rg1",
                        "location": "eastus",
                        "subscription_id": "00000000-0000-0000-0000-000000000001",
                        "app_config_stores": [
                            {
                                "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-1",
                                "name": "appconfig-store-1",
                                "location": "eastus",
                                "resource_group_name": "rg1",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                "key_values": []
                            },
                            {
                                "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-2",
                                "name": "appconfig-store-2",
                                "location": "westus",
                                "resource_group_name": "rg1",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                "key_values": []
                            }
                        ],
                        "cosmos_db_accounts": [], "key_vaults": [], "kusto_clusters": [],
                        "log_analytics_workspaces": [], "monitor_health_models": [],
                        "postgres_servers": [], "redis_caches": [], "redis_enterprise_clusters": [],
                        "search_services": [], "service_bus_namespaces": [], "storage_accounts": []
                    },
                    {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2",
                        "name": "rg2",
                        "location": "westus",
                        "subscription_id": "00000000-0000-0000-0000-000000000001",
                        "app_config_stores": [
                            {
                                "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-3",
                                "name": "appconfig-store-3",
                                "location": "centralus",
                                "resource_group_name": "rg2",
                                "subscription_id": "00000000-0000-0000-0000-000000000001",
                                "key_values": []
                            }
                        ],
                        "cosmos_db_accounts": [], "key_vaults": [], "kusto_clusters": [],
                        "log_analytics_workspaces": [], "monitor_health_models": [],
                        "postgres_servers": [], "redis_caches": [], "redis_enterprise_clusters": [],
                        "search_services": [], "service_bus_namespaces": [], "storage_accounts": []
                    },
                    {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg3-empty-stores",
                        "name": "rg3-empty-stores",
                        "location": "eastus",
                        "subscription_id": "00000000-0000-0000-0000-000000000001",
                        "app_config_stores": [],
                        "cosmos_db_accounts": [], "key_vaults": [], "kusto_clusters": [],
                        "log_analytics_workspaces": [], "monitor_health_models": [],
                        "postgres_servers": [], "redis_caches": [], "redis_enterprise_clusters": [],
                        "search_services": [], "service_bus_namespaces": [], "storage_accounts": []
                    }
                ]
            },
            {
                "id": "/subscriptions/00000000-0000-0000-0000-000000000002",
                "subscriptionId": "00000000-0000-0000-0000-000000000002",
                "displayName": "My Test Subscription 2 (No Stores)",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg_empty_in_sub2",
                        "name": "rg_empty_in_sub2",
                        "location": "eastus",
                        "subscription_id": "00000000-0000-0000-0000-000000000002",
                        "app_config_stores": [],
                        "cosmos_db_accounts": [], "key_vaults": [], "kusto_clusters": [],
                        "log_analytics_workspaces": [], "monitor_health_models": [],
                        "postgres_servers": [], "redis_caches": [], "redis_enterprise_clusters": [],
                        "search_services": [], "service_bus_namespaces": [], "storage_accounts": []
                    }
                ]
            },
            {
                "id": "/subscriptions/00000000-0000-0000-0000-000000000003",
                "subscriptionId": "00000000-0000-0000-0000-000000000003",
                "displayName": "My Test Subscription 3 (No RGs)",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": []
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_app_config_stores_success_by_id(self):
        subscription_id = "00000000-0000-0000-0000-000000000001"
        result = azmcp_appconfig_account_list(subscription=subscription_id)

        expected = [
            {'name': 'appconfig-store-1', 'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-1', 'location': 'eastus'},
            {'name': 'appconfig-store-2', 'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-2', 'location': 'westus'},
            {'name': 'appconfig-store-3', 'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-3', 'location': 'centralus'}
        ]
        
        # Sort by name for consistent comparison as order is not guaranteed
        self.assertCountEqual(result, expected)
        self.assertEqual(len(result), 3)

    def test_list_app_config_stores_success_by_display_name(self):
        subscription_name = "My Test Subscription 1"
        result = azmcp_appconfig_account_list(subscription=subscription_name)

        expected = [
            {'name': 'appconfig-store-1', 'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-1', 'location': 'eastus'},
            {'name': 'appconfig-store-2', 'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-2', 'location': 'westus'},
            {'name': 'appconfig-store-3', 'id': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2/providers/Microsoft.AppConfiguration/configurationStores/appconfig-store-3', 'location': 'centralus'}
        ]
        self.assertCountEqual(result, expected)
        self.assertEqual(len(result), 3)

    def test_list_app_config_stores_empty_result_no_stores_in_sub(self):
        subscription_id = "00000000-0000-0000-0000-000000000002"
        result = azmcp_appconfig_account_list(subscription=subscription_id)
        self.assertEqual(result, [])

    def test_list_app_config_stores_empty_result_no_rgs_in_sub(self):
        subscription_id = "00000000-0000-0000-0000-000000000003"
        result = azmcp_appconfig_account_list(subscription=subscription_id)
        self.assertEqual(result, [])

    def test_list_app_config_stores_subscription_id_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_account_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'non-existent-sub-id' not found.",
            subscription="non-existent-sub-id"
        )

    def test_list_app_config_stores_subscription_name_not_found(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_account_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="Subscription 'Non Existent Subscription Name' not found.",
            subscription="Non Existent Subscription Name"
        )

    def test_input_validation_missing_subscription_empty_string(self):
        # Assuming empty string for subscription is invalid
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_account_list,
            expected_exception_type=custom_errors.ValidationError,
            # The exact message depends on internal validation logic
            # For Pydantic, it might be "1 validation error for AzmcpAppconfigAccountListArgs\nsubscription\n  String should have at least 1 character"
            # Or a custom message like "Subscription ID or name cannot be empty."
            # Using a substring match for Pydantic-style errors or a more generic message.
            expected_message="Subscription ID or name must be provided.", # Adjust if function has more specific message
            subscription=""
        )
    
    def test_input_validation_missing_subscription_none(self):
        self.assert_error_behavior(
            func_to_call=azmcp_appconfig_account_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Subscription ID or name must be provided.", # Example message
            subscription=None # This will be passed as keyword arg
        )

    def test_list_app_config_stores_with_all_optional_params(self):
        subscription_id = "00000000-0000-0000-0000-000000000001"
        result = azmcp_appconfig_account_list(
            subscription=subscription_id,
            auth_method="credential",
            tenant="tenant-guid-1",
            retry_max_retries="3",
            retry_delay="5",
            retry_max_delay="60",
            retry_mode="exponential",
            retry_network_timeout="100"
        )
        expected_count = 3 # Based on sub1 setup
        self.assertEqual(len(result), expected_count)
        # Basic check that one of the expected items is present
        expected_item_names = {"appconfig-store-1", "appconfig-store-2", "appconfig-store-3"}
        returned_item_names = {item['name'] for item in result}
        self.assertEqual(expected_item_names, returned_item_names)

    def test_list_app_config_stores_subscription_with_mixed_rgs(self):
        # This is implicitly tested by test_list_app_config_stores_success_by_id,
        # as sub1 has RGs with stores and RGs without stores (rg3-empty-stores).
        # Re-asserting for clarity.
        subscription_id = "00000000-0000-0000-0000-000000000001"
        result = azmcp_appconfig_account_list(subscription=subscription_id)
        
        self.assertEqual(len(result), 3)
        store_names = {store['name'] for store in result}
        self.assertIn('appconfig-store-1', store_names)
        self.assertIn('appconfig-store-2', store_names)
        self.assertIn('appconfig-store-3', store_names)

if __name__ == '__main__':
    unittest.main()