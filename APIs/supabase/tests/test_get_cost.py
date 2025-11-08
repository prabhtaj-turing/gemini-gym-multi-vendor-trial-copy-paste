import unittest
import copy
from datetime import datetime
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import get_cost
from ..SimulationEngine import utils
from pydantic import ValidationError as PydanticValidationError

class TestGetCost(BaseTestCaseWithErrorHandler):

    def setUp(self):
        DB['organizations'] = [] 
        DB['projects'] = []

        # Populate DB with organizations and projects for testing
        DB['organizations'].extend([
            {"id": "org_free_no_projects", "name": "Org Free A", "plan": "free"},
            {"id": "org_free_one_project", "name": "Org Free B", "plan": "free"},
            {"id": "org_pro_no_projects", "name": "Org Pro A", "plan": "pro"},
            {"id": "org_pro_one_project", "name": "Org Pro B", "plan": "pro"},
            {"id": "org_pro_two_projects", "name": "Org Pro C", "plan": "pro"},
            {"id": "org_no_plan_info", "name": "Org No Plan"}, # For error testing
        ])

        DB['projects'].extend([
            # Projects for org_free_one_project
            {"id": "proj_free1", "organization_id": "org_free_one_project", "status": "ACTIVE_HEALTHY", "name": "Free Project 1"},
            # Projects for org_pro_one_project
            {"id": "proj_pro1", "organization_id": "org_pro_one_project", "status": "ACTIVE_HEALTHY", "name": "Pro Project 1"},
            # Projects for org_pro_two_projects
            {"id": "proj_pro2a", "organization_id": "org_pro_two_projects", "status": "ACTIVE_HEALTHY", "name": "Pro Project 2a"},
            {"id": "proj_pro2b", "organization_id": "org_pro_two_projects", "status": "INACTIVE", "name": "Pro Project 2b (Inactive)"}, # Inactive
            {"id": "proj_pro2c", "organization_id": "org_pro_two_projects", "status": "ACTIVE_HEALTHY", "name": "Pro Project 2c"},
        ])

    def tearDown(self):
        DB['organizations'] = []
        DB['projects'] = []

    # --- Success Cases ---
    def test_get_cost_branch(self):
        result = get_cost(type="branch", organization_id="org_free_no_projects") # Org ID is needed by Pydantic model
        self.assertEqual(result["type"], "branch")
        self.assertEqual(result["amount"], utils.get_cost_parameter('branch_hourly'))
        self.assertEqual(result["recurrence"], "hourly")
        self.assertEqual(result["currency"], utils.get_cost_parameter('default_currency'))
        self.assertIn("Standard cost for one new branch", result["description"])

    def test_get_cost_project_org_free_no_projects(self):
        result = get_cost(type="project", organization_id="org_free_no_projects")
        self.assertEqual(result["type"], "project")
        self.assertEqual(result["amount"], 0.0) # Free plan, 0 projects -> 0 cost
        self.assertEqual(result["recurrence"], "monthly")
        self.assertIn("free' plan", result["description"])

    def test_get_cost_project_org_free_one_project(self):
        result = get_cost(type="project", organization_id="org_free_one_project")
        self.assertEqual(result["type"], "project")
        self.assertEqual(result["amount"], 0.0) # Free plan, 1 project -> 0 cost for next
        self.assertEqual(result["recurrence"], "monthly")
        self.assertIn("free' plan", result["description"])

    def test_get_cost_project_org_pro_no_projects(self):
        # First active project on a Pro plan is free (included)
        result = get_cost(type="project", organization_id="org_pro_no_projects")
        self.assertEqual(result["type"], "project")
        self.assertEqual(result["amount"], 0.0)
        self.assertEqual(result["recurrence"], "monthly")
        self.assertIn("first active project", result["description"])
        self.assertIn(f"Next project cost: ${utils.get_cost_parameter('project_monthly'):.2f}", result["description"])


    def test_get_cost_project_org_pro_one_active_project(self):
        # Second active project on a Pro plan costs PROJECT_COST_MONTHLY
        result = get_cost(type="project", organization_id="org_pro_one_project")
        self.assertEqual(result["type"], "project")
        self.assertEqual(result["amount"],  utils.get_cost_parameter('project_monthly'))
        self.assertEqual(result["recurrence"], "monthly")
        self.assertIn(f"${utils.get_cost_parameter('project_monthly'):.2f} per month", result["description"])
        self.assertNotIn("first active project", result["description"])


    def test_get_cost_project_org_pro_multiple_active_projects(self):
        # Org Pro C has 2 active projects (proj_pro2a, proj_pro2c), so next costs.
        result = get_cost(type="project", organization_id="org_pro_two_projects")
        self.assertEqual(result["type"], "project")
        self.assertEqual(result["amount"], utils.get_cost_parameter('project_monthly'))
        self.assertEqual(result["recurrence"], "monthly")
        self.assertIn(f"${utils.get_cost_parameter('project_monthly'):.2f} per month", result["description"])

    # --- Error Cases ---
    def test_get_cost_organization_not_found(self):
        self.assert_error_behavior(
            func_to_call=get_cost,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Organization with ID 'org_does_not_exist' not found.",
            type="project",
            organization_id="org_does_not_exist"
        )

    def test_get_cost_invalid_type_argument(self):
        # This will be caught by Pydantic if 'type' is Literal['project', 'branch']
        self.assert_error_behavior(
            func_to_call=get_cost,
            expected_exception_type=PydanticValidationError, # Or PydanticValidationError if not wrapped
            expected_message="Input should be 'project' or 'branch'", # Substring from Pydantic for Literal/enum
            type="invalid_type",
            organization_id="org_free_no_projects"
        )


    def test_get_cost_empty_organization_id(self):
        # Pydantic Field(min_length=1) will catch this
        self.assert_error_behavior(
            func_to_call=get_cost,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            type="project",
            organization_id=""
        )

    def test_get_cost_org_with_no_plan_info(self):
        self.assert_error_behavior(
            func_to_call=get_cost,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Organization 'org_no_plan_info' has no plan information.",
            type="project",
            organization_id="org_no_plan_info"
        )

if __name__ == '__main__':
    unittest.main()