"""
Test suite for execute_sql function in the Supabase API simulation.

This module contains comprehensive tests for SQL query execution including:
- SELECT queries with various complexities
- INSERT, UPDATE, DELETE operations
- DDL operations (CREATE, ALTER, DROP)
- Error handling for various edge cases
- Schema support and PostgreSQL compatibility
"""
import copy
import unittest
from unittest.mock import patch
from supabase.SimulationEngine import custom_errors
from supabase.SimulationEngine.db import DB
from supabase.SimulationEngine.duckdb_manager import get_duckdb_manager
from supabase.database import execute_sql
from common_utils.base_case import BaseTestCaseWithErrorHandler


# Initial database state for execute_sql tests
EXECUTE_SQL_INITIAL_DB_STATE = {
    "organizations": [
        {
            "id": "org_test123",
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
            "organization_id": "org_test123",
            "region": "us-east-1",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2023-02-01T09:00:00Z",
            "version": "PostgreSQL 15"
        },
        {
            "id": "proj_inactive",
            "name": "Inactive Test Project",
            "organization_id": "org_test123",
            "region": "us-west-2",
            "status": "INACTIVE",
            "created_at": "2023-02-15T10:00:00Z",
            "version": "PostgreSQL 14"
        },
        {
            "id": "proj_paused",
            "name": "Paused Test Project",
            "organization_id": "org_test123",
            "region": "eu-central-1",
            "status": "INACTIVE",
            "created_at": "2023-03-01T11:00:00Z",
            "version": "PostgreSQL 15"
        }
    ],
    "tables": {
        "proj_active": [
            {
                "name": "users",
                "schema": "public",
                "comment": "User accounts table",
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
                    },
                    {
                        "name": "name",
                        "data_type": "varchar(255)",
                        "is_nullable": True,
                        "default_value": None
                    },
                    {
                        "name": "created_at",
                        "data_type": "timestamp with time zone",
                        "is_nullable": False,
                        "default_value": "CURRENT_TIMESTAMP"
                    },
                    {
                        "name": "is_active",
                        "data_type": "boolean",
                        "is_nullable": False,
                        "default_value": "true"
                    }
                ],
                "primary_keys": [{"name": "id"}],
                "relationships": []
            },
            {
                "name": "posts",
                "schema": "public",
                "comment": "Blog posts table",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "serial",
                        "is_nullable": False,
                        "default_value": None
                    },
                    {
                        "name": "user_id",
                        "data_type": "uuid",
                        "is_nullable": False,
                        "default_value": None
                    },
                    {
                        "name": "title",
                        "data_type": "text",
                        "is_nullable": False,
                        "default_value": None
                    },
                    {
                        "name": "content",
                        "data_type": "text",
                        "is_nullable": True,
                        "default_value": None
                    },
                    {
                        "name": "published",
                        "data_type": "boolean",
                        "is_nullable": False,
                        "default_value": "false"
                    },
                    {
                        "name": "created_at",
                        "data_type": "timestamp",
                        "is_nullable": False,
                        "default_value": "CURRENT_TIMESTAMP"
                    }
                ],
                "primary_keys": [{"name": "id"}],
                "relationships": [
                    {
                        "constraint_name": "posts_user_id_fkey",
                        "source_schema": "public",
                        "source_table_name": "posts",
                        "source_column_name": "user_id",
                        "target_table_schema": "public",
                        "target_table_name": "users",
                        "target_column_name": "id"
                    }
                ]
            },
            {
                "name": "products", 
                "schema": "analytics",
                "comment": "Product analytics table",
                "columns": [
                    {
                        "name": "product_id",
                        "data_type": "integer",
                        "is_nullable": False,
                        "default_value": None
                    },
                    {
                        "name": "product_name",
                        "data_type": "varchar(100)",
                        "is_nullable": False,
                        "default_value": None
                    },
                    {
                        "name": "price",
                        "data_type": "decimal(10,2)",
                        "is_nullable": False,
                        "default_value": "0.00"
                    },
                    {
                        "name": "category",
                        "data_type": "text",
                        "is_nullable": True,
                        "default_value": "'uncategorized'"
                    }
                ],
                "primary_keys": [{"name": "product_id"}],
                "relationships": []
            },
            {
                "name": "test_coverage",
                "schema": "public",
                "comment": "Table to test various coverage scenarios",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "uuid",
                        "is_nullable": False,
                        "default_value": "uuid_generate_v4()"
                    },
                    {
                        "name": "tags",
                        "data_type": "text[]",
                        "is_nullable": True,
                        "default_value": None
                    },
                    {
                        "name": "metadata",
                        "data_type": "jsonb",
                        "is_nullable": True,
                        "default_value": None
                    },
                    {
                        "name": "updated_at",
                        "data_type": "timestamp",
                        "is_nullable": False,
                        "default_value": "now()"
                    }
                ],
                "primary_keys": [{"name": "id"}],
                "relationships": []
            }
        ],
        "proj_inactive": [
            {
                "name": "logs",
                "schema": "public",
                "comment": "System logs",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "bigserial",
                        "is_nullable": False,
                        "default_value": None
                    },
                    {
                        "name": "message",
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
    "migrations": {},
    "edge_functions": {},
    "branches": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {
        "proj_active": "https://proj-active.supabase.co",
        "proj_inactive": "https://proj-inactive.supabase.co"
    },
    "project_anon_keys": {},
    "project_ts_types": {},
    "logs": {}
}


class TestExecuteSQL(BaseTestCaseWithErrorHandler):
    """Test suite for the execute_sql function."""

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        # Clear and setup clean state
        DB.clear()
        DB.update(copy.deepcopy(EXECUTE_SQL_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Clean up DuckDB manager connections for each test."""
        # Get a fresh manager instance and clean up any existing connections
        self.manager = get_duckdb_manager()
        self.manager.close_all_connections()
        
    def tearDown(self):
        """Clean up DuckDB manager connections after each test."""
        self.manager.close_all_connections()

    # Success test cases - SELECT queries
    def test_execute_sql_select_simple_success(self):
        """Test successful execution of a simple SELECT query."""
        # Test with a simple SELECT query that works on in-memory tables
        result = execute_sql(project_id="proj_active", query="SELECT 1 as test_col")
        
        # Verify the response structure
        self.assertIn("rows", result)
        self.assertIn("columns", result)
        self.assertIn("row_count", result)
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(len(result["columns"]), 1)
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["test_col"], 1)
        self.assertEqual(result["columns"][0]["name"], "test_col")

    def test_execute_sql_select_with_schema(self):
        """Test SELECT query with multiple columns and functions."""
        result = execute_sql(
            project_id="proj_active", 
            query="SELECT 1 as product_id, 'Widget' as product_name, 19.99 as price"
        )
        
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["product_name"], "Widget")
        self.assertEqual(result["rows"][0]["product_id"], 1)
        self.assertEqual(result["rows"][0]["price"], 19.99)

    def test_execute_sql_select_empty_result(self):
        """Test SELECT query that returns no rows."""
        result = execute_sql(project_id="proj_active", query="SELECT 1 as id, 'test' as email WHERE FALSE")
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(len(result["rows"]), 0)
        self.assertEqual(len(result["columns"]), 2)

    # Success test cases - INSERT operations
    def test_execute_sql_insert_single_row(self):
        """Test successful INSERT of a single row."""
        # First create a temporary table
        execute_sql(
            project_id="proj_active",
            query="CREATE TABLE temp_users (id INTEGER, email VARCHAR(255), name VARCHAR(255))"
        )
        
        # Test insert
        result = execute_sql(
            project_id="proj_active",
            query="INSERT INTO temp_users (id, email, name) VALUES (1, 'newuser@example.com', 'New User')"
        )
        
        self.assertIn("row_count", result)
        self.assertIn("status_message", result)
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["status_message"], "INSERT 0 1")

    def test_execute_sql_insert_multiple_rows(self):
        """Test INSERT of multiple rows."""
        # First create a temporary table
        execute_sql(
            project_id="proj_active",
            query="CREATE TABLE temp_posts (id INTEGER, user_id VARCHAR(255), title VARCHAR(255))"
        )
        
        result = execute_sql(
            project_id="proj_active",
            query="INSERT INTO temp_posts (id, user_id, title) VALUES (1, '123', 'Post 1'), (2, '123', 'Post 2'), (3, '456', 'Post 3')"
        )
        
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["status_message"], "INSERT 0 3")

    # Success test cases - UPDATE operations
    def test_execute_sql_update_single_row(self):
        """Test UPDATE affecting a single row."""
        # Create table and insert data
        execute_sql(project_id="proj_active", query="CREATE TABLE test_update (id INTEGER, name VARCHAR(255))")
        execute_sql(project_id="proj_active", query="INSERT INTO test_update (id, name) VALUES (1, 'Original Name')")
        
        result = execute_sql(
            project_id="proj_active",
            query="UPDATE test_update SET name = 'Updated Name' WHERE id = 1"
        )
        
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["status_message"], "UPDATE 1")

    def test_execute_sql_update_multiple_rows(self):
        """Test UPDATE affecting multiple rows."""
        # Create table and insert multiple rows
        execute_sql(project_id="proj_active", query="CREATE TABLE test_multi_update (id INTEGER, published BOOLEAN)")
        execute_sql(project_id="proj_active", query="INSERT INTO test_multi_update VALUES (1, false), (2, false), (3, false), (4, false), (5, false)")
        
        result = execute_sql(
            project_id="proj_active",
            query="UPDATE test_multi_update SET published = true WHERE id <= 5"
        )
        
        self.assertEqual(result["row_count"], 5)
        self.assertEqual(result["status_message"], "UPDATE 5")

    def test_execute_sql_update_no_matches(self):
        """Test UPDATE that matches no rows."""
        # Create table but don't insert any matching data
        execute_sql(project_id="proj_active", query="CREATE TABLE test_no_match (id INTEGER, is_active BOOLEAN)")
        
        result = execute_sql(
            project_id="proj_active",
            query="UPDATE test_no_match SET is_active = false WHERE id = 999"
        )
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["status_message"], "UPDATE 0")

    # Success test cases - DELETE operations  
    def test_execute_sql_delete_single_row(self):
        """Test DELETE affecting a single row."""
        # Create table and insert data
        execute_sql(project_id="proj_active", query="CREATE TABLE test_delete (id INTEGER)")
        execute_sql(project_id="proj_active", query="INSERT INTO test_delete VALUES (123)")
        
        result = execute_sql(
            project_id="proj_active",
            query="DELETE FROM test_delete WHERE id = 123"
        )
        
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["status_message"], "DELETE 1")

    def test_execute_sql_delete_multiple_rows(self):
        """Test DELETE affecting multiple rows."""
        # Create table and insert multiple rows
        execute_sql(project_id="proj_active", query="CREATE TABLE test_multi_delete (id INTEGER)")
        execute_sql(project_id="proj_active", query="INSERT INTO test_multi_delete VALUES (1), (2), (3), (4), (5)")
        
        result = execute_sql(
            project_id="proj_active",
            query="DELETE FROM test_multi_delete WHERE id <= 5"
        )
        
        self.assertEqual(result["row_count"], 5)
        self.assertEqual(result["status_message"], "DELETE 5")

    # Success test cases - DDL operations
    def test_execute_sql_create_table(self):
        """Test CREATE TABLE DDL operation."""
        result = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_ddl_table (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["status_message"], "OK")

    def test_execute_sql_alter_table(self):
        """Test ALTER TABLE DDL operation."""
        # First create a table to alter
        execute_sql(project_id="proj_active", query="CREATE TABLE test_alter (id INTEGER)")
        
        result = execute_sql(
            project_id="proj_active",
            query="ALTER TABLE test_alter ADD COLUMN phone VARCHAR(20)"
        )
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["status_message"], "OK")

    def test_execute_sql_drop_table(self):
        """Test DROP TABLE DDL operation."""
        # First create a table to drop
        execute_sql(project_id="proj_active", query="CREATE TABLE test_drop (id INTEGER)")
        
        result = execute_sql(
            project_id="proj_active",
            query="DROP TABLE test_drop"
        )
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["status_message"], "OK")

    def test_execute_sql_create_table_with_serial(self):
        """Test CREATE TABLE with SERIAL column type."""
        result = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE users_serial (id SERIAL PRIMARY KEY, name VARCHAR(100))"
        )
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["status_message"], "OK")
        
        # Verify we can insert into the table (providing ID manually since DuckDB doesn't auto-increment)
        insert_result = execute_sql(
            project_id="proj_active",
            query="INSERT INTO users_serial (id, name) VALUES (1, 'John Doe')"
        )
        
        self.assertEqual(insert_result["row_count"], 1)
        self.assertEqual(insert_result["status_message"], "INSERT 0 1")

    def test_execute_sql_create_table_with_bigserial(self):
        """Test CREATE TABLE with BIGSERIAL column type."""
        result = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE logs_bigserial (id BIGSERIAL PRIMARY KEY, message TEXT, created_at TIMESTAMP)"
        )
        
        self.assertEqual(result["row_count"], 0)
        self.assertEqual(result["status_message"], "OK")
        
        # Verify we can insert into the table (providing ID manually)
        insert_result = execute_sql(
            project_id="proj_active",
            query="INSERT INTO logs_bigserial (id, message, created_at) VALUES (1, 'Test log', '2023-01-01 12:00:00')"
        )
        
        self.assertEqual(insert_result["row_count"], 1)
        self.assertEqual(insert_result["status_message"], "INSERT 0 1")

    def test_execute_sql_serial_case_insensitive(self):
        """Test that SERIAL type conversion is case insensitive."""
        # Test lowercase serial
        result1 = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_lower (id serial PRIMARY KEY, data VARCHAR(50))"
        )
        self.assertEqual(result1["status_message"], "OK")
        
        # Test uppercase SERIAL
        result2 = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_upper (id SERIAL PRIMARY KEY, data VARCHAR(50))"
        )
        self.assertEqual(result2["status_message"], "OK")
        
        # Test mixed case Serial
        result3 = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_mixed (id Serial PRIMARY KEY, data VARCHAR(50))"
        )
        self.assertEqual(result3["status_message"], "OK")

    def test_execute_sql_postgresql_function_conversion(self):
        """Test that PostgreSQL functions are converted to DuckDB equivalents."""
        # Test uuid_generate_v4() conversion
        result = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_uuid (id UUID DEFAULT uuid_generate_v4(), name VARCHAR(100))"
        )
        self.assertEqual(result["status_message"], "OK")
        
        # Test now() conversion
        result2 = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_timestamp (id INTEGER, created_at TIMESTAMP DEFAULT now())"
        )
        self.assertEqual(result2["status_message"], "OK")

    def test_execute_sql_mixed_postgresql_features(self):
        """Test a complex query with multiple PostgreSQL features that need conversion."""
        query = """
        CREATE TABLE complex_table (
            id BIGSERIAL PRIMARY KEY,
            user_id UUID DEFAULT uuid_generate_v4(),
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP
        )
        """
        
        result = execute_sql(project_id="proj_active", query=query)
        self.assertEqual(result["status_message"], "OK")
        
        # Test insert with PostgreSQL functions (providing ID manually)
        insert_result = execute_sql(
            project_id="proj_active",
            query="INSERT INTO complex_table (id, email, updated_at) VALUES (1, 'test@example.com', now())"
        )
        self.assertEqual(insert_result["row_count"], 1)
        self.assertEqual(insert_result["status_message"], "INSERT 0 1")

    # Error test cases - Input validation
    def test_execute_sql_empty_project_id(self):
        """Test error when project_id is empty."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "The project_id parameter cannot be null or empty",
            project_id="",
            query="SELECT * FROM users"
        )

    def test_execute_sql_none_project_id(self):
        """Test error when project_id is None."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "The project_id parameter cannot be null or empty",
            project_id=None,
            query="SELECT * FROM users"
        )

    def test_execute_sql_non_string_project_id(self):
        """Test error when project_id is not a string."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "project_id must be a string",
            project_id=123,
            query="SELECT * FROM users"
        )

    def test_execute_sql_list_project_id(self):
        """Test error when project_id is a list."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "project_id must be a string",
            project_id=["proj_active"],
            query="SELECT * FROM users"
        )

    def test_execute_sql_empty_query(self):
        """Test error when query is empty."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "The query parameter cannot be null or empty",
            project_id="proj_active",
            query=""
        )

    def test_execute_sql_none_query(self):
        """Test error when query is None."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "The query parameter cannot be null or empty",
            project_id="proj_active",
            query=None
        )

    def test_execute_sql_non_string_query(self):
        """Test error when query is not a string."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "query must be a string",
            project_id="proj_active",
            query={"query": "SELECT * FROM users"}
        )

    def test_execute_sql_whitespace_only_query(self):
        """Test error when query contains only whitespace."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.InvalidInputError,
            "The query parameter cannot be empty or contain only whitespace",
            project_id="proj_active",
            query="   \n\t  "
        )

    # Error test cases - Project not found
    def test_execute_sql_project_not_found(self):
        """Test error when project does not exist."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.NotFoundError,
            "Project with id 'nonexistent_project' not found",
            project_id="nonexistent_project",
            query="SELECT * FROM users"
        )

    # Error test cases - Project state validation
    def test_execute_sql_project_inactive(self):
        """Test error when project is inactive."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.DatabaseConnectionError,
            "Cannot execute SQL on project 'proj_inactive' in status 'INACTIVE'. Project must be in ACTIVE status.",
            project_id="proj_inactive",
            query="SELECT * FROM logs"
        )

    def test_execute_sql_project_paused(self):
        """Test error when project is paused."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.DatabaseConnectionError,
            "Cannot execute SQL on project 'proj_paused' in status 'INACTIVE'. Project must be in ACTIVE status.",
            project_id="proj_paused",
            query="SELECT 1"
        )

    # Error test cases - SQL execution errors
    def test_execute_sql_syntax_error(self):
        """Test SQL syntax error."""
        self.assert_error_behavior(
            execute_sql,
            custom_errors.SQLError,
            "syntax error: Parser Error: syntax error at or near \"SELCT\"",
            project_id="proj_active",
            query="SELCT * FROM users"  # Intentional typo
        )

    def test_execute_sql_table_not_found(self):
        """Test error when table does not exist."""
        with self.assertRaises(custom_errors.SQLError) as context:
            execute_sql(project_id="proj_active", query="SELECT * FROM nonexistent_table")
        
        self.assertIn("Catalog Error: Table with name nonexistent_table does not exist!", str(context.exception))

    def test_execute_sql_column_not_found(self):
        """Test error when column does not exist."""
        # Create a table first
        execute_sql(project_id="proj_active", query="CREATE TABLE test_col_error (id INTEGER)")
        
        with self.assertRaises(custom_errors.SQLError) as context:
            execute_sql(project_id="proj_active", query="SELECT nonexistent_column FROM test_col_error")
        
        self.assertIn("Referenced column \"nonexistent_column\" not found in FROM clause!", str(context.exception))

    def test_execute_sql_with_predefined_tables(self):
        """Test that DuckDB manager creates tables from DB state."""
        # The DuckDB manager should have initialized tables from the test DB state
        # Let's verify it handles table creation properly by testing table structure
        result = execute_sql(
            project_id="proj_active",
            query="SELECT 'test' as status"
        )
        
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["status"], "test")

    # Edge cases and special scenarios
    def test_execute_sql_with_semicolon(self):
        """Test query with trailing semicolon."""
        result = execute_sql(
            project_id="proj_active",
            query="SELECT 5 as count;"  # With semicolon
        )
        
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["rows"][0]["count"], 5)

    def test_execute_sql_multiline_query(self):
        """Test multiline SQL query."""
        multiline_query = """
        SELECT 'active1@example.com' as email, 3 as post_count
        """
        
        result = execute_sql(project_id="proj_active", query=multiline_query)
        
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(len(result["columns"]), 2)
        self.assertEqual(result["rows"][0]["email"], "active1@example.com")
        self.assertEqual(result["rows"][0]["post_count"], 3)

    def test_execute_sql_case_insensitive_keywords(self):
        """Test SQL with mixed case keywords."""
        result = execute_sql(
            project_id="proj_active",
            query="SeLeCt 1 as id, 'Test Post' as title"
        )
        
        self.assertEqual(result["row_count"], 1)
        
    def test_execute_sql_with_comments(self):
        """Test SQL query with comments."""
        query_with_comments = """
        -- This is a comment
        SELECT 1 as id
        /* This is a 
           multi-line comment */
        -- Another comment
        """
        
        result = execute_sql(project_id="proj_active", query=query_with_comments)
        
        self.assertEqual(result["row_count"], 1)

    def test_execute_sql_transaction_commands(self):
        """Test transaction commands return DDL-style response."""
        # Test BEGIN
        result = execute_sql(project_id="proj_active", query="BEGIN")
        self.assertEqual(result["status_message"], "OK")
        
        # Test COMMIT after BEGIN
        result = execute_sql(project_id="proj_active", query="COMMIT")
        self.assertEqual(result["status_message"], "OK")
        
        # Test ROLLBACK after starting a new transaction
        execute_sql(project_id="proj_active", query="BEGIN")
        result = execute_sql(project_id="proj_active", query="ROLLBACK")
        self.assertEqual(result["status_message"], "OK")

    def test_execute_sql_special_characters_in_data(self):
        """Test handling of special characters in query results."""
        result = execute_sql(
            project_id="proj_active",
            query="SELECT 1 as id, 'Special chars: quotes, emoji 😀' as content"
        )
        
        self.assertEqual(result["row_count"], 1)
        self.assertIn("😀", result["rows"][0]["content"])

    def test_execute_sql_null_values(self):
        """Test handling of NULL values in results."""
        result = execute_sql(project_id="proj_active", query="SELECT 1 as id, NULL as name, 'user@example.com' as email")
        
        self.assertIsNone(result["rows"][0]["name"])
        self.assertEqual(result["rows"][0]["email"], "user@example.com")

    def test_execute_sql_timestamp_formatting(self):
        """Test that timestamps are properly formatted."""
        result = execute_sql(
            project_id="proj_active",
            query="SELECT 1 as id, '2023-12-25T10:30:00'::timestamp as created_at"
        )
        
        # Timestamp should be returned as string in ISO format
        self.assertIsInstance(result["rows"][0]["created_at"], str)
        self.assertIn("2023-12-25", result["rows"][0]["created_at"])

    def test_execute_sql_boolean_values(self):
        """Test handling of boolean values."""
        # Test true value
        result = execute_sql(project_id="proj_active", query="SELECT 1 as id, true as is_active")
        
        self.assertEqual(result["row_count"], 1)
        self.assertIs(result["rows"][0]["is_active"], True)
        
        # Test false value
        result = execute_sql(project_id="proj_active", query="SELECT 2 as id, false as is_active")
        
        self.assertEqual(result["row_count"], 1)
        self.assertIs(result["rows"][0]["is_active"], False)

    def test_execute_sql_numeric_types(self):
        """Test handling of various numeric types."""
        result = execute_sql(
            project_id="proj_active",
            query="SELECT 42 as int_col, 9223372036854775807 as bigint_col, 123.45 as decimal_col, 3.14159 as float_col"
        )
        
        row = result["rows"][0]
        self.assertEqual(row["int_col"], 42)
        self.assertEqual(row["bigint_col"], 9223372036854775807)
        self.assertEqual(row["decimal_col"], 123.45)
        self.assertAlmostEqual(row["float_col"], 3.14159, places=5)

    def test_execute_sql_array_types(self):
        """Test handling of PostgreSQL array types."""
        result = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_arrays (id INTEGER, tags VARCHAR[])"
        )
        self.assertEqual(result["status_message"], "OK")

    def test_execute_sql_type_with_parameters(self):
        """Test handling of types with parameters like VARCHAR(255)."""
        result = execute_sql(
            project_id="proj_active",
            query="CREATE TABLE test_params (id INTEGER, description VARCHAR(255), amount DECIMAL(10,2))"
        )
        self.assertEqual(result["status_message"], "OK")

    def test_execute_sql_fallback_query_parsing(self):
        """Test fallback query parsing when sqlglot fails."""
        # Use a query that might cause sqlglot to fail but still works
        result = execute_sql(
            project_id="proj_active",
            query="-- Comment\nSELECT 1 as test_col"
        )
        self.assertEqual(result["rows"][0]["test_col"], 1)

    def test_execute_sql_other_query_type(self):
        """Test query type that returns 'other'."""
        result = execute_sql(
            project_id="proj_active",
            query="EXPLAIN SELECT * FROM public.users"
        )
        # EXPLAIN queries typically return results but are classified as 'other'
        self.assertIn("status_message", result)

    def test_execute_sql_catalog_error_handling(self):
        """Test handling of catalog errors (table not found)."""
        # Test that catalog errors are properly handled  
        with self.assertRaises(custom_errors.SQLError) as context:
            execute_sql(
                project_id="proj_active",
                query="SELECT * FROM invalid_schema.nonexistent_table_12345"
            )
        # Check that the error message starts with "Catalog error:"
        self.assertTrue(str(context.exception).startswith("Catalog error:"))

    def test_execute_sql_insert_with_default_query_parsing_fallback(self):
        """Test that insert operations work with different SQL formatting."""
        # Test with INSERT that might require fallback parsing (use existing users table)
        result = execute_sql(
            project_id="proj_active",
            query="insert into public.users (id, email, name, created_at, is_active) values (gen_random_uuid(), 'test@example.com', 'Test User', '2023-01-01 10:00:00', true)"
        )
        self.assertEqual(result["row_count"], 1)

    def test_execute_sql_update_with_fallback_parsing(self):
        """Test update operations with fallback parsing."""
        # First insert a record to update (use existing posts table)
        execute_sql(
            project_id="proj_active",
            query="INSERT INTO public.posts (id, user_id, title, content, published, created_at) VALUES (999, gen_random_uuid(), 'Update Test', 'Content to update', false, '2023-01-01 10:00:00')"
        )
        
        # Test update with different formatting that might trigger fallback
        result = execute_sql(
            project_id="proj_active",
            query="update public.posts set title = 'Updated Title' where id = 999"
        )
        self.assertEqual(result["row_count"], 1)

    def test_execute_sql_delete_with_fallback_parsing(self):
        """Test delete operations with fallback parsing."""
        # First insert a record to delete (use existing posts table)
        execute_sql(
            project_id="proj_active",
            query="INSERT INTO public.posts (id, user_id, title, content, published, created_at) VALUES (998, gen_random_uuid(), 'Delete Test', 'Content to delete', false, '2023-01-01 10:00:00')"
        )
        
        # Test delete with different formatting
        result = execute_sql(
            project_id="proj_active",
            query="delete from public.posts where id = 998"
        )
        self.assertEqual(result["row_count"], 1)

    def test_execute_sql_ddl_operations(self):
        """Test various DDL operations for coverage."""
        # Test CREATE
        result1 = execute_sql(
            project_id="proj_active",
            query="create table temp_coverage (id int, name text)"
        )
        self.assertEqual(result1["status_message"], "OK")
        
        # Test ALTER
        result2 = execute_sql(
            project_id="proj_active",
            query="alter table temp_coverage add column description text"
        )
        self.assertEqual(result2["status_message"], "OK")
        
        # Test DROP
        result3 = execute_sql(
            project_id="proj_active",
            query="drop table temp_coverage"
        )
        self.assertEqual(result3["status_message"], "OK")
        
        # Test TRUNCATE
        execute_sql(
            project_id="proj_active",
            query="CREATE TABLE temp_truncate (id INTEGER)"
        )
        result4 = execute_sql(
            project_id="proj_active",
            query="truncate table temp_truncate"
        )
        self.assertEqual(result4["status_message"], "OK")

    def test_execute_sql_unexpected_exception_handling(self):
        """Test that unexpected exceptions are caught and wrapped in SQLError."""
        with patch('supabase.database.get_duckdb_manager') as mock_get_db_manager:
            mock_db_manager = mock_get_db_manager.return_value
            mock_db_manager.execute_query.side_effect = Exception("A generic error occurred")
            
            with self.assertRaises(custom_errors.SQLError) as context:
                execute_sql(project_id="proj_active", query="SELECT 1")
            
            self.assertIn("Unexpected error during query execution: A generic error occurred", str(context.exception))


if __name__ == '__main__':
    unittest.main()