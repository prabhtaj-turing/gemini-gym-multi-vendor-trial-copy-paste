"""Test cases for Supabase project-related functions."""
import unittest
import copy
from datetime import datetime
from unittest import mock

from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from ..project import get_anon_key, list_projects, pause_project, restore_project
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.models import Project, NON_PAUSABLE_STATUSES, ProjectStatus

# Initial database state for get_anon_key tests
GET_ANON_KEY_INITIAL_DB_STATE = {
    "organizations": [
        {
            "id": "org_abc123",
            "name": "Acme Corp",
            "created_at": "2023-01-15T10:00:00Z",
            "subscription_plan": {
                "id": "plan_pro",
                "name": "Pro Plan",
                "price": 25.00,
                "currency": "USD",
                "features": ["unlimited_projects", "priority_support"]
            }
        }
    ],
    "projects": [
        {
            "id": "proj_1a2b3c",
            "name": "Acme CRM",
            "organization_id": "org_abc123",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-02-01T09:15:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_4d5e6f",
            "name": "Analytics Dashboard",
            "organization_id": "org_abc123",
            "region": "eu-west-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-03-10T14:30:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_inactive",
            "name": "Old Project",
            "organization_id": "org_abc123",
            "region": "us-west-2",
            "status": "INACTIVE",
            "created_at": "2022-01-05T08:00:00Z",
            "version": "PostgreSQL 14"
        },
        {
            "id": "proj_no_key",
            "name": "Project Without Key",
            "organization_id": "org_abc123",
            "region": "ap-south-1",
            "status": "INITIALIZING",
            "created_at": "2023-04-01T12:00:00Z",
            "version": None
        },
    ],
    "project_anon_keys": {
        "proj_1a2b3c": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2oxYTJiM2MiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY3MzcxMzYwMCwiZXhwIjoxODMwNTcxMjAwfQ.test_anon_key_1",
        "proj_4d5e6f": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2o0ZDVlNmYiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY3MzcxMzYwMCwiZXhwIjoxODMwNTcxMjAwfQ.test_anon_key_2",
        "proj_inactive": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2ppbmFjdGl2ZSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjczNzEzNjAwLCJleHAiOjE4MzA1NzEyMDB9.test_anon_key_inactive"
        # Note: proj_no_key intentionally has no entry in project_anon_keys
    },
    "tables": {},
    "extensions": {},
    "migrations": {},
    "edge_functions": {},
    "branches": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {},
    "project_ts_types": {},
    "logs": {}
}


class TestGetAnonKey(BaseTestCaseWithErrorHandler):
    """Test suite for the get_anon_key function."""

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(GET_ANON_KEY_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def test_get_anon_key_success_active_project(self):
        """Test successful retrieval of anon key for an active project."""
        result = get_anon_key(project_id='proj_1a2b3c')
        expected = {
            'project_id': 'proj_1a2b3c',
            'anon_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2oxYTJiM2MiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY3MzcxMzYwMCwiZXhwIjoxODMwNTcxMjAwfQ.test_anon_key_1'
        }
        self.assertEqual(result, expected)

    def test_get_anon_key_success_different_project(self):
        """Test successful retrieval of anon key for another active project."""
        result = get_anon_key(project_id='proj_4d5e6f')
        expected = {
            'project_id': 'proj_4d5e6f',
            'anon_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2o0ZDVlNmYiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY3MzcxMzYwMCwiZXhwIjoxODMwNTcxMjAwfQ.test_anon_key_2'
        }
        self.assertEqual(result, expected)

    def test_get_anon_key_success_inactive_project(self):
        """Test that inactive projects can still return their anon key if it exists."""
        result = get_anon_key(project_id='proj_inactive')
        expected = {
            'project_id': 'proj_inactive',
            'anon_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByb2ppbmFjdGl2ZSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjczNzEzNjAwLCJleHAiOjE4MzA1NzEyMDB9.test_anon_key_inactive'
        }
        self.assertEqual(result, expected)

    def test_get_anon_key_project_without_key(self):
        """Test error when project exists but has no anon key."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ResourceNotFoundError,
            'No anon key found for project: proj_no_key',
            project_id='proj_no_key'
        )

    def test_get_anon_key_non_existent_project(self):
        """Test error when project ID does not exist."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.NotFoundError,
            'Project not found: proj_nonexistent',
            project_id='proj_nonexistent'
        )

    def test_get_anon_key_empty_id(self):
        """Test error when project_id is empty string."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            project_id=''
        )

    def test_get_anon_key_none_id(self):
        """Test error when project_id is None."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            project_id=None
        )

    def test_get_anon_key_non_string_id(self):
        """Test error when project_id is not a string."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=123
        )

    def test_get_anon_key_list_id(self):
        """Test error when project_id is a list."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=['proj_1a2b3c']
        )

    def test_get_anon_key_dict_id(self):
        """Test error when project_id is a dictionary."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'id must be string type',
            project_id={'id': 'proj_1a2b3c'}
        )

    def test_get_anon_key_whitespace_id(self):
        """Test error when project_id contains only whitespace."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            project_id='   '
        )

    def test_get_anon_key_response_structure(self):
        """Test that response matches expected structure with all required fields."""
        result = get_anon_key(project_id='proj_1a2b3c')
        
        # Check that response has exactly the expected keys
        expected_keys = {'project_id', 'anon_key'}
        self.assertEqual(set(result.keys()), expected_keys)
        
        # Check data types
        self.assertIsInstance(result['project_id'], str)
        self.assertIsInstance(result['anon_key'], str)
        
        # Verify project_id in response matches input
        self.assertEqual(result['project_id'], 'proj_1a2b3c')

    def test_get_anon_key_jwt_format(self):
        """Test that anon key follows JWT format (header.payload.signature)."""
        result = get_anon_key(project_id='proj_1a2b3c')
        anon_key = result['anon_key']
        
        # JWT should have exactly 3 parts separated by dots
        parts = anon_key.split('.')
        self.assertEqual(len(parts), 3, "JWT should have 3 parts separated by dots")
        
        # Each part should be non-empty
        for i, part in enumerate(parts):
            self.assertTrue(len(part) > 0, f"JWT part {i+1} should not be empty")

    def test_get_anon_key_different_keys_for_different_projects(self):
        """Test that different projects have different anon keys."""
        result1 = get_anon_key(project_id='proj_1a2b3c')
        result2 = get_anon_key(project_id='proj_4d5e6f')
        
        # Keys should be different
        self.assertNotEqual(result1['anon_key'], result2['anon_key'])
        
        # But both should be valid JWTs
        self.assertEqual(len(result1['anon_key'].split('.')), 3)
        self.assertEqual(len(result2['anon_key'].split('.')), 3)

    def test_get_anon_key_boolean_id(self):
        """Test error when project_id is a boolean."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=True
        )

    def test_get_anon_key_float_id(self):
        """Test error when project_id is a float."""
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=3.14
        )

    def test_get_anon_key_project_check_before_key_check(self):
        """Test that project existence is checked before anon key existence."""
        # Create a project ID that doesn't exist in projects list
        # Even if we were to add it to project_anon_keys, it should fail on project check first
        non_existent_project = 'proj_ghost'
        
        # The error should be about project not found, not anon key not found
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.NotFoundError,
            f'Project not found: {non_existent_project}',
            project_id=non_existent_project
        )

    def test_get_anon_key_initializing_project_with_no_key(self):
        """Test that initializing projects without keys properly report missing key."""
        # proj_no_key exists in projects but has no anon key
        # This tests the second level of validation
        self.assert_error_behavior(
            get_anon_key,
            custom_errors.ResourceNotFoundError,
            'No anon key found for project: proj_no_key',
            project_id='proj_no_key'
        )


class TestListProjects(BaseTestCaseWithErrorHandler): # type: ignore
    def setUp(self):
        """Set up the test environment before each test."""
        # Store a deep copy of the original global DB state
        self._original_DB_state = copy.deepcopy(DB) # type: ignore
        
        # Clear the global DB for a clean test slate
        DB.clear() # type: ignore

        # Initialize DB with a basic structure.
        # Tests will primarily populate DB['projects'].
        # Other keys are added for completeness if any internal logic might expect them,
        # though list_projects is simple.
        DB['projects'] = [] # type: ignore
        DB['organizations'] = [] # type: ignore
        DB['tables'] = {} # type: ignore
        DB['extensions'] = {} # type: ignore
        DB['migrations'] = {} # type: ignore
        DB['edge_functions'] = {} # type: ignore
        DB['branches'] = {} # type: ignore
        DB['costs'] = {} # type: ignore
        DB['unconfirmed_costs'] = {} # type: ignore
        DB['project_urls'] = {} # type: ignore
        DB['project_anon_keys'] = {} # type: ignore
        DB['project_ts_types'] = {} # type: ignore
        DB['logs'] = {} # type: ignore

    def tearDown(self):
        """Clean up the test environment after each test."""
        # Clear the global DB and restore its original state
        DB.clear() # type: ignore
        DB.update(self._original_DB_state) # type: ignore

    def test_list_projects_empty(self):
        """Test listing projects when DB['projects'] is an empty list."""
        DB['projects'] = [] # type: ignore # Explicitly set for clarity, though setUp does this
        result = list_projects() # type: ignore
        self.assertEqual(result, [])

    def test_list_projects_key_missing_in_db(self):
        """Test listing projects when the 'projects' key is entirely missing from DB."""
        # setUp initializes DB['projects'], so we must delete it for this test.
        if 'projects' in DB: # type: ignore
            del DB['projects'] # type: ignore
        self.assert_error_behavior(
            list_projects,
            KeyError,
            "'projects'"
        )

    def test_list_projects_single_project(self):
        """Test listing a single project, ensuring all fields are correctly formatted and 'version' is excluded."""
        created_at_dt = datetime(2023, 1, 15, 10, 30, 0) # Naive datetime
        project_data_in_db = {
            "id": "proj_single_123",
            "name": "My First Project",
            "organization_id": "org_abc_789",
            "region": "eu-central-1",
            "status": "ACTIVE_HEALTHY",  # Corresponds to ProjectStatus.ACTIVE_HEALTHY.value
            "created_at": created_at_dt.isoformat(),
            "version": "14.1"  # This field should be ignored in the output
        }
        DB['projects'] = [project_data_in_db] # type: ignore

        result = list_projects() # type: ignore
        self.assertEqual(len(result), 1, "Should return a list with one project.")
        
        expected_project_output = {
            "id": "proj_single_123",
            "name": "My First Project",
            "organization_id": "org_abc_789",
            "region": "eu-central-1",
            "status": "ACTIVE_HEALTHY", # Status as string
            "created_at": created_at_dt.isoformat() # created_at as ISO string
        }
        self.assertEqual(result[0], expected_project_output, "Project data does not match expected output.")
        self.assertNotIn("version", result[0], "The 'version' field should not be present in the output.")

    def test_list_projects_multiple_projects(self):
        """Test listing multiple projects, checking order and formatting."""
        dt1 = datetime(2023, 1, 1, 10, 0, 0)
        dt2 = datetime(2023, 2, 15, 12, 30, 0)

        project1_db = {
            "id": "proj_multi_1",
            "name": "Project Alpha",
            "organization_id": "org_multi_A",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": dt1.isoformat(),
            "version": "15.0" # To be ignored
        }
        project2_db = {
            "id": "proj_multi_2",
            "name": "Project Beta",
            "organization_id": "org_multi_B",
            "region": "eu-west-2",
            "status": "INACTIVE",
            "created_at": dt2.isoformat()
            # No version field here, which is also fine for DB data
        }
        DB['projects'] = [project1_db, project2_db] # type: ignore

        result = list_projects() # type: ignore
        self.assertEqual(len(result), 2, "Should return a list with two projects.")

        expected_output1 = {
            "id": "proj_multi_1",
            "name": "Project Alpha",
            "organization_id": "org_multi_A",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": dt1.isoformat()
        }
        expected_output2 = {
            "id": "proj_multi_2",
            "name": "Project Beta",
            "organization_id": "org_multi_B",
            "region": "eu-west-2",
            "status": "INACTIVE",
            "created_at": dt2.isoformat()
        }
        

        # Assuming the function preserves the order from DB['projects']
        self.assertEqual(result[0], expected_output1, "First project data mismatch.")
        self.assertNotIn("version", result[0], "Version field should be excluded from first project.")
        self.assertEqual(result[1], expected_output2, "Second project data mismatch.")
        self.assertNotIn("version", result[1], "Version field should be excluded (if present in DB) from second project.")

    def test_list_projects_various_statuses(self):
        """Test listing projects with different valid statuses, ensuring status is string."""
        dt1 = datetime(2023, 3, 1, 0, 0, 0)
        dt2 = datetime(2023, 3, 2, 0, 0, 0)
        dt3 = datetime(2023, 3, 3, 0, 0, 0)

        # Using string values for statuses, corresponding to ProjectStatus enum values
        project_statuses_db_data = [
            {"id": "proj_stat_1", "name": "Status Coming Up", "organization_id": "org_stat", "region": "reg1", "status": "COMING_UP", "created_at": dt1.isoformat()},
            {"id": "proj_stat_2", "name": "Status INACTIVE", "organization_id": "org_stat", "region": "reg2", "status": "INACTIVE", "created_at": dt2.isoformat()},
            {"id": "proj_stat_3", "name": "Status Creating", "organization_id": "org_stat", "region": "reg3", "status": "CREATING_PROJECT", "created_at": dt3.isoformat()},
        ]
        DB['projects'] = project_statuses_db_data # type: ignore

        result = list_projects() # type: ignore
        self.assertEqual(len(result), 3)

        self.assertEqual(result[0]['status'], "COMING_UP")
        self.assertEqual(result[0]['created_at'], dt1.isoformat())
        self.assertEqual(result[1]['status'], "INACTIVE")
        self.assertEqual(result[1]['created_at'], dt2.isoformat())
        self.assertEqual(result[2]['status'], "CREATING_PROJECT")
        self.assertEqual(result[2]['created_at'], dt3.isoformat())

    def test_list_projects_datetime_precision_and_isoformat(self):
        """Test correct ISO 8601 formatting of datetime objects, including microseconds."""
        dt_with_micros = datetime(2023, 5, 20, 15, 45, 30, 123456)
        project_db_data = {
            "id": "proj_datetime_micros",
            "name": "Datetime Microseconds Test",
            "organization_id": "org_dt_micro",
            "region": "reg_dt_micro",
            "status": "ACTIVE_HEALTHY",
            "created_at": dt_with_micros.isoformat()
        }
        DB['projects'] = [project_db_data] # type: ignore

        result = list_projects() # type: ignore
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['created_at'], dt_with_micros.isoformat(),
                         "Datetime with microseconds not formatted correctly to ISO 8601.")

    def test_list_projects_ignores_extra_fields_in_db_project_dict(self):
        """Test that extraneous fields in DB project dictionaries are not included in the output."""
        dt = datetime(2023, 6, 1, 12, 0, 0)
        project_db_with_extras = {
            "id": "proj_extra_fields_test",
            "name": "Extra Fields Test Project",
            "organization_id": "org_extra",
            "region": "reg_extra",
            "status": "ACTIVE_HEALTHY",
            "created_at": dt.isoformat(),
            "version": "16.beta",                 # This should be ignored
            "custom_field_1": "some_random_value", # This should be ignored
            "another_internal_detail": {"key": "value_pair"} # This should be ignored
        }
        DB['projects'] = [project_db_with_extras] # type: ignore

        result = list_projects() # type: ignore
        self.assertEqual(len(result), 1)
        
        output_project = result[0]
        expected_keys = {"id", "name", "organization_id", "region", "status", "created_at"}
        self.assertEqual(set(output_project.keys()), expected_keys,
                         "Output project dictionary contains unexpected or missing keys.")
        
        # Verify values of expected keys for completeness
        self.assertEqual(output_project['id'], "proj_extra_fields_test")
        self.assertEqual(output_project['name'], "Extra Fields Test Project")
        self.assertEqual(output_project['created_at'], dt.isoformat())

    def test_list_projects_db_state_unmodified(self):
        """Test that the list_projects function does not modify the global DB state."""
        dt = datetime(2023, 7, 1, 0, 0, 0)
        project_db_data = {
            "id": "proj_unmodified_test",
            "name": "DB Unmodified Test",
            "organization_id": "org_unmod",
            "region": "reg_unmod",
            "status": "ACTIVE_HEALTHY",
            "created_at": dt.isoformat()
        }
        DB['projects'] = [project_db_data] # type: ignore
        
        # Make a deep copy of the DB state before the call
        original_db_state_copy = copy.deepcopy(DB) # type: ignore

        _ = list_projects() # type: ignore # Call the function, result not used for this assertion

        # Assert that the global DB state remains unchanged
        self.assertEqual(DB, original_db_state_copy,
                         "The list_projects function should not modify the DB state.")

class TestRestoreProject(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Store original DB state
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear() # Clear the actual global DB

        # Populate DB directly for this test class
        DB['organizations'] = [
            {
                'id': 'org_123',
                'name': 'Test Organization',
                'created_at': datetime(2023, 1, 1, 0, 0, 0).isoformat(),
                'subscription_plan': {
                    'id': 'plan_free',
                    'name': 'Free Plan',
                    'price': 0.0,
                    'currency': 'USD',
                    'features': ['basic_features']
                }
            }
        ]
        DB['projects'] = [
            {
                'id': 'proj_INACTIVE',
                'name': 'INACTIVE Project',
                'organization_id': 'org_123',
                'region': 'us-east-1',
                'status': 'INACTIVE',
                'created_at': datetime(2023, 1, 1, 12, 0, 0).isoformat()
            },
            {
                'id': 'proj_active',
                'name': 'Active Project',
                'organization_id': 'org_123',
                'region': 'us-east-1',
                'status': 'ACTIVE_HEALTHY',
                'created_at': datetime(2023, 1, 2, 12, 0, 0).isoformat()
            },
            {
                'id': 'proj_creating',
                'name': 'Creating Project',
                'organization_id': 'org_123',
                'region': 'us-east-1',
                'status': 'CREATING',
                'created_at': datetime(2023, 1, 3, 12, 0, 0).isoformat()
            },
            {
                'id': 'proj_inactive',
                'name': 'Inactive Project',
                'organization_id': 'org_123',
                'region': 'us-east-1',
                'status': 'INACTIVE',
                'created_at': datetime(2023, 1, 4, 12, 0, 0).isoformat()
            },
            {
                'id': 'proj_restoring_already',
                'name': 'Restoring Already Project',
                'organization_id': 'org_123',
                'region': 'us-east-1',
                'status': 'RESTORING',
                'created_at': datetime(2023, 1, 5, 12, 0, 0).isoformat()
            },
            {
                'id': 'proj_pausing',
                'name': 'Pausing Project',
                'organization_id': 'org_123',
                'region': 'us-east-1',
                'status': 'PAUSING',
                'created_at': datetime(2023, 1, 6, 12, 0, 0).isoformat()
            }
        ]
        DB['tables'] = {}
        DB['extensions'] = {}
        DB['migrations'] = {}
        DB['edge_functions'] = {}
        DB['branches'] = {}
        DB['costs'] = {}
        DB['unconfirmed_costs'] = {}
        DB['project_urls'] = {
            'proj_active': 'https://active-project.supabase.co'
        }
        DB['project_anon_keys'] = {
            'proj_active': 'active_anon_key_for_proj_active'
        }
        DB['project_ts_types'] = {}
        DB['logs'] = {}

    def tearDown(self):
        # Restore original DB state
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_project_from_db(self, project_id: str):
        for project in DB.get('projects', []):
            if project['id'] == project_id:
                return project
        return None

    def test_restore_project_success_from_INACTIVE(self):
        project_id = 'proj_INACTIVE'
        
        # Ensure URLs/keys are not present for the INACTIVE project, simulating prior pause action
        DB['project_urls'].pop(project_id, None)
        DB['project_anon_keys'].pop(project_id, None)

        response = restore_project(project_id=project_id)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get('project_id'), project_id)
        self.assertEqual(response.get('status'), 'RESTORING') # As per docstring example
        self.assertEqual(response.get('message'), f"Project {project_id} is being restored.")

        updated_project = self._get_project_from_db(project_id)
        self.assertIsNotNone(updated_project)
        self.assertEqual(updated_project.get('status'), 'RESTORING')

        # Assuming 'RESTORING' status does not immediately re-add URLs/keys
        # (this would happen when it transitions to 'ACTIVE_HEALTHY')
        self.assertNotIn(project_id, DB['project_urls'])
        self.assertNotIn(project_id, DB['project_anon_keys'])

    def test_restore_project_not_found_error(self):
        non_existent_project_id = 'project_does_not_exist_id'
        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Project with ID '{non_existent_project_id}' not found.",
            project_id=non_existent_project_id
        )

    def test_restore_project_operation_not_permitted_active_status(self):
        project_id = 'proj_active'
        project = self._get_project_from_db(project_id)
        original_status = project['status'] if project else 'UNKNOWN'
        
        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Project '{project_id}' cannot be restored. Project must be in 'INACTIVE' status, but current status is '{original_status}'.",
            project_id=project_id
        )
        updated_project = self._get_project_from_db(project_id)
        self.assertEqual(updated_project['status'], original_status) # Status unchanged

    def test_restore_project_operation_not_permitted_creating_status(self):
        project_id = 'proj_creating'
        project = self._get_project_from_db(project_id)
        original_status = project['status'] if project else 'UNKNOWN'

        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Project '{project_id}' cannot be restored. Project must be in 'INACTIVE' status, but current status is '{original_status}'.",
            project_id=project_id
        )
        updated_project = self._get_project_from_db(project_id)
        self.assertEqual(updated_project['status'], original_status)


    def test_restore_project_operation_not_permitted_already_restoring_status(self):
        project_id = 'proj_restoring_already'
        project = self._get_project_from_db(project_id)
        original_status = project['status'] if project else 'UNKNOWN'

        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Project '{project_id}' cannot be restored. Project must be in 'INACTIVE' status, but current status is '{original_status}'.",
            project_id=project_id
        )
        updated_project = self._get_project_from_db(project_id)
        self.assertEqual(updated_project['status'], original_status)

    def test_restore_project_operation_not_permitted_pausing_status(self):
        project_id = 'proj_pausing'
        project = self._get_project_from_db(project_id)
        original_status = project['status'] if project else 'UNKNOWN'

        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Project '{project_id}' cannot be restored. Project must be in 'INACTIVE' status, but current status is '{original_status}'.",
            project_id=project_id
        )
        updated_project = self._get_project_from_db(project_id)
        self.assertEqual(updated_project['status'], original_status)

    def test_restore_project_validation_error_project_id_integer(self):
        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Project ID must be a string.",
            project_id=12345
        )

    def test_restore_project_validation_error_project_id_none(self):
        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Project ID must be a string.",
            project_id=None
        )

    def test_restore_project_validation_error_project_id_empty_string(self):
        # Assuming empty string for project_id is invalid and caught by validation
        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Project ID cannot be empty.", 
            project_id=""
        )

    def test_restore_project_validation_error_project_id_list(self):
        self.assert_error_behavior(
            func_to_call=restore_project,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Project ID must be a string.",
            project_id=[]
        )

    def test_restore_project_unexpected_update_failure(self):
        """
        Tests that an OperationNotPermittedError is raised if the database update
        function unexpectedly fails by returning a falsy value.
        """
        project_id = 'proj_INACTIVE'
        new_status = ProjectStatus.RESTORING.value
        with unittest.mock.patch('supabase.project.utils.update_project_status_and_cascade', return_value=None) as mock_update_call:
            
            # Use the existing error assertion helper to check for the correct exception and message.
            self.assert_error_behavior(
                func_to_call=restore_project,
                expected_exception_type=custom_errors.OperationNotPermittedError,
                expected_message=(
                    f"An unexpected error occurred while attempting to update project "
                    f"'{project_id}' status to '{new_status}'."
                ),
                project_id=project_id
            )

            # Verify that the mocked update function was indeed called with the correct parameters.
            mock_update_call.assert_called_once_with(DB, project_id, new_status)

            # Finally, ensure the project's status in the database remains 'INACTIVE' because
            # the mocked update operation "failed".
            updated_project = self._get_project_from_db(project_id)
            self.assertEqual(updated_project.get('status'), 'INACTIVE')

# Initial database state for pause_project tests
PAUSE_PROJECT_INITIAL_DB_STATE = {
    "organizations": [
        {
            "id": "org_abc123",
            "name": "Acme Corp",
            "created_at": "2023-01-15T10:00:00Z",
            "subscription_plan": {
                "id": "plan_pro",
                "name": "Pro Plan",
                "price": 25.00,
                "currency": "USD",
                "features": ["unlimited_projects", "priority_support"]
            }
        }
    ],
    "projects": [
        {
            "id": "proj_active",
            "name": "Active Project",
            "organization_id": "org_abc123",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-02-01T09:15:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_inactive",
            "name": "Inactive Project",
            "organization_id": "org_abc123",
            "region": "eu-west-1",
            "status": "INACTIVE",
            "created_at": "2023-03-10T14:30:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_coming_up",
            "name": "Coming Up Project",
            "organization_id": "org_abc123",
            "region": "ap-south-1",
            "status": "COMING_UP",
            "created_at": "2023-04-01T12:00:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_already_INACTIVE",
            "name": "Already INACTIVE Project",
            "organization_id": "org_abc123",
            "region": "us-west-2",
            "status": "INACTIVE",
            "created_at": "2023-01-20T08:30:00Z",
            "version": "PostgreSQL 14"
        },
        {
            "id": "proj_pausing",
            "name": "Currently Pausing Project",
            "organization_id": "org_abc123",
            "region": "eu-central-1",
            "status": "PAUSING",
            "created_at": "2023-02-15T11:45:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_creating",
            "name": "Creating Project",
            "organization_id": "org_abc123",
            "region": "ap-southeast-1",
            "status": "CREATING",
            "created_at": "2023-05-01T16:20:00Z",
            "version": None
        },
        {
            "id": "proj_initializing",
            "name": "Initializing Project",
            "organization_id": "org_abc123",
            "region": "us-central-1",
            "status": "INITIALIZING",
            "created_at": "2023-05-02T10:10:00Z",
            "version": None
        },
        {
            "id": "proj_restoring",
            "name": "Restoring Project",
            "organization_id": "org_abc123",
            "region": "eu-north-1",
            "status": "RESTORING",
            "created_at": "2023-03-25T14:00:00Z",
            "version": "PostgreSQL 14"
        },
    ],
    "project_anon_keys": {},
    "tables": {},
    "extensions": {},
    "migrations": {},
    "edge_functions": {},
    "branches": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {},
    "project_ts_types": {},
    "logs": {}
}


class TestPauseProject(BaseTestCaseWithErrorHandler):
    """Test suite for the pause_project function."""

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(PAUSE_PROJECT_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Reset DB state before each test."""
        DB.clear()
        DB.update(copy.deepcopy(PAUSE_PROJECT_INITIAL_DB_STATE))

    def test_pause_project_success_active_project(self):
        """Test successful pausing of an active project."""
        result = pause_project(project_id='proj_active')
        
        expected = {
            'project_id': 'proj_active',
            'status': 'INACTIVE',
            'message': 'Project proj_active has been paused successfully'
        }
        self.assertEqual(result, expected)
        
        # Verify the project status was updated in the database
        projects = DB["projects"]
        project = next(p for p in projects if p["id"] == "proj_active")
        self.assertEqual(project["status"], "INACTIVE")


    def test_pause_project_success_coming_up_project(self):
        """Test successful pausing of a coming up project."""
        result = pause_project(project_id='proj_coming_up')
        
        expected = {
            'project_id': 'proj_coming_up',
            'status': 'INACTIVE',
            'message': 'Project proj_coming_up has been paused successfully'
        }
        self.assertEqual(result, expected)
        
        # Verify the project status was updated in the database
        projects = DB["projects"]
        project = next(p for p in projects if p["id"] == "proj_coming_up")
        self.assertEqual(project["status"], "INACTIVE")

    def test_pause_project_already_INACTIVE(self):
        """Test error when trying to pause an already INACTIVE project."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.OperationNotPermittedError,
            'Project in INACTIVE status cannot be paused',
            project_id='proj_already_INACTIVE'
        )

    def test_pause_project_currently_pausing(self):
        """Test error when trying to pause a project that is currently pausing."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.OperationNotPermittedError,
            'Project in PAUSING status cannot be paused',
            project_id='proj_pausing'
        )

    def test_pause_project_non_existent_project(self):
        """Test error when project ID does not exist."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.NotFoundError,
            'Project not found: proj_nonexistent',
            project_id='proj_nonexistent'
        )

    def test_pause_project_empty_id(self):
        """Test error when project_id is empty string."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            project_id=''
        )

    def test_pause_project_none_id(self):
        """Test error when project_id is None."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            project_id=None
        )

    def test_pause_project_whitespace_id(self):
        """Test error when project_id contains only whitespace."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            project_id='   '
        )

    def test_pause_project_non_string_id(self):
        """Test error when project_id is not a string."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=123
        )

    def test_pause_project_list_id(self):
        """Test error when project_id is a list."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=['proj_active']
        )

    def test_pause_project_dict_id(self):
        """Test error when project_id is a dictionary."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'id must be string type',
            project_id={'id': 'proj_active'}
        )

    def test_pause_project_boolean_id(self):
        """Test error when project_id is a boolean."""
        self.assert_error_behavior(
            pause_project,
            custom_errors.ValidationError,
            'id must be string type',
            project_id=True
        )

    def test_pause_project_response_structure(self):
        """Test that response matches expected structure with all required fields."""
        result = pause_project(project_id='proj_active')
        
        # Check that response has exactly the expected keys
        expected_keys = {'project_id', 'status', 'message'}
        self.assertEqual(set(result.keys()), expected_keys)
        
        # Check data types
        self.assertIsInstance(result['project_id'], str)
        self.assertIsInstance(result['status'], str)
        self.assertIsInstance(result['message'], str)
        
        # Verify project_id in response matches input
        self.assertEqual(result['project_id'], 'proj_active')
        # Verify status is INACTIVE
        self.assertEqual(result['status'], 'INACTIVE')

    def test_pause_project_database_persistence(self):
        """Test that pausing a project persists the status change in database."""
        # Get initial status
        projects = DB["projects"]
        project_before = next(p for p in projects if p["id"] == "proj_active")
        initial_status = project_before["status"]
        self.assertEqual(initial_status, "ACTIVE_HEALTHY")
        
        # Pause the project
        pause_project(project_id='proj_active')
        
        # Verify status changed in database
        project_after = next(p for p in projects if p["id"] == "proj_active")
        self.assertEqual(project_after["status"], "INACTIVE")

    def test_pause_project_valid_status_transitions(self):
        """Test that all pausable statuses can transition to INACTIVE."""
        pausable_statuses = [status for status in [
            "ACTIVE_HEALTHY", "INACTIVE", "COMING_UP"
        ] if status not in NON_PAUSABLE_STATUSES]
        
        for status in pausable_statuses:
            with self.subTest(status=status):
                # Reset database
                self.setUp()
                
                # Find a project with the desired status or create test data
                if status == "ACTIVE_HEALTHY":
                    project_id = "proj_active"
                elif status == "INACTIVE":
                    project_id = "proj_inactive"
                elif status == "COMING_UP":
                    project_id = "proj_coming_up"
                
                # Pause the project
                result = pause_project(project_id=project_id)
                
                # Verify success
                self.assertEqual(result['status'], 'INACTIVE')
                self.assertIn('paused successfully', result['message'])

    def test_pause_project_non_pausable_statuses_coverage(self):
        """Test that all NON_PAUSABLE_STATUSES are properly rejected."""
        
        status_to_project_map = {
            "PAUSING": "proj_pausing",
            "INACTIVE": "proj_inactive"
        }

        for status in NON_PAUSABLE_STATUSES:
            with self.subTest(status=status):
                project_id = status_to_project_map.get(status)
                if project_id:
                    self.assert_error_behavior(
                        pause_project,
                        custom_errors.OperationNotPermittedError,
                        f'Project in {status} status cannot be paused',
                        project_id=project_id
                    )


if __name__ == '__main__':
    unittest.main()