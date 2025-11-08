import unittest
import copy
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from unittest import mock

from common_utils.base_case import BaseTestCaseWithErrorHandler
from github_actions.SimulationEngine.custom_errors import NotFoundError, InvalidInputError
from github_actions.get_workflow_run_jobs_module import get_workflow_run_jobs, DEFAULT_PAGE, DEFAULT_PER_PAGE 
from github_actions.SimulationEngine.db import DB
from github_actions.SimulationEngine import utils
from github_actions.SimulationEngine.models import (
    ActorType, WorkflowState, WorkflowRunStatus, JobStatus, StepStatus,
    WorkflowRunConclusion, JobConclusion, StepConclusion
)

def dt_to_iso_z(dt_obj: Optional[Any]) -> Optional[str]:
    if dt_obj is None: return None
    if isinstance(dt_obj, str): return dt_obj 
    if not isinstance(dt_obj, datetime):
        raise TypeError(f"Expected datetime or string for dt_to_iso_z, got {type(dt_obj)}")
    dt_utc = dt_obj.astimezone(timezone.utc) if dt_obj.tzinfo else dt_obj.replace(tzinfo=timezone.utc)
    return dt_utc.isoformat(timespec='microseconds').replace('+00:00', 'Z')

class TestGetWorkflowRunJobs(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self.DB_backup = copy.deepcopy(DB)
        DB.clear()
        DB['repositories'] = {}
        DB['next_repo_id'] = 1; DB['next_workflow_id'] = 1; DB['next_run_id'] = 1; 
        DB['next_job_id'] = 1; DB['next_user_id'] = 1

        self.owner_login = 'testOwner'
        self.repo_name = 'Test-Repo'
        self.owner_data_dict = {'login': self.owner_login, 'id': 1, 'node_id': 'U_OWNER_1', 'type': ActorType.USER.value, 'site_admin': False}
        
        self.repo_dict_in_db = utils.add_repository(owner=self.owner_data_dict, repo_name=self.repo_name, repo_id=101)
        self.repo_key = f"{self.owner_login.lower()}/{self.repo_name.lower()}"

        workflow_def = {'name': 'CI Workflow', 'path': '.github/workflows/ci.yml', 'state': WorkflowState.ACTIVE.value}
        self.workflow_1_dict_in_db = utils.add_or_update_workflow(self.owner_login, self.repo_name, workflow_def)
        self.workflow_1_id = self.workflow_1_dict_in_db['id']
        
        now = datetime.now(timezone.utc)
        self.job1_input = { 
            'name': 'build', 'status': JobStatus.COMPLETED.value, 'conclusion': JobConclusion.SUCCESS.value,
            'started_at': now - timedelta(minutes=10), 'completed_at': now - timedelta(minutes=5),
            'steps': [{'name': 'Run build script', 'status': StepStatus.COMPLETED.value, 'conclusion': StepConclusion.SUCCESS.value,
                       'number': 1, 'started_at': now - timedelta(minutes=9, seconds=30), 'completed_at': now - timedelta(minutes=8)}],
            'labels': ['ubuntu-latest'], 'runner_name': 'GitHub Actions 1'
        }
        self.job2_input = { 
            'name': 'test', 'status': JobStatus.IN_PROGRESS.value, 'conclusion': None,
            'started_at': now - timedelta(minutes=4), 'completed_at': None,
            'labels': ['windows-latest'], 'runner_name': 'GitHub Actions 2'
        }
        self.job3_input = {
            'name': 'build', 'status': JobStatus.IN_PROGRESS.value, 'conclusion': None,
            'started_at': now, 'completed_at': None,
            'labels': ['ubuntu-latest'], 'runner_name': 'GitHub Actions 3'
        }
        self.job4_input = {
            'name': 'deploy', 'status': JobStatus.QUEUED.value, 'conclusion': None,
            'started_at': None, 'completed_at': None,
            'labels': ['self-hosted'], 'runner_name': None
        }
        run_input_data = {
            'workflow_id': self.workflow_1_id, 'head_sha': 'run1sha', 'event': 'push',
            'created_at': now - timedelta(minutes=20), 'updated_at': now - timedelta(minutes=1),
            'jobs': [self.job1_input, self.job2_input, self.job3_input, self.job4_input]
        }
        self.run_with_jobs_dict_in_db = utils.add_workflow_run(self.owner_login, self.repo_name, run_input_data)
        self.run_1_id = self.run_with_jobs_dict_in_db['id']

    def tearDown(self):
        DB.clear()
        DB.update(self.DB_backup)

    def test_get_jobs_all_no_pagination(self):
        result = get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, filter='all')
        self.assertEqual(result['total_count'], 4)
        self.assertEqual(len(result['jobs']), 4)
        job_names = {job['name'] for job in result['jobs']}
        self.assertEqual(job_names, {'build', 'test', 'deploy'})

    def test_get_jobs_latest_filter(self):
        result = get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, filter='latest')
        self.assertEqual(result['total_count'], 3) 
        self.assertEqual(len(result['jobs']), 3)
        build_jobs = [job for job in result['jobs'] if job['name'] == 'build']
        self.assertEqual(len(build_jobs), 1)
        self.assertEqual(build_jobs[0]['status'], JobStatus.IN_PROGRESS.value)

    def test_get_jobs_default_filter_is_latest(self):
        result_default = get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id)
        self.assertEqual(result_default['total_count'], 3)
        result_none_filter = get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, filter=None)
        self.assertEqual(result_none_filter['total_count'], 3)
        self.assertEqual(result_default['jobs'], result_none_filter['jobs'])

    def test_get_jobs_pagination(self):
        result_page1 = get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, filter='all', per_page=2, page=1)
        self.assertEqual(result_page1['total_count'], 4)
        self.assertEqual(len(result_page1['jobs']), 2)
        
        result_page2 = get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, filter='all', per_page=2, page=2)
        self.assertEqual(result_page2['total_count'], 4)
        self.assertEqual(len(result_page2['jobs']), 2)

        ids_page1 = {job['id'] for job in result_page1['jobs']}
        ids_page2 = {job['id'] for job in result_page2['jobs']}
        self.assertEqual(len(ids_page1.intersection(ids_page2)), 0)

    def test_pagination_with_explicit_none_for_page_params(self):
        result = get_workflow_run_jobs(
            self.owner_login, self.repo_name, self.run_1_id, 
            filter='all', page=None, per_page=None
        )
        self.assertEqual(result['total_count'], 4)
        self.assertEqual(len(result['jobs']), 4) 

        result_none_page = get_workflow_run_jobs(
            self.owner_login, self.repo_name, self.run_1_id,
            filter='all', page=None, per_page=2
        )
        self.assertEqual(result_none_page['total_count'], 4)
        self.assertEqual(len(result_none_page['jobs']), 2)

        result_none_per_page = get_workflow_run_jobs(
            self.owner_login, self.repo_name, self.run_1_id,
            filter='all', page=1, per_page=None
        )
        self.assertEqual(result_none_per_page['total_count'], 4)
        self.assertEqual(len(result_none_per_page['jobs']), 4)

    def test_input_validation_params(self):
        # Owner validation
        with self.assertRaisesRegex(InvalidInputError, "Owner must be a non-empty string."):
            get_workflow_run_jobs(owner="", repo=self.repo_name, run_id=self.run_1_id)
        with self.assertRaisesRegex(InvalidInputError, "Owner must be a non-empty string."):
            # @ts-ignore
            get_workflow_run_jobs(owner=None, repo=self.repo_name, run_id=self.run_1_id)
        with self.assertRaisesRegex(InvalidInputError, "Owner must be a non-empty string."):
            # @ts-ignore
            get_workflow_run_jobs(owner=123, repo=self.repo_name, run_id=self.run_1_id)

        # Repo validation
        with self.assertRaisesRegex(InvalidInputError, "Repo must be a non-empty string."):
            get_workflow_run_jobs(owner=self.owner_login, repo=" ", run_id=self.run_1_id)
        with self.assertRaisesRegex(InvalidInputError, "Repo must be a non-empty string."):
            # @ts-ignore
            get_workflow_run_jobs(owner=self.owner_login, repo=None, run_id=self.run_1_id)
        with self.assertRaisesRegex(InvalidInputError, "Repo must be a non-empty string."):
            # @ts-ignore
            get_workflow_run_jobs(owner=self.owner_login, repo=123, run_id=self.run_1_id)

        # Run ID validation
        with self.assertRaisesRegex(InvalidInputError, "Run ID must be a positive integer."):
            get_workflow_run_jobs(owner=self.owner_login, repo=self.repo_name, run_id=0)
        with self.assertRaisesRegex(InvalidInputError, "Run ID must be a positive integer."):
            # @ts-ignore
            get_workflow_run_jobs(owner=self.owner_login, repo=self.repo_name, run_id=None)
        with self.assertRaisesRegex(InvalidInputError, "Run ID must be a positive integer."):
            # @ts-ignore
            get_workflow_run_jobs(owner=self.owner_login, repo=self.repo_name, run_id="abc")


        # Filter validation
        with self.assertRaisesRegex(InvalidInputError, "Invalid filter value"):
            get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, filter="invalid")
        
        # Page validation
        with self.assertRaisesRegex(InvalidInputError, "Page number must be a positive integer."):
            get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, page=0)
        with self.assertRaisesRegex(InvalidInputError, "Page number must be a positive integer."):
            # @ts-ignore
            get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, page="abc")
        
        # Per_page validation
        with self.assertRaisesRegex(InvalidInputError, "Results per page must be an integer between 1 and 100."):
            get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, per_page=0)
        with self.assertRaisesRegex(InvalidInputError, "Results per page must be an integer between 1 and 100."):
            get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, per_page=101)
        with self.assertRaisesRegex(InvalidInputError, "Results per page must be an integer between 1 and 100."):
            # @ts-ignore
            get_workflow_run_jobs(self.owner_login, self.repo_name, self.run_1_id, per_page="abc")


    def test_not_found_errors(self):
        with self.assertRaisesRegex(NotFoundError, "Repository 'badowner/Test-Repo' not found."):
            get_workflow_run_jobs(owner="badowner", repo=self.repo_name, run_id=self.run_1_id)
        with self.assertRaisesRegex(NotFoundError, f"Repository '{self.owner_login}/badrepo' not found."):
            get_workflow_run_jobs(owner=self.owner_login, repo="badrepo", run_id=self.run_1_id)
        with self.assertRaisesRegex(NotFoundError, f"Workflow run with ID '999' not found in repository '{self.owner_login}/{self.repo_name}'."):
            get_workflow_run_jobs(owner=self.owner_login, repo=self.repo_name, run_id=999)
            
    def test_run_with_no_jobs(self):
        run_no_jobs_input = {
            'workflow_id': self.workflow_1_id, 'head_sha': 'nojobssha', 'event': 'workflow_dispatch',
            'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow(),
            'jobs': [] 
        }
        run_no_jobs_dict = utils.add_workflow_run(self.owner_login, self.repo_name, run_no_jobs_input)
        run_id_no_jobs = run_no_jobs_dict['id']

        result = get_workflow_run_jobs(self.owner_login, self.repo_name, run_id_no_jobs, filter='all')
        self.assertEqual(result['total_count'], 0)
        self.assertEqual(len(result['jobs']), 0)

if __name__ == '__main__':
    unittest.main()