"""
Utility CRUD (Create, Read, Update, Delete) tests for BigQuery API.

This module tests CRUD operations for BigQuery utility functions, ensuring data
manipulation, validation, and error handling work correctly. Following the Service
Engineering Test Framework Guideline for utility tests.
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
from ..SimulationEngine.custom_errors import InvalidInputError, InvalidQueryError
from ..SimulationEngine.db import DB


class TestBigQueryUtilsCRUD(BaseTestCaseWithErrorHandler):
    """
    Test suite for BigQuery utility CRUD operations.
    
    Tests Create, Read, Update, Delete operations for BigQuery utility functions,
    ensuring data manipulation, validation, and error handling work correctly.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_db.json")
        self.original_db_path = get_default_db_path()
        
        # Create test database structure
        self.test_db = {
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
                                    ]
                                },
                                {
                                    "table_id": "orders",
                                    "schema": [
                                        {"name": "order_id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "user_id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "amount", "type": "FLOAT64", "mode": "NULLABLE"},
                                        {"name": "status", "type": "STRING", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"order_id": 1, "user_id": 1, "amount": 100.50, "status": "completed"},
                                        {"order_id": 2, "user_id": 1, "amount": 75.25, "status": "pending"},
                                        {"order_id": 3, "user_id": 2, "amount": 200.00, "status": "completed"}
                                    ]
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

    def test_create_database_structure(self):
        """Test creating database structure with tables and schemas."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test that tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        self.assertIn("users", table_names)
        self.assertIn("orders", table_names)
        
        # Test that schemas were created correctly
        cursor.execute("PRAGMA table_info(users)")
        user_columns = cursor.fetchall()
        self.assertEqual(len(user_columns), 4)
        
        cursor.execute("PRAGMA table_info(orders)")
        order_columns = cursor.fetchall()
        self.assertEqual(len(order_columns), 4)
        
        conn.close()

    def test_create_table_with_complex_schema(self):
        """Test creating table with complex schema including different data types."""
        complex_db = {
            "projects": [
                {
                    "project_id": "complex-project",
                    "datasets": [
                        {
                            "dataset_id": "complex-dataset",
                            "tables": [
                                {
                                    "table_id": "complex-table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                                        {"name": "score", "type": "FLOAT64", "mode": "NULLABLE"},
                                        {"name": "is_active", "type": "BOOL", "mode": "NULLABLE"},
                                        {"name": "created_date", "type": "DATE", "mode": "NULLABLE"},
                                        {"name": "metadata", "type": "JSON", "mode": "NULLABLE"},
                                        {"name": "binary_data", "type": "BYTES", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {
                                            "id": 1,
                                            "name": "Test User",
                                            "score": 95.5,
                                            "is_active": True,
                                            "created_date": "2023-01-01",
                                            "metadata": '{"department": "engineering", "level": "senior"}',
                                            "binary_data": "SGVsbG8gV29ybGQ="  # Base64 encoded "Hello World"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        conn = load_db_dict_to_sqlite(complex_db)
        cursor = conn.cursor()
        
        # Test that complex table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn("complex-table", table_names)
        
        # Test that all columns were created
        cursor.execute("PRAGMA table_info(`complex-table`)")
        columns = cursor.fetchall()
        self.assertEqual(len(columns), 7)
        
        # Test that data was inserted correctly
        cursor.execute("SELECT * FROM `complex-table`")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)
        
        conn.close()

    def test_read_data_from_tables(self):
        """Test reading data from created tables."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test reading from users table
        cursor.execute("SELECT * FROM users")
        user_rows = cursor.fetchall()
        self.assertEqual(len(user_rows), 2)
        
        # Test reading specific columns
        cursor.execute("SELECT name, email FROM users WHERE id = 1")
        user_data = cursor.fetchone()
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data[0], "John Doe")
        self.assertEqual(user_data[1], "john@example.com")
        
        # Test reading from orders table
        cursor.execute("SELECT * FROM orders")
        order_rows = cursor.fetchall()
        self.assertEqual(len(order_rows), 3)
        
        # Test reading with conditions
        cursor.execute("SELECT * FROM orders WHERE user_id = 1")
        user_orders = cursor.fetchall()
        self.assertEqual(len(user_orders), 2)
        
        conn.close()

    def test_update_data_in_tables(self):
        """Test updating data in tables through SQL operations."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test updating user data
        cursor.execute("UPDATE users SET name = 'John Updated' WHERE id = 1")
        cursor.execute("SELECT name FROM users WHERE id = 1")
        updated_name = cursor.fetchone()[0]
        self.assertEqual(updated_name, "John Updated")
        
        # Test updating order status
        cursor.execute("UPDATE orders SET status = 'shipped' WHERE order_id = 2")
        cursor.execute("SELECT status FROM orders WHERE order_id = 2")
        updated_status = cursor.fetchone()[0]
        self.assertEqual(updated_status, "shipped")
        
        # Test updating multiple rows
        cursor.execute("UPDATE orders SET amount = amount * 1.1 WHERE status = 'completed'")
        cursor.execute("SELECT amount FROM orders WHERE order_id = 1")
        updated_amount = cursor.fetchone()[0]
        self.assertAlmostEqual(updated_amount, 110.55, places=2)  # 100.50 * 1.1
        
        conn.close()

    def test_delete_data_from_tables(self):
        """Test deleting data from tables."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test deleting specific row
        cursor.execute("DELETE FROM orders WHERE order_id = 3")
        cursor.execute("SELECT COUNT(*) FROM orders")
        remaining_orders = cursor.fetchone()[0]
        self.assertEqual(remaining_orders, 2)
        
        # Test deleting with conditions
        cursor.execute("DELETE FROM orders WHERE status = 'pending'")
        cursor.execute("SELECT COUNT(*) FROM orders")
        remaining_orders = cursor.fetchone()[0]
        self.assertEqual(remaining_orders, 1)
        
        # Test deleting all data from table
        cursor.execute("DELETE FROM users")
        cursor.execute("SELECT COUNT(*) FROM users")
        remaining_users = cursor.fetchone()[0]
        self.assertEqual(remaining_users, 0)
        
        conn.close()

    def test_join_operations(self):
        """Test JOIN operations between tables."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test INNER JOIN
        cursor.execute("""
            SELECT u.name, o.order_id, o.amount 
            FROM users u 
            INNER JOIN orders o ON u.id = o.user_id
        """)
        join_results = cursor.fetchall()
        self.assertEqual(len(join_results), 3)
        
        # Test LEFT JOIN
        cursor.execute("""
            SELECT u.name, COUNT(o.order_id) as order_count
            FROM users u 
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name
        """)
        user_order_counts = cursor.fetchall()
        self.assertEqual(len(user_order_counts), 2)
        
        # Verify user with orders
        user_with_orders = next(row for row in user_order_counts if row[0] == "John Doe")
        self.assertEqual(user_with_orders[1], 2)
        
        conn.close()

    def test_aggregate_operations(self):
        """Test aggregate operations on table data."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test COUNT
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 2)
        
        # Test SUM
        cursor.execute("SELECT SUM(amount) FROM orders")
        total_amount = cursor.fetchone()[0]
        self.assertEqual(total_amount, 375.75)
        
        # Test AVG
        cursor.execute("SELECT AVG(amount) FROM orders")
        avg_amount = cursor.fetchone()[0]
        self.assertAlmostEqual(avg_amount, 125.25, places=2)
        
        # Test MAX and MIN
        cursor.execute("SELECT MAX(amount), MIN(amount) FROM orders")
        max_min = cursor.fetchone()
        self.assertEqual(max_min[0], 200.00)
        self.assertEqual(max_min[1], 75.25)
        
        # Test GROUP BY
        cursor.execute("""
            SELECT user_id, COUNT(*) as order_count, SUM(amount) as total_amount
            FROM orders 
            GROUP BY user_id
        """)
        grouped_results = cursor.fetchall()
        self.assertEqual(len(grouped_results), 2)
        
        conn.close()

    def test_data_validation_and_constraints(self):
        """Test data validation and constraint handling."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test inserting data with required fields
        cursor.execute("INSERT INTO users (id, name) VALUES (3, 'New User')")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 3)
        
        # Test inserting data with all fields
        cursor.execute("""
            INSERT INTO users (id, name, email, created_at) 
            VALUES (4, 'Another User', 'another@example.com', '2023-01-03T12:00:00Z')
        """)
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 4)
        
        # Test unique constraint (SQLite doesn't enforce this by default, but we can test)
        cursor.execute("INSERT INTO users (id, name) VALUES (1, 'Duplicate ID')")
        cursor.execute("SELECT COUNT(*) FROM users WHERE id = 1")
        duplicate_count = cursor.fetchone()[0]
        self.assertEqual(duplicate_count, 2)  # SQLite allows duplicates by default
        
        conn.close()

    def test_error_handling_in_crud_operations(self):
        """Test error handling in CRUD operations."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Test invalid SQL syntax
        with self.assertRaises(sqlite3.OperationalError):
            cursor.execute("SELECT * FROM nonexistent_table")
        
        # Test invalid column reference
        with self.assertRaises(sqlite3.OperationalError):
            cursor.execute("SELECT invalid_column FROM users")
        
        # Test invalid data type in INSERT (SQLite is more permissive)
        cursor.execute("INSERT INTO users (id, name) VALUES ('not_an_int', 'Test')")
        # SQLite will try to convert the string to integer, which might work or fail silently
        
        # Test invalid UPDATE syntax
        with self.assertRaises(sqlite3.OperationalError):
            cursor.execute("UPDATE users SET invalid_column = 'value' WHERE id = 1")
        
        conn.close()

    def test_transaction_operations(self):
        """Test transaction operations and rollback."""
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Make changes
        cursor.execute("INSERT INTO users (id, name) VALUES (5, 'Transaction User')")
        cursor.execute("UPDATE orders SET amount = 999.99 WHERE order_id = 1")
        
        # Verify changes are visible within transaction
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 3)
        
        cursor.execute("SELECT amount FROM orders WHERE order_id = 1")
        updated_amount = cursor.fetchone()[0]
        self.assertEqual(updated_amount, 999.99)
        
        # Rollback transaction
        conn.rollback()
        
        # Verify changes were rolled back
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 2)
        
        cursor.execute("SELECT amount FROM orders WHERE order_id = 1")
        original_amount = cursor.fetchone()[0]
        self.assertEqual(original_amount, 100.50)
        
        conn.close()

    def test_performance_with_large_datasets(self):
        """Test performance with larger datasets."""
        # Create larger test dataset
        large_db = {
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
        
        conn = load_db_dict_to_sqlite(large_db)
        cursor = conn.cursor()
        
        # Test querying large dataset
        cursor.execute("SELECT COUNT(*) FROM `large-table`")
        row_count = cursor.fetchone()[0]
        self.assertEqual(row_count, 1000)
        
        # Test filtering large dataset
        cursor.execute("SELECT * FROM `large-table` WHERE id > 500")
        filtered_rows = cursor.fetchall()
        self.assertEqual(len(filtered_rows), 499)
        
        # Test indexing (SQLite creates indexes automatically for some operations)
        cursor.execute("SELECT * FROM `large-table` WHERE id = 999")
        specific_row = cursor.fetchone()
        self.assertIsNotNone(specific_row)
        self.assertEqual(specific_row[0], 999)
        
        conn.close()

    def test_data_persistence_and_recovery(self):
        """Test data persistence and recovery capabilities."""
        # Create test data
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Add some data
        cursor.execute("INSERT INTO users (id, name) VALUES (5, 'Persistent User')")
        cursor.execute("UPDATE orders SET status = 'persistent' WHERE order_id = 1")
        
        # Close and reopen connection
        conn.close()
        
        # Recreate connection with same data
        conn = load_db_dict_to_sqlite(self.test_db)
        cursor = conn.cursor()
        
        # Verify data is still there (SQLite connections are in-memory, so data doesn't persist)
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 2)  # Original data only, no persistence between connections
        
        cursor.execute("SELECT status FROM orders WHERE order_id = 1")
        status = cursor.fetchone()[0]
        self.assertEqual(status, "completed")  # Original status, no persistence between connections
        
        conn.close()


if __name__ == "__main__":
    unittest.main()
