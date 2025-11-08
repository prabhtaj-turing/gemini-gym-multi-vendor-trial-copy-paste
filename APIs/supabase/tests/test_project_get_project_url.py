import copy
from datetime import datetime, timezone
import unittest
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from supabase.project import get_project_url


class TestGetProjectUrl(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.org_id1 = 'org_041e2f831f134a758259a0b978885aea'
        self.project_id1 = 'proj_6b8a2d3e5f7c4g1h9i0j'
        self.project_id2 = 'proj_c1d2e3f4g5h6i7j8k9l0'
        self.project_id_inactive = 'proj_inactive_7m8n9o0p1q2r'
        DB['organizations'] = [{'id': self.org_id1, 'name': 'Test Organization Alpha', 'created_at': datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(), 'subscription_plan': {'id': 'plan_basic', 'name': 'Basic', 'price': 0, 'currency': 'USD', 'features': ['feature1']}}]
        DB['projects'] = [{'id': self.project_id1, 'name': 'Main Project', 'organization_id': self.org_id1, 'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023, 1, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat(), 'version': '15.1'}, {'id': self.project_id2, 'name': 'Auxiliary Project', 'organization_id': self.org_id1, 'region': 'eu-west-2', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023, 1, 11, 10, 0, 0, tzinfo=timezone.utc).isoformat(), 'version': '15.1'}, {'id': self.project_id_inactive, 'name': 'Archived Project', 'organization_id': self.org_id1, 'region': 'ap-southeast-1', 'status': 'INACTIVE', 'created_at': datetime(2023, 1, 12, 10, 0, 0, tzinfo=timezone.utc).isoformat(), 'version': '14.5'}]
        DB['project_urls'] = {self.project_id1: f'https://api.{self.project_id1}.supabase.co', self.project_id_inactive: f'https://api.{self.project_id_inactive}.supabase.co'}
        DB['tables'] = {}
        DB['extensions'] = {}
        DB['migrations'] = {}
        DB['edge_functions'] = {}
        DB['branches'] = {}
        DB['costs'] = {}
        DB['unconfirmed_costs'] = {}
        DB['project_anon_keys'] = {self.project_id1: 'anon_key_1', self.project_id_inactive: 'anon_key_inactive'}
        DB['project_ts_types'] = {}
        DB['logs'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_project_url_success(self):
        """Test successfully retrieving a project's API URL."""
        expected_url = DB['project_urls'][self.project_id1]
        result = get_project_url(project_id=self.project_id1)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('project_id'), self.project_id1)
        self.assertEqual(result.get('api_url'), expected_url)
        self.assertEqual(set(result.keys()), {'project_id', 'api_url'})

    def test_get_project_url_for_inactive_project_with_url(self):
        """Test retrieving URL for an inactive project if its URL is still recorded."""
        expected_url = DB['project_urls'][self.project_id_inactive]
        result = get_project_url(project_id=self.project_id_inactive)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('project_id'), self.project_id_inactive)
        self.assertEqual(result.get('api_url'), expected_url)
        self.assertEqual(set(result.keys()), {'project_id', 'api_url'})

    def test_get_project_url_project_not_found(self):
        """Test attempting to get URL for a non-existent project_id."""
        non_existent_project_id = 'proj_non_existent_id_12345'
        self.assert_error_behavior(func_to_call=get_project_url, project_id=non_existent_project_id, expected_exception_type=custom_errors.NotFoundError, expected_message=f"Project with ID '{non_existent_project_id}' not found.")

    def test_get_project_url_project_exists_but_url_missing(self):
        """Test when project exists but its URL is not in project_urls.
    The function should return successfully with api_url as None.
    """
        result = get_project_url(project_id=self.project_id2)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('project_id'), self.project_id2)
        self.assertIsNone(result.get('api_url'))
        self.assertEqual(set(result.keys()), {'project_id', 'api_url'})

    def test_get_project_url_validation_error_project_id_none(self):
        """Test get_project_url with project_id as None."""
        self.assert_error_behavior(func_to_call=get_project_url, project_id=None, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: project_id must be a string.')

    def test_get_project_url_validation_error_project_id_not_string(self):
        """Test get_project_url with project_id as a non-string type (int)."""
        self.assert_error_behavior(func_to_call=get_project_url, project_id=12345, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: project_id must be a string.')

    def test_get_project_url_validation_error_project_id_empty_string(self):
        """Test get_project_url with an empty string for project_id.
    This should result in a NotFoundError as an empty string project ID is not expected to exist.
    """
        self.assert_error_behavior(func_to_call=get_project_url, project_id='', expected_exception_type=custom_errors.NotFoundError, expected_message="Project with ID '' not found.")
if __name__ == '__main__':
    unittest.main()