import unittest
import copy
from datetime import datetime, timezone

from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..edge import list_edge_functions
from ..SimulationEngine import custom_errors

class TestListEdgeFunctions(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.org_id_1 = "org_044f182b_3420_4f40_90a7_3c598d054358"
        self.org_id_no_feature = "org_10f86939_5214_4a71_8810_9f8887a099f8"
        self.org_id_no_plan_features_list = "org_2a1c3b8e_1234_5678_abcd_ef1234567890"
        self.org_id_no_subscription_plan_field = "org_3b2d4c9f_4321_8765_dcba_fe0987654321"
        self.org_id_no_subscription_plan_object = "org_4c3e5d0a_5432_9876_cdef_ab1234567890"


        self.project_id_1 = "proj_7a8b1c2d_e3f4_5g6h_7i8j_9k0l1m2n3o4p" # Has functions
        self.project_id_2 = "proj_b2c3d4e5_f6g7_h8i9_j0k1_l2m3n4o5p6q7" # No functions defined for it
        self.project_id_3 = "proj_c3d4e5f6_g7h8_i9j0_k1l2_m3n4o5p6q7r8" # Org has no edge_functions feature
        self.project_id_4 = "proj_d4e5f6g7_h8i9_j0k1_l2m3_n4o5p6q7r8s9" # No entry in DB['edge_functions']
        self.project_id_5 = "proj_e5f6g7h8_i9j0_k1l2_m3n4_o5p6q7r8s9t0" # Entry in DB['edge_functions'] is None
        self.project_id_org_no_plan_features = "proj_f6g7h8i9_j0k1_l2m3_n4o5_p6q7r8s9t0u1"
        self.project_id_org_no_plan_field = "proj_g7h8i9j0_k1l2_m3n4_o5p6_q7r8s9t0u1v2"
        self.project_id_org_no_plan_object = "proj_h8i9j0k1_l2m3_n4o5_p6q7_r8s9t0u1v2w3"


        DB["organizations"] = [
            {
                "id": self.org_id_1, "name": "Org One",
                "created_at": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                "subscription_plan": {
                    "id": "plan_pro", "name": "Pro Plan", "price": 25, "currency": "USD",
                    "features": ["edge_functions_enabled", "another_feature"]
                }
            },
            {
                "id": self.org_id_no_feature, "name": "Org No Edge Feature",
                "created_at": datetime(2023, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                "subscription_plan": {
                    "id": "plan_free", "name": "Free Plan", "price": 0, "currency": "USD",
                    "features": ["some_other_feature"]
                }
            },
            {
                "id": self.org_id_no_plan_features_list, "name": "Org No Plan Features List",
                "created_at": datetime(2023, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                "subscription_plan": {
                    "id": "plan_custom_empty", "name": "Custom Empty Features", "price": 0, "currency": "USD",
                    "features": []
                }
            },
            {
                "id": self.org_id_no_subscription_plan_field, "name": "Org No Subscription Plan Field",
                "created_at": datetime(2023, 1, 4, 10, 0, 0, tzinfo=timezone.utc),
                "subscription_plan": {
                    "id": "plan_custom_no_features_attr", "name": "Custom No Features Attr", "price": 0, "currency": "USD"
                    # 'features' attribute missing from subscription_plan
                }
            },
            {
                "id": self.org_id_no_subscription_plan_object, "name": "Org No Subscription Plan Object",
                "created_at": datetime(2023, 1, 5, 10, 0, 0, tzinfo=timezone.utc)
                # 'subscription_plan' attribute missing from organization
            }
        ]

        DB["projects"] = [
            {
                "id": self.project_id_1, 
                "name": "Project Alpha", 
                "organization_id": self.org_id_1, 
                "region": "us-east-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 10, tzinfo=timezone.utc),
                "plan": "pro",
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_2, 
                "name": "Project Beta", 
                "organization_id": self.org_id_1, 
                "region": "us-west-2", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 11, tzinfo=timezone.utc),
                "plan": "pro",
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_3, 
                "name": "Project Gamma", 
                "organization_id": self.org_id_no_feature, 
                "region": "eu-central-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 12, tzinfo=timezone.utc),
                "plan": "pro",
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_4, 
                "name": "Project Delta", 
                "organization_id": self.org_id_1, 
                "region": "ap-southeast-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 13, tzinfo=timezone.utc),
                "plan": "pro",
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_5, 
                "name": "Project Epsilon", 
                "organization_id": self.org_id_1, 
                "region": "sa-east-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 14, tzinfo=timezone.utc),
                "plan": "pro",
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_org_no_plan_features, 
                "name": "Project Zeta", 
                "organization_id": self.org_id_no_plan_features_list, 
                "region": "us-east-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc),
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_org_no_plan_field, 
                "name": "Project Eta", 
                "organization_id": self.org_id_no_subscription_plan_field, 
                "region": "us-east-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 16, tzinfo=timezone.utc),
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
            {
                "id": self.project_id_org_no_plan_object, 
                "name": "Project Theta", 
                "organization_id": self.org_id_no_subscription_plan_object, 
                "region": "us-east-1", 
                "status": "ACTIVE_HEALTHY", 
                "created_at": datetime(2023, 1, 17, tzinfo=timezone.utc),
                "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
                "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
            },
        ]

        self.func1_created_at = datetime(2023, 2, 1, 10, 30, 0, tzinfo=timezone.utc)
        self.func1_updated_at = datetime(2023, 2, 15, 11, 45, 0, tzinfo=timezone.utc)
        self.func2_created_at = datetime(2023, 3, 1, 12, 15, 0, tzinfo=timezone.utc)
        self.func2_updated_at = datetime(2023, 3, 10, 13, 5, 0, tzinfo=timezone.utc)

        DB["edge_functions"] = {
            self.project_id_1: [
                {
                    "id": "func_id_1", "slug": "my-first-function", "name": "My First Function",
                    "version": "v1.0.1", "status": "ACTIVE_HEALTHY",
                    "created_at": self.func1_created_at, "updated_at": self.func1_updated_at
                },
                {
                    "id": "func_id_2", "slug": "data-processor", "name": "Data Processor",
                    "version": "v0.2.0", "status": "BUILDING",
                    "created_at": self.func2_created_at, "updated_at": self.func2_updated_at
                }
            ],
            # self.project_id_2 has an entry in DB["edge_functions"] but it's an empty list
            self.project_id_2: [],
            # self.project_id_4: no entry in DB["edge_functions"] for this project
            self.project_id_5: None, # Entry for this project_id is explicitly None
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_edge_functions_success_multiple_functions(self):
        functions = list_edge_functions(project_id=self.project_id_1)
        self.assertEqual(len(functions), 2)

        expected_func1 = {
            "id": "func_id_1", "slug": "my-first-function", "name": "My First Function",
            "version": "v1.0.1", "status": "ACTIVE_HEALTHY",
            "created_at": self.func1_created_at.isoformat(),
            "updated_at": self.func1_updated_at.isoformat()
        }
        expected_func2 = {
            "id": "func_id_2", "slug": "data-processor", "name": "Data Processor",
            "version": "v0.2.0", "status": "BUILDING",
            "created_at": self.func2_created_at.isoformat(),
            "updated_at": self.func2_updated_at.isoformat()
        }
        self.assertIn(expected_func1, functions)
        self.assertIn(expected_func2, functions)

    def test_list_edge_functions_success_no_functions_defined(self):
        functions = list_edge_functions(project_id=self.project_id_2)
        self.assertEqual(len(functions), 0)
        self.assertIsInstance(functions, list)

    def test_list_edge_functions_project_not_found(self):
        self.assert_error_behavior(
            func_to_call=list_edge_functions,
            project_id="non_existent_project_id",
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Project with ID non_existent_project_id not found."
        )

    def test_list_edge_functions_project_exists_but_no_edge_functions_key_in_db(self):
        functions = list_edge_functions(project_id=self.project_id_4)
        self.assertEqual(len(functions), 0)
        self.assertIsInstance(functions, list)

    def test_list_edge_functions_project_edge_functions_entry_is_none(self):
        functions = list_edge_functions(project_id=self.project_id_5)
        self.assertEqual(len(functions), 0)
        self.assertIsInstance(functions, list)

    def test_list_edge_functions_invalid_project_id_empty_string(self):
        # Assuming empty string project_id is considered invalid by the function's validation
        self.assert_error_behavior(
            func_to_call=list_edge_functions,
            project_id="",
            expected_exception_type=custom_errors.ValidationError, # Using custom_errors.ValidationError
            expected_message="Project ID cannot be empty." # Example message
        )

    def test_list_edge_functions_invalid_project_id_type_integer(self):
        # Assuming non-string project_id is caught by validation
        self.assert_error_behavior(
            func_to_call=list_edge_functions,
            project_id=12345,
            expected_exception_type=custom_errors.ValidationError, # Using custom_errors.ValidationError
            expected_message="Project ID must be a string." # Example message
        )

    def test_list_edge_functions_invalid_project_id_type_none(self):
        self.assert_error_behavior(
            func_to_call=list_edge_functions,
            project_id=None,
            expected_exception_type=custom_errors.ValidationError, # Using custom_errors.ValidationError
            expected_message="Project ID must be a string." # Example message, or "Project ID cannot be null."
        )

if __name__ == '__main__':
    unittest.main()