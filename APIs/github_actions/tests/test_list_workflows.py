import unittest
import copy
from datetime import datetime, timezone, timedelta

# Imports for Pydantic models from the DB schema for DB setup
from github_actions.SimulationEngine.models import WorkflowState, ActorType
from github_actions.SimulationEngine.custom_errors import NotFoundError, InvalidInputError
from github_actions.list_workflows_module import list_workflows
from common_utils.base_case import BaseTestCaseWithErrorHandler
from github_actions.SimulationEngine.models import ListWorkflowsResponse
from github_actions.SimulationEngine.db import DB


class TestListWorkflows(BaseTestCaseWithErrorHandler):
    """Test suite for the list_workflows function."""

    def _format_iso_datetime(self, dt: datetime) -> str:
        """Helper to format datetime to ISO 8601 with Z for test data setup."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    def _get_expected_workflow_item_dict(self, db_workflow_data: dict) -> dict:
        """Converts a DB workflow dictionary to the expected API response item dictionary."""
        return {
            "id": db_workflow_data['id'],
            "node_id": db_workflow_data['node_id'],
            "name": db_workflow_data['name'],
            "path": db_workflow_data['path'],
            "state": db_workflow_data['state'],
            "created_at": db_workflow_data['created_at'],
            "updated_at": db_workflow_data['updated_at'],
        }

    def setUp(self):
        """Set up test data in the global DB."""
        self.DB = DB
        self.DB.clear()

        self.owner_login = "TestOwner"
        self.repo_name1 = "TestRepo1"
        self.repo_name_empty = "EmptyRepo"
        self.repo_name_case_test = "CaseSensitiveRepoName"

        self.user_test_owner = {
            'login': self.owner_login,
            'id': 1,
            'node_id': 'U_NODE_1',
            'type': ActorType.USER.value,
            'site_admin': False
        }

        # Workflows for TestRepo1 - IDs are used for sorting assumption
        self.wf1_data = {
            'id': 101, 'node_id': 'WF_NODE_101', 'name': 'Workflow Alpha', 'path': '.github/workflows/alpha.yml',
            'state': WorkflowState.ACTIVE.value,
            'created_at': self._format_iso_datetime(datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)),
            'updated_at': self._format_iso_datetime(datetime(2023, 1, 1, 11, 0, 0, tzinfo=timezone.utc)),
            'repo_owner_login': self.owner_login, 'repo_name': self.repo_name1
        }
        self.wf2_data = {
            'id': 102, 'node_id': 'WF_NODE_102', 'name': 'Workflow Beta', 'path': '.github/workflows/beta.yml',
            'state': WorkflowState.DISABLED_MANUALLY.value,
            'created_at': self._format_iso_datetime(datetime(2023, 1, 2, 10, 0, 0, tzinfo=timezone.utc)),
            'updated_at': self._format_iso_datetime(datetime(2023, 1, 2, 11, 0, 0, tzinfo=timezone.utc)),
            'repo_owner_login': self.owner_login, 'repo_name': self.repo_name1
        }
        self.wf3_data = {
            'id': 103, 'node_id': 'WF_NODE_103', 'name': 'Workflow Gamma', 'path': '.github/workflows/gamma.yml',
            'state': WorkflowState.ACTIVE.value,
            'created_at': self._format_iso_datetime(datetime(2023, 1, 3, 10, 0, 0, tzinfo=timezone.utc)),
            'updated_at': None, # Storing None directly if it can be None
            'repo_owner_login': self.owner_login, 'repo_name': self.repo_name1
        }
        # If wf3_data must have updated_at as a string:
        # self.wf3_data['updated_at'] = self._format_iso_datetime(datetime(2023, 1, 3, 11, 0, 0, tzinfo=timezone.utc))


        self.all_workflows_repo1_sorted = [
            self._get_expected_workflow_item_dict(self.wf1_data),
            self._get_expected_workflow_item_dict(self.wf2_data),
            self._get_expected_workflow_item_dict(self.wf3_data),
        ]

        self.DB['repositories'] = {
            f"{self.owner_login.lower()}/{self.repo_name1.lower()}": {
                'id': 1, 'node_id': 'R_NODE_1', 'name': self.repo_name1,
                'owner': copy.deepcopy(self.user_test_owner), 'private': False,
                'workflows': {
                    self.wf1_data['id']: copy.deepcopy(self.wf1_data),
                    self.wf2_data['id']: copy.deepcopy(self.wf2_data),
                    self.wf3_data['id']: copy.deepcopy(self.wf3_data),
                },
                'workflow_runs': {}
            },
            f"{self.owner_login.lower()}/{self.repo_name_empty.lower()}": {
                'id': 2, 'node_id': 'R_NODE_2', 'name': self.repo_name_empty,
                'owner': copy.deepcopy(self.user_test_owner), 'private': False,
                'workflows': {},
                'workflow_runs': {}
            },
            f"{self.owner_login.lower()}/{self.repo_name_case_test.lower()}": {
                'id': 3, 'node_id': 'R_NODE_3', 'name': self.repo_name_case_test,
                'owner': copy.deepcopy(self.user_test_owner), 'private': False,
                'workflows': {
                     # Create a distinct workflow for this test repo
                     self.wf1_data['id']: {**copy.deepcopy(self.wf1_data),
                                           'repo_name': self.repo_name_case_test,
                                           'name': "Case Test Workflow"}
                },
                'workflow_runs': {}
            }
        }

        self.many_workflows_repo_name = "ManyWorkflowsRepo"
        many_workflows_dict_unsorted = {}
        for i in range(1, 106): # 105 workflows
            wf_id = 200 + i
            created_dt = datetime(2023, 2, 1, 10, 0, i % 60, tzinfo=timezone.utc) + timedelta(days=i)
            updated_dt = datetime(2023, 2, 1, 11, 0, i % 60, tzinfo=timezone.utc) + timedelta(days=i)
            wf_data = {
                'id': wf_id, 'node_id': f'WF_NODE_MW_{wf_id}', 'name': f'Many Workflow {i}',
                'path': f'.github/workflows/many_wf_{i}.yml',
                'state': WorkflowState.ACTIVE.value,
                'created_at': self._format_iso_datetime(created_dt),
                'updated_at': self._format_iso_datetime(updated_dt),
                'repo_owner_login': self.owner_login, 'repo_name': self.many_workflows_repo_name
            }
            many_workflows_dict_unsorted[wf_data['id']] = wf_data

        self.DB['repositories'][f"{self.owner_login.lower()}/{self.many_workflows_repo_name.lower()}"] = {
            'id': 4, 'node_id': 'R_NODE_4', 'name': self.many_workflows_repo_name,
            'owner': copy.deepcopy(self.user_test_owner), 'private': False,
            'workflows': many_workflows_dict_unsorted,
            'workflow_runs': {}
        }
        self.many_workflows_list_expected = [
            self._get_expected_workflow_item_dict(data) for data in sorted(many_workflows_dict_unsorted.values(), key=lambda x: x['id'])
        ]

    def test_list_workflows_success_defaults(self):
        """Test listing workflows with default pagination."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1) # type: ignore

        # The function returns a dict, which can be validated by the Pydantic model
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 3)
        # Default per_page is 30, so all 3 workflows should be returned
        self.assertEqual(len(validated_response.workflows), 3)

        # Assuming workflows are sorted by ID by the function under test
        self.assertEqual(
            [wf.model_dump() for wf in validated_response.workflows], # type: ignore
            self.all_workflows_repo1_sorted 
        )

    def test_list_workflows_case_insensitive_owner_repo(self):
        """Test case-insensitivity of owner and repo names."""
        response_upper = list_workflows(owner=self.owner_login.upper(), repo=self.repo_name1.upper()) # type: ignore
        validated_upper = ListWorkflowsResponse(**response_upper) # type: ignore
        self.assertEqual(validated_upper.total_count, 3)
        self.assertEqual(len(validated_upper.workflows), 3)

        # Test with the specific repo set up for case testing
        response_mixed_case_repo = list_workflows(owner=self.owner_login.lower(), repo="casesensitivereponame") # type: ignore
        validated_mixed_case = ListWorkflowsResponse(**response_mixed_case_repo) # type: ignore
        self.assertEqual(validated_mixed_case.total_count, 1)
        self.assertEqual(len(validated_mixed_case.workflows), 1)

        # Retrieve the single workflow from the DB for comparison
        db_workflow_for_case_test_repo = self.DB['repositories'][f"{self.owner_login.lower()}/{self.repo_name_case_test.lower()}"]['workflows'][self.wf1_data['id']]
        expected_wf_item = self._get_expected_workflow_item_dict(db_workflow_for_case_test_repo)
        self.assertEqual(validated_mixed_case.workflows[0].model_dump(), expected_wf_item) # type: ignore

    def test_list_workflows_empty_repo(self):
        """Test listing workflows from a repository with no workflows."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name_empty) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 0)
        self.assertEqual(len(validated_response.workflows), 0)

    def test_list_workflows_pagination_page1_per_page1(self):
        """Test pagination: first page, one item per page."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=1, per_page=1) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 1)
        self.assertEqual(validated_response.workflows[0].model_dump(), self.all_workflows_repo1_sorted[0]) # type: ignore

    def test_list_workflows_pagination_page2_per_page1(self):
        """Test pagination: second page, one item per page."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=2, per_page=1) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 1)
        self.assertEqual(validated_response.workflows[0].model_dump(), self.all_workflows_repo1_sorted[1]) # type: ignore

    def test_list_workflows_pagination_page_last_per_page1(self):
        """Test pagination: last page with items, one item per page."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=3, per_page=1) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 1)
        self.assertEqual(validated_response.workflows[0].model_dump(), self.all_workflows_repo1_sorted[2]) # type: ignore

    def test_list_workflows_pagination_page_out_of_bounds(self):
        """Test pagination: page number beyond available items."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=4, per_page=1) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 0) # No items on this page

    def test_list_workflows_pagination_per_page_covers_all(self):
        """Test pagination: per_page is larger than total items."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=1, per_page=5) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 3)
        self.assertEqual([wf.model_dump() for wf in validated_response.workflows], self.all_workflows_repo1_sorted) # type: ignore

    def test_list_workflows_pagination_max_per_page(self):
        """Test pagination: using maximum allowed items per page (100)."""
        response = list_workflows(owner=self.owner_login, repo=self.many_workflows_repo_name, page=1, per_page=100) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 105) # Total workflows in this repo
        self.assertEqual(len(validated_response.workflows), 100) # Max per page
        self.assertEqual(
            [wf.model_dump() for wf in validated_response.workflows], # type: ignore
            self.many_workflows_list_expected[:100]
        )

    def test_list_workflows_pagination_second_page_max_per_page(self):
        """Test pagination: second page when using maximum per_page."""
        response = list_workflows(owner=self.owner_login, repo=self.many_workflows_repo_name, page=2, per_page=100) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 105)
        self.assertEqual(len(validated_response.workflows), 5) # Remaining 5 workflows
        self.assertEqual(
            [wf.model_dump() for wf in validated_response.workflows], # type: ignore
            self.many_workflows_list_expected[100:]
        )

    def test_list_workflows_pagination_per_page_just_under_max(self):
        """Test pagination: per_page is 99 (less than max 100)."""
        response = list_workflows(owner=self.owner_login, repo=self.many_workflows_repo_name, page=1, per_page=99) # type: ignore
        validated_response = ListWorkflowsResponse(**response) # type: ignore
        self.assertEqual(validated_response.total_count, 105)
        self.assertEqual(len(validated_response.workflows), 99)
        self.assertEqual(
            [wf.model_dump() for wf in validated_response.workflows], # type: ignore
            self.many_workflows_list_expected[:99]
        )

    def test_list_workflows_invalid_page_not_integer(self):
        """Test error for page number not being an integer."""
        with self.assertRaises(InvalidInputError) as context:
            list_workflows(owner=self.owner_login, repo=self.repo_name1, page="two", per_page=10) # type: ignore
        self.assertEqual(
            str(context.exception),
            "Page number must be an integer. Received: two (type: str)"
        )

    # Error Handling Tests
    def test_list_workflows_not_found_owner(self):
        """Test error when owner does not exist."""
        owner_name = "NonExistentOwner"
        repo_name = self.repo_name1
        self.assert_error_behavior(
            func_to_call=list_workflows,
            expected_exception_type=NotFoundError,
            expected_message=f"Repository '{owner_name}/{repo_name}' not found or not accessible.",
            owner=owner_name,
            repo=repo_name
        )

    def test_list_workflows_not_found_repo(self):
        """Test error when repository does not exist for a valid owner."""
        owner_name = self.owner_login
        repo_name = "NonExistentRepo"
        self.assert_error_behavior(
            func_to_call=list_workflows,
            expected_exception_type=NotFoundError,
            expected_message=f"Repository '{owner_name}/{repo_name}' not found or not accessible.",
            owner=owner_name,
            repo=repo_name
        )

    def test_list_workflows_invalid_page_zero(self):
        """Test error for invalid page number (0)."""
        self.assert_error_behavior(
            func_to_call=list_workflows,
            expected_exception_type=InvalidInputError,
            expected_message="Page number must be a positive integer. Received: 0",
            owner=self.owner_login,
            repo=self.repo_name1,
            page=0
        )

    def test_list_workflows_invalid_page_negative(self):
        """Test error for invalid page number (negative)."""
        self.assert_error_behavior(
            func_to_call=list_workflows,
            expected_exception_type=InvalidInputError,
            expected_message="Page number must be a positive integer. Received: -1",
            owner=self.owner_login,
            repo=self.repo_name1,
            page=-1
        )

    def test_list_workflows_invalid_per_page_zero(self):
        """Test error for invalid per_page value (0)."""
        self.assert_error_behavior(
            func_to_call=list_workflows,
            expected_exception_type=InvalidInputError,
            expected_message="Results per page must be an integer greater than or equal to 1. Received: 0", # Updated message
            owner=self.owner_login,
            repo=self.repo_name1,
            per_page=0
        )

    def test_list_workflows_invalid_per_page_negative(self):
        """Test error for invalid per_page value (negative)."""
        self.assert_error_behavior(
            func_to_call=list_workflows,
            expected_exception_type=InvalidInputError,
            expected_message="Results per page must be an integer greater than or equal to 1. Received: -1", # Updated message
            owner=self.owner_login,
            repo=self.repo_name1,
            per_page=-1
        )

    # Owner Validation Tests
    def test_list_workflows_invalid_owner_empty(self):
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message="Owner must be a non-empty string.",
            owner="", repo=self.repo_name1
        )

    def test_list_workflows_invalid_owner_whitespace(self):
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message="Owner must be a non-empty string.",
            owner="   ", repo=self.repo_name1
        )

    def test_list_workflows_invalid_owner_type(self):
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message="Owner must be a non-empty string.",
            owner=123, repo=self.repo_name1 # type: ignore
        )

    # Repo Validation Tests
    def test_list_workflows_invalid_repo_empty(self):
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message="Repo must be a non-empty string.",
            owner=self.owner_login, repo=""
        )

    def test_list_workflows_invalid_repo_whitespace(self):
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message="Repo must be a non-empty string.",
            owner=self.owner_login, repo="   "
        )

    def test_list_workflows_invalid_repo_type(self):
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message="Repo must be a non-empty string.",
            owner=self.owner_login, repo=123 # type: ignore
        )

    def test_list_workflows_invalid_per_page_type_string(self):
        per_page_val = "xyz"
        self.assert_error_behavior(
            func_to_call=list_workflows, expected_exception_type=InvalidInputError,
            expected_message=f"Results per page must be an integer. Received: {per_page_val} (type: {type(per_page_val).__name__})",
            owner=self.owner_login, repo=self.repo_name1, per_page=per_page_val # type: ignore
        )

    def test_list_workflows_valid_per_page_min_edge(self):
        """Test per_page at the minimum valid edge (1)."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=1, per_page=1)
        validated_response = ListWorkflowsResponse(**response)
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 1) # Expect 1 item

    def test_list_workflows_valid_per_page_max_edge(self):
        """Test per_page at the maximum valid edge (100)."""
        # This is already covered by test_list_workflows_pagination_max_per_page
        # but explicitly calling it out as an edge case test.
        response = list_workflows(owner=self.owner_login, repo=self.many_workflows_repo_name, page=1, per_page=100)
        validated_response = ListWorkflowsResponse(**response)
        self.assertEqual(validated_response.total_count, 105)
        self.assertEqual(len(validated_response.workflows), 100)

    def test_list_workflows_page_none_uses_default(self):
        """Test that page=None uses the default value (1)."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, page=None, per_page=1) # type: ignore
        validated_response = ListWorkflowsResponse(**response)
        self.assertEqual(validated_response.total_count, 3)
        self.assertEqual(len(validated_response.workflows), 1)
        self.assertEqual(validated_response.workflows[0].model_dump(), self.all_workflows_repo1_sorted[0])


    def test_list_workflows_per_page_none_uses_default(self):
        """Test that per_page=None uses the default value (30)."""
        response = list_workflows(owner=self.owner_login, repo=self.repo_name1, per_page=None) # type: ignore
        validated_response = ListWorkflowsResponse(**response)
        self.assertEqual(validated_response.total_count, 3)
        # Since total is 3 and default per_page is 30, all 3 should be returned
        self.assertEqual(len(validated_response.workflows), 3)
        self.assertEqual([wf.model_dump() for wf in validated_response.workflows], self.all_workflows_repo1_sorted)


if __name__ == '__main__':
    unittest.main()