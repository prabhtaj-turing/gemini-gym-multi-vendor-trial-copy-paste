import unittest
import copy
from datetime import datetime, timezone, timedelta
from ..SimulationEngine import custom_errors
from ..branch import create_branch
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestCreateBranch(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.org_id_with_branching = 'org_001_branching_enabled'
        self.org_id_without_branching = 'org_002_branching_disabled'
        self.project_id_main = 'proj_main_001'
        self.project_id_no_branching_feature_org = 'proj_main_002'
        self.project_id_org_not_found_in_db = 'proj_main_003'
        current_time = datetime.now(timezone.utc)
        self.iso_current_time_str = current_time.isoformat()
        DB['organizations'] = [{
            'id': self.org_id_with_branching, 
            'name': 'Org With Branching', 
            'created_at': current_time - timedelta(days=10), 
            'plan': 'pro',
            'opt_in_tags': ['AI_SQL_GENERATOR_OPT_IN', 'AI_DATA_GENERATOR_OPT_IN', 'AI_LOG_GENERATOR_OPT_IN'],
            'allowed_release_channels': ['internal', 'alpha', 'beta', 'ga', 'withdrawn', 'preview']
        }, {'id': self.org_id_without_branching, 'name': 'Org No Branching', 'created_at': current_time - timedelta(days=10), 'plan': 'free', 'opt_in_tags': ['AI_SQL_GENERATOR_OPT_IN', 'AI_DATA_GENERATOR_OPT_IN', 'AI_LOG_GENERATOR_OPT_IN'], 'allowed_release_channels': ['internal', 'alpha', 'beta', 'ga', 'withdrawn', 'preview']}]
        DB['projects'] = [{'id': self.project_id_main, 'name': 'Main Project Alpha', 'organization_id': self.org_id_with_branching, 'region': 'us-west-1', 'status': 'ACTIVE_HEALTHY', 'created_at': current_time - timedelta(days=5)}, {'id': self.project_id_no_branching_feature_org, 'name': 'Project Beta (No Branching Org)', 'organization_id': self.org_id_without_branching, 'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': current_time - timedelta(days=5)}, {'id': self.project_id_org_not_found_in_db, 'name': 'Project Gamma (Org Not Found)', 'organization_id': 'org_non_existent_004', 'region': 'eu-central-1', 'status': 'ACTIVE_HEALTHY', 'created_at': current_time - timedelta(days=5)}]
        DB['branches'] = {}
        DB['project_urls'] = {}
        DB['project_anon_keys'] = {}
        DB['project_ts_types'] = {}
        DB['logs'] = {}
        DB['tables'] = {}
        DB['extensions'] = {}
        DB['migrations'] = {}
        DB['edge_functions'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_iso_format_and_recent(self, timestamp_str, max_delta_seconds=5):
        try:
            if timestamp_str.endswith('Z'):
                dt_obj = datetime.fromisoformat(timestamp_str[:-1] + '+00:00')
            else:
                dt_obj = datetime.fromisoformat(timestamp_str)
            self.assertIsNotNone(dt_obj)
            self.assertEqual(dt_obj.tzinfo, timezone.utc, 'Timestamp should be UTC.')
        except ValueError:
            self.fail(f"Timestamp '{timestamp_str}' is not a valid ISO 8601 string.")

    def test_create_branch_success_default_name(self):
        result = create_branch(ref=self.project_id_main, name='develop')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'develop')
        self.assertEqual(result['project_ref'], self.project_id_main)
        self.assertIsInstance(result['id'], str)
        self.assertTrue(len(result['id']) > 10, 'Branch ID seems too short.')
        self.assertIn(result['status'], ['CREATING_PROJECT'])
        self._assert_iso_format_and_recent(result['created_at'])
        self.assertIn(self.project_id_main, DB['branches'])
        project_branches = DB['branches'][self.project_id_main]
        self.assertEqual(len(project_branches), 1)
        db_branch = project_branches[0]
        self.assertEqual(db_branch['id'], result['id'])
        self.assertEqual(db_branch['name'], 'develop')
        self.assertEqual(db_branch['project_ref'], self.project_id_main)
        self.assertEqual(db_branch['status'], result['status'])
        self.assertIsInstance(db_branch['created_at'], str)
        self.assertIsInstance(db_branch['updated_at'], str)

    def test_create_branch_success_custom_name(self):
        custom_name = 'feature-new-ux-final'
        result = create_branch(ref=self.project_id_main, name=custom_name)
        self.assertEqual(result['name'], custom_name)
        self.assertEqual(result['project_ref'], self.project_id_main)
        self.assertIsInstance(result['id'], str)
        self.assertTrue(len(result['id']) > 0)
        self.assertIn(result['status'], ['CREATING_PROJECT'])
        self._assert_iso_format_and_recent(result['created_at'])
        self.assertIn(self.project_id_main, DB['branches'])
        db_branch = DB['branches'][self.project_id_main][0]
        self.assertEqual(db_branch['name'], custom_name)

    def test_create_branch_with_existing_schema(self):
        """Test that a new branch correctly inherits the parent's schema."""
        # Setup: Add some schema to the parent project
        project_ref = self.project_id_main
        DB['tables'][project_ref] = [
            {'name': 'parent_table_1', 'schema': 'public', 'columns': []},
            {'name': 'parent_table_2', 'schema': 'private', 'columns': []},
        ]
        DB['migrations'][project_ref] = [
            {'version': '1', 'status': 'APPLIED_SUCCESSFULLY'},
            {'version': '2', 'status': 'APPLIED_SUCCESSFULLY'},
        ]
        DB['extensions'][project_ref] = [
            {'name': 'pg_cron', 'version': '1.4'},
        ]

        # Act: Create the branch
        result = create_branch(ref=project_ref, name='develop')
        branch_project_id = result['project_ref']

        # Assert: Check that the schema was copied
        self.assertIn(branch_project_id, DB['tables'])
        self.assertEqual(len(DB['tables'][branch_project_id]), 2)
        self.assertEqual(DB['tables'][branch_project_id][0]['name'], 'parent_table_1')

        self.assertIn(branch_project_id, DB['migrations'])
        self.assertEqual(len(DB['migrations'][branch_project_id]), 2)
        self.assertEqual(DB['migrations'][branch_project_id][0]['status'], 'APPLIED_SUCCESSFULLY')

        self.assertIn(branch_project_id, DB['extensions'])
        self.assertEqual(len(DB['extensions'][branch_project_id]), 1)
        self.assertEqual(DB['extensions'][branch_project_id][0]['name'], 'pg_cron')

    def test_create_multiple_branches_for_same_project_generates_unique_ids(self):
        result1 = create_branch(ref=self.project_id_main, name='branch-alpha')
        result2 = create_branch(ref=self.project_id_main, name='branch-beta')
        self.assertNotEqual(result1['id'], result2['id'], 'Branch IDs must be unique.')
        project_branches = DB['branches'][self.project_id_main]
        self.assertEqual(len(project_branches), 2)
        self.assertEqual(project_branches[0]['name'], 'branch-alpha')
        self.assertEqual(project_branches[1]['name'], 'branch-beta')

    def test_create_branch_error_parent_project_not_found(self):
        non_existent_project_id = 'proj_non_existent_id_123'
        self.assert_error_behavior(func_to_call=create_branch, expected_exception_type=custom_errors.NotFoundError, expected_message=f"Parent project with ID '{non_existent_project_id}' not found.", ref=non_existent_project_id, name='develop')

    def test_create_branch_error_validation_project_id_is_none(self):
        self.assert_error_behavior(
            func_to_call=create_branch, 
            expected_exception_type=custom_errors.ValidationError, 
            expected_message='Input validation failed: ref cannot be None or empty.', ref=None, name='develop')

    def test_create_branch_error_validation_name_empty(self):
        self.assert_error_behavior(func_to_call=create_branch, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: Branch name cannot be empty.', ref=self.project_id_main, name='')

    def test_create_branch_error_duplicate_name(self):
        """Test that creating a branch with a duplicate name for the same project raises a ValidationError."""
        name = 'feature-branch-duplicate'
        # Create the branch successfully the first time.
        create_branch(ref=self.project_id_main, name=name)
        
        # Attempt to create a branch with the same name again.
        expected_message = f"A branch with the name '{name}' already exists for project '{self.project_id_main}'."
        self.assert_error_behavior(
            func_to_call=create_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message=expected_message,
            ref=self.project_id_main,
            name=name,
        )
    

    def test_create_branch_error_branching_not_enabled_for_project_organization(self):
        self.assert_error_behavior(
            func_to_call=create_branch, 
            expected_exception_type=custom_errors.BranchingNotEnabledError, 
            expected_message=f"Branching feature is not enabled for the organization of project '{self.project_id_no_branching_feature_org}'.", 
            ref=self.project_id_no_branching_feature_org, 
            name='develop'
            )

    def test_create_branch_error_project_organization_not_found_in_db(self):
        expected_organization_id = 'org_non_existent_004'
        self.assert_error_behavior(
            func_to_call=create_branch, 
            expected_exception_type=custom_errors.NotFoundError, 
            expected_message=f"Organization '{expected_organization_id}' associated with project '{self.project_id_org_not_found_in_db}' not found.", 
            ref=self.project_id_org_not_found_in_db, 
            name='develop'
            )

if __name__ == '__main__':
    unittest.main()