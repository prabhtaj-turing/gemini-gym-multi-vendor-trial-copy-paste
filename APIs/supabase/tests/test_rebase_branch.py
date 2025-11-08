import unittest
import copy
from datetime import datetime, timezone
from ..SimulationEngine import custom_errors
from ..branch import rebase_branch
from typing import Optional, Dict, Any
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Assume DB, rebase_branch, BaseTestCaseWithErrorHandler are globally available
# For local testing, these would need to be defined or mocked.

class TestRebaseBranch(BaseTestCaseWithErrorHandler):

    def _get_branch_from_db(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """Helper to retrieve a branch from the DB for assertions."""
        for _, branches_list in DB.get('branches', {}).items(): # Iterate through lists of branches per parent project
            for branch in branches_list:
                if branch['id'] == branch_id:
                    return branch
        return None

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.parent_project_id = "proj_parent_main_abc123"
        self.org_id = "org_test_rebase_xyz789"
        self.now = datetime.now(timezone.utc)

        DB['organizations'] = [
            {"id": self.org_id, "name": "Test Org Rebase", "created_at": self.now, "subscription_plan": None}
        ]
        DB['projects'] = [
            {"id": self.parent_project_id, "name": "Parent Project", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_active", "name": "DB Active Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_uptodate", "name": "DB Up-to-date Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_conflict", "name": "DB Conflict Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_local_changes", "name": "DB Local Changes Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_creating", "name": "DB Creating Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_merging", "name": "DB Merging Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_already_rebasing", "name": "DB Already Rebasing Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
            {"id": "db_branch_error_state", "name": "DB Error State Branch", "organization_id": self.org_id, "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.now, "version": "15"},
        ]

        DB['branches'] = {
            self.parent_project_id: [
                {"id": "branch_active_1", "name": "Active Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_active", "status": "ACTIVE_HEALTHY", "created_at": self.now, "last_activity_at": self.now},
                {"id": "branch_uptodate_1", "name": "Up-to-date Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_uptodate", "status": "ACTIVE_HEALTHY", "created_at": self.now, "last_activity_at": self.now},
                {"id": "branch_conflict_1", "name": "Conflict Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_conflict", "status": "ACTIVE_HEALTHY", "created_at": self.now, "last_activity_at": self.now},
                {"id": "branch_local_changes_1", "name": "Local Changes Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_local_changes", "status": "ACTIVE_HEALTHY", "created_at": self.now, "last_activity_at": self.now, "internal_props": {"has_uncommitted_schema_changes": True}}, # Hypothetical property
                {"id": "branch_creating_1", "name": "Creating Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_creating", "status": "CREATING", "created_at": self.now, "last_activity_at": self.now},
                {"id": "branch_merging_1", "name": "Merging Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_merging", "status": "MERGING", "created_at": self.now, "last_activity_at": self.now},
                {"id": "branch_already_rebasing_1", "name": "Already Rebasing Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_already_rebasing", "status": "REBASING", "created_at": self.now, "last_activity_at": self.now},
                {"id": "branch_error_1", "name": "Error Branch", "parent_project_id": self.parent_project_id, "branch_project_id": "db_branch_error_state", "status": "ERROR", "created_at": self.now, "last_activity_at": self.now},
            ]
        }
        DB['migrations'] = {
            self.parent_project_id: [
                {"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now, "query": "CREATE TABLE t1 (id int);"},
                {"version": "p_v2", "name": "P M2", "status": "applied", "applied_at": self.now, "query": "ALTER TABLE t1 ADD COLUMN c1 text;"},
                {"version": "p_v3", "name": "P M3", "status": "applied", "applied_at": self.now, "query": "CREATE TABLE t2 (id int);"}, # Newest on parent
            ],
            "db_branch_active": [ # Behind parent
                {"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now}, {"version": "p_v2", "name": "P M2", "status": "applied", "applied_at": self.now},
            ],
            "db_branch_uptodate": [ # Same as parent
                {"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now}, {"version": "p_v2", "name": "P M2", "status": "applied", "applied_at": self.now}, {"version": "p_v3", "name": "P M3", "status": "applied", "applied_at": self.now},
            ],
            "db_branch_conflict": [ # Has conflicting local migration that would clash with parent's p_v2 or p_v3
                {"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now}, {"version": "b_v_conflict", "name": "Branch Conflict Mig", "status": "applied", "applied_at": self.now, "query": "ALTER TABLE t1 DROP COLUMN c1;"}, # Conflicts with p_v2
            ],
            "db_branch_local_changes": [{"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now}], # Standard migrations, but branch has 'internal_props' flag
            "db_branch_creating": [], "db_branch_merging": [], "db_branch_already_rebasing": [], "db_branch_error_state": [],
        }
        # Initialize other potentially accessed keys to prevent KeyErrors in the function under test
        DB["tables"] = {}
        DB["extensions"] = {}
        DB["edge_functions"] = {}
        DB["costs"] = {}
        DB["unconfirmed_costs"] = {}
        DB["project_urls"] = {}
        DB["project_anon_keys"] = {}
        DB["project_ts_types"] = {}
        DB["logs"] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_rebase_successful_applies_migrations(self):
        branch_id = "branch_active_1"
        response = rebase_branch(branch_id=branch_id)

        self.assertEqual(response['branch_id'], branch_id)
        self.assertEqual(response['status'], 'COMPLETED')
        self.assertIsInstance(response['rebase_operation_id'], str)
        self.assertTrue(len(response['rebase_operation_id']) > 0, "Rebase operation ID should not be empty.")

        updated_branch_in_db = self._get_branch_from_db(branch_id)
        self.assertIsNotNone(updated_branch_in_db)
        self.assertEqual(updated_branch_in_db['status'], 'ACTIVE_HEALTHY')
        
        # Verify that migrations were actually applied to the branch project
        dev_project_id = updated_branch_in_db['branch_project_id']
        dev_migrations = DB.get('migrations', {}).get(dev_project_id, [])
        
        # Should have the original migrations plus the rebased ones
        migration_versions = [m.get('version') for m in dev_migrations]
        self.assertIn('p_v1', migration_versions)  # Original
        self.assertIn('p_v2', migration_versions)  # Original
        
        # Should have new migrations applied from production (p_v3)
        rebased_migrations = [m for m in dev_migrations if m.get('name', '').startswith('rebased_from_prod_')]
        self.assertTrue(len(rebased_migrations) > 0, "Should have rebased migrations from production")

    def test_rebase_successful_already_uptodate_completes(self):
        branch_id = "branch_uptodate_1"
        response = rebase_branch(branch_id=branch_id)

        self.assertEqual(response['branch_id'], branch_id)
        self.assertEqual(response['status'], 'COMPLETED')
        if response['rebase_operation_id'] is not None: # Optional for COMPLETED
            self.assertIsInstance(response['rebase_operation_id'], str)

        updated_branch_in_db = self._get_branch_from_db(branch_id)
        self.assertIsNotNone(updated_branch_in_db)
        # If rebase completes synchronously, branch should be in a stable, usable state.
        self.assertEqual(updated_branch_in_db['status'], 'ACTIVE_HEALTHY')

    def test_rebase_branch_not_found(self):
        non_existent_branch_id = "branch_that_does_not_exist"
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"Branch with ID '{non_existent_branch_id}' not found.",
            branch_id=non_existent_branch_id
        )

    def test_rebase_invalid_branch_id_empty(self):
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: branch_id cannot be empty.", # Example message
            branch_id=""
        )

    def test_rebase_invalid_branch_id_none(self):
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: branch_id must be a string.", # Example message
            branch_id=None
        )

    def test_rebase_conflict_error(self):
        branch_id_conflict = "branch_conflict_1"
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.RebaseConflictError,
            expected_message=f"Rebase failed for branch '{branch_id_conflict}' due to migration conflicts.", # Example message
            branch_id=branch_id_conflict
        )
        branch_after_attempt = self._get_branch_from_db(branch_id_conflict)
        self.assertIsNotNone(branch_after_attempt)
        self.assertEqual(branch_after_attempt['status'], 'ACTIVE_HEALTHY', "Branch status should not change on conflict error.")


    def test_rebase_operation_not_permitted_status_creating(self):
        branch_id_creating = "branch_creating_1"
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{branch_id_creating}' is not in a rebasable state (current status: CREATING).",
            branch_id=branch_id_creating
        )

    def test_rebase_operation_not_permitted_status_merging(self):
        branch_id_merging = "branch_merging_1"
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{branch_id_merging}' is not in a rebasable state (current status: MERGING).",
            branch_id=branch_id_merging
        )

    def test_rebase_operation_not_permitted_status_already_rebasing(self):
        branch_id_rebasing = "branch_already_rebasing_1"
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{branch_id_rebasing}' is not in a rebasable state (current status: REBASING).",
            branch_id=branch_id_rebasing
        )

    def test_rebase_operation_not_permitted_status_error(self):
        branch_id_error = "branch_error_1"
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{branch_id_error}' is not in a rebasable state (current status: ERROR).",
            branch_id=branch_id_error
        )

    def test_rebase_operation_not_permitted_local_changes(self):
        branch_id_local_changes = "branch_local_changes_1"
        # This test relies on the 'internal_props': {'has_uncommitted_schema_changes': True}
        # in the branch setup, or equivalent internal logic in the rebase_branch function.
        self.assert_error_behavior(
            func_to_call=rebase_branch,
            expected_exception_type=custom_errors.OperationNotPermittedError,
            expected_message=f"Branch '{branch_id_local_changes}' has local changes not captured in migrations and cannot be rebased.",
            branch_id=branch_id_local_changes
        )
        branch_after_attempt = self._get_branch_from_db(branch_id_local_changes)
        self.assertIsNotNone(branch_after_attempt)
        self.assertEqual(branch_after_attempt['status'], 'ACTIVE_HEALTHY', "Branch status should not change on this error.")

    def test_rebase_with_malformed_db_branches_not_dict(self):
        """Test coverage for line 19: when DB['branches'] is not a dict"""
        # Temporarily corrupt the DB structure
        original_branches = DB.get('branches')
        DB['branches'] = "not_a_dict"  # Make it a string instead of dict
        
        try:
            self.assert_error_behavior(
                func_to_call=rebase_branch,
                expected_exception_type=custom_errors.ResourceNotFoundError,
                expected_message="Branch with ID 'any_branch' not found.",
                branch_id="any_branch"
            )
        finally:
            # Restore original branches
            DB['branches'] = original_branches

    def test_rebase_with_malformed_db_branches_list_not_list(self):
        """Test coverage for line 25: when branches_list under a project is not a list"""
        # Temporarily corrupt the DB structure
        original_branches = DB.get('branches')
        DB['branches'] = {
            self.parent_project_id: "not_a_list",  # Make it a string instead of list
            "another_project": []
        }
        
        try:
            self.assert_error_behavior(
                func_to_call=rebase_branch,
                expected_exception_type=custom_errors.ResourceNotFoundError,
                expected_message="Branch with ID 'any_branch' not found.",
                branch_id="any_branch"
            )
        finally:
            # Restore original branches
            DB['branches'] = original_branches

    def test_rebase_with_dev_project_no_existing_migrations(self):
        """Test coverage for line 104: when dev project has no migrations list in DB"""
        # Create a branch with a dev project that has no migrations
        test_branch_id = "branch_no_migrations"
        test_dev_project_id = "db_branch_no_migrations"
        
        # Add the branch to DB
        DB['branches'][self.parent_project_id].append({
            "id": test_branch_id,
            "name": "No Migrations Branch",
            "parent_project_id": self.parent_project_id,
            "branch_project_id": test_dev_project_id,
            "status": "ACTIVE_HEALTHY",
            "created_at": self.now,
            "last_activity_at": self.now
        })
        
        # Add the dev project but ensure it has NO entry in migrations
        DB['projects'].append({
            "id": test_dev_project_id,
            "name": "DB No Migrations Branch",
            "organization_id": self.org_id,
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": self.now,
            "version": "15"
        })
        
        # Make sure the dev project is NOT in migrations (this triggers line 104)
        if test_dev_project_id in DB.get('migrations', {}):
            del DB['migrations'][test_dev_project_id]
        
        try:
            # This should trigger the line 104: all_migrations_in_db[dev_project_id] = []
            response = rebase_branch(branch_id=test_branch_id)
            
            # Should complete rebasing since parent has migrations but dev project had none
            self.assertEqual(response['branch_id'], test_branch_id)
            self.assertEqual(response['status'], 'COMPLETED')
            self.assertIsInstance(response['rebase_operation_id'], str)
            
            # Verify the dev project now has migrations applied from production
            self.assertIn(test_dev_project_id, DB['migrations'])
            dev_migrations = DB['migrations'][test_dev_project_id]
            
            # Should have rebased migrations from production
            rebased_migrations = [m for m in dev_migrations if m.get('name', '').startswith('rebased_from_prod_')]
            self.assertTrue(len(rebased_migrations) > 0, "Should have rebased migrations from production")
            
        finally:
            # Clean up the test data
            DB['branches'][self.parent_project_id] = [
                b for b in DB['branches'][self.parent_project_id] 
                if b.get('id') != test_branch_id
            ]
            DB['projects'] = [
                p for p in DB['projects'] 
                if p.get('id') != test_dev_project_id
            ]
            if test_dev_project_id in DB.get('migrations', {}):
                del DB['migrations'][test_dev_project_id]

    def test_rebase_migration_conflict_during_application(self):
        """Test that migration conflicts during actual application are handled properly."""
        # Create a test branch with a conflicting migration setup
        test_branch_id = "branch_migration_conflict"
        test_dev_project_id = "db_branch_migration_conflict"
        
        # Add the branch to DB
        DB['branches'][self.parent_project_id].append({
            "id": test_branch_id,
            "name": "Migration Conflict Branch",
            "parent_project_id": self.parent_project_id,
            "branch_project_id": test_dev_project_id,
            "status": "ACTIVE_HEALTHY",
            "created_at": self.now,
            "last_activity_at": self.now
        })
        
        # Add the dev project 
        DB['projects'].append({
            "id": test_dev_project_id,
            "name": "DB Migration Conflict Branch",
            "organization_id": self.org_id,
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": self.now,
            "version": "15"
        })
        
        # Set up migrations that will cause a conflict when applied
        DB['migrations'][test_dev_project_id] = [
            {"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now, "query": "CREATE TABLE t1 (id int);"},
            {"version": "conflicting_migration", "name": "Conflicting Migration", "status": "applied", "applied_at": self.now, "query": "CREATE TABLE t2 (name text);"}  # This will conflict with production's p_v3
        ]
        
        try:
            # This should fail due to migration conflict during application
            with self.assertRaises(custom_errors.RebaseConflictError) as context:
                rebase_branch(branch_id=test_branch_id)
            
            # Check that the error message contains the expected text
            error_message = str(context.exception)
            self.assertIn(f"Rebase failed for branch '{test_branch_id}' due to migration conflict", error_message)
            
            # Verify branch status was set to ERROR due to migration failure
            updated_branch = self._get_branch_from_db(test_branch_id)
            self.assertEqual(updated_branch['status'], 'ERROR')
            
        finally:
            # Clean up the test data
            DB['branches'][self.parent_project_id] = [
                b for b in DB['branches'][self.parent_project_id] 
                if b.get('id') != test_branch_id
            ]
            DB['projects'] = [
                p for p in DB['projects'] 
                if p.get('id') != test_dev_project_id
            ]
            if test_dev_project_id in DB.get('migrations', {}):
                del DB['migrations'][test_dev_project_id]

    def test_rebase_skips_migration_without_query(self):
        """Test coverage for line 151: when a migration has no query field."""
        test_branch_id = "branch_no_query"
        test_dev_project_id = "db_branch_no_query"
        
        # Add the branch to DB
        DB['branches'][self.parent_project_id].append({
            "id": test_branch_id,
            "name": "No Query Branch",
            "parent_project_id": self.parent_project_id,
            "branch_project_id": test_dev_project_id,
            "status": "ACTIVE_HEALTHY",
            "created_at": self.now,
            "last_activity_at": self.now
        })
        
        # Add the dev project
        DB['projects'].append({
            "id": test_dev_project_id,
            "name": "DB No Query Branch",
            "organization_id": self.org_id,
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": self.now,
            "version": "15"
        })
        
        # Set up production migration with empty query (triggers line 151)
        DB['migrations'][self.parent_project_id].append({
            "version": "p_v4", 
            "name": "P M4 No Query", 
            "status": "applied", 
            "applied_at": self.now, 
            "query": ""  # Empty query - should trigger continue on line 151
        })
        
        # Dev project has all migrations except the no-query one (so only p_v4 will be considered for rebase)
        DB['migrations'][test_dev_project_id] = [
            {"version": "p_v1", "name": "P M1", "status": "applied", "applied_at": self.now},
            {"version": "p_v2", "name": "P M2", "status": "applied", "applied_at": self.now},
            {"version": "p_v3", "name": "P M3", "status": "applied", "applied_at": self.now}
        ]
        
        try:
            # Should complete successfully, skipping the migration without query
            response = rebase_branch(branch_id=test_branch_id)
            
            self.assertEqual(response['branch_id'], test_branch_id)
            self.assertEqual(response['status'], 'COMPLETED')
            self.assertIsInstance(response['rebase_operation_id'], str)
            
            # Verify branch status is ACTIVE
            updated_branch = self._get_branch_from_db(test_branch_id)
            self.assertEqual(updated_branch['status'], 'ACTIVE_HEALTHY')
            
        finally:
            # Clean up the test data
            DB['branches'][self.parent_project_id] = [
                b for b in DB['branches'][self.parent_project_id] 
                if b.get('id') != test_branch_id
            ]
            DB['projects'] = [
                p for p in DB['projects'] 
                if p.get('id') != test_dev_project_id
            ]
            if test_dev_project_id in DB.get('migrations', {}):
                del DB['migrations'][test_dev_project_id]
            # Remove the test migration from production
            DB['migrations'][self.parent_project_id] = [
                m for m in DB['migrations'][self.parent_project_id] 
                if m.get('version') != 'p_v4'
            ]

    def test_rebase_unexpected_error_during_migration(self):
        """
        Tests that a non-MigrationError during migration application is wrapped
        in RebaseConflictError and sets branch status to 'ERROR'. This covers the
        generic 'except Exception' block in the rebase_branch function.
        """
        branch_id_for_test = "branch_active_1"
        
        # Corrupt the branch data so that apply_migration receives an invalid
        # project_id, causing a TypeError when it's used as a dict key.
        # This will trigger the generic 'except Exception' block.
        branch_to_corrupt = self._get_branch_from_db(branch_id_for_test)
        self.assertIsNotNone(branch_to_corrupt)
        branch_to_corrupt['branch_project_id'] = None
        
        # Expect a RebaseConflictError that wraps the original unexpected error
        with self.assertRaises(custom_errors.RebaseConflictError) as context:
            rebase_branch(branch_id=branch_id_for_test)
        
        # Verify the exception message to ensure it's from the correct code path
        self.assertIn(
            f"Rebase failed for branch '{branch_id_for_test}' with unexpected error",
            str(context.exception)
        )
        
        # Check that the branch status was set to 'ERROR' as per the exception handler
        branch_after_attempt = self._get_branch_from_db(branch_id_for_test)
        self.assertIsNotNone(branch_after_attempt)
        self.assertEqual(branch_after_attempt['status'], 'ERROR')


if __name__ == '__main__':
    unittest.main()