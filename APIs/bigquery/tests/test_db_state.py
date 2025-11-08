"""
Database state (Load/Save) tests for BigQuery API.

This module tests that BigQuery data can be saved and loaded correctly, ensuring
backward compatibility and proper state management. Following the Service Engineering
Test Framework Guideline for state tests.
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
    load_db_dict_to_sqlite,
    get_default_db_path,
    set_default_db_path,
    DateTimeEncoder
)
from ..SimulationEngine.custom_errors import InvalidInputError
from ..SimulationEngine.db import save_state, load_state, DB


class TestBigQueryDBState(BaseTestCaseWithErrorHandler):
    """
    Test suite for BigQuery database state management.
    
    Tests that data can be saved and loaded correctly, ensuring backward compatibility
    and proper state management for the BigQuery simulation engine.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_db.json")
        self.original_db_path = get_default_db_path()
        
        # Sample database state for testing
        self.sample_db_state = {
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
                                        {"name": "email", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "John Doe", "email": "john@example.com"},
                                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
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

    def test_save_database_state_to_json(self):
        """Test saving database state to JSON file."""
        # Save sample database state to JSON
        with open(self.test_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_db_state, f, cls=DateTimeEncoder, indent=2)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Verify file content
        with open(self.test_db_path, 'r', encoding='utf-8') as f:
            loaded_state = json.load(f)
        
        self.assertEqual(loaded_state, self.sample_db_state)

    def test_load_database_state_from_json(self):
        """Test loading database state from JSON file."""
        # Save sample database state to JSON
        with open(self.test_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_db_state, f, cls=DateTimeEncoder, indent=2)
        
        # Load database state from JSON
        with open(self.test_db_path, 'r', encoding='utf-8') as f:
            loaded_state = json.load(f)
        
        # Verify loaded state matches original
        self.assertEqual(loaded_state, self.sample_db_state)
        
        # Verify structure integrity
        self.assertIn("projects", loaded_state)
        self.assertIsInstance(loaded_state["projects"], list)
        self.assertEqual(len(loaded_state["projects"]), 1)
        
        project = loaded_state["projects"][0]
        self.assertIn("project_id", project)
        self.assertIn("datasets", project)
        self.assertEqual(project["project_id"], "test-project")

    def test_load_database_state_to_sqlite(self):
        """Test loading database state into SQLite."""
        # Load database state into SQLite
        conn = load_db_dict_to_sqlite(self.sample_db_state)
        cursor = conn.cursor()
        
        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("users", table_names)
        
        # Verify data was loaded
        cursor.execute("SELECT COUNT(*) FROM users")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 2)
        
        # Verify specific data
        cursor.execute("SELECT name, email FROM users WHERE id = 1")
        user_data = cursor.fetchone()
        self.assertEqual(user_data[0], "John Doe")
        self.assertEqual(user_data[1], "john@example.com")
        
        conn.close()

    def test_backward_compatibility_old_format(self):
        """Test backward compatibility with older database format."""
        # Simulate older database format (without some newer fields)
        old_format_db = {
            "projects": [
                {
                    "project_id": "old-project",
                    "datasets": [
                        {
                            "dataset_id": "old-dataset",
                            "tables": [
                                {
                                    "table_id": "old-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"}
                                    ],
                                    "rows": [
                                        {"id": 1}
                                    ]
                                    # Missing newer fields like type, creation_time, etc.
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Should handle old format gracefully
        conn = load_db_dict_to_sqlite(old_format_db)
        cursor = conn.cursor()
        
        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("old-table", table_names)
        
        # Verify data was loaded
        cursor.execute("SELECT COUNT(*) FROM `old-table`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 1)
        
        conn.close()

    def test_backward_compatibility_new_format(self):
        """Test that new format works with existing data."""
        # Create database with new format features
        new_format_db = {
            "projects": [
                {
                    "project_id": "new-project",
                    "datasets": [
                        {
                            "dataset_id": "new-dataset",
                            "tables": [
                                {
                                    "table_id": "new-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "metadata", "type": "JSON", "mode": "NULLABLE"},
                                        {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {
                                            "id": 1,
                                            "metadata": '{"version": "2.0", "features": ["json", "timestamp"]}',
                                            "created_at": "2023-01-01T10:00:00Z"
                                        }
                                    ],
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T10:00:00Z",
                                    "last_modified_time": "2023-01-01T10:00:00Z",
                                    "labels": {"environment": "test"},
                                    "description": "Test table with new features"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Should handle new format correctly
        conn = load_db_dict_to_sqlite(new_format_db)
        cursor = conn.cursor()
        
        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("new-table", table_names)
        
        # Verify data was loaded
        cursor.execute("SELECT COUNT(*) FROM `new-table`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 1)
        
        conn.close()

    def test_database_state_persistence(self):
        """Test that database state persists across operations."""
        # Create initial state
        initial_state = {
            "projects": [
                {
                    "project_id": "persistent-project",
                    "datasets": [
                        {
                            "dataset_id": "persistent-dataset",
                            "tables": [
                                {
                                    "table_id": "persistent-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "value", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "value": "initial"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Load state into SQLite
        conn = load_db_dict_to_sqlite(initial_state)
        cursor = conn.cursor()
        
        # Verify initial state
        cursor.execute("SELECT COUNT(*) FROM `persistent-table`")
        initial_count = cursor.fetchone()[0]
        self.assertEqual(initial_count, 1)
        
        # Modify data
        cursor.execute("INSERT INTO `persistent-table` (id, value) VALUES (2, 'added')")
        cursor.execute("UPDATE `persistent-table` SET value = 'updated' WHERE id = 1")
        
        # Verify modifications
        cursor.execute("SELECT COUNT(*) FROM `persistent-table`")
        modified_count = cursor.fetchone()[0]
        self.assertEqual(modified_count, 2)
        
        cursor.execute("SELECT value FROM `persistent-table` WHERE id = 1")
        updated_value = cursor.fetchone()[0]
        self.assertEqual(updated_value, "updated")
        
        conn.close()

    def test_database_state_validation(self):
        """Test validation of database state structure."""
        # Test valid state
        valid_state = {
            "projects": [
                {
                    "project_id": "valid-project",
                    "datasets": [
                        {
                            "dataset_id": "valid-dataset",
                            "tables": [
                                {
                                    "table_id": "valid-table",
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
        
        # Should load without errors
        conn = load_db_dict_to_sqlite(valid_state)
        conn.close()
        
        # Test invalid state (missing required fields)
        invalid_states = [
            {},  # Empty dict
            {"projects": []},  # Empty projects
            {"projects": [{"project_id": "test"}]},  # Missing datasets
            {"projects": [{"project_id": "test", "datasets": []}]},  # Empty datasets
        ]
        
        for invalid_state in invalid_states:
            with self.subTest(invalid_state=invalid_state):
                # Should handle gracefully (may not create tables but shouldn't crash)
                conn = load_db_dict_to_sqlite(invalid_state)
                conn.close()
        
        # Test None projects (should raise TypeError)
        with self.assertRaises(TypeError):
            load_db_dict_to_sqlite({"projects": None})

    def test_database_state_error_recovery(self):
        """Test error recovery in database state operations."""
        # Test with corrupted JSON
        corrupted_json = '{"projects": [{"project_id": "test", "datasets": [{"dataset_id": "test", "tables": [{"table_id": "test", "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}], "rows": []}]}]}]}'
        
        # Save corrupted JSON
        with open(self.test_db_path, 'w', encoding='utf-8') as f:
            f.write(corrupted_json)
        
        # Should be able to load corrupted JSON (it's actually valid)
        with open(self.test_db_path, 'r', encoding='utf-8') as f:
            loaded_state = json.load(f)
        
        # Should load into SQLite
        conn = load_db_dict_to_sqlite(loaded_state)
        conn.close()
        
        # Test with truly invalid JSON
        invalid_json = '{"projects": [{"project_id": "test", "datasets": [{"dataset_id": "test", "tables": [{"table_id": "test", "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}], "rows": []}]}]}'
        
        with open(self.test_db_path, 'w', encoding='utf-8') as f:
            f.write(invalid_json)
        
        # Should raise JSON decode error
        with self.assertRaises(json.JSONDecodeError):
            with open(self.test_db_path, 'r', encoding='utf-8') as f:
                json.load(f)

    def test_database_state_performance(self):
        """Test performance with large database states."""
        # Create large database state
        large_state = {
            "projects": [
                {
                    "project_id": "large-project",
                    "datasets": [
                        {
                            "dataset_id": "large-dataset",
                            "tables": [
                                {
                                    "table_id": "large-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "value", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": i, "value": f"value_{i}"} 
                                        for i in range(1000)
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Test saving large state
        with open(self.test_db_path, 'w', encoding='utf-8') as f:
            json.dump(large_state, f, cls=DateTimeEncoder, indent=2)
        
        # Verify file size is reasonable
        file_size = os.path.getsize(self.test_db_path)
        self.assertGreater(file_size, 0)
        self.assertLess(file_size, 1024 * 1024)  # Less than 1MB
        
        # Test loading large state
        with open(self.test_db_path, 'r', encoding='utf-8') as f:
            loaded_state = json.load(f)
        
        self.assertEqual(loaded_state, large_state)
        
        # Test loading into SQLite
        conn = load_db_dict_to_sqlite(large_state)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM `large-table`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 1000)
        
        conn.close()

    def test_database_state_cleanup(self):
        """Test cleanup of database state resources."""
        # Create database state
        conn = load_db_dict_to_sqlite(self.sample_db_state)
        
        # Verify connection is active
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 2)
        
        # Close connection
        conn.close()
        
        # Verify connection is closed
        with self.assertRaises(sqlite3.ProgrammingError):
            cursor.execute("SELECT 1")

    def test_database_state_file_operations(self):
        """Test file operations for database state."""
        # Test setting custom database path (create file first)
        custom_path = os.path.join(self.test_dir, "custom_db.json")
        
        # Create the file first
        with open(custom_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_db_state, f, cls=DateTimeEncoder, indent=2)
        
        set_default_db_path(custom_path)
        
        # Verify path was set
        self.assertEqual(get_default_db_path(), custom_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(custom_path))
        
        # Test loading from custom path
        with open(custom_path, 'r', encoding='utf-8') as f:
            loaded_state = json.load(f)
        
        self.assertEqual(loaded_state, self.sample_db_state)

    def test_save_state_function(self):
        """Test the save_state function from db.py."""
        # Create a test file path
        test_save_path = os.path.join(self.test_dir, "test_save_state.json")
        
        # Save the current state
        save_state(test_save_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(test_save_path))
        
        # Verify file content
        with open(test_save_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # Verify the saved data has the expected structure
        self.assertIn("projects", saved_data)
        self.assertIsInstance(saved_data["projects"], list)

    def test_load_state_function(self):
        """Test the load_state function from db.py."""
        # Create a test file with custom data
        test_load_path = os.path.join(self.test_dir, "test_load_state.json")
        custom_data = {
            "projects": [
                {
                    "project_id": "load-test-project",
                    "datasets": [
                        {
                            "dataset_id": "load-test-dataset",
                            "tables": [
                                {
                                    "table_id": "load-test-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"}
                                    ],
                                    "rows": [{"id": 1}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Save custom data to file
        with open(test_load_path, 'w', encoding='utf-8') as f:
            json.dump(custom_data, f, indent=2)
        
        # Store original DB state
        original_db = DB.copy()
        
        try:
            # Load the custom state
            load_state(test_load_path)
            
            # Verify DB was updated
            self.assertIn("projects", DB)
            self.assertEqual(len(DB["projects"]), 1)
            self.assertEqual(DB["projects"][0]["project_id"], "load-test-project")
            
        finally:
            # Restore original DB state
            DB.clear()
            DB.update(original_db)

    def test_save_and_load_state_integration(self):
        """Test save_state and load_state functions work together."""
        # Create test data
        test_data = {
            "projects": [
                {
                    "project_id": "integration-test",
                    "datasets": [
                        {
                            "dataset_id": "integration-dataset",
                            "tables": [
                                {
                                    "table_id": "integration-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "Test User"},
                                        {"id": 2, "name": "Another User"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Store original DB state
        original_db = DB.copy()
        
        try:
            # Update DB with test data
            DB.clear()
            DB.update(test_data)
            
            # Save state
            test_save_path = os.path.join(self.test_dir, "integration_test.json")
            save_state(test_save_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(test_save_path))
            
            # Clear DB
            DB.clear()
            self.assertEqual(len(DB), 0)
            
            # Load state back
            load_state(test_save_path)
            
            # Verify data was restored
            self.assertIn("projects", DB)
            self.assertEqual(len(DB["projects"]), 1)
            self.assertEqual(DB["projects"][0]["project_id"], "integration-test")
            
            # Verify table data
            table = DB["projects"][0]["datasets"][0]["tables"][0]
            self.assertEqual(table["table_id"], "integration-table")
            self.assertEqual(len(table["rows"]), 2)
            
        finally:
            # Restore original DB state
            DB.clear()
            DB.update(original_db)

    def test_save_state_error_handling(self):
        """Test save_state function error handling."""
        # Test with invalid file path (directory that doesn't exist)
        invalid_path = "/nonexistent/directory/test.json"
        
        with self.assertRaises(FileNotFoundError):
            save_state(invalid_path)

    def test_load_state_error_handling(self):
        """Test load_state function error handling."""
        # Test with non-existent file
        non_existent_path = os.path.join(self.test_dir, "non_existent.json")
        
        with self.assertRaises(FileNotFoundError):
            load_state(non_existent_path)
        
        # Test with invalid JSON file
        invalid_json_path = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_path, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        with self.assertRaises(json.JSONDecodeError):
            load_state(invalid_json_path)


if __name__ == "__main__":
    unittest.main()
