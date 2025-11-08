import unittest
import copy
from datetime import datetime
from unittest.mock import patch, MagicMock

from supabase.SimulationEngine import custom_errors
from supabase.SimulationEngine.db import DB
from supabase.SimulationEngine.duckdb_manager import get_duckdb_manager
from supabase.database import apply_migration
from common_utils.base_case import BaseTestCaseWithErrorHandler


# Initial database state for apply_migration tests
APPLY_MIGRATION_INITIAL_DB_STATE = {
    "organizations": [
        {
            "id": "org_test",
            "name": "Test Organization",
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
            "name": "Active Test Project",
            "organization_id": "org_test",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-02-01T09:00:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_inactive",
            "name": "Inactive Test Project",
            "organization_id": "org_test",
            "region": "us-west-2",
            "status": "INACTIVE",
            "created_at": "2023-02-15T10:00:00Z",
            "version": "PostgreSQL 14"
        }
    ],
    "tables": {
        "proj_active": [
            {
                "name": "users",
                "schema": "public",
                "comment": "Existing users table",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "uuid",
                        "is_nullable": False,
                        "default_value": "gen_random_uuid()"
                    },
                    {
                        "name": "email",
                        "data_type": "text",
                        "is_nullable": False,
                        "default_value": None
                    }
                ],
                "primary_keys": [{"name": "id"}],
                "relationships": []
            }
        ]
    },
    "extensions": {},
    "migrations": {
        "proj_active": [],  # Start with empty migrations
        "proj_inactive": []  # Also initialize for inactive project
    },
    "edge_functions": {},
    "branches": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {},
    "project_anon_keys": {},
    "project_ts_types": {},
    "logs": {}
}


class TestApplyMigration(BaseTestCaseWithErrorHandler):
    """Test suite for the apply_migration function."""

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(APPLY_MIGRATION_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Reset migrations for clean state for each test."""
        # Reset migrations for clean state
        DB["migrations"]["proj_active"] = []
        
        # Clear any DuckDB connections to ensure clean database state between tests
        manager = get_duckdb_manager()
        manager.close_all_connections()

    # Success test cases
    def test_apply_migration_create_table_success(self):
        """Test successful migration that creates a new table."""
        project_id = "proj_active"
        migration_name = "create_posts_table"
        migration_query = "CREATE TABLE posts (id SERIAL PRIMARY KEY, title TEXT NOT NULL, content TEXT);"

        result = apply_migration(project_id, migration_name, migration_query)

        # Verify successful response
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], migration_name)
        self.assertEqual(result["status"], "APPLIED_SUCCESSFULLY")
        self.assertIsInstance(result["version"], str)
        self.assertTrue(len(result["version"]) > 0)
        self.assertIsNone(result["message"])

        # Verify migration was recorded in DB
        self.assertIn(project_id, DB["migrations"])
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 1)

        stored_migration = project_migrations[0]
        self.assertEqual(stored_migration["name"], migration_name)
        self.assertEqual(stored_migration["query"], migration_query)
        self.assertEqual(stored_migration["status"], "APPLIED_SUCCESSFULLY")
        self.assertEqual(stored_migration["version"], result["version"])
        self.assertIsInstance(stored_migration["applied_at"], datetime)

    def test_apply_migration_alter_table_success(self):
        """Test successful migration that alters an existing table."""
        project_id = "proj_active"
        migration_name = "add_users_created_at"
        migration_query = "ALTER TABLE public.users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"

        result = apply_migration(project_id, migration_name, migration_query)

        self.assertEqual(result["status"], "APPLIED_SUCCESSFULLY")
        self.assertEqual(result["name"], migration_name)
        
        # Verify migration recorded
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 1)
        self.assertEqual(project_migrations[0]["name"], migration_name)

    def test_apply_migration_multiple_migrations_success(self):
        """Test applying multiple migrations to the same project."""
        project_id = "proj_active"
        
        # First migration
        result1 = apply_migration(project_id, "create_posts", "CREATE TABLE posts (id SERIAL PRIMARY KEY);")
        version1 = result1["version"]
        
        # Second migration  
        result2 = apply_migration(project_id, "create_comments", "CREATE TABLE comments (id SERIAL PRIMARY KEY);")
        version2 = result2["version"]

        # Verify both succeeded
        self.assertEqual(result1["status"], "APPLIED_SUCCESSFULLY")
        self.assertEqual(result2["status"], "APPLIED_SUCCESSFULLY")
        self.assertNotEqual(version1, version2)  # Should have unique versions

        # Verify both recorded in DB
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 2)
        self.assertEqual(project_migrations[0]["name"], "create_posts")
        self.assertEqual(project_migrations[1]["name"], "create_comments")

    def test_apply_migration_project_without_existing_migrations(self):
        """Test migration on project that doesn't have migrations structure - should fail."""
        # Remove migrations for this project to test validation
        if "proj_active" in DB["migrations"]:
            del DB["migrations"]["proj_active"]
        
        project_id = "proj_active"
        migration_name = "initial_schema"
        migration_query = "CREATE TABLE initial (id SERIAL PRIMARY KEY);"

        # Should raise NotFoundError when migrations structure doesn't exist
        self.assert_error_behavior(
            apply_migration,
            custom_errors.NotFoundError,
            "No migrations found for project 'proj_active'. Project may not be properly initialized.",
            project_id=project_id,
            name=migration_name,
            query=migration_query
        )

    # Error test cases - Input validation
    def test_apply_migration_empty_project_id(self):
        """Test error when project_id is empty."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Project ID cannot be empty.",
            project_id="",
            name="test_migration",
            query="SELECT 1;"
        )

    def test_apply_migration_none_project_id(self):
        """Test error when project_id is None."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Project ID must be a string.",
            project_id=None,
            name="test_migration",
            query="SELECT 1;"
        )

    def test_apply_migration_non_string_project_id(self):
        """Test error when project_id is not a string."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Project ID must be a string.",
            project_id=123,
            name="test_migration",
            query="SELECT 1;"
        )

    def test_apply_migration_empty_name(self):
        """Test error when migration name is empty."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Migration name cannot be empty.",
            project_id="proj_active",
            name="",
            query="SELECT 1;"
        )

    def test_apply_migration_none_name(self):
        """Test error when migration name is None."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Migration name must be a string.",
            project_id="proj_active",
            name=None,
            query="SELECT 1;"
        )

    def test_apply_migration_empty_query(self):
        """Test error when query is empty."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Migration query cannot be empty.",
            project_id="proj_active",
            name="test_migration",
            query=""
        )

    def test_apply_migration_none_query(self):
        """Test error when query is None."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.ValidationError,
            "Migration query must be a string.",
            project_id="proj_active",
            name="test_migration",
            query=None
        )

    # Error test cases - Project not found
    def test_apply_migration_project_not_found(self):
        """Test error when project does not exist."""
        self.assert_error_behavior(
            apply_migration,
            custom_errors.NotFoundError,
            "Project with ID 'nonexistent_project' not found.",
            project_id="nonexistent_project",
            name="test_migration",
            query="SELECT 1;"
        )

    # Error test cases - SQL execution failures
    def test_apply_migration_sql_syntax_error(self):
        """Test migration failure due to SQL syntax error."""
        project_id = "proj_active"
        migration_name = "invalid_syntax_migration"
        migration_query = "CREATE TABEL invalid (id SERIAL);"  # Intentional typo

        with self.assertRaises(custom_errors.MigrationError) as context:
            apply_migration(project_id, migration_name, migration_query)
        
        # Check that error message contains the expected parts
        error_msg = str(context.exception)
        self.assertIn("Migration 'invalid_syntax_migration' failed:", error_msg)
        self.assertIn("syntax error", error_msg)

        # Verify failed migration was still recorded
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 1)
        stored_migration = project_migrations[0]
        self.assertEqual(stored_migration["name"], migration_name)
        self.assertEqual(stored_migration["status"], "FAILED")

    def test_apply_migration_table_already_exists_error(self):
        """Test migration failure when table already exists."""
        project_id = "proj_active"
        migration_name = "duplicate_table_migration"
        migration_query = "CREATE TABLE public.users (id SERIAL PRIMARY KEY);"

        with self.assertRaises(custom_errors.MigrationError) as context:
            apply_migration(project_id, migration_name, migration_query)
        
        # Check that error message contains the expected parts
        error_msg = str(context.exception)
        self.assertIn("Migration 'duplicate_table_migration' failed:", error_msg)
        self.assertIn("already exists", error_msg)

        # Verify failed migration was recorded
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 1)
        self.assertEqual(project_migrations[0]["status"], "FAILED")

    def test_apply_migration_column_does_not_exist_error(self):
        """Test migration failure when trying to alter non-existent column."""
        project_id = "proj_active"
        migration_name = "alter_nonexistent_column"
        migration_query = "ALTER TABLE public.users DROP COLUMN nonexistent_column;"

        with self.assertRaises(custom_errors.MigrationError) as context:
            apply_migration(project_id, migration_name, migration_query)
        
        # Check that error message contains the expected parts
        error_msg = str(context.exception)
        self.assertIn("Migration 'alter_nonexistent_column' failed:", error_msg)
        self.assertIn("does not have a column", error_msg)

    def test_apply_migration_database_connection_error(self):
        """Test migration failure due to database connection error."""
        project_id = "proj_inactive"  # Use inactive project to trigger status error
        migration_name = "connection_error_migration"
        migration_query = "CREATE TABLE test (id SERIAL);"

        with self.assertRaises(custom_errors.MigrationError) as context:
            apply_migration(project_id, migration_name, migration_query)
        
        # Check that error message contains the expected parts
        error_msg = str(context.exception)
        self.assertIn("Migration 'connection_error_migration' failed:", error_msg)
        self.assertIn("INACTIVE", error_msg)

    def test_apply_migration_insert_nonexistent_table_error(self):
        """Test migration failure when inserting into a non-existent table."""
        project_id = "proj_active"
        migration_name = "insert_nonexistent_table"
        migration_query = "INSERT INTO nonexistent_table (id) VALUES (1);"

        with self.assertRaises(custom_errors.MigrationError) as context:
            apply_migration(project_id, migration_name, migration_query)
        
        error_msg = str(context.exception)
        self.assertIn("Migration 'insert_nonexistent_table' failed:", error_msg)
        self.assertIn("does not exist", error_msg)

        # Verify failed migration was recorded
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 1)
        self.assertEqual(project_migrations[0]["status"], "FAILED")

    def test_apply_migration_unexpected_error_on_record(self):
        """Test migration failure due to an unexpected error during migration recording."""
        project_id = "proj_active"
        migration_name = "unexpected_record_error"
        migration_query = "CREATE TABLE unexpected_record_test (id SERIAL);"

        # Create a mock that looks like a list and whose append method will fail on the first call
        # but succeed on the second call (which occurs in the 'except' block).
        mock_migrations_list = MagicMock()
        mock_migrations_list.append.side_effect = [TypeError("Simulated type error on append"), None]

        with patch.dict(DB['migrations'], {project_id: mock_migrations_list}):
            with self.assertRaises(custom_errors.MigrationError) as context:
                apply_migration(project_id, migration_name, migration_query)

        error_msg = str(context.exception)
        self.assertIn(f"Migration '{migration_name}' failed with unexpected error:", error_msg)
        self.assertIn("Simulated type error on append", error_msg)
        
        # Verify append was called twice: once in the `try` block (failed), and once in the `except` block (succeeded).
        self.assertEqual(mock_migrations_list.append.call_count, 2)

    def test_apply_migration_unexpected_error(self):
        """Test migration failure due to an unexpected error during migration recording."""
        project_id = "proj_active"
        migration_name = "unexpected_error_migration"
        migration_query = "CREATE TABLE unexpected_test (id SERIAL);"

        # Use a mock to simulate an error during the first append operation.
        mock_migrations_list = MagicMock()
        mock_migrations_list.append.side_effect = [AttributeError("Simulated attribute error"), None]
        
        with patch.dict(DB['migrations'], {project_id: mock_migrations_list}):
            with self.assertRaises(custom_errors.MigrationError) as context:
                apply_migration(project_id, migration_name, migration_query)

        error_msg = str(context.exception)
        self.assertIn(f"Migration '{migration_name}' failed with unexpected error:", error_msg)
        self.assertIn("Simulated attribute error", error_msg)
        self.assertEqual(mock_migrations_list.append.call_count, 2)

    # Edge cases and special scenarios
    def test_apply_migration_with_complex_ddl(self):
        """Test migration with complex DDL including constraints and indexes."""
        project_id = "proj_active"
        migration_name = "complex_schema_migration"
        complex_query = """
        CREATE TABLE orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            total DECIMAL(10,2) NOT NULL CHECK (total > 0),
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_orders_user_id ON orders(user_id);
        CREATE INDEX idx_orders_status ON orders(status);
        """

        result = apply_migration(project_id, migration_name, complex_query)

        self.assertEqual(result["status"], "APPLIED_SUCCESSFULLY")
        self.assertEqual(result["name"], migration_name)
        
        # Verify complex query was passed through correctly
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(project_migrations[0]["query"], complex_query)

    def test_apply_migration_case_insensitive_naming(self):
        """Test that migration names are case-sensitive and stored as-is."""
        project_id = "proj_active"
        migration_name_mixed_case = "Create_Users_Table_V2"
        migration_query = "CREATE TABLE users_v2 (id SERIAL PRIMARY KEY);"

        result = apply_migration(project_id, migration_name_mixed_case, migration_query)

        self.assertEqual(result["status"], "APPLIED_SUCCESSFULLY")
        self.assertEqual(result["name"], migration_name_mixed_case)
        
        # Verify name stored exactly as provided
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(project_migrations[0]["name"], migration_name_mixed_case)

    def test_apply_migration_with_long_query(self):
        """Test migration with very long SQL query."""
        project_id = "proj_active"
        migration_name = "long_query_migration"
        
        # Create a long query with many columns
        columns = [f"col_{i} TEXT" for i in range(100)]
        long_query = f"CREATE TABLE large_table (id SERIAL PRIMARY KEY, {', '.join(columns)});"

        result = apply_migration(project_id, migration_name, long_query)

        self.assertEqual(result["status"], "APPLIED_SUCCESSFULLY")
        
        # Verify long query was stored correctly
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(project_migrations[0]["query"], long_query)

    def test_apply_migration_version_uniqueness(self):
        """Test that migration versions are unique even with same name."""
        project_id = "proj_active"
        migration_name = "same_name_migration"
        
        # Apply same-named migration twice
        result1 = apply_migration(project_id, migration_name, "CREATE TABLE test1 (id SERIAL);")
        result2 = apply_migration(project_id, migration_name, "CREATE TABLE test2 (id SERIAL);")

        # Versions should be different
        self.assertNotEqual(result1["version"], result2["version"])
        
        # Both should have same name but different versions in storage
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 2)
        self.assertEqual(project_migrations[0]["name"], migration_name)
        self.assertEqual(project_migrations[1]["name"], migration_name)
        self.assertNotEqual(project_migrations[0]["version"], project_migrations[1]["version"])

    def test_apply_migration_timestamp_precision(self):
        """Test that applied_at timestamps have proper precision."""
        project_id = "proj_active"
        migration_name = "timestamp_test_migration"
        migration_query = "CREATE TABLE timestamp_test (id SERIAL PRIMARY KEY);"

        apply_migration(project_id, migration_name, migration_query)

        project_migrations = DB["migrations"][project_id]
        stored_migration = project_migrations[0]
        
        # Verify applied_at is a datetime with timezone info
        self.assertIsInstance(stored_migration["applied_at"], datetime)
        self.assertIsNotNone(stored_migration["applied_at"].tzinfo)

    def test_apply_migration_with_serial_types(self):
        """Test that migrations work with SERIAL and BIGSERIAL types (real implementation)."""
        project_id = "proj_active"
        migration_name = "create_table_with_serial"
        migration_query = """
        CREATE TABLE test_serial (
            id SERIAL PRIMARY KEY,
            big_id BIGSERIAL,
            name VARCHAR(100)
        );
        """

        result = apply_migration(project_id, migration_name, migration_query)

        self.assertEqual(result["status"], "APPLIED_SUCCESSFULLY")
        
        # Verify migration was recorded
        project_migrations = DB["migrations"][project_id]
        self.assertEqual(len(project_migrations), 1)
        self.assertEqual(project_migrations[0]["status"], "APPLIED_SUCCESSFULLY")


if __name__ == '__main__':
    unittest.main()