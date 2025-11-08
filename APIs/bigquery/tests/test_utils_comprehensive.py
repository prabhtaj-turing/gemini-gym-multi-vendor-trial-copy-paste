"""
Comprehensive utility tests for BigQuery API.

This module tests the utils.py module to ensure all utility functions
work correctly, including timestamp handling, table operations, database management,
and in-memory DB operations.
Following the Service Engineering Test Framework Guideline for comprehensive testing.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, mock_open
from typing import Dict, Any, List
from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine.utils import (
    get_current_timestamp_ms,
    get_table_from_path,
    convert_timestamp_to_milliseconds,
    format_table_metadata,
    find_table_by_name,
    get_table_size_info,
    is_table_expired,
    get_table_age,
    initialize_sqlite_db,
    create_table_schema,
    load_database_from_json,
    load_db_dict_to_sqlite,
    _get_current_utc_timestamp_iso,
    create_project,
    create_dataset,
    create_table,
    insert_rows,
    DateTimeEncoder
)
from ..SimulationEngine.models import BigQueryDatabase, Table, FieldMode
from ..SimulationEngine.custom_errors import InvalidInputError
from ..SimulationEngine.db import DB


class TestBigQueryUtilsComprehensive(BaseTestCaseWithErrorHandler):
    """
    Comprehensive test suite for BigQuery utilities.
    
    Tests all utility functions including timestamp handling, table operations,
    database management, and in-memory DB operations.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        
        # Store original DB state
        self.original_db = DB.copy()
        
        # Sample database structure for testing (matching Pydantic model structure)
        self.sample_db_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "metadata": {
                                        "table_id": "test_table",
                                        "dataset_id": "test_dataset",
                                        "project_id": "test-project",
                                        "type": "TABLE",
                                        "creation_time": "2023-01-01T00:00:00Z",
                                        "last_modified_time": "2023-01-02T00:00:00Z",
                                        "expiration_time": None,
                                        "num_rows": 3,
                                        "size_bytes": 100,
                                        "fields": [
                                            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                            {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                                            {"name": "active", "type": "BOOLEAN", "mode": "REQUIRED"},
                                            {"name": "data", "type": "JSON", "mode": "NULLABLE"}
                                        ]
                                    },
                                    "rows": [
                                        {"id": 1, "name": "Alice", "active": True, "data": {"age": 25}},
                                        {"id": 2, "name": "Bob", "active": False, "data": {"age": 30}},
                                        {"id": 3, "name": None, "active": True, "data": None}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Create test database file
        self.test_db_path = os.path.join(self.test_dir, "test_db.json")
        with open(self.test_db_path, 'w') as f:
            json.dump(self.sample_db_data, f, indent=2)

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db)
        
        # Remove test directory and all files recursively
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)

    def test_get_current_timestamp_ms(self):
        """Test get_current_timestamp_ms function."""
        # Test that it returns an integer timestamp in milliseconds
        timestamp = get_current_timestamp_ms()
        self.assertIsInstance(timestamp, int)
        
        # Test that the timestamp is reasonable (within last few seconds)
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.assertAlmostEqual(timestamp, now_ms, delta=5000)  # Within 5 seconds

    def test_get_table_from_path_found(self):
        """Test get_table_from_path when table exists."""
        # Load test database
        db = BigQueryDatabase(**self.sample_db_data)
        
        # Test finding existing table
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        self.assertIsNotNone(table)
        self.assertEqual(table.metadata.table_id, "test_table")
        self.assertEqual(table.metadata.project_id, "test-project")
        self.assertEqual(table.metadata.dataset_id, "test_dataset")

    def test_get_table_from_path_not_found(self):
        """Test get_table_from_path when table doesn't exist."""
        # Load test database
        db = BigQueryDatabase(**self.sample_db_data)
        
        # Test with non-existent project
        table = get_table_from_path(db, "nonexistent.test_dataset.test_table")
        self.assertIsNone(table)
        
        # Test with non-existent dataset
        table = get_table_from_path(db, "test-project.nonexistent.test_table")
        self.assertIsNone(table)
        
        # Test with non-existent table
        table = get_table_from_path(db, "test-project.test_dataset.nonexistent")
        self.assertIsNone(table)

    def test_convert_timestamp_to_milliseconds(self):
        """Test convert_timestamp_to_milliseconds function."""
        # Test with None
        result = convert_timestamp_to_milliseconds(None)
        self.assertIsNone(result)
        
        # Test with datetime
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = convert_timestamp_to_milliseconds(dt)
        expected = int(dt.timestamp() * 1000)
        self.assertEqual(result, expected)
        self.assertIsInstance(result, int)

    def test_format_table_metadata(self):
        """Test format_table_metadata function."""
        # Load test database and get table
        db = BigQueryDatabase(**self.sample_db_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        # Format metadata
        metadata = format_table_metadata(table)
        
        # Verify formatted metadata
        self.assertEqual(metadata['table_id'], 'test_table')
        self.assertEqual(metadata['dataset_id'], 'test_dataset')
        self.assertEqual(metadata['project_id'], 'test-project')
        self.assertEqual(metadata['type'], 'TABLE')
        self.assertIsInstance(metadata['creation_time'], int)
        self.assertIsInstance(metadata['last_modified_time'], int)
        self.assertIsNone(metadata['expiration_time'])
        self.assertIn('schema', metadata)
        self.assertIn('fields', metadata['schema'])

    def test_find_table_by_name_found(self):
        """Test find_table_by_name when table exists."""
        # Load test database
        db = BigQueryDatabase(**self.sample_db_data)
        
        # Find table by name
        table = find_table_by_name(db, "test_table")
        self.assertIsNotNone(table)
        self.assertEqual(table.metadata.table_id, "test_table")

    def test_find_table_by_name_not_found(self):
        """Test find_table_by_name when table doesn't exist."""
        # Load test database
        db = BigQueryDatabase(**self.sample_db_data)
        
        # Try to find non-existent table
        table = find_table_by_name(db, "nonexistent_table")
        self.assertIsNone(table)

    def test_get_table_size_info(self):
        """Test get_table_size_info function."""
        # Load test database and get table
        db = BigQueryDatabase(**self.sample_db_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        # Get size info
        size_info = get_table_size_info(table)
        
        # Verify size info
        self.assertIn('num_rows', size_info)
        self.assertIn('size_bytes', size_info)
        self.assertIn('avg_row_size', size_info)
        self.assertEqual(size_info['num_rows'], 3)  # We have 3 rows in test data
        self.assertIsInstance(size_info['size_bytes'], int)
        self.assertIsInstance(size_info['avg_row_size'], float)
        self.assertGreater(size_info['size_bytes'], 0)

    def test_get_table_size_info_empty_table(self):
        """Test get_table_size_info with empty table."""
        # Create table with no rows
        empty_table_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset", 
                            "tables": [
                                {
                                    "metadata": {
                                        "table_id": "empty_table",
                                        "dataset_id": "test_dataset",
                                        "project_id": "test-project",
                                        "type": "TABLE",
                                        "creation_time": "2023-01-01T00:00:00Z",
                                        "last_modified_time": "2023-01-01T00:00:00Z",
                                        "expiration_time": None,
                                        "num_rows": 0,
                                        "size_bytes": 0,
                                        "fields": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}]
                                    },
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        db = BigQueryDatabase(**empty_table_data)
        table = get_table_from_path(db, "test-project.test_dataset.empty_table")
        
        size_info = get_table_size_info(table)
        self.assertEqual(size_info['num_rows'], 0)
        self.assertEqual(size_info['size_bytes'], 0)
        self.assertEqual(size_info['avg_row_size'], 0)

    def test_is_table_expired_no_expiration(self):
        """Test is_table_expired with no expiration time."""
        # Load test database and get table
        db = BigQueryDatabase(**self.sample_db_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        # Test table with no expiration
        expired = is_table_expired(table)
        self.assertFalse(expired)

    def test_is_table_expired_with_future_expiration(self):
        """Test is_table_expired with future expiration time."""
        # Create table data with future expiration
        future_expiration = datetime.now(timezone.utc) + timedelta(days=1)
        table_data = self.sample_db_data.copy()
        table_data["projects"][0]["datasets"][0]["tables"][0]["metadata"]["expiration_time"] = future_expiration.isoformat()
        
        db = BigQueryDatabase(**table_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        expired = is_table_expired(table)
        self.assertFalse(expired)

    def test_is_table_expired_with_past_expiration(self):
        """Test is_table_expired with past expiration time."""
        # Create table data with past expiration
        past_expiration = datetime.now(timezone.utc) - timedelta(days=1)
        table_data = self.sample_db_data.copy()
        table_data["projects"][0]["datasets"][0]["tables"][0]["metadata"]["expiration_time"] = past_expiration.isoformat()
        
        db = BigQueryDatabase(**table_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        expired = is_table_expired(table)
        self.assertTrue(expired)

    def test_get_table_age_with_creation_time(self):
        """Test get_table_age with creation time."""
        # Load test database and get table
        db = BigQueryDatabase(**self.sample_db_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        # Get table age
        age = get_table_age(table)
        self.assertIsNotNone(age)
        self.assertIsInstance(age, float)
        self.assertGreater(age, 0)  # Should be positive (table created in past)

    def test_get_table_age_no_creation_time(self):
        """Test get_table_age with no creation time."""
        # Since Pydantic requires creation_time, we'll test with a table that has it
        # and mock the function to simulate no creation time
        db = BigQueryDatabase(**self.sample_db_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        # Mock the creation_time to be None for this test
        with patch.object(table.metadata, 'creation_time', None):
            age = get_table_age(table)
            self.assertIsNone(age)

    def test_initialize_sqlite_db_success(self):
        """Test initialize_sqlite_db with valid project and dataset."""
        # Create a simple database structure for the test
        simple_db_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "Alice"},
                                        {"id": 2, "name": "Bob"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Mock everything needed for the test
        with patch('APIs.bigquery.SimulationEngine.utils._DEFAULT_DB_PATH', '/fake/path'):
            with patch('APIs.bigquery.SimulationEngine.utils.get_default_sqlite_db_dir', return_value=self.test_dir):
                with patch('builtins.open', mock_open(read_data=json.dumps(simple_db_data))):
                    with patch('sqlite3.connect') as mock_connect:
                        mock_conn = mock_connect.return_value
                        mock_cursor = mock_conn.cursor.return_value
                        
                        # Test initialization
                        initialize_sqlite_db("test-project", "test_dataset")
                        
                        # Verify the function was called
                        mock_connect.assert_called_once()
                        mock_cursor.execute.assert_called()

    def test_initialize_sqlite_db_project_not_found(self):
        """Test initialize_sqlite_db with non-existent project."""
        # Create a simple database structure for the test
        simple_db_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": []
                        }
                    ]
                }
            ]
        }
        
        simple_db_path = os.path.join(self.test_dir, "simple_db2.json")
        with open(simple_db_path, 'w') as f:
            json.dump(simple_db_data, f, indent=2)
        
        with patch('APIs.bigquery.SimulationEngine.utils._DEFAULT_DB_PATH', simple_db_path):
            with self.assertRaises(ValueError) as context:
                initialize_sqlite_db("nonexistent-project", "test_dataset")
            
            self.assertIn("not found in default database", str(context.exception))

    def test_initialize_sqlite_db_dataset_not_found(self):
        """Test initialize_sqlite_db with non-existent dataset."""
        # Create a simple database structure for the test
        simple_db_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": []
                        }
                    ]
                }
            ]
        }
        
        simple_db_path = os.path.join(self.test_dir, "simple_db3.json")
        with open(simple_db_path, 'w') as f:
            json.dump(simple_db_data, f, indent=2)
        
        with patch('APIs.bigquery.SimulationEngine.utils._DEFAULT_DB_PATH', simple_db_path):
            with self.assertRaises(ValueError) as context:
                initialize_sqlite_db("test-project", "nonexistent_dataset")
            
            self.assertIn("not found in default database", str(context.exception))

    def test_initialize_sqlite_db_permission_error_handling(self):
        """Test initialize_sqlite_db with permission error handling."""
        # Create a simple database structure for the test
        simple_db_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}],
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        simple_db_path = os.path.join(self.test_dir, "simple_db4.json")
        with open(simple_db_path, 'w') as f:
            json.dump(simple_db_data, f, indent=2)
        
        with patch('APIs.bigquery.SimulationEngine.utils._DEFAULT_DB_PATH', simple_db_path):
            with patch('APIs.bigquery.SimulationEngine.utils.get_default_sqlite_db_dir', return_value=self.test_dir):
                with patch('builtins.open', mock_open(read_data=json.dumps(simple_db_data))):
                    with patch('os.remove', side_effect=PermissionError("Permission denied")):
                        # Should handle permission error gracefully
                        initialize_sqlite_db("test-project", "test_dataset")

    def test_create_table_schema(self):
        """Test create_table_schema function."""
        # Load test database and get table
        db = BigQueryDatabase(**self.sample_db_data)
        table = get_table_from_path(db, "test-project.test_dataset.test_table")
        
        # Create schema
        schema_sql = create_table_schema(table)
        
        # Verify schema SQL
        self.assertIsInstance(schema_sql, str)
        self.assertIn('CREATE TABLE IF NOT EXISTS "test_table"', schema_sql)
        self.assertIn('"id" INTEGER', schema_sql)
        self.assertIn('"name" TEXT NULL', schema_sql)
        self.assertIn('"active" INTEGER', schema_sql)
        self.assertIn('"data" TEXT NULL', schema_sql)

    def test_load_database_from_json_success(self):
        """Test load_database_from_json with valid file."""
        # Load database from JSON
        db = load_database_from_json(self.test_db_path)
        
        # Verify database was loaded correctly
        self.assertIsInstance(db, BigQueryDatabase)
        self.assertEqual(len(db.projects), 1)
        self.assertEqual(db.projects[0].project_id, "test-project")
        self.assertEqual(len(db.projects[0].datasets), 1)
        self.assertEqual(db.projects[0].datasets[0].dataset_id, "test_dataset")

    def test_load_database_from_json_file_not_found(self):
        """Test load_database_from_json with non-existent file."""
        non_existent_path = os.path.join(self.test_dir, "nonexistent.json")
        
        with self.assertRaises(FileNotFoundError) as context:
            load_database_from_json(non_existent_path)
        
        self.assertIn("Database file not found", str(context.exception))

    def test_load_db_dict_to_sqlite_success(self):
        """Test load_db_dict_to_sqlite function."""
        # Create data structure that matches what load_db_dict_to_sqlite expects
        simple_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "Alice"},
                                        {"id": 2, "name": "Bob"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Load dictionary to SQLite
        conn = load_db_dict_to_sqlite(simple_data)
        
        # Verify connection is valid
        self.assertIsInstance(conn, sqlite3.Connection)
        
        # Verify table was created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("test_table", table_names)
        
        # Verify data was inserted
        cursor.execute('SELECT * FROM "test_table"')
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 2)  # We only inserted 2 rows in the test data
        
        conn.close()

    def test_load_db_dict_to_sqlite_invalid_projects(self):
        """Test load_db_dict_to_sqlite with invalid projects structure."""
        invalid_data = {"projects": None}
        
        # Should handle invalid structure but will raise TypeError when iterating
        with self.assertRaises(TypeError):
            load_db_dict_to_sqlite(invalid_data)

    def test_load_db_dict_to_sqlite_serialization_error(self):
        """Test load_db_dict_to_sqlite with JSON serialization error."""
        # Create data with unserializable JSON
        data_with_complex_json = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "data", "type": "JSON", "mode": "NULLABLE"}],
                                    "rows": [{"data": object()}]  # Unserializable object
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Should handle serialization error gracefully
        conn = load_db_dict_to_sqlite(data_with_complex_json)
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_load_db_dict_to_sqlite_sqlite_error(self):
        """Test load_db_dict_to_sqlite with SQLite error."""
        # Create data with invalid table name
        invalid_table_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "invalid table name with spaces",
                                    "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}],
                                    "rows": [{"id": 1}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Should handle SQLite error gracefully
        conn = load_db_dict_to_sqlite(invalid_table_data)
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_current_utc_timestamp_iso(self):
        """Test _get_current_utc_timestamp_iso function."""
        timestamp = _get_current_utc_timestamp_iso()
        
        # Verify format
        self.assertIsInstance(timestamp, str)
        self.assertTrue(timestamp.endswith('Z'))
        
        # Verify it's a valid datetime string
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        self.assertIsInstance(parsed, datetime)

    def test_create_project_new(self):
        """Test create_project with new project."""
        # Clear DB for clean test
        DB.clear()
        
        # Create new project
        project = create_project("new-project")
        
        # Verify project was created
        self.assertEqual(project['project_id'], "new-project")
        self.assertIn('datasets', project)
        self.assertEqual(len(project['datasets']), 0)
        
        # Verify it's in the global DB
        self.assertIn('projects', DB)
        self.assertEqual(len(DB['projects']), 1)
        self.assertEqual(DB['projects'][0]['project_id'], "new-project")

    def test_create_project_existing(self):
        """Test create_project with existing project."""
        # Set up DB with existing project
        DB.clear()
        DB.update({
            "projects": [
                {"project_id": "existing-project", "datasets": []}
            ]
        })
        
        # Try to create existing project
        project = create_project("existing-project")
        
        # Should return existing project
        self.assertEqual(project['project_id'], "existing-project")
        
        # Should not create duplicate
        self.assertEqual(len(DB['projects']), 1)

    def test_create_project_empty_db(self):
        """Test create_project with empty DB."""
        # Clear DB completely
        DB.clear()
        
        # Create project
        project = create_project("test-project")
        
        # Verify project was created and DB structure initialized
        self.assertEqual(project['project_id'], "test-project")
        self.assertIn('projects', DB)
        self.assertEqual(len(DB['projects']), 1)

    def test_create_dataset_new(self):
        """Test create_dataset with new dataset."""
        # Clear DB for clean test
        DB.clear()
        
        # Create new dataset (should also create project)
        dataset = create_dataset("test-project", "new-dataset")
        
        # Verify dataset was created
        self.assertEqual(dataset['dataset_id'], "new-dataset")
        self.assertIn('tables', dataset)
        self.assertEqual(len(dataset['tables']), 0)
        
        # Verify project was also created
        self.assertIn('projects', DB)
        self.assertEqual(len(DB['projects']), 1)
        self.assertEqual(DB['projects'][0]['project_id'], "test-project")

    def test_create_dataset_existing(self):
        """Test create_dataset with existing dataset."""
        # Set up DB with existing dataset
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {"dataset_id": "existing-dataset", "tables": []}
                    ]
                }
            ]
        })
        
        # Try to create existing dataset
        dataset = create_dataset("test-project", "existing-dataset")
        
        # Should return existing dataset
        self.assertEqual(dataset['dataset_id'], "existing-dataset")
        
        # Should not create duplicate
        self.assertEqual(len(DB['projects'][0]['datasets']), 1)

    def test_create_dataset_missing_datasets_key(self):
        """Test create_dataset when project exists but has no datasets key."""
        # Set up DB with project missing datasets key
        DB.clear()
        DB.update({
            "projects": [
                {"project_id": "test-project"}  # No datasets key
            ]
        })
        
        # Create dataset
        dataset = create_dataset("test-project", "new-dataset")
        
        # Should create dataset and initialize datasets list
        self.assertEqual(dataset['dataset_id'], "new-dataset")
        self.assertIn('datasets', DB['projects'][0])
        self.assertEqual(len(DB['projects'][0]['datasets']), 1)

    def test_create_table_new(self):
        """Test create_table with new table."""
        # Clear DB for clean test
        DB.clear()
        
        schema = [
            {"name": "id", "type": "INT64", "mode": "REQUIRED"},
            {"name": "name", "type": "STRING", "mode": "NULLABLE"}
        ]
        
        # Create new table (should also create project and dataset)
        table = create_table("test-project", "test-dataset", "new-table", schema)
        
        # Verify table was created
        self.assertEqual(table['table_id'], "new-table")
        self.assertEqual(table['schema'], schema)
        self.assertIn('rows', table)
        self.assertEqual(len(table['rows']), 0)
        self.assertEqual(table['type'], 'TABLE')
        self.assertIn('creation_time', table)
        self.assertIn('last_modified_time', table)

    def test_create_table_existing(self):
        """Test create_table with existing table."""
        # Set up DB with existing table
        DB.clear()
        existing_schema = [{"name": "id", "type": "INT64", "mode": "REQUIRED"}]
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {
                                    "table_id": "existing-table",
                                    "schema": existing_schema,
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        })
        
        new_schema = [{"name": "name", "type": "STRING", "mode": "NULLABLE"}]
        
        # Try to create existing table
        table = create_table("test-project", "test-dataset", "existing-table", new_schema)
        
        # Should return existing table (not overwrite)
        self.assertEqual(table['table_id'], "existing-table")
        self.assertEqual(table['schema'], existing_schema)  # Original schema preserved

    def test_create_table_with_custom_parameters(self):
        """Test create_table with custom creation and expiration times."""
        # Clear DB for clean test
        DB.clear()
        
        schema = [{"name": "id", "type": "INT64", "mode": "REQUIRED"}]
        creation_time = "2023-01-01T00:00:00Z"
        expiration_time = "2024-01-01T00:00:00Z"
        
        # Create table with custom parameters
        table = create_table(
            "test-project", 
            "test-dataset", 
            "custom-table", 
            schema,
            table_type="VIEW",
            creation_time=creation_time,
            expiration_time=expiration_time
        )
        
        # Verify custom parameters
        self.assertEqual(table['type'], 'VIEW')
        self.assertEqual(table['creation_time'], creation_time)
        self.assertEqual(table['expiration_time'], expiration_time)

    def test_create_table_missing_tables_key(self):
        """Test create_table when dataset exists but has no tables key."""
        # Set up DB with dataset missing tables key
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {"dataset_id": "test-dataset"}  # No tables key
                    ]
                }
            ]
        })
        
        schema = [{"name": "id", "type": "INT64", "mode": "REQUIRED"}]
        
        # Create table
        table = create_table("test-project", "test-dataset", "new-table", schema)
        
        # Should create table and initialize tables list
        self.assertEqual(table['table_id'], "new-table")
        self.assertIn('tables', DB['projects'][0]['datasets'][0])
        self.assertEqual(len(DB['projects'][0]['datasets'][0]['tables']), 1)

    def test_insert_rows_success(self):
        """Test insert_rows with valid data."""
        # Set up DB with existing table
        DB.clear()
        DB.update({
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
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        })
        
        # Insert rows
        rows_to_insert = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        result = insert_rows("test-project", "test-dataset", "test-table", rows_to_insert)
        
        # Verify insertion was successful
        self.assertTrue(result)
        
        # Verify rows were added
        table = DB['projects'][0]['datasets'][0]['tables'][0]
        self.assertEqual(len(table['rows']), 2)
        self.assertEqual(table['rows'][0]['id'], 1)
        self.assertEqual(table['rows'][1]['name'], "Bob")
        
        # Verify last_modified_time was updated
        self.assertIn('last_modified_time', table)

    def test_insert_rows_project_not_found(self):
        """Test insert_rows with non-existent project."""
        DB.clear()
        
        with self.assertRaises(ValueError) as context:
            insert_rows("nonexistent-project", "test-dataset", "test-table", [{"id": 1}])
        
        self.assertIn("Project 'nonexistent-project' not found", str(context.exception))

    def test_insert_rows_dataset_not_found(self):
        """Test insert_rows with non-existent dataset."""
        # Set up DB with project but no matching dataset
        DB.clear()
        DB.update({
            "projects": [
                {"project_id": "test-project", "datasets": []}
            ]
        })
        
        with self.assertRaises(ValueError) as context:
            insert_rows("test-project", "nonexistent-dataset", "test-table", [{"id": 1}])
        
        self.assertIn("Dataset 'nonexistent-dataset' not found", str(context.exception))

    def test_insert_rows_table_not_found(self):
        """Test insert_rows with non-existent table."""
        # Set up DB with project and dataset but no matching table
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {"dataset_id": "test-dataset", "tables": []}
                    ]
                }
            ]
        })
        
        with self.assertRaises(ValueError) as context:
            insert_rows("test-project", "test-dataset", "nonexistent-table", [{"id": 1}])
        
        self.assertIn("Table 'nonexistent-table' not found", str(context.exception))

    def test_insert_rows_invalid_rows_type(self):
        """Test insert_rows with invalid rows type."""
        # Set up DB with existing table
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {"table_id": "test-table", "rows": []}
                            ]
                        }
                    ]
                }
            ]
        })
        
        with self.assertRaises(ValueError) as context:
            insert_rows("test-project", "test-dataset", "test-table", "not a list")
        
        self.assertIn("rows_to_insert must be a list", str(context.exception))

    def test_insert_rows_invalid_row_type(self):
        """Test insert_rows with invalid row type in list."""
        # Set up DB with existing table
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {"table_id": "test-table", "rows": []}
                            ]
                        }
                    ]
                }
            ]
        })
        
        with self.assertRaises(ValueError) as context:
            insert_rows("test-project", "test-dataset", "test-table", [{"id": 1}, "not a dict"])
        
        self.assertIn("Each item in rows_to_insert must be a dictionary", str(context.exception))

    def test_insert_rows_missing_rows_key(self):
        """Test insert_rows when table has no rows key."""
        # Set up DB with table missing rows key
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test-dataset",
                            "tables": [
                                {"table_id": "test-table"}  # No rows key
                            ]
                        }
                    ]
                }
            ]
        })
        
        # Insert rows
        result = insert_rows("test-project", "test-dataset", "test-table", [{"id": 1}])
        
        # Should succeed and initialize rows list
        self.assertTrue(result)
        table = DB['projects'][0]['datasets'][0]['tables'][0]
        self.assertIn('rows', table)
        self.assertEqual(len(table['rows']), 1)

    def test_datetime_encoder(self):
        """Test DateTimeEncoder for JSON serialization."""
        encoder = DateTimeEncoder()
        
        # Test with datetime object
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = encoder.default(dt)
        self.assertEqual(result, dt.isoformat())
        
        # Test with non-datetime object (should use default behavior)
        with self.assertRaises(TypeError):
            encoder.default(object())

    def test_load_db_dict_to_sqlite_boolean_handling(self):
        """Test load_db_dict_to_sqlite with boolean field handling."""
        boolean_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "boolean_table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "active", "type": "BOOLEAN", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "active": True},
                                        {"id": 2, "active": False},
                                        {"id": 3, "active": None}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(boolean_data)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "boolean_table" ORDER BY id')
        rows = cursor.fetchall()
        
        # Verify boolean conversion
        self.assertEqual(rows[0][1], 1)  # True -> 1
        self.assertEqual(rows[1][1], 0)  # False -> 0
        self.assertIsNone(rows[2][1])    # None -> None
        
        conn.close()

    def test_load_db_dict_to_sqlite_non_dict_list_json_handling(self):
        """Test load_db_dict_to_sqlite with non-dict/list JSON values."""
        json_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "json_table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "data", "type": "JSON", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "data": "simple string"},
                                        {"id": 2, "data": 42},
                                        {"id": 3, "data": True},
                                        {"id": 4, "data": object()}  # Non-serializable
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(json_data)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "json_table" ORDER BY id')
        rows = cursor.fetchall()
        
        # Verify JSON handling for non-dict/list values
        self.assertEqual(rows[0][1], "simple string")
        self.assertEqual(rows[1][1], "42")
        self.assertEqual(rows[2][1], "True")
        self.assertIsNone(rows[3][1])  # Object should become None
        
        conn.close()

    def test_initialize_sqlite_db_permission_error_with_connection_retry(self):
        """Test initialize_sqlite_db with permission error and connection retry."""
        simple_db_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}],
                                    "rows": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('APIs.bigquery.SimulationEngine.utils._DEFAULT_DB_PATH', '/fake/path'):
            with patch('APIs.bigquery.SimulationEngine.utils.get_default_sqlite_db_dir', return_value=self.test_dir):
                with patch('builtins.open', mock_open(read_data=json.dumps(simple_db_data))):
                    with patch('os.path.exists', return_value=True):
                        with patch('os.remove', side_effect=PermissionError("Permission denied")):
                            with patch('sqlite3.connect') as mock_connect:
                                mock_conn = mock_connect.return_value
                                mock_cursor = mock_conn.cursor.return_value
                                
                                # Test initialization
                                initialize_sqlite_db("test-project", "test_dataset")
                                
                                # Verify the function was called
                                mock_connect.assert_called()

    def test_load_db_dict_to_sqlite_temp_db_removal_error(self):
        """Test load_db_dict_to_sqlite with temp DB removal error."""
        simple_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}],
                                    "rows": [{"id": 1}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('tempfile.gettempdir', return_value=self.test_dir):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove', side_effect=OSError("Permission denied")):
                    with patch('sqlite3.connect') as mock_connect:
                        mock_conn = mock_connect.return_value
                        mock_cursor = mock_conn.cursor.return_value
                        
                        # Test loading
                        result = load_db_dict_to_sqlite(simple_data)
                        
                        # Verify the function was called
                        mock_connect.assert_called_once()
                        self.assertIsNotNone(result)

    def test_load_db_dict_to_sqlite_json_serialization_error(self):
        """Test load_db_dict_to_sqlite with JSON serialization error."""
        # Create data with non-serializable object
        class NonSerializable:
            pass
        
        simple_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "id", "type": "JSON", "mode": "NULLABLE"}],
                                    "rows": [{"id": NonSerializable()}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('tempfile.gettempdir', return_value=self.test_dir):
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = mock_connect.return_value
                mock_cursor = mock_conn.cursor.return_value
                
                # Test loading - should handle TypeError gracefully
                result = load_db_dict_to_sqlite(simple_data)
                
                # Verify the function was called
                mock_connect.assert_called_once()
                self.assertIsNotNone(result)

    def test_load_db_dict_to_sqlite_json_serialization_typeerror_specific(self):
        """Test load_db_dict_to_sqlite with specific TypeError during JSON serialization."""
        # Create a mock that raises TypeError specifically for json.dumps
        class MockJSON:
            def __init__(self):
                self.call_count = 0
            
            def dumps(self, obj):
                self.call_count += 1
                if self.call_count == 1:  # First call raises TypeError
                    raise TypeError("Object not JSON serializable")
                return json.dumps(obj)  # Subsequent calls work normally
        
        mock_json = MockJSON()
        
        simple_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "id", "type": "JSON", "mode": "NULLABLE"}],
                                    "rows": [{"id": {"key": "value"}}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('tempfile.gettempdir', return_value=self.test_dir):
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = mock_connect.return_value
                mock_cursor = mock_conn.cursor.return_value
                
                # Patch json.dumps to use our mock
                with patch('APIs.bigquery.SimulationEngine.utils.json.dumps', side_effect=mock_json.dumps):
                    # Test loading - should handle TypeError gracefully
                    result = load_db_dict_to_sqlite(simple_data)
                    
                    # Verify the function was called
                    mock_connect.assert_called_once()
                    self.assertIsNotNone(result)

    def test_load_db_dict_to_sqlite_sqlite_error(self):
        """Test load_db_dict_to_sqlite with SQLite error during insert."""
        simple_data = {
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}],
                                    "rows": [{"id": 1}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch('tempfile.gettempdir', return_value=self.test_dir):
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = mock_connect.return_value
                mock_cursor = mock_conn.cursor.return_value
                mock_cursor.execute.side_effect = [
                    None,  # CREATE TABLE succeeds
                    sqlite3.Error("UNIQUE constraint failed")  # INSERT fails
                ]
                
                # Test loading - should handle SQLite error gracefully
                result = load_db_dict_to_sqlite(simple_data)
                
                # Verify the function was called
                mock_connect.assert_called_once()
                self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
