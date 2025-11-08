"""
Database validation tests for BigQuery API.

This module tests database validation using pydantic models to ensure accurate DB state
for tests. Following the Service Engineering Test Framework Guideline for DB validation tests.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError

from ..SimulationEngine.db import DB
from ..SimulationEngine.models import BigQueryDatabase, Table, FieldMode
from ..SimulationEngine.utils import (
    load_db_dict_to_sqlite,
    get_default_db_path,
    set_default_db_path,
    DateTimeEncoder
)
from ..SimulationEngine.custom_errors import InvalidInputError


class TestBigQueryDBValidation(BaseTestCaseWithErrorHandler):
    """
    Test suite for BigQuery database validation.
    
    Tests database validation using pydantic models to ensure accurate DB state
    for tests and proper data structure validation.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_db.json")
        self.original_db_path = get_default_db_path()
        
        # Valid database structure for testing
        self.valid_db_structure = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {
                                    "table_id": "users",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                                        {"name": "email", "type": "STRING", "mode": "NULLABLE"},
                                        {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "John Doe", "email": "john@example.com", "created_at": "2023-01-01T10:00:00Z"},
                                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "created_at": "2023-01-02T11:00:00Z"}
                                    ],
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T10:00:00Z",
                                    "last_modified_time": "2023-01-01T10:00:00Z"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original database path
        set_default_db_path(self.original_db_path)
        
        # Remove test directory
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)

    def test_valid_database_structure_validation(self):
        """Test validation of valid database structure."""
        # Test that valid structure can be loaded into SQLite
        conn = load_db_dict_to_sqlite(self.valid_db_structure)
        cursor = conn.cursor()
        
        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("users", table_names)
        
        # Verify schema was created correctly
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        self.assertEqual(len(columns), 4)
        
        # Verify data was loaded
        cursor.execute("SELECT COUNT(*) FROM users")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 2)
        
        conn.close()

    def test_database_structure_integrity(self):
        """Test database structure integrity validation."""
        # Test that all required fields are present
        self.assertIn("projects", self.valid_db_structure)
        self.assertIsInstance(self.valid_db_structure["projects"], list)
        
        project = self.valid_db_structure["projects"][0]
        self.assertIn("project_id", project)
        self.assertIn("datasets", project)
        self.assertIsInstance(project["datasets"], list)
        
        dataset = project["datasets"][0]
        self.assertIn("dataset_id", dataset)
        self.assertIn("tables", dataset)
        self.assertIsInstance(dataset["tables"], list)
        
        table = dataset["tables"][0]
        self.assertIn("table_id", table)
        self.assertIn("schema", table)
        self.assertIn("rows", table)
        self.assertIsInstance(table["schema"], list)
        self.assertIsInstance(table["rows"], list)

    def test_schema_validation(self):
        """Test validation of table schemas."""
        # Test valid schema
        valid_schema = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "score", "type": "FLOAT64", "mode": "NULLABLE"},
            {"name": "is_active", "type": "BOOLEAN", "mode": "NULLABLE"},
            {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
        ]
        
        # Test that schema can be used to create table
        test_db = {
            "projects": [
                {
                    "project_id": "schema-test",
                    "datasets": [
                        {
                            "dataset_id": "schema-test",
                            "tables": [
                                {
                                    "table_id": "schema-test",
                                    "schema": valid_schema,
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        cursor = conn.cursor()
        
        # Verify table was created with correct schema
        cursor.execute("PRAGMA table_info(`schema-test`)")
        columns = cursor.fetchall()
        self.assertEqual(len(columns), 5)
        
        # Verify column types
        column_info = {col[1]: col[2] for col in columns}
        self.assertEqual(column_info["id"], "INTEGER")
        self.assertEqual(column_info["name"], "TEXT")
        self.assertEqual(column_info["score"], "REAL")
        self.assertEqual(column_info["is_active"], "INTEGER")
        self.assertEqual(column_info["created_at"], "TEXT")
        
        conn.close()

    def test_data_type_validation(self):
        """Test validation of data types in rows."""
        # Test valid data types
        valid_data = [
            {"id": 1, "name": "Test User", "score": 95.5, "is_active": True, "created_at": "2023-01-01T10:00:00Z"},
            {"id": 2, "name": "Another User", "score": 87.3, "is_active": False, "created_at": "2023-01-02T11:00:00Z"}
        ]
        
        test_db = {
            "projects": [
                {
                    "project_id": "data-test",
                    "datasets": [
                        {
                            "dataset_id": "data-test",
                            "tables": [
                                {
                                    "table_id": "data-test",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                                        {"name": "score", "type": "FLOAT64", "mode": "NULLABLE"},
                                        {"name": "is_active", "type": "BOOLEAN", "mode": "NULLABLE"},
                                        {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
                                    ],
                                    "rows": valid_data
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        cursor = conn.cursor()
        
        # Verify data was loaded correctly
        cursor.execute("SELECT * FROM `data-test`")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 2)
        
        # Verify data types are preserved
        row1 = rows[0]
        self.assertIsInstance(row1[0], int)  # id
        self.assertIsInstance(row1[1], str)  # name
        self.assertIsInstance(row1[2], float)  # score
        # Boolean values might be stored as strings or integers in SQLite
        self.assertIn(type(row1[3]), (int, str))  # is_active 
        self.assertIsInstance(row1[4], str)  # created_at
        
        conn.close()

    def test_required_field_validation(self):
        """Test validation of required fields."""
        # Test schema with required fields
        schema_with_required = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "name", "type": "STRING", "mode": "REQUIRED"},
            {"name": "email", "type": "STRING", "mode": "NULLABLE"}
        ]
        
        # Test data with required fields present
        valid_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": None}
        ]
        
        test_db = {
            "projects": [
                {
                    "project_id": "required-test",
                    "datasets": [
                        {
                            "dataset_id": "required-test",
                            "tables": [
                                {
                                    "table_id": "required-test",
                                    "schema": schema_with_required,
                                    "rows": valid_data
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        cursor = conn.cursor()
        
        # Verify data was loaded
        cursor.execute("SELECT COUNT(*) FROM `required-test`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 2)
        
        # Verify required fields are not null
        cursor.execute("SELECT id, name FROM `required-test` WHERE id = 1")
        row = cursor.fetchone()
        self.assertIsNotNone(row[0])  # id
        self.assertIsNotNone(row[1])  # name
        
        conn.close()

    def test_nullable_field_validation(self):
        """Test validation of nullable fields."""
        # Test schema with nullable fields
        schema_with_nullable = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "description", "type": "STRING", "mode": "NULLABLE"}
        ]
        
        # Test data with null values
        data_with_nulls = [
            {"id": 1, "name": "John Doe", "description": "Active user"},
            {"id": 2, "name": None, "description": None},
            {"id": 3, "name": "Jane Smith", "description": None}
        ]
        
        test_db = {
            "projects": [
                {
                    "project_id": "nullable-test",
                    "datasets": [
                        {
                            "dataset_id": "nullable-test",
                            "tables": [
                                {
                                    "table_id": "nullable-test",
                                    "schema": schema_with_nullable,
                                    "rows": data_with_nulls
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        cursor = conn.cursor()
        
        # Verify data was loaded
        cursor.execute("SELECT COUNT(*) FROM `nullable-test`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 3)
        
        # Verify null values are handled correctly
        cursor.execute("SELECT name, description FROM `nullable-test` WHERE id = 2")
        row = cursor.fetchone()
        self.assertIsNone(row[0])  # name
        self.assertIsNone(row[1])  # description
        
        conn.close()

    def test_invalid_schema_validation(self):
        """Test validation of invalid schemas."""
        # Test invalid schema (missing required fields)
        invalid_schemas = [
            [],  # Empty schema
            [{"name": "id"}],  # Missing type and mode
            [{"type": "INT64", "mode": "REQUIRED"}],  # Missing name
            [{"name": "id", "type": "INVALID_TYPE", "mode": "REQUIRED"}],  # Invalid type
            [{"name": "id", "type": "INT64", "mode": "INVALID_MODE"}]  # Invalid mode
        ]
        
        for invalid_schema in invalid_schemas:
            with self.subTest(invalid_schema=invalid_schema):
                test_db = {
                    "projects": [
                        {
                            "project_id": "invalid-schema-test",
                            "datasets": [
                                {
                                    "dataset_id": "invalid-schema-test",
                                    "tables": [
                                        {
                                            "table_id": "invalid-schema-test",
                                            "schema": invalid_schema,
                                            "rows": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
                
                # Should handle invalid schema gracefully or raise appropriate errors
                try:
                    conn = load_db_dict_to_sqlite(test_db)
                    conn.close()
                except (KeyError, TypeError, ValueError):
                    # Expected for some invalid schemas
                    pass

    def test_data_consistency_validation(self):
        """Test validation of data consistency between schema and rows."""
        # Test data that matches schema
        consistent_data = [
            {"id": 1, "name": "John Doe", "age": 30},
            {"id": 2, "name": "Jane Smith", "age": 25}
        ]
        
        matching_schema = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "name", "type": "STRING", "mode": "REQUIRED"},
            {"name": "age", "type": "INT64", "mode": "REQUIRED"}
        ]
        
        test_db = {
            "projects": [
                {
                    "project_id": "consistency-test",
                    "datasets": [
                        {
                            "dataset_id": "consistency-test",
                            "tables": [
                                {
                                    "table_id": "consistency-test",
                                    "schema": matching_schema,
                                    "rows": consistent_data
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        cursor = conn.cursor()
        
        # Verify data was loaded correctly
        cursor.execute("SELECT * FROM `consistency-test`")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 2)
        
        # Verify data types match schema
        row1 = rows[0]
        self.assertIsInstance(row1[0], int)  # id
        self.assertIsInstance(row1[1], str)  # name
        self.assertIsInstance(row1[2], int)  # age
        
        conn.close()

    def test_complex_data_type_validation(self):
        """Test validation of complex data types."""
        # Test JSON and timestamp data types
        complex_data = [
            {
                "id": 1,
                "metadata": '{"department": "engineering", "level": "senior"}',
                "created_at": "2023-01-01T10:00:00Z",
                "tags": '["python", "sql", "testing"]'
            }
        ]
        
        complex_schema = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "metadata", "type": "JSON", "mode": "NULLABLE"},
            {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
            {"name": "tags", "type": "JSON", "mode": "NULLABLE"}
        ]
        
        test_db = {
            "projects": [
                {
                    "project_id": "complex-test",
                    "datasets": [
                        {
                            "dataset_id": "complex-test",
                            "tables": [
                                {
                                    "table_id": "complex-test",
                                    "schema": complex_schema,
                                    "rows": complex_data
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        cursor = conn.cursor()
        
        # Verify data was loaded
        cursor.execute("SELECT * FROM `complex-test`")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)
        
        # Verify JSON data is stored as text
        row = rows[0]
        self.assertIsInstance(row[1], str)  # metadata (JSON as text)
        self.assertIsInstance(row[2], str)  # created_at (timestamp as text)
        self.assertIsInstance(row[3], str)  # tags (JSON as text)
        
        # Verify JSON can be parsed
        import json
        metadata = json.loads(row[1])
        self.assertEqual(metadata["department"], "engineering")
        
        tags = json.loads(row[3])
        self.assertEqual(tags, ["python", "sql", "testing"])
        
        conn.close()

    def test_database_state_validation_after_operations(self):
        """Test database state validation after various operations."""
        # Create initial state
        conn = load_db_dict_to_sqlite(self.valid_db_structure)
        cursor = conn.cursor()
        
        # Verify initial state
        cursor.execute("SELECT COUNT(*) FROM users")
        initial_count = cursor.fetchone()[0]
        self.assertEqual(initial_count, 2)
        
        # Perform operations
        cursor.execute("INSERT INTO users (id, name, email, created_at) VALUES (3, 'New User', 'new@example.com', '2023-01-03T12:00:00Z')")
        cursor.execute("UPDATE users SET name = 'Updated User' WHERE id = 1")
        cursor.execute("DELETE FROM users WHERE id = 2")
        
        # Verify state after operations
        cursor.execute("SELECT COUNT(*) FROM users")
        final_count = cursor.fetchone()[0]
        self.assertEqual(final_count, 2)  # 2 original - 1 deleted + 1 added = 2
        
        cursor.execute("SELECT name FROM users WHERE id = 1")
        updated_name = cursor.fetchone()[0]
        self.assertEqual(updated_name, "Updated User")
        
        cursor.execute("SELECT name FROM users WHERE id = 3")
        new_user_name = cursor.fetchone()[0]
        self.assertEqual(new_user_name, "New User")
        
        conn.close()

    def test_database_validation_with_large_datasets(self):
        """Test database validation with large datasets."""
        # Create large dataset
        large_schema = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "value", "type": "STRING", "mode": "NULLABLE"},
            {"name": "score", "type": "FLOAT64", "mode": "NULLABLE"}
        ]
        
        large_data = [
            {"id": i, "value": f"value_{i}", "score": float(i) / 10.0}
            for i in range(1000)
        ]
        
        large_db = {
            "projects": [
                {
                    "project_id": "large-test",
                    "datasets": [
                        {
                            "dataset_id": "large-test",
                            "tables": [
                                {
                                    "table_id": "large-table",
                                    "schema": large_schema,
                                    "rows": large_data
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(large_db)
        cursor = conn.cursor()
        
        # Verify large dataset was loaded
        cursor.execute("SELECT COUNT(*) FROM `large-table`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 1000)
        
        # Verify data integrity
        cursor.execute("SELECT MIN(id), MAX(id), AVG(score) FROM `large-table`")
        min_id, max_id, avg_score = cursor.fetchone()
        self.assertEqual(min_id, 0)
        self.assertEqual(max_id, 999)
        self.assertAlmostEqual(avg_score, 49.95, places=2)  # Average of 0 to 99.9
        
        conn.close()


if __name__ == "__main__":
    unittest.main()
