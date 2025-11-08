import unittest
import copy
from ..SimulationEngine import custom_errors
from .. import DB
from .. import azmcp_group_list
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestAzmcpGroupList(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["subscriptions"] = [
            {
                "id": "internal-sub-id-1", 
                "subscriptionId": "00000000-0000-0000-0000-000000000001",
                "displayName": "Subscription One",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [
                    {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1-sub1",
                        "name": "rg1-sub1",
                        "location": "eastus",
                        "managedBy": "externalManager/123",
                        "tags": {"env": "dev", "project": "alpha"},
                        "subscription_id": "00000000-0000-0000-0000-000000000001" # Internal tracking, not part of return schema
                    },
                    {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2-sub1",
                        "name": "rg2-sub1",
                        "location": "westus",
                        "managedBy": None,
                        "tags": None,
                        "subscription_id": "00000000-0000-0000-0000-000000000001"
                    }
                ]
            },
            {
                "id": "internal-sub-id-2",
                "subscriptionId": "00000000-0000-0000-0000-000000000002",
                "displayName": "Subscription Two",
                "state": "Enabled",
                "tenantId": "tenant-guid-1",
                "resource_groups": [] 
            },
            {
                "id": "internal-sub-id-3",
                "subscriptionId": "00000000-0000-0000-0000-000000000003",
                "displayName": "Subscription Three",
                "state": "Enabled",
                "tenantId": "tenant-guid-2",
                "resource_groups": [
                     {
                        "id": "/subscriptions/00000000-0000-0000-0000-000000000003/resourceGroups/rg-minimal",
                        "name": "rg-minimal",
                        "location": "centralus",
                        "managedBy": None,
                        "tags": None,
                        "subscription_id": "00000000-0000-0000-0000-000000000003"
                    }
                ]
            }
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_resource_groups_success_multiple_groups(self):
        sub_id = "00000000-0000-0000-0000-000000000001"
        result = azmcp_group_list(subscription=sub_id)
        
        self.assertIsInstance(result, list)
        
        expected_rg1 = {
            "name": "rg1-sub1",
            "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1-sub1",
            "location": "eastus",
            "managedBy": "externalManager/123",
            "tags": {"env": "dev", "project": "alpha"}
        }
        expected_rg2 = {
            "name": "rg2-sub1",
            "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2-sub1",
            "location": "westus",
            "managedBy": None,
            "tags": None
        }
        
        self.assertCountEqual(result, [expected_rg1, expected_rg2])

    def test_list_resource_groups_success_no_groups(self):
        sub_id = "00000000-0000-0000-0000-000000000002"
        result = azmcp_group_list(subscription=sub_id)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_list_resource_groups_success_minimal_fields(self):
        sub_id = "00000000-0000-0000-0000-000000000003"
        result = azmcp_group_list(subscription=sub_id)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        expected_rg_minimal = {
            "name": "rg-minimal",
            "id": "/subscriptions/00000000-0000-0000-0000-000000000003/resourceGroups/rg-minimal",
            "location": "centralus",
            "managedBy": None,
            "tags": None
        }
        self.assertEqual(result[0], expected_rg_minimal)

    def test_list_resource_groups_with_all_optional_params_success(self):
        sub_id = "00000000-0000-0000-0000-000000000001"
        result = azmcp_group_list(
            subscription=sub_id,
            auth_method="credential",
            tenant="tenant-guid-1",
            retry_max_retries="3",
            retry_delay="5",
            retry_max_delay="60",
            retry_mode="exponential",
            retry_network_timeout="30"
        )
        self.assertIsInstance(result, list)
        
        expected_rg1 = {
            "name": "rg1-sub1",
            "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg1-sub1",
            "location": "eastus",
            "managedBy": "externalManager/123",
            "tags": {"env": "dev", "project": "alpha"}
        }
        expected_rg2 = {
            "name": "rg2-sub1",
            "id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg2-sub1",
            "location": "westus",
            "managedBy": None,
            "tags": None
        }
        self.assertCountEqual(result, [expected_rg1, expected_rg2])


    def test_subscription_not_found_raises_subscriptionnotfounderror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_group_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError,
            expected_message="The specified Azure subscription was not found or is not accessible.",
            subscription="non-existent-sub-id"
        )

    def test_empty_subscription_string_raises_subscriptionnotfounderror(self):
        # Assuming empty string is not caught by Pydantic min_length=1 and leads to not found.
        # If it were a Pydantic validation error, the type would be custom_errors.ValidationError.
        self.assert_error_behavior(
            func_to_call=azmcp_group_list,
            expected_exception_type=custom_errors.SubscriptionNotFoundError, 
            expected_message="The specified Azure subscription was not found or is not accessible.",
            subscription=""
        )

    def test_invalid_subscription_type_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=azmcp_group_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string", 
            subscription=12345 
        )

    def test_retry_mode_invalid_value_raises_validationerror(self):
        # Assuming 'retry_mode' expects specific enum values.
        self.assert_error_behavior(
            func_to_call=azmcp_group_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be 'fixed' or 'exponential'", 
            subscription="00000000-0000-0000-0000-000000000001",
            retry_mode="invalid-mode"
        )

    def test_auth_method_invalid_value_raises_validationerror(self):
        # Assuming 'auth_method' expects specific enum values.
        self.assert_error_behavior(
            func_to_call=azmcp_group_list,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be 'credential', 'key' or 'connectionString'",
            subscription="00000000-0000-0000-0000-000000000001",
            auth_method="sso_token" 
        )

if __name__ == '__main__':
    unittest.main()