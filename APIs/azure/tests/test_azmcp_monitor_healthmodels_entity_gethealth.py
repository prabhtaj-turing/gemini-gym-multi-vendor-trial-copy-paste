import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..monitor import azmcp_monitor_healthmodels_entity_gethealth
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestAzmcpMonitorHealthmodelsEntityGethealth(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self._setup_db_data()

    def _setup_db_data(self):
        self.sub_id_1 = "00000000-0000-0000-0000-000000000001"
        self.rg_name_1 = "rg-test-1"
        self.model_name_1 = "health-model-A"
        self.entity_id_healthy = "vm-01"
        self.entity_id_unhealthy = "vm-02"
        self.entity_id_warning = "vm-03"
        self.entity_id_no_causes = "vm-04" 

        DB["subscriptions"] = [
            {
                "id": f"/subscriptions/{self.sub_id_1}", 
                "subscriptionId": self.sub_id_1, 
                "displayName": "Test Subscription 1",
                "state": "Enabled",
                "tenantId": "tenant-id-1",
                "resource_groups": [
                    {
                        "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/{self.rg_name_1}",
                        "name": self.rg_name_1,
                        "location": "eastus",
                        "subscription_id": self.sub_id_1, 
                        "monitor_health_models": [
                            {
                                "name": self.model_name_1,
                                "resource_group_name": self.rg_name_1, 
                                "subscription_id": self.sub_id_1, 
                                "entities": [
                                    {
                                        "entityId": self.entity_id_healthy,
                                        "healthState": "Healthy",
                                        "causes": []
                                    },
                                    {
                                        "entityId": self.entity_id_unhealthy,
                                        "healthState": "Unhealthy",
                                        "causes": [
                                            {
                                                "description": "CPU saturation",
                                                "severity": "Critical",
                                                "recommendedActions": ["Scale up compute", "Optimize workload"]
                                            },
                                            {
                                                "description": "Memory pressure",
                                                "severity": "Error",
                                                "recommendedActions": ["Increase RAM", "Check for memory leaks"]
                                            }
                                        ]
                                    },
                                    {
                                        "entityId": self.entity_id_warning,
                                        "healthState": "Warning",
                                        "causes": [
                                            {
                                                "description": "Disk nearing capacity",
                                                "severity": "Warning",
                                                "recommendedActions": ["Archive old data", "Expand disk"]
                                            }
                                        ]
                                    },
                                    {
                                        "entityId": self.entity_id_no_causes,
                                        "healthState": "Healthy",
                                        "causes": [] 
                                    }
                                ]
                            },
                            { 
                                "name": "health-model-B", 
                                "resource_group_name": self.rg_name_1,
                                "subscription_id": self.sub_id_1,
                                "entities": [
                                    {
                                        "entityId": "app-service-01",
                                        "healthState": "Healthy",
                                        "causes": []
                                    }
                                ]
                            }
                        ]
                    },
                    { 
                        "id": f"/subscriptions/{self.sub_id_1}/resourceGroups/rg-other",
                        "name": "rg-other", 
                        "location": "westus",
                        "subscription_id": self.sub_id_1,
                        "monitor_health_models": []
                    }
                ]
            },
            { 
                "id": "/subscriptions/00000000-0000-0000-0000-000000000002",
                "subscriptionId": "00000000-0000-0000-0000-000000000002", 
                "displayName": "Test Subscription 2",
                "state": "Enabled",
                "tenantId": "tenant-id-2",
                "resource_groups": []
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Success Cases ---
    def test_get_healthy_entity_success(self):
        result = azmcp_monitor_healthmodels_entity_gethealth(
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["entityId"], self.entity_id_healthy)
        self.assertEqual(result["healthState"], "Healthy")
        self.assertEqual(result["causes"], [])

    def test_get_unhealthy_entity_with_multiple_causes_success(self):
        result = azmcp_monitor_healthmodels_entity_gethealth(
            entity=self.entity_id_unhealthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )
        self.assertEqual(result["entityId"], self.entity_id_unhealthy)
        self.assertEqual(result["healthState"], "Unhealthy")
        self.assertEqual(len(result["causes"]), 2)
        self.assertEqual(result["causes"][0]["description"], "CPU saturation")
        self.assertEqual(result["causes"][0]["severity"], "Critical")
        self.assertEqual(result["causes"][0]["recommendedActions"], ["Scale up compute", "Optimize workload"])
        self.assertEqual(result["causes"][1]["description"], "Memory pressure")
        self.assertEqual(result["causes"][1]["severity"], "Error")
        self.assertEqual(result["causes"][1]["recommendedActions"], ["Increase RAM", "Check for memory leaks"])

    def test_get_warning_entity_with_single_cause_success(self):
        result = azmcp_monitor_healthmodels_entity_gethealth(
            entity=self.entity_id_warning,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )
        self.assertEqual(result["entityId"], self.entity_id_warning)
        self.assertEqual(result["healthState"], "Warning")
        self.assertEqual(len(result["causes"]), 1)
        self.assertEqual(result["causes"][0]["description"], "Disk nearing capacity")
        self.assertEqual(result["causes"][0]["severity"], "Warning")
        self.assertEqual(result["causes"][0]["recommendedActions"], ["Archive old data", "Expand disk"])

    def test_get_entity_with_no_causes_explicitly_success(self):
        result = azmcp_monitor_healthmodels_entity_gethealth(
            entity=self.entity_id_no_causes,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )
        self.assertEqual(result["entityId"], self.entity_id_no_causes)
        self.assertEqual(result["healthState"], "Healthy")
        self.assertEqual(result["causes"], [])

    def test_get_entity_with_all_optional_params_success(self):
        result = azmcp_monitor_healthmodels_entity_gethealth(
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1,
            auth_method='credential',
            retry_delay='5',
            retry_max_delay='60',
            retry_max_retries='3',
            retry_mode='exponential',
            retry_network_timeout='30',
            tenant='tenant-id-1'
        )
        self.assertEqual(result["entityId"], self.entity_id_healthy)

    # --- Resource Not Found Error Cases ---
    def test_get_entity_subscription_not_found_raises_resource_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="The specified Azure resource was not found.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription="non-existent-sub"
        )

    def test_get_entity_resource_group_not_found_raises_resource_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="The specified Azure resource was not found.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group="non-existent-rg",
            subscription=self.sub_id_1
        )

    def test_get_entity_model_not_found_raises_resource_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="The specified Azure resource was not found.",
            entity=self.entity_id_healthy,
            model_name="non-existent-model",
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )

    def test_get_entity_entity_not_found_in_model_raises_resource_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="The specified Azure resource was not found.",
            entity="non-existent-entity",
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )
    
    # --- Invalid Input Error Cases ---
    def test_get_entity_empty_entity_id_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'entity' cannot be empty.",
            entity="", 
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )

    def test_get_entity_empty_model_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'model_name' cannot be empty.",
            entity=self.entity_id_healthy,
            model_name="", 
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1
        )

    def test_get_entity_empty_resource_group_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'resource_group' cannot be empty.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group="", 
            subscription=self.sub_id_1
        )

    def test_get_entity_empty_subscription_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Required parameter 'subscription' cannot be empty.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription="" 
        )

    def test_get_entity_invalid_auth_method_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid 'auth_method': 'invalid_auth'. Allowed values are 'credential', 'key', 'connectionString'.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1,
            auth_method="invalid_auth" 
        )

    def test_get_entity_invalid_retry_mode_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Invalid 'retry_mode': 'invalid_mode'. Allowed values are 'fixed', 'exponential'.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1,
            retry_mode="invalid_mode"
        )

    def test_get_entity_invalid_retry_delay_format_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'retry_delay' ('not_a_number') must be a string representing a non-negative integer.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1,
            retry_delay="not_a_number"
        )
    
    def test_get_entity_invalid_retry_max_retries_format_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'retry_max_retries' ('not_an_int') must be a string representing a non-negative integer.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1,
            retry_max_retries="not_an_int"
        )

    def test_get_entity_invalid_retry_network_timeout_format_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=azmcp_monitor_healthmodels_entity_gethealth,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parameter 'retry_network_timeout' ('thirty') must be a string representing a non-negative integer.",
            entity=self.entity_id_healthy,
            model_name=self.model_name_1,
            resource_group=self.rg_name_1,
            subscription=self.sub_id_1,
            retry_network_timeout="thirty" 
        )

if __name__ == '__main__':
    unittest.main()