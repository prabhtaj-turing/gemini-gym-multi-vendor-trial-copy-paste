"""
Utility tests for BigQuery API.

This module tests shared helper functions in the BigQuery API, ensuring formatting,
parsing, and error handling work correctly. Following the Service Engineering Test Framework
Guideline for utility tests.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List
from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine.utils import (
    bq_type_to_sqlite_type,
    parse_full_table_name,
    load_db_dict_to_sqlite,
    get_default_db_path,
    set_default_db_path,
    get_default_sqlite_db_dir,
    DateTimeEncoder
)
from ..SimulationEngine.custom_errors import InvalidInputError, InvalidQueryError
from ..SimulationEngine.models import BigQueryDatabase, Table, FieldMode


class TestBigQueryUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for BigQuery utility functions.
    
    Tests shared helper functions to ensure they are deterministic, handle bad input
    gracefully, and work correctly for clients/colabs usage.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_db.json")
        self.original_db_path = get_default_db_path()

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original database path
        set_default_db_path(self.original_db_path)
        
        # Remove test directory
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)

    def test_bq_type_to_sqlite_type_conversion(self):
        """Test BigQuery to SQLite type conversion."""
        # Test all supported type conversions
        test_cases = [
            ({"type": "STRING"}, "TEXT"),
            ({"type": "INT64"}, "INTEGER"),
            ({"type": "FLOAT64"}, "REAL"),
            ({"type": "BOOLEAN"}, "INTEGER"),
            ({"type": "TIMESTAMP"}, "TEXT"),
            ({"type": "DATE"}, "TEXT"),
            ({"type": "DATETIME"}, "TEXT"),
            ({"type": "TIME"}, "TEXT"),
            ({"type": "BYTES"}, "BLOB"),
            ({"type": "NUMERIC"}, "REAL"),
            ({"type": "BIGNUMERIC"}, "REAL"),
            ({"type": "JSON"}, "TEXT"),
            ({"type": "GEOGRAPHY"}, "TEXT"),
            ({"type": "ARRAY"}, "TEXT"),
            ({"type": "STRUCT"}, "TEXT"),
        ]
        
        for bq_type_obj, expected_sqlite_type in test_cases:
            with self.subTest(bq_type=bq_type_obj["type"]):
                result = bq_type_to_sqlite_type(bq_type_obj)
                self.assertEqual(result, expected_sqlite_type)

    def test_bq_type_to_sqlite_type_invalid_input(self):
        """Test BigQuery to SQLite type conversion with invalid input."""
        # Test with None
        with self.assertRaises(AttributeError):
            bq_type_to_sqlite_type(None)
        
        # Test with empty dict
        result = bq_type_to_sqlite_type({})
        self.assertEqual(result, "TEXT")  # Default fallback
        
        # Test with missing type key
        result = bq_type_to_sqlite_type({"name": "test"})
        self.assertEqual(result, "TEXT")  # Default fallback
        
        # Test with unsupported type
        result = bq_type_to_sqlite_type({"type": "UNSUPPORTED_TYPE"})
        self.assertEqual(result, "TEXT")  # Default fallback

    def test_parse_full_table_name_valid(self):
        """Test parsing valid fully qualified table names."""
        test_cases = [
            ("project.dataset.table", ("project", "dataset", "table")),
            ("project-id.dataset-id.table-id", ("project-id", "dataset-id", "table-id")),
            ("project_id.dataset_id.table_id", ("project_id", "dataset_id", "table_id")),
        ]
        
        for table_name, expected in test_cases:
            with self.subTest(table_name=table_name):
                result = parse_full_table_name(table_name)
                self.assertEqual(result, expected)

    def test_parse_full_table_name_invalid(self):
        """Test parsing invalid table names."""
        invalid_names = [
            "",  # Empty string
            "table",  # No project.dataset prefix
            "dataset.table",  # Missing project
            "project.dataset",  # Missing table
            "project.dataset.table.extra",  # Too many parts
            "project..table",  # Empty dataset
            ".dataset.table",  # Empty project
            "project.dataset.",  # Empty table
        ]
        
        for table_name in invalid_names:
            with self.subTest(table_name=table_name):
                with self.assertRaises(InvalidInputError):
                    parse_full_table_name(table_name)

    def test_parse_full_table_name_edge_cases(self):
        """Test parsing table names with edge cases."""
        # Test with special characters in names (hyphens are actually valid)
        result = parse_full_table_name("project.dataset.table-name")
        self.assertEqual(result, ("project", "dataset", "table-name"))
        
        # Test with underscores (should work)
        result = parse_full_table_name("project_name.dataset_name.table_name")
        self.assertEqual(result, ("project_name", "dataset_name", "table_name"))
        
        # Test with truly invalid characters
        with self.assertRaises(InvalidInputError):
            parse_full_table_name("project.dataset.table name")  # Space is invalid

    def test_load_db_dict_to_sqlite_valid(self):
        """Test loading valid database dictionary to SQLite."""
        test_db = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {
                                    "table_id": "test-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                                        {"name": "value", "type": "FLOAT64", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "test1", "value": 10.5},
                                        {"id": 2, "name": "test2", "value": 20.7}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(test_db)
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # Test that table was created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("test-table", table_names)
        
        # Test that data was loaded
        cursor.execute("SELECT * FROM `test-table`")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 2)
        
        conn.close()

    def test_load_db_dict_to_sqlite_empty(self):
        """Test loading empty database dictionary to SQLite."""
        empty_db = {"projects": []}
        
        conn = load_db_dict_to_sqlite(empty_db)
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # Test that no tables were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        self.assertEqual(len(tables), 0)
        
        conn.close()

    def test_load_db_dict_to_sqlite_invalid_schema(self):
        """Test loading database with invalid schema."""
        invalid_db = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {
                                    "table_id": "test-table",
                                    "schema": [
                                        {"name": "id", "type": "INVALID_TYPE", "mode": "REQUIRED"}
                                    ],
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Should handle invalid schema gracefully
        conn = load_db_dict_to_sqlite(invalid_db)
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_set_default_db_path(self):
        """Test getting and setting default database path."""
        # Test initial path
        original_path = get_default_db_path()
        self.assertIsInstance(original_path, str)
        self.assertTrue(len(original_path) > 0)
        
        # Test setting new path (create a temporary file first)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"projects": []}')
            temp_path = f.name
        
        try:
            set_default_db_path(temp_path)
            self.assertEqual(get_default_db_path(), temp_path)
        finally:
            # Clean up
            os.unlink(temp_path)
        
        # Test setting invalid path
        with self.assertRaises(FileNotFoundError):
            set_default_db_path("/nonexistent/path/db.json")

    def test_get_default_sqlite_db_dir(self):
        """Test getting default SQLite database directory."""
        db_dir = get_default_sqlite_db_dir()
        self.assertIsInstance(db_dir, str)
        self.assertTrue(len(db_dir) > 0)

    def test_datetime_encoder(self):
        """Test custom JSON encoder for datetime objects."""
        encoder = DateTimeEncoder()
        
        # Test with datetime object
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        encoded = encoder.default(dt)
        self.assertIsInstance(encoded, str)
        self.assertEqual(encoded, "2023-01-01T12:00:00+00:00")
        
        # Test with non-datetime object (should use parent class)
        with self.assertRaises(TypeError):
            encoder.default("not a datetime")

    def test_utility_functions_deterministic(self):
        """Test that utility functions are deterministic."""
        # Test bq_type_to_sqlite_type is deterministic
        bq_type = {"type": "STRING"}
        result1 = bq_type_to_sqlite_type(bq_type)
        result2 = bq_type_to_sqlite_type(bq_type)
        self.assertEqual(result1, result2)
        
        # Test parse_full_table_name is deterministic
        table_name = "project.dataset.table"
        result1 = parse_full_table_name(table_name)
        result2 = parse_full_table_name(table_name)
        self.assertEqual(result1, result2)

    def test_utility_functions_error_handling(self):
        """Test that utility functions handle errors gracefully."""
        # Test with None values
        with self.assertRaises(AttributeError):
            bq_type_to_sqlite_type(None)
        
        with self.assertRaises(InvalidInputError):
            parse_full_table_name(None)
        
        # Test with empty strings
        with self.assertRaises(InvalidInputError):
            parse_full_table_name("")
        
        # Test with malformed input
        with self.assertRaises(AttributeError):
            bq_type_to_sqlite_type("not a dict")

    def test_sqlite_connection_cleanup(self):
        """Test that SQLite connections are properly managed."""
        test_db = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {
                                    "table_id": "test-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"}
                                    ],
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Test multiple connections
        conn1 = load_db_dict_to_sqlite(test_db)
        conn2 = load_db_dict_to_sqlite(test_db)
        
        self.assertIsInstance(conn1, sqlite3.Connection)
        self.assertIsInstance(conn2, sqlite3.Connection)
        
        # Test that connections can be closed
        conn1.close()
        conn2.close()
        
        # Test that closed connections raise errors
        with self.assertRaises(sqlite3.ProgrammingError):
            conn1.execute("SELECT 1")

    def test_complex_schema_handling(self):
        """Test handling of complex BigQuery schemas."""
        complex_schema = [
            {"name": "simple_string", "type": "STRING", "mode": "NULLABLE"},
            {"name": "required_int", "type": "INT64", "mode": "REQUIRED"},
            {"name": "repeated_float", "type": "FLOAT64", "mode": "REPEATED"},
            {"name": "timestamp_field", "type": "TIMESTAMP", "mode": "NULLABLE"},
            {"name": "json_field", "type": "JSON", "mode": "NULLABLE"},
            {"name": "numeric_field", "type": "NUMERIC", "mode": "NULLABLE"},
        ]
        
        test_db = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {
                                    "table_id": "complex-table",
                                    "schema": complex_schema,
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
        
        # Test that table was created with complex schema
        cursor.execute("PRAGMA table_info(`complex-table`)")
        columns = cursor.fetchall()
        self.assertEqual(len(columns), 6)
        
        conn.close()


if __name__ == "__main__":
    unittest.main()
