import unittest
import copy
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from pydantic import ValidationError

from supabase.project import get_project

from ..SimulationEngine.db import DB

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors

class TestGetProject(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.project1_created_at_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.project2_created_at_dt = datetime(2023, 1, 2, 10, 30, 0, tzinfo=timezone.utc)
        self.project_restricted_created_at_dt = datetime(2023, 1, 3, 8, 0, 0, tzinfo=timezone.utc)
        DB['projects'] = [{'id': 'proj_valid_1', 'name': 'Active Project One', 'organization_id': 'org_123', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'version': '15.1.0.122', 'created_at': self.project1_created_at_dt.isoformat()}, {'id': 'proj_valid_2_no_version', 'name': 'Inactive Project Two', 'organization_id': 'org_123', 'region': 'eu-central-1', 'status': 'INACTIVE', 'version': None, 'created_at': self.project2_created_at_dt.isoformat()}, {'id': 'proj_restricted_789', 'name': 'Restricted Access Project', 'organization_id': 'org_456_restricted', 'region': 'ap-southeast-2', 'status': 'ACTIVE_HEALTHY', 'version': '16.0', 'created_at': self.project_restricted_created_at_dt.isoformat()}]
        DB['organizations'] = []
        DB['tables'] = {}
        DB['extensions'] = {}
        DB['migrations'] = {}
        DB['edge_functions'] = {}
        DB['branches'] = {}
        DB['costs'] = {}
        DB['unconfirmed_costs'] = {}
        DB['project_urls'] = {}
        DB['project_anon_keys'] = {}
        DB['project_ts_types'] = {}
        DB['logs'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_project_success_project_found(self):
        """Test successfully retrieving an existing project with all fields."""
        project_id = 'proj_valid_1'
        result = get_project(id=project_id)
        expected_data = {'id': 'proj_valid_1', 'name': 'Active Project One', 'organization_id': 'org_123', 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'version': '15.1.0.122', 'created_at': self.project1_created_at_dt.isoformat()}
        self.assertEqual(result, expected_data)

    def test_get_project_success_project_with_null_version(self):
        """Test successfully retrieving a project where the version is None in DB, returned as empty string."""
        project_id = 'proj_valid_2_no_version'
        result = get_project(id=project_id)
        expected_data = {'id': 'proj_valid_2_no_version', 'name': 'Inactive Project Two', 'organization_id': 'org_123', 'region': 'eu-central-1', 'status': 'INACTIVE', 'version': '', 'created_at': self.project2_created_at_dt.isoformat()}
        self.assertEqual(result, expected_data)

    def test_get_project_not_found_raises_notfounderror(self):
        """Test that NotFoundError is raised for a non-existent project ID."""
        non_existent_id = 'proj_non_existent_id_123'
        self.assert_error_behavior(func_to_call=get_project, expected_exception_type=custom_errors.NotFoundError, expected_message=f"Project with ID '{non_existent_id}' not found.", id=non_existent_id)

    def test_get_project_not_found_when_projects_list_is_empty(self):
        """Test NotFoundError when DB['projects'] is empty."""
        DB['projects'] = []
        non_existent_id = 'proj_any_id_as_list_is_empty'
        self.assert_error_behavior(func_to_call=get_project, expected_exception_type=custom_errors.NotFoundError, expected_message=f"Project with ID '{non_existent_id}' not found.", id=non_existent_id)

    def test_get_project_empty_id_raises_validationerror(self):
        """Test that ValidationError is raised if the project ID is an empty string."""
        self.assert_error_behavior(func_to_call=get_project, expected_exception_type=custom_errors.ValidationError, expected_message='String should have at least 1 character', id='')

    def test_get_project_invalid_id_type_raises_validationerror(self):
        """Test that ValidationError is raised if the project ID is not a string."""
        self.assert_error_behavior(func_to_call=get_project, expected_exception_type=custom_errors.ValidationError, expected_message='Input should be a valid string', id=12345)

    def test_get_project_pydantic_validation_error_with_no_error_details(self):
        """Test that a generic ValidationError is raised for a Pydantic error with no details."""
        with patch('supabase.project.GetProjectInput') as mock_get_project_input:
            pydantic_error_with_no_details = ValidationError.from_exception_data(title="Dummy", line_errors=[])
            
            mock_get_project_input.side_effect = pydantic_error_with_no_details
            
            self.assert_error_behavior(
                func_to_call=get_project,
                expected_exception_type=custom_errors.ValidationError,
                expected_message="Input validation failed.",
                id="any-project-id"
            )

if __name__ == '__main__':
    unittest.main()