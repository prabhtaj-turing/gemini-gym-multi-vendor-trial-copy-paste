import unittest
import copy
from datetime import datetime, timezone
from typing import List
from ..SimulationEngine.duckdb_manager import get_duckdb_manager, SupabaseDuckDBManager
from ..SimulationEngine import custom_errors
from ..branch import reset_branch
from ..SimulationEngine.models import ResetBranchInputArgs
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError
import re
from ..database import execute_sql
from unittest.mock import patch

# Initial database state for reset_branch tests
RESET_BRANCH_INITIAL_DB_STATE = {
    "organizations": [
        {"id": "org1", "name": "Test Org 1", "created_at": datetime.now(timezone.utc), "subscription_plan": None}
    ],
    "projects": [
        {
            "id": "parent_proj_1", "name": "Parent Project 1", "organization_id": "org1",
            "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": datetime.now(timezone.utc), "version": "15"
        },
        {
            "id": "branch_db_1", "name": "DB for branch1", "organization_id": "org1",
            "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": datetime.now(timezone.utc), "version": "15"
        },
        {
            "id": "branch_db_2_empty_migrations", "name": "DB for branch2 (empty migrations)", "organization_id": "org1",
            "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": datetime.now(timezone.utc), "version": "15"
        },
        {
            "id": "branch_db_3_no_migration_key", "name": "DB for branch3 (no migration key)", "organization_id": "org1",
            "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": datetime.now(timezone.utc), "version": "15"
        }
    ],
    "branches": {
        "parent_proj_1": [
            {
                "id": "branch1_std", "name": "dev-main", "parent_project_id": "parent_proj_1",
                "branch_project_id": "branch_db_1", "status": "ACTIVE_HEALTHY",
                "created_at": datetime.now(timezone.utc), "last_activity_at": datetime.now(timezone.utc)
            },
            {
                "id": "branch2_empty_migrations", "name": "feat-empty", "parent_project_id": "parent_proj_1",
                "branch_project_id": "branch_db_2_empty_migrations", "status": "UPDATING",
                "created_at": datetime.now(timezone.utc), "last_activity_at": datetime.now(timezone.utc)
            },
             {
                "id": "branch3_no_migration_key", "name": "feat-no-key", "parent_project_id": "parent_proj_1",
                "branch_project_id": "branch_db_3_no_migration_key", "status": "ACTIVE_HEALTHY",
                "created_at": datetime.now(timezone.utc), "last_activity_at": datetime.now(timezone.utc)
            }
        ]
    },
    "migrations": {
        "branch_db_1": [
            {"version": "m0_base", "name": "Base Schema", "status": "applied", "applied_at": datetime.now(timezone.utc), 
            "query": "CREATE SCHEMA IF NOT EXISTS base_schema; CREATE TABLE IF NOT EXISTS base_schema.dummy_table (id INTEGER);"},
            {"version": "m1_users", "name": "Add Users Table", "status": "applied", "applied_at": datetime.now(timezone.utc), 
            "query": "CREATE TABLE IF NOT EXISTS public.users (user_id INTEGER PRIMARY KEY, email VARCHAR UNIQUE, created_at TIMESTAMP);"},
            {"version": "m2_posts", "name": "Add Posts Table", "status": "applied", "applied_at": datetime.now(timezone.utc), 
            "query": "CREATE TABLE IF NOT EXISTS public.posts (post_id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES public.users(user_id), content TEXT);"},
            {"version": "m3_comments", "name": "Add Comments Table", "status": "pending", "applied_at": None, 
            "query": "CREATE TABLE IF NOT EXISTS public.comments (comment_id INTEGER PRIMARY KEY, post_id INTEGER REFERENCES public.posts(post_id), comment_text TEXT);"}
        ],
        "branch_db_2_empty_migrations": [],
    },
    "tables": {},
    "extensions": {},
    "edge_functions": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {},
    "project_anon_keys": {},
    "project_ts_types": {},
    "logs": {}
}

class TestResetBranch(BaseTestCaseWithErrorHandler):

    @classmethod
    def setUpClass(cls):
        """Save original DB state."""
        cls.original_db_state = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Set up a fresh DB state and manager for each test."""
        DB.clear()
        DB.update(copy.deepcopy(RESET_BRANCH_INITIAL_DB_STATE))
        self.manager = get_duckdb_manager()
        self.manager.close_all_connections()

    def tearDown(self):
        """Clean up DuckDB manager connections after each test."""
        self.manager.close_all_connections()

    def _find_branch_in_db(self, branch_id: str):
        for _, branch_list in DB.get("branches", {}).items():
            for branch in branch_list:
                if branch["id"] == branch_id:
                    return branch
        return None

    def test_reset_branch_success_no_migration_version(self):
        branch_id = "branch1_std"
        branch = self._find_branch_in_db(branch_id)
        self.assertIsNotNone(branch, "Test setup error: branch not found.")
        branch_project_id = branch["branch_project_id"]

        result = reset_branch(branch_id=branch_id)

        expected_result = {
            "branch_id": branch_id,
            "status": "COMPLETED",
            "target_migration_version": None
        }
        self.assertEqual(result, expected_result)

        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], "ACTIVE_HEALTHY")

        migrations = DB["migrations"][branch_project_id]
        for mig in migrations:
            self.assertEqual(mig["status"], "pending", f"Migration {mig['version']} should be pending.")
            self.assertIsNone(mig["applied_at"], f"Migration {mig['version']} applied_at should be None.")

    def test_reset_branch_success_with_specific_migration_version(self):
        branch_id = "branch1_std"
        target_version = "m1_users"
        branch = self._find_branch_in_db(branch_id)
        self.assertIsNotNone(branch, "Test setup error: branch not found.")
        branch_project_id = branch["branch_project_id"]

        result = reset_branch(branch_id=branch_id, migration_version=target_version)

        expected_result = {
            "branch_id": branch_id,
            "status": "COMPLETED",
            "target_migration_version": target_version
        }
        self.assertEqual(result, expected_result)

        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], "ACTIVE_HEALTHY")

        migrations = DB["migrations"][branch_project_id] # Assumes this list is ordered
        apply_until_target = True
        for mig in migrations:
            current_mig_status = "pending" # Default for after target
            if apply_until_target:
                current_mig_status = "applied"
                if mig["version"] == target_version:
                    apply_until_target = False
            
            self.assertEqual(mig["status"], current_mig_status, f"Migration {mig['version']} status incorrect.")
            if current_mig_status == "applied":
                self.assertIsNotNone(mig["applied_at"], f"Migration {mig['version']} applied_at should not be None for applied status.")
            else:
                self.assertIsNone(mig["applied_at"], f"Migration {mig['version']} applied_at should be None for pending status.")

    def test_reset_branch_to_latest_applied_migration_version(self):
        branch_id = "branch1_std"
        target_version = "m2_posts" # Initially applied in setup
        branch = self._find_branch_in_db(branch_id)
        self.assertIsNotNone(branch, "Test setup error: branch not found.")
        branch_project_id = branch["branch_project_id"]

        result = reset_branch(branch_id=branch_id, migration_version=target_version)
        self.assertEqual(result["target_migration_version"], target_version)

        migrations = DB["migrations"][branch_project_id]
        expected_statuses = {"m0_base": "applied", "m1_users": "applied", "m2_posts": "applied", "m3_comments": "pending"}
        for mig in migrations:
            self.assertEqual(mig["status"], expected_statuses[mig["version"]])
            if expected_statuses[mig["version"]] == "applied":
                self.assertIsNotNone(mig["applied_at"])
            else:
                self.assertIsNone(mig["applied_at"])

    def test_reset_branch_non_existent_branch_id_raises_notfounderror(self):
        branch_id = "non_existent_branch"
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Branch with ID '{branch_id}' not found.",
            branch_id=branch_id
        )

    def test_reset_branch_invalid_migration_version_raises_notfounderror(self):
        branch_id = "branch1_std"
        migration_version = "invalid_mv_id"
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Target migration version '{migration_version}' not found in sequence.",
            branch_id=branch_id,
            migration_version=migration_version
        )

    def test_reset_branch_empty_branch_id_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character", # Substring match for Pydantic
            branch_id=""
        )

    def test_reset_branch_invalid_branch_id_type_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string", # Substring match
            branch_id=123
        )

    def test_reset_branch_invalid_migration_version_type_raises_validationerror(self):
        branch_id = "branch1_std"
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string", # Substring match
            branch_id=branch_id,
            migration_version=12345
        )

    def test_reset_branch_success_for_branch_with_empty_migrations_list_no_version(self):
        branch_id = "branch2_empty_migrations"
        
        result = reset_branch(branch_id=branch_id)
        expected_result = {
            "branch_id": branch_id,
            "status": "COMPLETED",
            "target_migration_version": None
        }
        self.assertEqual(result, expected_result)
        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], "ACTIVE_HEALTHY")

        branch_project_id = updated_branch["branch_project_id"]
        self.assertEqual(DB["migrations"][branch_project_id], [])

    def test_reset_branch_error_for_branch_with_empty_migrations_list_with_version(self):
        branch_id = "branch2_empty_migrations"
        migration_version = "some_version"
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Migration version '{migration_version}' not found for branch '{branch_id}'",
            branch_id=branch_id,
            migration_version=migration_version
        )

    def test_reset_branch_success_for_branch_with_no_migrations_key_no_version(self):
        branch_id = "branch3_no_migration_key"
        
        result = reset_branch(branch_id=branch_id)
        expected_result = {
            "branch_id": branch_id,
            "status": "COMPLETED",
            "target_migration_version": None
        }
        self.assertEqual(result, expected_result)
        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], "ACTIVE_HEALTHY")

        branch_project_id = updated_branch["branch_project_id"]
        self.assertNotIn(branch_project_id, DB["migrations"])

    def test_reset_branch_error_for_branch_with_no_migrations_key_with_version(self):
        branch_id = "branch3_no_migration_key"
        migration_version = "any_version"
        self.assert_error_behavior(
            func_to_call=reset_branch,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Migration version '{migration_version}' not found for branch '{branch_id}'",
            branch_id=branch_id,
            migration_version=migration_version
        )

    def test_reset_branch_to_first_migration_version(self):
        branch_id = "branch1_std"
        target_version = "m0_base"
        branch = self._find_branch_in_db(branch_id)
        self.assertIsNotNone(branch, "Test setup error: branch not found.")
        branch_project_id = branch["branch_project_id"]

        result = reset_branch(branch_id=branch_id, migration_version=target_version)
        self.assertEqual(result["target_migration_version"], target_version)

        migrations = DB["migrations"][branch_project_id]
        expected_statuses = {"m0_base": "applied", "m1_users": "pending", "m2_posts": "pending", "m3_comments": "pending"}
        for mig in migrations:
            self.assertEqual(mig["status"], expected_statuses[mig["version"]])
            if expected_statuses[mig["version"]] == "applied":
                self.assertIsNotNone(mig["applied_at"])
            else:
                self.assertIsNone(mig["applied_at"])

    def test_reset_branch_updates_branch_status_from_non_active(self):
        branch_id = "branch2_empty_migrations" # Initial status is 'UPDATING'
        initial_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(initial_branch["status"], "UPDATING")

        result = reset_branch(branch_id=branch_id)
        self.assertEqual(result["status"], "COMPLETED")
        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], "ACTIVE_HEALTHY")

    def test_reset_branch_api_error_on_migration_sort_type_error(self):
        """Test that ApiError is raised for TypeError during migration version sorting."""
        branch_id = "branch1_std"
        branch = self._find_branch_in_db(branch_id)
        self.assertIsNotNone(branch)
        branch_project_id = branch["branch_project_id"]

        # Introduce an incompatible migration version type to cause a TypeError on sort
        DB["migrations"][branch_project_id].append(
            {'version': 9999, 'name': 'Int Version', 'status': 'applied', 'query': 'SELECT 1;'}
        )
        original_status = branch["status"]

        with self.assertRaises(custom_errors.ApiError) as cm:
            reset_branch(branch_id=branch_id, migration_version="m1_users")

        expected_error_msg = f"Internal error: Could not sort migration versions for project '{branch_project_id}'."
        self.assertEqual(str(cm.exception), expected_error_msg)

        # Verify that the branch status was reverted
        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], original_status)

        # Cleanup
        DB["migrations"][branch_project_id].pop()

    def test_reset_branch_migration_missing_query_raises_migrationerror(self):
        """
        Test that reset_branch raises MigrationError if a migration is missing its SQL query.
        """
        branch_id = "branch1_std"
        branch = self._find_branch_in_db(branch_id)
        self.assertIsNotNone(branch)
        branch_project_id = branch["branch_project_id"]

        # Add a migration with a missing query.
        malformed_migration = {
            "version": "m4_no_query",
            "name": "No Query Migration",
            "status": "applied",
            "query": None
        }
        DB["migrations"][branch_project_id].append(malformed_migration)

        expected_message = f"Migration '{malformed_migration['name']}' is missing its SQL query."

        with self.assertRaises(custom_errors.MigrationError) as cm:
            reset_branch(branch_id=branch_id, migration_version=malformed_migration["version"])

        self.assertEqual(str(cm.exception), expected_message)

        # Cleanup
        DB["migrations"][branch_project_id].pop()

    def test_reset_branch_verifies_schema_changes(self):
        """Verify that migrations applied during reset have a real effect on the database."""
        branch_id = "branch1_std"
        target_version = "m2_posts"
        branch = self._find_branch_in_db(branch_id)
        branch_project_id = branch["branch_project_id"]

        # Act: Reset the branch to a specific migration
        reset_branch(branch_id=branch_id, migration_version=target_version)

        # Assert: Check the actual database schema
        users_table_query = "SELECT table_name FROM information_schema.tables WHERE table_name = 'users' AND table_schema = 'public'"
        posts_table_query = "SELECT table_name FROM information_schema.tables WHERE table_name = 'posts' AND table_schema = 'public'"
        
        users_result = self.manager.execute_query(project_id=branch_project_id, query=users_table_query)
        posts_result = self.manager.execute_query(project_id=branch_project_id, query=posts_table_query)

        self.assertEqual(users_result["row_count"], 1, "The 'users' table should exist after reset.")
        self.assertEqual(posts_result["row_count"], 1, "The 'posts' table should exist after reset.")

        # The 'comments' table should NOT exist as it's after the target version
        comments_table_query = "SELECT table_name FROM information_schema.tables WHERE table_name = 'comments' AND table_schema = 'public'"
        comments_result = self.manager.execute_query(project_id=branch_project_id, query=comments_table_query)
        
        self.assertEqual(comments_result["row_count"], 0, "The 'comments' table should not exist after reset to an earlier migration.")

    def test_reset_branch_migration_error_handling(self):
        """Test various error conditions during the migration process of a branch reset."""
        branch_id = "branch1_std"
        branch = self._find_branch_in_db(branch_id)
        branch_project_id = branch["branch_project_id"]

        # Test case for TypeError during sorting
        DB["migrations"][branch_project_id].append({'version': 12345, 'name': 'Invalid Version Type', 'status': 'applied', 'query': 'SELECT 1'})
        with self.assertRaises(custom_errors.ApiError) as context:
            reset_branch(branch_id=branch_id, migration_version="m2_posts")
        self.assertIn("Could not sort migration versions", str(context.exception))
        DB["migrations"][branch_project_id].pop() # Clean up

        # Test case for missing query in migration
        DB["migrations"][branch_project_id].append({'version': 'm4_no_query', 'name': 'No Query Migration', 'status': 'applied', 'query': None})
        with self.assertRaises(custom_errors.MigrationError) as context:
            reset_branch(branch_id=branch_id, migration_version="m4_no_query")
        self.assertIn("is missing its SQL query", str(context.exception))
        DB["migrations"][branch_project_id].pop() # Clean up

        # Test case for unexpected error during migration
        with patch('supabase.SimulationEngine.duckdb_manager.SupabaseDuckDBManager.execute_query', side_effect=Exception("Unexpected DB error")):
            with self.assertRaises(custom_errors.MigrationError) as context:
                reset_branch(branch_id=branch_id, migration_version="m1_users")
            self.assertIn("Failed to apply migration", str(context.exception))

        def test_reset_branch_missing_branch_project_id(self):
            """Test that ApiError is raised if a branch is missing 'branch_project_id'."""
            branch_id = "branch_missing_bpid"
            # Add a malformed branch to the DB for this test
            DB["branches"]["parent_proj_1"].append({
                "id": branch_id,
                "name": "Branch Without BPID",
                "parent_project_id": "parent_proj_1",
                # "branch_project_id" is intentionally missing
                "status": "ACTIVE_HEALTHY",
                "created_at": datetime.now(timezone.utc),
                "last_activity_at": datetime.now(timezone.utc)
            })

            self.assert_error_behavior(
                func_to_call=reset_branch,
                expected_exception_type=custom_errors.ApiError,
                expected_message=f"Branch '{branch_id}' is missing 'branch_project_id'.",
                branch_id=branch_id
            )

    def test_reset_branch_schema_reset_failure(self):
        """Test that ApiError is raised when the schema reset fails."""
        branch_id = "branch1_std"
        branch = self._find_branch_in_db(branch_id)
        branch_project_id = branch["branch_project_id"]
        error_message = "Simulated DB schema reset failure."

        with patch.object(self.manager, 'reset_project_schema', side_effect=Exception(error_message)):
            self.assert_error_behavior(
                func_to_call=reset_branch,
                expected_exception_type=custom_errors.ApiError,
                expected_message=f"Failed to reset underlying database schema for project '{branch_project_id}': {error_message}",
                branch_id=branch_id
            )

        # Verify the branch status was reverted to its original state
        updated_branch = self._find_branch_in_db(branch_id)
        self.assertEqual(updated_branch["status"], "ACTIVE_HEALTHY")


if __name__ == '__main__':
    unittest.main()