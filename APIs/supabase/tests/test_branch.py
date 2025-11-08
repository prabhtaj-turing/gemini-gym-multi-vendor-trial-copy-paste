"""
Test suite for branch-related functionalities in the Supabase API simulation.
"""
import copy
import unittest
from datetime import datetime, timezone

from supabase.SimulationEngine import custom_errors, models, utils
from supabase.SimulationEngine.db import DB
from supabase.branch import list_branches, delete_branch
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Initial DB state for list_branches function tests
LIST_BRANCHES_INITIAL_DB_STATE = {
    "organizations": [
        {
            "id": "org_abc123",
            "name": "Acme Corp",
            "created_at": "2023-01-15T10:00:00Z",
            "plan": "pro",
            "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
            "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
        },
        {
            "id": "org_free",
            "name": "Free Org",
            "created_at": "2023-02-01T10:00:00Z",
            "plan": "free",
            "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
            "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"],
        }
    ],
    "projects": [
        {
            "id": "proj_1a2b3c",
            "name": "Acme CRM",
            "organization_id": "org_abc123",
            "region": "us-east-1",
            "status": models.ProjectStatus.ACTIVE_HEALTHY.value,
            "created_at": "2023-02-01T09:15:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_no_branches",
            "name": "No Branches Project",
            "organization_id": "org_abc123",
            "region": "us-west-2",
            "status": models.ProjectStatus.ACTIVE_HEALTHY.value,
            "created_at": "2023-03-01T10:00:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_no_branching",
            "name": "Free Project",
            "organization_id": "org_free",
            "region": "us-east-1",
            "status": models.ProjectStatus.ACTIVE_HEALTHY.value,
            "created_at": "2023-02-15T10:00:00Z",
            "version": "PostgreSQL 15"
        }
    ],
    "branches": {
        "proj_1a2b3c": [
            {
                "id": "branch_1",
                "name": "feature/user-auth",
                "status": models.BranchStatus.CREATING_PROJECT.value,
                "created_at": "2023-10-15T14:30:00Z",
                "updated_at": "2023-10-20T16:45:00Z",
                "project_ref": "proj_1a2b3c",
                "parent_project_ref": "proj_1a2b3c",
                "is_default": False,
                "git_branch": None,
                "persistent": True,
                "region": "us-east-1",
                "review_requested_at": None,
                "with_data": True
            },
            {
                "id": "branch_2",
                "name": "feature/payments",
                "status": models.BranchStatus.FUNCTIONS_DEPLOYED.value,
                "created_at": "2023-10-18T10:00:00Z",
                "updated_at": "2023-10-18T10:00:00Z",
                "project_ref": "proj_1a2b3c",
                "parent_project_ref": "proj_1a2b3c",
                "is_default": False,
                "git_branch": None,
                "persistent": True,
                "region": "us-east-1",
                "review_requested_at": None,
                "with_data": True
            },
            {
                "id": "branch_3",
                "name": "bugfix/critical-error",
                "status": models.BranchStatus.FUNCTIONS_FAILED.value,
                "created_at": "2023-10-19T09:00:00Z",
                "updated_at": "2023-10-21T11:30:00Z",
                "project_ref": "proj_1a2b3c",
                "parent_project_ref": "proj_1a2b3c",
                "is_default": False,
                "git_branch": None,
                "persistent": True,
                "region": "us-east-1",
                "review_requested_at": None,
                "with_data": True
            }
        ],
        "proj_no_branches": []
    }
}


class TestListBranches(BaseTestCaseWithErrorHandler):
    """
    Test suite for the list_branches function.
    """

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(LIST_BRANCHES_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def test_list_branches_success_multiple_branches(self):
        """Test successful listing of multiple branches for a project."""
        branches = list_branches(project_id='proj_1a2b3c')
        
        # Should return 3 branches
        self.assertEqual(len(branches), 3)
        
        # Check first branch (feature/user-auth)
        branch_1 = next(b for b in branches if b['id'] == 'branch_1')
        expected_branch_1 = {
            'id': 'branch_1',
            'name': 'feature/user-auth',
            'project_ref': 'proj_1a2b3c',
            'status': models.BranchStatus.CREATING_PROJECT.value,
            'created_at': '2023-10-15T14:30:00Z',
            'updated_at': '2023-10-20T16:45:00Z',
            'parent_project_ref': 'proj_1a2b3c',
            'is_default': False,
            'git_branch': None,
            'persistent': True,
            'region': 'us-east-1',
            'review_requested_at': None,
            'with_data': True
        }
        self.assertEqual(branch_1, expected_branch_1)
        
        # Check second branch (feature/payments)
        branch_2 = next(b for b in branches if b['id'] == 'branch_2')
        expected_branch_2 = {
            'id': 'branch_2',
            'name': 'feature/payments',
            'project_ref': 'proj_1a2b3c',
            'status': models.BranchStatus.FUNCTIONS_DEPLOYED.value,
            'created_at': '2023-10-18T10:00:00Z',
            'updated_at': '2023-10-18T10:00:00Z',
            'parent_project_ref': 'proj_1a2b3c',
            'is_default': False,
            'git_branch': None,
            'persistent': True,
            'region': 'us-east-1',
            'review_requested_at': None,
            'with_data': True
        }
        self.assertEqual(branch_2, expected_branch_2)
        
        # Check third branch (bugfix/critical-error)
        branch_3 = next(b for b in branches if b['id'] == 'branch_3')
        expected_branch_3 = {
            'id': 'branch_3',
            'name': 'bugfix/critical-error',
            'project_ref': 'proj_1a2b3c',
            'status': models.BranchStatus.FUNCTIONS_FAILED.value,
            'created_at': '2023-10-19T09:00:00Z',
            'updated_at': '2023-10-21T11:30:00Z',
            'parent_project_ref': 'proj_1a2b3c',
            'is_default': False,
            'git_branch': None,
            'persistent': True,
            'region': 'us-east-1',
            'review_requested_at': None,
            'with_data': True
        }
        self.assertEqual(branch_3, expected_branch_3)
        

    def test_list_branches_success_no_branches_for_project(self):
        """Test listing branches for a project that has no branches."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="found no branches for project_id: proj_no_branches",
            project_id='proj_no_branches'
        )

    def test_list_branches_project_not_found(self):
        """Test listing branches for a non-existent project."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message="Project with id 'non_existent_project' not found",
            project_id='non_existent_project'
        )

    def test_list_branches_empty_project_id_raises_validation_error(self):
        """Test that empty project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='The id parameter can not be null or empty',
            project_id=''
        )

    def test_list_branches_whitespace_project_id_raises_validation_error(self):
        """Test that whitespace-only project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='The id parameter can not be null or empty',
            project_id='   '
        )

    def test_list_branches_none_project_id_raises_validation_error(self):
        """Test that None project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='The id parameter can not be null or empty',
            project_id=None
        )

    def test_list_branches_invalid_project_id_type_integer_raises_validation_error(self):
        """Test that integer project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='id must be string type',
            project_id=123
        )

    def test_list_branches_invalid_project_id_type_list_raises_validation_error(self):
        """Test that list project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='The id parameter can not be null or empty',  # Empty list is caught by first check
            project_id=[]
        )

    def test_list_branches_invalid_project_id_type_dict_raises_validation_error(self):
        """Test that dict project_id raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='The id parameter can not be null or empty',  # Empty dict is caught by first check
            project_id={}
        )

    def test_list_branches_branching_not_enabled_raises_error(self):
        """Test that BranchingNotEnabledError is raised for projects without branching feature."""
        self.assert_error_behavior(
            func_to_call=list_branches,
            expected_exception_type=custom_errors.BranchingNotEnabledError,
            expected_message="Branching is not enabled for project 'proj_no_branching'. Please upgrade your subscription plan to access this feature.",
            project_id='proj_no_branching'
        )

    def test_list_branches_success_with_different_status_values(self):
        """Test that branches with various status values are returned correctly."""
        # Add a branch with FUNCTIONS_FAILED status
        error_branch = {
            "id": "branch_error",
            "name": "feature/broken",
            "project_ref": "proj_1a2b3c",
            "status": models.BranchStatus.FUNCTIONS_FAILED.value,
            "created_at": "2023-10-22T12:00:00Z",
            "last_activity_at": "2023-10-22T12:05:00Z"
        }
        DB['branches']['proj_1a2b3c'].append(error_branch)
        
        try:
            branches = list_branches(project_id='proj_1a2b3c')
            
            # Should now return 4 branches
            self.assertEqual(len(branches), 4)
            
            # Verify the error branch is included
            error_branch_result = next(b for b in branches if b['id'] == 'branch_error')
            expected_error_branch = {
                'id': 'branch_error',
                'name': 'feature/broken',
                'project_ref': 'proj_1a2b3c',
                'status': models.BranchStatus.FUNCTIONS_FAILED.value,
                'created_at': '2023-10-22T12:00:00Z',
                'last_activity_at': '2023-10-22T12:05:00Z'
            }
            self.assertEqual(error_branch_result, expected_error_branch)
            
        finally:
            # Clean up - remove the added branch
            DB['branches']['proj_1a2b3c'] = [
                b for b in DB['branches']['proj_1a2b3c'] if b['id'] != 'branch_error'
            ]

class TestDeleteBranch(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.org1_id = "org_066db7c7a96947b391690d1a3670ce78"
        self.project1_id = "proj_6b8c808a8e59419a828769a3c799f0a7"
        self.project2_id = "proj_f3c4e1a2b5d84f9c9a0b7d6e5c4a3b21"

        self.branch_active_deletable_id = "branch_1e1a1f98abc34c73a6a0a2a891187c7f"
        self.branch_main_protected_id = "branch_2d2b2g87xyz23b62b5b9b1b780076b6e"
        self.branch_merging_status_id = "branch_3c3c3h76pqr12a51a4a8a0a679965a5d"
        self.branch_error_status_deletable_id = "branch_4b4d4i65stu01z40z3z7z9z568854z4c"
        self.branch_project2_active_id = "branch_5a5e5j54vwx90y39y2y6y8y457743y3b"
        self.branch_p1_another_active_id = "branch_6f6f6k43lmn89x28x1x5x7x346632x2a"

        DB["organizations"] = [
            {"id": self.org1_id, "name": "Org One", "created_at": datetime.now(timezone.utc), 
             "subscription_plan": {"id": "plan_free", "name": "Free", "price": 0, "currency": "USD", "features": ["branching_enabled"]}}
        ]
        DB["projects"] = [
            {"id": self.project1_id, "name": "Project Alpha", "organization_id": self.org1_id, "region": "us-west-1", "status": "ACTIVE_HEALTHY", "created_at": datetime.now(timezone.utc)},
            {"id": self.project2_id, "name": "Project Beta", "organization_id": self.org1_id, "region": "eu-central-1", "status": "ACTIVE_HEALTHY", "created_at": datetime.now(timezone.utc)},
        ]
        DB["branches"] = {
            self.project1_id: [
                {
                    "id": self.branch_active_deletable_id, 
                    "name": "feature-branch-x",
                    "project_ref": self.project1_id,
                    "parent_project_ref": self.project1_id,
                    "status": models.BranchStatus.FUNCTIONS_DEPLOYED.value,
                    "created_at": datetime.now(timezone.utc), 
                    "updated_at": datetime.now(timezone.utc),
                    "is_default": False
                },
                {
                    "id": self.branch_main_protected_id, 
                    "name": "main", 
                    "project_ref": self.project1_id,
                    "parent_project_ref": self.project1_id,
                    "status": "CREATING_PROJECT",
                    "created_at": datetime.now(timezone.utc), 
                    "updated_at": datetime.now(timezone.utc),
                    "is_default": True
                },
                {
                    "id": self.branch_merging_status_id, 
                    "name": "hotfix-merging", 
                    "parent_project_ref": self.project1_id,
                    "project_ref": self.project1_id,
                    "status": models.BranchStatus.CREATING_PROJECT.value,
                    "created_at": datetime.now(timezone.utc), 
                    "updated_at": datetime.now(timezone.utc),
                    "is_default": False
                },
                {
                    "id": self.branch_error_status_deletable_id, 
                    "name": "failed-branch", 
                    "parent_project_ref": self.project1_id,
                    "project_ref": self.project1_id,
                    "status": "FUNCTIONS_PASSED",
                    "created_at": datetime.now(timezone.utc), 
                    "updated_at": datetime.now(timezone.utc),
                    "is_default": False
                },
                {
                    "id": self.branch_p1_another_active_id, 
                    "name": "another-active-branch", 
                    "parent_project_ref": self.project1_id,
                    "project_ref": self.project1_id,
                    "status": "FUNCTIONS_DEPLOYED",
                    "created_at": datetime.now(timezone.utc), 
                    "updated_at": datetime.now(timezone.utc),
                    "is_default": False
                },
                
            ],
            self.project2_id: [
                {
                    "id": self.branch_project2_active_id, 
                    "name": "dev-branch-p2", 
                    "parent_project_ref": self.project2_id,
                    "project_ref": self.project2_id,
                    "status": "FUNCTIONS_DEPLOYED",
                    "created_at": datetime.now(timezone.utc), 
                    "updated_at": datetime.now(timezone.utc),
                    "is_default": False
                }
            ]
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_delete_branch_success_active_branch(self):
        branch_id_to_delete = self.branch_active_deletable_id
        
        self.assertIsNotNone(utils.get_branch_by_id_from_db(DB,branch_id_to_delete), "Branch should exist before deletion.")
        initial_branch_count_p1 = len(DB["branches"][self.project1_id])

        response = delete_branch(branch_id=branch_id_to_delete)

        expected_response = {
            "branch_id": branch_id_to_delete,
            "status": "DELETED",
            "message": f"Branch '{branch_id_to_delete}' has been successfully deleted."
        }
        self.assertEqual(response, expected_response)
        self.assertIsNone(utils.get_branch_by_id_from_db(DB,branch_id_to_delete), "Branch should be removed after deletion.")
        self.assertEqual(len(DB["branches"][self.project1_id]), initial_branch_count_p1 - 1)
        
        # Ensure other branches are unaffected
        self.assertIsNotNone(utils.get_branch_by_id_from_db(DB,self.branch_main_protected_id))
        self.assertIsNotNone(utils.get_branch_by_id_from_db(DB,self.branch_project2_active_id))

    def test_delete_branch_success_error_status_branch(self):
        branch_id_to_delete = self.branch_error_status_deletable_id
        self.assertIsNotNone(utils.get_branch_by_id_from_db(DB,branch_id_to_delete))
        initial_branch_count_p1 = len(DB["branches"][self.project1_id])

        response = delete_branch(branch_id=branch_id_to_delete)

        expected_response = {
            "branch_id": branch_id_to_delete,
            "status": "DELETED",
            "message": f"Branch '{branch_id_to_delete}' has been successfully deleted."
        }
        self.assertEqual(response, expected_response)
        self.assertIsNone(utils.get_branch_by_id_from_db(DB,branch_id_to_delete))
        self.assertEqual(len(DB["branches"][self.project1_id]), initial_branch_count_p1 - 1)

    def test_delete_branch_success_removes_project_key_if_last_branch(self):
        # Project2 initially has one branch
        self.assertIn(self.project2_id, DB["branches"])
        self.assertEqual(len(DB["branches"][self.project2_id]), 1)
        branch_id_to_delete = self.branch_project2_active_id
        
        response = delete_branch(branch_id=branch_id_to_delete)

        expected_response = {
            "branch_id": branch_id_to_delete,
            "status": "DELETED",
            "message": f"Branch '{branch_id_to_delete}' has been successfully deleted."
        }
        self.assertEqual(response, expected_response)
        self.assertIsNone(utils.get_branch_by_id_from_db(DB,branch_id_to_delete))
        # Assuming the function removes the project key from DB["branches"] if its list becomes empty
        self.assertNotIn(self.project2_id, DB["branches"])

    def test_delete_branch_not_found_non_existent_id(self):
        non_existent_id = "branch_id_does_not_exist_anywhere"
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Branch with ID '{non_existent_id}' not found.",
            branch_id=non_existent_id
        )

    def test_delete_branch_not_found_when_branches_key_missing_in_db(self):
        del DB["branches"]
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Branch with ID '{self.branch_active_deletable_id}' not found.",
            branch_id=self.branch_active_deletable_id
        )

    def test_delete_branch_not_found_when_branches_dict_is_empty(self):
        DB["branches"] = {}
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Branch with ID '{self.branch_active_deletable_id}' not found.",
            branch_id=self.branch_active_deletable_id
        )
    
    def test_delete_branch_not_found_when_branch_list_for_its_project_is_empty(self):
        # Remove the branch from its original list to simulate it not being found there
        # This test ensures that if a branch ID was expected in a certain project's list and it's gone, it's not found.
        DB["branches"][self.project1_id] = [b for b in DB["branches"][self.project1_id] if b["id"] != self.branch_active_deletable_id]
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Branch with ID '{self.branch_active_deletable_id}' not found.",
            branch_id=self.branch_active_deletable_id
        )

    def test_delete_branch_operation_not_permitted_main_branch(self):
        branch_to_protect = utils.get_branch_by_id_from_db(DB,self.branch_main_protected_id)
        self.assertIsNotNone(branch_to_protect) # Ensure test setup is correct
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{self.branch_main_protected_id}' is the main production branch and cannot be deleted.",
            branch_id=self.branch_main_protected_id,
        )

    def _add_branch_for_status_test(self, project_id, branch_id, name, status):
        if project_id not in DB["branches"]:
            DB["branches"][project_id] = []
        new_branch = {
            "id": branch_id, 
            "name": name, 
            "parent_project_ref": project_id,
            "project_ref": project_id,
            "status": status,
            "created_at": datetime.now(timezone.utc), 
            "updated_at": datetime.now(timezone.utc),
            "is_default": False
        }
        DB["branches"][project_id].append(new_branch)
        return new_branch

    def _test_delete_branch_operation_not_permitted_for_status(self, status_value):
        name = f"branch-status-{status_value.lower()}"
        branch_id = f"temp_branch_{status_value.lower()}_{datetime.now(timezone.utc).timestamp()}" # Unique ID
        
        added_branch = self._add_branch_for_status_test(self.project1_id, branch_id, name, status_value)
        
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{added_branch['id']}' cannot be deleted in its current state: {status_value}.",
            branch_id=added_branch['id']
        )
        # Verify branch was not deleted
        self.assertIsNotNone(utils.get_branch_by_id_from_db(DB,added_branch['id']))

    def test_delete_branch_operation_not_permitted_status_functions_failed(self):
        self._test_delete_branch_operation_not_permitted_for_status("FUNCTIONS_FAILED")

    def test_delete_branch_operation_not_permitted_status_creating_project(self):
        self._test_delete_branch_operation_not_permitted_for_status("CREATING_PROJECT")

    def test_delete_branch_validation_error_branch_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="branch_id must be a non-empty string.", # Assuming exact match for custom ValidationError
            branch_id=12345
        )

    def test_delete_branch_validation_error_branch_id_empty_string(self):
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="branch_id must be a non-empty string.",
            branch_id=""
        )

    def test_delete_branch_validation_error_branch_id_none(self):
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="branch_id must be a non-empty string.",
            branch_id=None
        )
    
    def test_delete_branch_not_found_invalid_db_schema_branches_not_a_dict(self):
        """
        Tests NotFoundError is raised if DB['branches'] is not a dictionary.
        This covers the schema validation check at the start of the function.
        """
        branch_id_to_check = self.branch_active_deletable_id
        
        # Overwrite DB["branches"] with an invalid type (a list instead of a dict)
        DB["branches"] = ["this is not a valid structure for branches"]
        
        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Branch with ID '{branch_id_to_check}' not found (invalid branches structure in DB).",
            branch_id=branch_id_to_check
        )

    def test_delete_branch_malformed_data_missing_project_id(self):
        """Test ValidationError for malformed branch data missing project ID fields."""
        branch_id_to_test = "branch_malformed_missing_id"
        malformed_branch = {
            "id": branch_id_to_test,
            "name": "malformed-branch",
            "parent_project_ref": self.project1_id,
            # "branch_project_id" is intentionally missing.
            "status": "FUNCTIONS_DEPLOYED",
            "created_at": datetime.now(timezone.utc),
            "last_activity_at": datetime.now(timezone.utc),
        }
        DB["branches"][self.project1_id].append(malformed_branch)

        self.assert_error_behavior(
            func_to_call=delete_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message=f"Branch data for '{branch_id_to_test}' is malformed (missing project ID fields).",
            branch_id=branch_id_to_test,
        )

if __name__ == '__main__':
    unittest.main()