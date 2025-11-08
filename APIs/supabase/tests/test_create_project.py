import unittest
import copy
from datetime import datetime, timezone

# CRITICAL IMPORT FOR CUSTOM ERRORS
from ..SimulationEngine import custom_errors
from ..project import create_project
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError

class TestCreateProject(BaseTestCaseWithErrorHandler):

    VALID_REGIONS = [
        "us-west-1", "us-east-1", "us-east-2", "ca-central-1",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-central-2",
        "eu-north-1", "ap-south-1", "ap-southeast-1", "ap-northeast-1",
        "ap-northeast-2", "ap-southeast-2", "sa-east-1"
    ]
    
    EXPECTED_INITIAL_STATUSES = ["CREATING", "INITIALIZING"]

    def _is_iso_timestamp(self, timestamp_str: str) -> bool:
        if not isinstance(timestamp_str, str):
            return False
        try:
            # Attempt to parse, handling 'Z' for UTC if present
            dt_obj = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "organizations": [],
            "projects": [],
            "tables": {},
            "extensions": {},
            "migrations": {},
            "edge_functions": {},
            "branches": {},
            "costs": {},
            "unconfirmed_costs": {},
            "project_urls": {},
            "project_anon_keys": {},
            "project_ts_types": {},
            "logs": {}
        })

        DB['organizations'].append({
            'id': 'org_123', 
            'name': 'Test Org 1', 
            'created_at': datetime.now(timezone.utc), 
            'plan': 'free',
            'opt_in_tags': ['AI_SQL_GENERATOR_OPT_IN', 'AI_DATA_GENERATOR_OPT_IN', 'AI_LOG_GENERATOR_OPT_IN'],
            'allowed_release_channels': ['internal', 'alpha', 'beta', 'ga', 'withdrawn', 'preview']
        })
        DB['organizations'].append({
            'id': 'org_456', 
            'name': 'Test Org 2', 
            'created_at': datetime.now(timezone.utc),
            'plan': 'pro',
            'opt_in_tags': ['AI_SQL_GENERATOR_OPT_IN', 'AI_DATA_GENERATOR_OPT_IN', 'AI_LOG_GENERATOR_OPT_IN'],
            'allowed_release_channels': ['internal', 'alpha', 'beta', 'ga', 'withdrawn', 'preview']
        })

        DB['costs']['cost_project_valid_general'] = {
            'type': 'project', 'amount': 10.0, 'currency': 'USD', 
            'recurrence': 'monthly', 'description': 'Valid project cost confirmation for general use',
            'confirmation_id': 'cost_project_valid_general'
        }
        DB['costs']['cost_branch_mismatch'] = {
            'type': 'branch', 'amount': 5.0, 'currency': 'USD', 
            'recurrence': 'monthly', 'description': 'Valid branch cost, but wrong type for project',
            'confirmation_id': 'cost_branch_mismatch'
        }
        DB['costs']['cost_to_be_consumed_default'] = {
            'type': 'project', 'amount': 10.0, 'currency': 'USD', 
            'recurrence': 'monthly', 'description': 'Cost for default region test',
            'confirmation_id': 'cost_to_be_consumed_default'
        }
        DB['costs']['cost_to_be_consumed_specific'] = {
            'type': 'project', 'amount': 10.0, 'currency': 'USD', 
            'recurrence': 'monthly', 'description': 'Cost for specific region test',
            'confirmation_id': 'cost_to_be_consumed_specific'
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_create_project_success_default_region(self):
        project_name = "My Test Project Default Region"
        org_id = "org_123"
        cost_id = "cost_to_be_consumed_default"

        response = create_project(
            name=project_name,
            organization_id=org_id,
            confirm_cost_id=cost_id
        )

        self.assertIsInstance(response, dict)
        self.assertIn("id", response)
        self.assertIsInstance(response["id"], str)
        self.assertTrue(len(response["id"]) > 0, "Project ID should not be empty")
        project_id = response["id"]

        self.assertEqual(response["name"], project_name)
        self.assertEqual(response["organization_id"], org_id)
        self.assertIn("region", response)
        self.assertIsInstance(response["region"], str)
        self.assertIn(response["region"], self.VALID_REGIONS, "Default region must be a valid region")
        
        self.assertIn("status", response)
        self.assertIn(response["status"], self.EXPECTED_INITIAL_STATUSES)
        
        self.assertIn("created_at", response)
        self.assertTrue(self._is_iso_timestamp(response["created_at"]), "created_at is not a valid ISO timestamp")

        self.assertEqual(len(DB["projects"]), 1)
        db_project = DB["projects"][0]
        self.assertEqual(db_project["id"], project_id)
        self.assertEqual(db_project["name"], project_name)
        self.assertEqual(db_project["organization_id"], org_id)
        self.assertEqual(db_project["region"], response["region"])
        self.assertIn(db_project["status"], self.EXPECTED_INITIAL_STATUSES)
        self.assertIsInstance(db_project["created_at"], str)
        self.assertTrue(self._is_iso_timestamp(db_project["created_at"]), "DB created_at is not a valid ISO timestamp")

        self.assertNotIn(cost_id, DB["costs"], "Cost ID should be consumed")

    def test_create_project_success_specific_region(self):
        project_name = "My Test Project Specific Region"
        org_id = "org_456"
        cost_id = "cost_to_be_consumed_specific"
        specific_region = "eu-west-2"

        response = create_project(
            name=project_name,
            organization_id=org_id,
            confirm_cost_id=cost_id,
            region=specific_region
        )

        self.assertIsInstance(response, dict)
        self.assertEqual(response["name"], project_name)
        self.assertEqual(response["organization_id"], org_id)
        self.assertEqual(response["region"], specific_region)
        self.assertIn(response["status"], self.EXPECTED_INITIAL_STATUSES)
        self.assertTrue(self._is_iso_timestamp(response["created_at"]))
        
        project_id = response["id"]
        self.assertTrue(len(project_id) > 0)

        self.assertEqual(len(DB["projects"]), 1)
        db_project = DB["projects"][0]
        self.assertEqual(db_project["id"], project_id)
        self.assertEqual(db_project["region"], specific_region)

        self.assertNotIn(cost_id, DB["costs"])

    def test_create_project_success_with_all_valid_regions(self):
        org_id = 'org_123'
        base_project_name = "ProjectRegLoop"
        initial_project_count = len(DB['projects'])
        initial_cost_count = len(DB['costs']) # Should be 4 from setUp

        temp_cost_ids_added = []
        for i, region_code in enumerate(self.VALID_REGIONS):
            project_name = f"{base_project_name}_{i}"
            cost_id = f'cost_confirm_region_test_{i}'
            temp_cost_ids_added.append(cost_id)
            DB['costs'][cost_id] = {
                'type': 'project', 'amount': 10.0, 'currency': 'USD',
                'recurrence': 'monthly', 'description': f'Test project cost for {region_code}',
                'confirmation_id': cost_id
            }
            
            with self.subTest(region=region_code, project_name=project_name):
                response = create_project(
                    name=project_name,
                    organization_id=org_id,
                    confirm_cost_id=cost_id,
                    region=region_code
                )
                self.assertEqual(response['name'], project_name)
                self.assertEqual(response['organization_id'], org_id)
                self.assertEqual(response['region'], region_code)
                self.assertIn(response['status'], self.EXPECTED_INITIAL_STATUSES)
                self.assertTrue(self._is_iso_timestamp(response['created_at']))
                self.assertTrue(len(response['id']) > 0)
                self.assertNotIn(cost_id, DB['costs'])
        
        self.assertEqual(len(DB['projects']), initial_project_count + len(self.VALID_REGIONS))
        self.assertEqual(len(DB['costs']), initial_cost_count, "Costs not related to this loop should remain.")


    def test_create_project_invalid_input_empty_name(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=custom_errors.InvalidInputError,
            name="",
            organization_id="org_123",
            confirm_cost_id="cost_project_valid_general",
            expected_message="Project name cannot be empty."
        )

    def test_create_project_invalid_input_empty_organization_id(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=custom_errors.InvalidInputError,
            name="Test Project",
            organization_id="",
            confirm_cost_id="cost_project_valid_general",
            expected_message="Organization ID cannot be empty."
        )

    def test_create_project_invalid_input_empty_confirm_cost_id(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=custom_errors.InvalidInputError,
            name="Test Project",
            organization_id="org_123",
            confirm_cost_id="",
            expected_message="Confirmation cost ID cannot be empty."
        )
    
    def test_create_project_not_found_organization(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=custom_errors.NotFoundError,
            name="Test Project",
            organization_id="org_non_existent",
            confirm_cost_id="cost_project_valid_general",
            expected_message="Organization with ID 'org_non_existent' not found."
        )

    def test_create_project_cost_confirmation_error_invalid_id(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=custom_errors.CostConfirmationError,
            name="Test Project",
            organization_id="org_123",
            confirm_cost_id="cost_id_does_not_exist",
            expected_message="Cost confirmation ID 'cost_id_does_not_exist' is invalid or not found."
        )

    def test_create_project_cost_confirmation_error_mismatched_type(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=custom_errors.CostConfirmationError,
            name="Test Project",
            organization_id="org_123",
            confirm_cost_id="cost_branch_mismatch", 
            expected_message="Cost confirmation 'cost_branch_mismatch' is not for a project creation."
        )

    def test_create_project_validation_error_invalid_name_type(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=PydanticValidationError, # Assuming this is the one for Pydantic-like validation
            name=12345, 
            organization_id="org_123",
            confirm_cost_id="cost_project_valid_general",
            expected_message="Input should be a valid string" # Example, actual message may vary
        )

    def test_create_project_validation_error_invalid_org_id_type(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=PydanticValidationError,
            name="Valid Name",
            organization_id=12345, 
            confirm_cost_id="cost_project_valid_general",
            expected_message="Input should be a valid string"
        )

    def test_create_project_validation_error_invalid_cost_id_type(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=PydanticValidationError,
            name="Valid Name",
            organization_id="org_123",
            confirm_cost_id=12345, 
            expected_message="Input should be a valid string"
        )

    def test_create_project_validation_error_invalid_region_type(self):
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=PydanticValidationError,
            name="Valid Name",
            organization_id="org_123",
            confirm_cost_id="cost_project_valid_general",
            region=12345, 
            expected_message="Input should be 'us-west-1', 'us-east-1', 'us-east-2', 'ca-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-central-2', 'eu-north-1', 'ap-south-1', 'ap-southeast-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-2' or 'sa-east-1'"
        )

    def test_create_project_validation_error_invalid_region_value(self):
        invalid_region = "antarctica-south-1"
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=PydanticValidationError,
            name="Valid Name",
            organization_id="org_123",
            confirm_cost_id="cost_project_valid_general",
            region=invalid_region,
            expected_message=f"Input should be 'us-west-1', 'us-east-1', 'us-east-2', 'ca-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-central-2', 'eu-north-1', 'ap-south-1', 'ap-southeast-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-2' or 'sa-east-1'"
        )

if __name__ == '__main__':
    unittest.main()