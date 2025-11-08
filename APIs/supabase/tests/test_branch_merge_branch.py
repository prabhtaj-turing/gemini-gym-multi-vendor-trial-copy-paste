import unittest
import copy
from datetime import datetime, timezone
from .. import database
from unittest.mock import patch

from ..SimulationEngine.db import DB
from ..branch import merge_branch

from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine import custom_errors

class TestMergeBranch(BaseTestCaseWithErrorHandler):
    PARENT_PROJECT_ID = "proj_parent_123"
    BRANCH_PROJECT_ID_1 = "proj_branch_abc_items"
    BRANCH_PROJECT_ID_2 = "proj_branch_def_no_items"
    BRANCH_PROJECT_ID_CONFLICT_MIG = "proj_branch_ghi_conflict_mig"
    BRANCH_PROJECT_ID_CONFLICT_FUNC = "proj_branch_jkl_conflict_func"
    BRANCH_PROJECT_ID_CREATING = "proj_branch_mno_creating"
    BRANCH_PROJECT_ID_MERGING = "proj_branch_pqr_merging"
    BRANCH_PROJECT_ID_ERROR = "proj_branch_stu_error"


    BRANCH_ID_ACTIVE = "branch_active_xyz789"
    BRANCH_ID_NO_ITEMS = "branch_noitems_uvw456"
    BRANCH_ID_CREATING = "branch_creating_123abc"
    BRANCH_ID_MERGING_STATE = "branch_merging_456def"
    BRANCH_ID_ERROR_STATE = "branch_error_789ghi"
    BRANCH_ID_CONFLICT_MIGRATION = "branch_conflict_mig_1jkl"
    BRANCH_ID_CONFLICT_FUNCTION = "branch_conflict_func_1mno"
    
    ORG_ID = "org_test_supa777"

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Initialize database manager
        from ..SimulationEngine.duckdb_manager import get_duckdb_manager
        self.db_manager = get_duckdb_manager()
        if not hasattr(self.db_manager, '_connections'):
            self.db_manager._connections = {}
        if not hasattr(self.db_manager, '_project_tables'):
            self.db_manager._project_tables = {}

        now = datetime.now(timezone.utc)
        self.initial_timestamp = now 

        DB['organizations'] = [
            {'id': self.ORG_ID, 'name': 'Test Org', 'created_at': now, 'subscription_plan': None}
        ]
        DB['projects'] = [
            {'id': self.PARENT_PROJECT_ID, 'name': 'Parent Project', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_1, 'name': 'Branch Alpha DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_2, 'name': 'Branch Beta DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_CONFLICT_MIG, 'name': 'Branch Conflict Mig DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_CONFLICT_FUNC, 'name': 'Branch Conflict Func DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_CREATING, 'name': 'Branch Creating DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_MERGING, 'name': 'Branch Merging DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
            {'id': self.BRANCH_PROJECT_ID_ERROR, 'name': 'Branch Error DB', 'organization_id': self.ORG_ID, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'region': 'us-west-1', 'version': '15'},
        ]
        DB['branches'] = {
            self.PARENT_PROJECT_ID: [
                {'id': self.BRANCH_ID_ACTIVE, 'name': 'Active Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_1, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'last_activity_at': self.initial_timestamp},
                {'id': self.BRANCH_ID_NO_ITEMS, 'name': 'No Items Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_2, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'last_activity_at': self.initial_timestamp},
                {'id': self.BRANCH_ID_CREATING, 'name': 'Creating Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_CREATING, 'status': 'CREATING', 'created_at': now, 'last_activity_at': self.initial_timestamp},
                {'id': self.BRANCH_ID_MERGING_STATE, 'name': 'Merging State Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_MERGING, 'status': 'MERGING', 'created_at': now, 'last_activity_at': self.initial_timestamp},
                {'id': self.BRANCH_ID_ERROR_STATE, 'name': 'Error State Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_ERROR, 'status': 'ERROR', 'created_at': now, 'last_activity_at': self.initial_timestamp},
                {'id': self.BRANCH_ID_CONFLICT_MIGRATION, 'name': 'Conflict Mig Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_CONFLICT_MIG, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'last_activity_at': self.initial_timestamp},
                {'id': self.BRANCH_ID_CONFLICT_FUNCTION, 'name': 'Conflict Func Branch', 'parent_project_id': self.PARENT_PROJECT_ID, 'branch_project_id': self.BRANCH_PROJECT_ID_CONFLICT_FUNC, 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'last_activity_at': self.initial_timestamp},
            ]
        }
        DB['migrations'] = {
            self.PARENT_PROJECT_ID: [
                {'version': 'mig_parent_base_001', 'name': 'Parent Initial Migration', 'status': 'applied', 'applied_at': now, 'query': 'CREATE TABLE parent_stuff_table;'}
            ],
            self.BRANCH_PROJECT_ID_1: [
                {'version': 'mig_branch1_001', 'name': 'Branch1 Migration Alpha', 'status': 'applied', 'applied_at': now, 'query': 'CREATE TABLE branch1_alpha_table;'},
                {'version': 'mig_branch1_002', 'name': 'Branch1 Migration Beta', 'status': 'applied', 'applied_at': now, 'query': 'CREATE TABLE branch1_beta_table;'}
            ],
            self.BRANCH_PROJECT_ID_2: [], 
            self.BRANCH_PROJECT_ID_CONFLICT_MIG: [
                 {'version': 'mig_conflict_001', 'name': 'Branch Migration Conflict Version', 'status': 'applied', 'applied_at': now, 'query': 'ALTER TABLE parent_stuff_table ADD COLUMN new_col_from_branch_conflict;'}
            ],
        }
        DB['migrations'][self.PARENT_PROJECT_ID].append(
             {'version': 'mig_conflict_001', 'name': 'Parent Migration Original Conflict Version', 'status': 'applied', 'applied_at': now, 'query': 'ALTER TABLE parent_stuff_table ADD COLUMN new_col_from_parent_original;'}
        )

        DB['edge_functions'] = {
            self.PARENT_PROJECT_ID: [
                {'id': 'func_parent_base_id', 'slug': 'parent-base-func', 'name': 'Parent Base Function', 'version': '1.0.0', 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'updated_at': now, 'entrypoint_path': 'index.ts', 'import_map_path': 'import_map.json', 'files': [{'name':'index.js', 'content':'parent base content'}]}
            ],
            self.BRANCH_PROJECT_ID_1: [
                {'id': 'func_branch1_new_id', 'slug': 'branch1-new-func', 'name': 'Branch1 New Function', 'version': '1.0.0', 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'updated_at': now, 'entrypoint_path': 'index.ts', 'import_map_path': 'import_map.json', 'files': [{'name':'index.js', 'content':'branch1 new func content'}]},
                {'id': 'func_branch1_update_id', 'slug': 'parent-base-func', 'name': 'Parent Base Function Updated by Branch1', 'version': '1.1.0', 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'updated_at': now, 'entrypoint_path': 'index.ts', 'import_map_path': 'import_map.json', 'files': [{'name':'index.js', 'content':'branch1 updated parent-base-func content'}]} 
            ],
            self.BRANCH_PROJECT_ID_2: [], 
            self.BRANCH_PROJECT_ID_CONFLICT_FUNC: [
                {'id': 'func_branch_conflict_id', 'slug': 'conflict-slug-func', 'name': 'Branch Conflict Slug Function', 'version': '1.0.0', 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'updated_at': now, 'entrypoint_path': 'index.ts', 'import_map_path': 'import_map.json', 'files': [{'name':'index.js', 'content':'branch conflict slug func content'}]}
            ]
        }
        DB['edge_functions'][self.PARENT_PROJECT_ID].append(
            {'id': 'func_parent_conflict_id', 'slug': 'conflict-slug-func', 'name': 'Parent Original Conflict Slug Function', 'version': '1.0.0', 'status': 'ACTIVE_HEALTHY', 'created_at': now, 'updated_at': now, 'entrypoint_path': 'index.ts', 'import_map_path': 'import_map.json', 'files': [{'name':'index.js', 'content':'parent original conflict slug func content'}]}
        )
        
        DB['tables'] = {}
        DB['extensions'] = {}
        DB['costs'] = {}
        DB['unconfirmed_costs'] = {}
        DB['project_urls'] = {}
        DB['project_anon_keys'] = {}
        DB['project_ts_types'] = {}
        DB['logs'] = {}


    def tearDown(self):
        # Close any open database connections
        for conn in self.db_manager._connections.values():
            try:
                conn.close()
            except:
                pass
        self.db_manager._connections = {}
        self.db_manager._project_tables = {}
        
        DB.clear()
        DB.update(self._original_DB_state)

    def _find_branch_in_db(self, branch_id):
        for parent_proj_id, branch_list in DB.get('branches', {}).items():
            for branch in branch_list:
                if branch['id'] == branch_id:
                    return branch
        return None

    # --- Success Test Cases ---
    def test_merge_successful_branch_with_items(self):
        response = merge_branch(branch_id=self.BRANCH_ID_ACTIVE)

        self.assertIsInstance(response, dict)
        self.assertEqual(response['branch_id'], self.BRANCH_ID_ACTIVE)
        self.assertEqual(response['target_project_id'], self.PARENT_PROJECT_ID)
        self.assertIn(response['status'], ['MERGING', 'COMPLETED'])
        self.assertTrue(response.get('merge_request_id', '').startswith('mr_')) 

        updated_branch = self._find_branch_in_db(self.BRANCH_ID_ACTIVE)
        self.assertIsNotNone(updated_branch)
        self.assertIn(updated_branch['status'], ['MERGING', 'COMPLETED'])
        self.assertGreater(updated_branch['last_activity_at'], self.initial_timestamp)

        parent_migrations = DB['migrations'].get(self.PARENT_PROJECT_ID, [])
        self.assertEqual(len(parent_migrations), 6) 
        self.assertTrue(any(m['version'] == 'mig_branch1_001' for m in parent_migrations))
        self.assertTrue(any(m['version'] == 'mig_branch1_002' for m in parent_migrations))

        parent_functions = DB['edge_functions'].get(self.PARENT_PROJECT_ID, [])
        self.assertEqual(len(parent_functions), 3) 
        
        updated_parent_func = next((f for f in parent_functions if f['slug'] == 'parent-base-func'), None)
        self.assertIsNotNone(updated_parent_func)
        self.assertEqual(updated_parent_func['version'], '1.1.0')
        self.assertEqual(updated_parent_func['files'][0]['content'], 'branch1 updated parent-base-func content')

        new_branch_func = next((f for f in parent_functions if f['slug'] == 'branch1-new-func'), None)
        self.assertIsNotNone(new_branch_func)
        self.assertEqual(new_branch_func['version'], '1.0.0')

    def test_merge_successful_branch_with_no_items(self):
        response = merge_branch(branch_id=self.BRANCH_ID_NO_ITEMS)

        self.assertEqual(response['branch_id'], self.BRANCH_ID_NO_ITEMS)
        self.assertEqual(response['target_project_id'], self.PARENT_PROJECT_ID)
        self.assertIn(response['status'], ['MERGING', 'COMPLETED'])

        updated_branch = self._find_branch_in_db(self.BRANCH_ID_NO_ITEMS)
        self.assertIsNotNone(updated_branch)
        self.assertIn(updated_branch['status'], ['MERGING', 'COMPLETED'])
        self.assertGreater(updated_branch['last_activity_at'], self.initial_timestamp)

        parent_migrations = DB['migrations'].get(self.PARENT_PROJECT_ID, [])
        self.assertEqual(len(parent_migrations), 2) 
        
        parent_functions = DB['edge_functions'].get(self.PARENT_PROJECT_ID, [])
        self.assertEqual(len(parent_functions), 2)

    # --- Error Test Cases ---
    def test_merge_branch_not_found(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Branch with ID 'non_existent_branch_id_123' not found.",
            branch_id="non_existent_branch_id_123"
        )

    def test_merge_branch_status_creating_not_permitted(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message="Branch is not in a mergable state. Current status: CREATING.",
            branch_id=self.BRANCH_ID_CREATING
        )

    def test_merge_branch_status_merging_not_permitted(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message="Branch is not in a mergable state. Current status: MERGING.",
            branch_id=self.BRANCH_ID_MERGING_STATE
        )

    def test_merge_branch_status_error_not_permitted(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message="Branch is not in a mergable state. Current status: ERROR.",
            branch_id=self.BRANCH_ID_ERROR_STATE
        )

    def test_merge_branch_migration_conflict(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.MergeConflictError,
            expected_message="Migration conflict detected for version mig_conflict_001.",
            branch_id=self.BRANCH_ID_CONFLICT_MIGRATION
        )

    def test_merge_branch_edge_function_conflict(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.MergeConflictError,
            expected_message="Edge function conflict detected for slug 'conflict-slug-func'.",
            branch_id=self.BRANCH_ID_CONFLICT_FUNCTION
        )

    # --- Validation Error Test Cases ---
    def test_merge_branch_validation_error_empty_branch_id(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Branch ID cannot be empty.",
            branch_id=""
        )

    def test_merge_branch_validation_error_invalid_type_branch_id(self):
        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Branch ID must be a string.",
            branch_id=777888
        )

    def test_merge_branch_migration_status_not_applied(self):
        """Test that migrations with status other than APPLIED or APPLIED_SUCCESSFULLY are skipped."""
        # Add a migration with PENDING status to the branch
        DB['migrations'][self.BRANCH_PROJECT_ID_1].append({
            'version': 'mig_branch1_pending',
            'name': 'Branch1 Migration Pending',
            'status': 'PENDING',
            'applied_at': None,
            'query': 'CREATE TABLE branch1_pending_table;'
        })

        response = merge_branch(branch_id=self.BRANCH_ID_ACTIVE)

        self.assertEqual(response['status'], 'COMPLETED')
        # Verify the pending migration was not merged
        parent_migrations = DB['migrations'].get(self.PARENT_PROJECT_ID, [])
        self.assertFalse(any(m['version'] == 'mig_branch1_pending' for m in parent_migrations))

    def test_merge_branch_migration_status_failed(self):
        """Test that migrations with FAILED status in target project raise conflict error."""
        # Add a failed migration to the parent project
        DB['migrations'][self.PARENT_PROJECT_ID].append({
            'version': 'mig_failed_001',
            'name': 'Failed Migration',
            'status': 'FAILED',
            'applied_at': datetime.now(timezone.utc),
            'query': 'CREATE TABLE failed_table;'
        })

        # Add the same migration version to the branch
        DB['migrations'][self.BRANCH_PROJECT_ID_1].append({
            'version': 'mig_failed_001',
            'name': 'Failed Migration',
            'status': 'APPLIED',
            'applied_at': datetime.now(timezone.utc),
            'query': 'CREATE TABLE failed_table;'
        })

        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.MergeConflictError,
            expected_message="Migration conflict detected for version mig_failed_001.",
            branch_id=self.BRANCH_ID_ACTIVE
        )

    def test_merge_branch_edge_function_same_version_different_content(self):
        """Test that edge functions with same version but different content raise conflict error."""
        # Add an edge function to the parent project
        DB['edge_functions'][self.PARENT_PROJECT_ID].append({
            'id': 'func_same_version_id',
            'slug': 'same-version-func',
            'name': 'Same Version Function',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'parent content'}]
        })

        # Add the same function with different content to the branch
        DB['edge_functions'][self.BRANCH_PROJECT_ID_1].append({
            'id': 'func_same_version_id_branch',
            'slug': 'same-version-func',
            'name': 'Same Version Function',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'branch content'}]
        })

        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.MergeConflictError,
            expected_message="Edge function conflict detected for slug 'same-version-func'.",
            branch_id=self.BRANCH_ID_ACTIVE
        )

    def test_merge_branch_edge_function_new_version_success(self):
        """Test that edge functions with new version are merged successfully."""
        # Add an edge function to the parent project
        DB['edge_functions'][self.PARENT_PROJECT_ID].append({
            'id': 'func_version_update_id',
            'slug': 'version-update-func',
            'name': 'Version Update Function',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'old content'}]
        })

        # Add a newer version of the same function to the branch
        DB['edge_functions'][self.BRANCH_PROJECT_ID_1].append({
            'id': 'func_version_update_id_branch',
            'slug': 'version-update-func',
            'name': 'Version Update Function',
            'version': '1.1.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'new content'}]
        })

        response = merge_branch(branch_id=self.BRANCH_ID_ACTIVE)
        self.assertEqual(response['status'], 'COMPLETED')

        # Verify the newer version was merged
        parent_functions = DB['edge_functions'].get(self.PARENT_PROJECT_ID, [])
        updated_func = next((f for f in parent_functions if f['slug'] == 'version-update-func'), None)
        self.assertIsNotNone(updated_func)
        self.assertEqual(updated_func['version'], '1.1.0')
        self.assertEqual(updated_func['files'][0]['content'], 'new content')

    def test_merge_branch_status_invalid(self):
        """Test that branch with invalid status raises OperationNotPermittedError."""
        # Create a branch with an invalid status
        invalid_status_branch_id = "branch_invalid_status_xyz"
        DB['branches'][self.PARENT_PROJECT_ID].append({
            'id': invalid_status_branch_id,
            'name': 'Invalid Status Branch',
            'parent_project_id': self.PARENT_PROJECT_ID,
            'branch_project_id': self.BRANCH_PROJECT_ID_1,
            'status': 'INVALID_STATUS',
            'created_at': datetime.now(timezone.utc),
            'last_activity_at': datetime.now(timezone.utc)
        })

        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message="Branch is not in a mergable state. Current status: INVALID_STATUS.",
            branch_id=invalid_status_branch_id
        )

    def test_merge_branch_migration_without_version(self):
        """Test that migrations without version are skipped."""
        # Add a migration without version to the branch
        DB['migrations'][self.BRANCH_PROJECT_ID_1].append({
            'name': 'Migration Without Version',
            'status': 'APPLIED',
            'applied_at': datetime.now(timezone.utc),
            'query': 'CREATE TABLE no_version_table;'
        })

        response = merge_branch(branch_id=self.BRANCH_ID_ACTIVE)
        self.assertEqual(response['status'], 'COMPLETED')

        # Verify the migration without version was not merged
        parent_migrations = DB['migrations'].get(self.PARENT_PROJECT_ID, [])
        self.assertFalse(any(m.get('name') == 'Migration Without Version' for m in parent_migrations))

    def test_merge_branch_edge_function_without_slug(self):
        """Test that edge functions without slug are skipped."""
        # Add an edge function without slug to the branch
        DB['edge_functions'][self.BRANCH_PROJECT_ID_1].append({
            'id': 'func_no_slug_id',
            'name': 'Function Without Slug',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'no slug content'}]
        })

        response = merge_branch(branch_id=self.BRANCH_ID_ACTIVE)
        self.assertEqual(response['status'], 'COMPLETED')

        # Verify the function without slug was not merged
        parent_functions = DB['edge_functions'].get(self.PARENT_PROJECT_ID, [])
        self.assertFalse(any(f.get('name') == 'Function Without Slug' for f in parent_functions))

    def test_merge_branch_edge_function_existing_slug_same_version(self):
        """Test that edge functions with existing slug and same version but different content raise conflict."""
        # Add an edge function to the parent project
        DB['edge_functions'][self.PARENT_PROJECT_ID].append({
            'id': 'func_existing_slug_id',
            'slug': 'existing-slug-func',
            'name': 'Existing Slug Function',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'parent content'}]
        })

        # Add the same function with same version but different content to the branch
        DB['edge_functions'][self.BRANCH_PROJECT_ID_1].append({
            'id': 'func_existing_slug_id_branch',
            'slug': 'existing-slug-func',
            'name': 'Existing Slug Function',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'branch content'}]
        })

        self.assert_error_behavior(
            func_to_call=merge_branch,
            expected_exception_type=custom_errors.MergeConflictError,
            expected_message="Edge function conflict detected for slug 'existing-slug-func'.",
            branch_id=self.BRANCH_ID_ACTIVE
        )

        # Verify the branch status was reverted
        branch = self._find_branch_in_db(self.BRANCH_ID_ACTIVE)
        self.assertEqual(branch['status'], 'ACTIVE_HEALTHY')
        
    def test_merge_branch_failed_to_apply_migration(self):
        """Test merge fails with MergeConflictError when apply_migration raises MigrationError."""
        migration_name = "Failing Migration"
        error_message = "Simulated migration failure."

        def selective_apply_migration_side_effect(project_id, name, query):
            if name == migration_name:
                raise custom_errors.MigrationError(error_message)
            return None # Successful migration for others
        
        DB['migrations'][self.BRANCH_PROJECT_ID_1].append({
            'version': 'mig_fails_to_apply',
            'name': migration_name,
            'status': 'APPLIED',
            'applied_at': datetime.now(timezone.utc),
            'query': 'SELECT * FROM non_existent_table;'
        })

        expected_message = f"Failed to apply migration '{migration_name}' to target project: {error_message}"

        with patch.object(database, 'apply_migration', side_effect=selective_apply_migration_side_effect):
            self.assert_error_behavior(
                func_to_call=merge_branch,
                expected_exception_type=custom_errors.MergeConflictError,
                expected_message=expected_message,
                branch_id=self.BRANCH_ID_ACTIVE
            )

        # Verify the branch status was reverted to its original state
        branch = self._find_branch_in_db(self.BRANCH_ID_ACTIVE)
        self.assertEqual(branch['status'], 'ACTIVE_HEALTHY')

    def test_merge_branch_edge_function_existing_slug_different_version(self):
        """Test that edge functions with existing slug but different version are merged successfully."""
        # Add an edge function to the parent project with version 1.0.0
        DB['edge_functions'][self.PARENT_PROJECT_ID].append({
            'id': 'func_version_update_id',
            'slug': 'version-update-func',
            'name': 'Version Update Function',
            'version': '1.0.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'old content'}]
        })

        # Add the same function with version 1.1.0 to the branch
        DB['edge_functions'][self.BRANCH_PROJECT_ID_1].append({
            'id': 'func_version_update_id_branch',
            'slug': 'version-update-func',
            'name': 'Version Update Function',
            'version': '1.1.0',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'entrypoint_path': 'index.ts',
            'import_map_path': 'import_map.json',
            'files': [{'name': 'index.js', 'content': 'new content'}]
        })

        response = merge_branch(branch_id=self.BRANCH_ID_ACTIVE)
        self.assertEqual(response['status'], 'COMPLETED')

        # Verify the newer version was merged
        parent_functions = DB['edge_functions'].get(self.PARENT_PROJECT_ID, [])
        updated_func = next((f for f in parent_functions if f['slug'] == 'version-update-func'), None)
        self.assertIsNotNone(updated_func)
        self.assertEqual(updated_func['version'], '1.1.0')
        self.assertEqual(updated_func['files'][0]['content'], 'new content')
        self.assertEqual(updated_func['status'], 'ACTIVE_HEALTHY')
        self.assertIsNotNone(updated_func['updated_at'])

    def test_merge_branch_unexpected_error(self):
        """Test that unexpected errors during merge are handled gracefully."""
        # Create a branch with valid data
        invalid_branch_id = "branch_invalid_data_xyz"
        DB['branches'][self.PARENT_PROJECT_ID].append({
            'id': invalid_branch_id,
            'name': 'Invalid Data Branch',
            'parent_project_id': self.PARENT_PROJECT_ID,
            'branch_project_id': self.BRANCH_PROJECT_ID_1,
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc),
            'last_activity_at': datetime.now(timezone.utc)
        })

        # Add an invalid migration that will cause an error during sorting
        # by making the version a non-string type that can't be compared
        DB['migrations'][self.BRANCH_PROJECT_ID_1].append({
            'version': {'invalid': 'version'},  # This will cause a TypeError during sorting
            'name': 'Invalid Migration',
            'status': 'APPLIED',
            'applied_at': datetime.now(timezone.utc),
            'query': 'CREATE TABLE invalid_table;'
        })

        response = merge_branch(branch_id=invalid_branch_id)
        
        # Verify the response indicates failure
        self.assertEqual(response['status'], 'FAILED')
        self.assertEqual(response['branch_id'], invalid_branch_id)
        self.assertEqual(response['target_project_id'], self.PARENT_PROJECT_ID)
        self.assertTrue(response.get('merge_request_id', '').startswith('mr_'))

        # Verify the branch status was updated to ERROR
        branch = self._find_branch_in_db(invalid_branch_id)
        self.assertIsNotNone(branch)
        self.assertEqual(branch['status'], 'ERROR')
        self.assertGreater(branch['last_activity_at'], self.initial_timestamp)

if __name__ == '__main__':
    unittest.main()