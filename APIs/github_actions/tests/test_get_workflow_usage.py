import unittest
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from unittest import mock

from common_utils.base_case import BaseTestCaseWithErrorHandler
from github_actions.SimulationEngine.custom_errors import NotFoundError, InvalidInputError
from github_actions.get_workflow_usage_module import get_workflow_usage
from github_actions.SimulationEngine.db import DB
from github_actions.SimulationEngine import utils
from github_actions.SimulationEngine.models import (
    ActorType, WorkflowState, WorkflowUsageStats, BillableOSEntry
)

class TestGetWorkflowUsage(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self.DB_backup = copy.deepcopy(DB)
        DB.clear()
        DB['repositories'] = {}
        DB['next_repo_id'] = 1; DB['next_workflow_id'] = 1; DB['next_user_id'] = 1

        self.owner_login = 'testOwner'
        self.repo_name = 'Test-Repo'
        self.owner_data_dict = {'login': self.owner_login, 'id': 1, 'node_id': 'U_OWNER_1', 'type': ActorType.USER.value, 'site_admin': False}
        
        self.repo_dict_in_db = utils.add_repository(owner=self.owner_data_dict, repo_name=self.repo_name)
        self.repo_key = f"{self.owner_login.lower()}/{self.repo_name.lower()}"

        self.usage_model_wf1 = WorkflowUsageStats(
            billable={
                "UBUNTU": BillableOSEntry(total_ms=120000, jobs=2),
                "MACOS": BillableOSEntry(total_ms=60000, jobs=1)
            }
        )
        wf1_def = {'name': 'CI Workflow', 'path': '.github/workflows/ci.yml', 
                   'state': WorkflowState.ACTIVE.value, 
                   'usage': self.usage_model_wf1.model_dump(mode='json')}
        self.wf1_dict_in_db = utils.add_or_update_workflow(self.owner_login, self.repo_name, wf1_def)
        self.wf1_id = self.wf1_dict_in_db['id']
        self.wf1_path = self.wf1_dict_in_db['path']
        self.expected_billable_wf1 = self.usage_model_wf1.model_dump(mode='json')['billable']

        usage_model_wf2 = WorkflowUsageStats(billable={})
        wf2_def = {'name': 'Empty Usage Workflow', 'path': '.github/workflows/empty.yml', 
                   'state': WorkflowState.ACTIVE.value, 'usage': usage_model_wf2.model_dump(mode='json')}
        self.wf2_dict_in_db = utils.add_or_update_workflow(self.owner_login, self.repo_name, wf2_def)
        self.wf2_id = self.wf2_dict_in_db['id']

        wf3_def = {'name': 'No Usage Field Workflow', 'path': '.github/workflows/no_usage.yml', 
                   'state': WorkflowState.ACTIVE.value, 'usage': None}
        self.wf3_dict_in_db = utils.add_or_update_workflow(self.owner_login, self.repo_name, wf3_def)
        self.wf3_id = self.wf3_dict_in_db['id']
        
        wf4_def = {'name': 'No Billable Key Workflow', 'path': '.github/workflows/no_billable.yml', 
                   'state': WorkflowState.ACTIVE.value, 'usage': {"some_other_key": "value"}}
        self.wf4_dict_in_db = utils.add_or_update_workflow(self.owner_login, self.repo_name, wf4_def)
        self.wf4_id = self.wf4_dict_in_db['id']

    def tearDown(self):
        DB.clear()
        DB.update(self.DB_backup)

    def test_get_workflow_usage_success_with_data_by_id(self):
        result = get_workflow_usage(self.owner_login, self.repo_name, self.wf1_id)
        self.assertEqual(result, {"billable": self.expected_billable_wf1})

    def test_get_workflow_usage_success_with_data_by_filename(self):
        result = get_workflow_usage(self.owner_login, self.repo_name, self.wf1_path)
        self.assertEqual(result, {"billable": self.expected_billable_wf1})

    def test_get_workflow_usage_empty_billable(self):
        result = get_workflow_usage(self.owner_login, self.repo_name, self.wf2_id)
        self.assertEqual(result, {"billable": {}})

    def test_get_workflow_usage_no_usage_field(self):
        result = get_workflow_usage(self.owner_login, self.repo_name, self.wf3_id)
        self.assertEqual(result, {"billable": {}})
        
    def test_get_workflow_usage_no_billable_key_in_usage(self):
        result = get_workflow_usage(self.owner_login, self.repo_name, self.wf4_id)
        self.assertEqual(result, {"billable": {}})

    def test_input_validation(self):
        with self.assertRaisesRegex(InvalidInputError, "Owner must be a non-empty string."):
            get_workflow_usage(owner="", repo=self.repo_name, workflow_id=self.wf1_id)
        with self.assertRaisesRegex(InvalidInputError, "Repo must be a non-empty string."):
            get_workflow_usage(owner=self.owner_login, repo=" ", workflow_id=self.wf1_id)
        
        # Test for workflow_id = None (line 47)
        with self.assertRaisesRegex(InvalidInputError, "Workflow ID/filename must be provided and non-empty."):
            # @ts-ignore
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=None)
        
        # Test for string workflow_id that is empty or whitespace
        with self.assertRaisesRegex(InvalidInputError, "Workflow ID \\(if string filename\\) must not be empty."):
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id="") # Caught by string specific check
        with self.assertRaisesRegex(InvalidInputError, "Workflow ID \\(if string filename\\) must not be empty."):
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id="   ")
        
        # Test for wrong types (float, boolean for workflow_id) (line 49)
        expected_type_error_msg = "Workflow ID must be a non-empty string \\(filename\\) or an integer \\(ID\\)."
        with self.assertRaisesRegex(InvalidInputError, expected_type_error_msg):
            # @ts-ignore
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=12.34) 
        with self.assertRaisesRegex(InvalidInputError, expected_type_error_msg):
             # @ts-ignore
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=True) 
        with self.assertRaisesRegex(InvalidInputError, expected_type_error_msg):
             # @ts-ignore
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=[]) # Example of another wrong type

        # Test for integer workflow_id <= 0
        with self.assertRaisesRegex(InvalidInputError, "Workflow ID \\(if integer\\) must be positive."):
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=0)
        with self.assertRaisesRegex(InvalidInputError, "Workflow ID \\(if integer\\) must be positive."):
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=-1)


    def test_not_found_owner(self):
        with self.assertRaisesRegex(NotFoundError, "Repository 'badowner/Test-Repo' not found."):
            get_workflow_usage(owner="badowner", repo=self.repo_name, workflow_id=self.wf1_id)

    def test_not_found_repo(self):
        with self.assertRaisesRegex(NotFoundError, f"Repository '{self.owner_login}/badrepo' not found."):
            get_workflow_usage(owner=self.owner_login, repo="badrepo", workflow_id=self.wf1_id)

    def test_not_found_workflow_id_int(self):
        with self.assertRaisesRegex(NotFoundError, f"Workflow with ID/filename '999' not found in repository '{self.owner_login}/{self.repo_name}'."):
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id=999)

    def test_not_found_workflow_filename(self):
        with self.assertRaisesRegex(NotFoundError, f"Workflow with ID/filename 'nonexistent.yml' not found in repository '{self.owner_login}/{self.repo_name}'."):
            get_workflow_usage(owner=self.owner_login, repo=self.repo_name, workflow_id="nonexistent.yml")

if __name__ == '__main__':
    unittest.main()