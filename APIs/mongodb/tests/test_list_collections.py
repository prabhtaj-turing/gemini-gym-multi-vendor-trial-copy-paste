import unittest
import copy
from pathlib import Path # For managing temp state file
from typing import Any, Dict, Optional, List

# Assuming relative imports are correct for your project structure
from ..SimulationEngine import custom_errors 
from ..collection_management import list_collections # Function under test
from ..SimulationEngine.db import DB, MongoDB, save_state, load_state # Import MongoDB class and state functions
from common_utils.base_case import BaseTestCaseWithErrorHandler # For assert_error_behavior
from pydantic import ValidationError as PydanticValidationError


class TestListCollections(BaseTestCaseWithErrorHandler):
    """
    Test suite for list_collections function with comprehensive coverage.
    """

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()
        # Reset DB to clean state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        # Ensure a connection is active
        DB.switch_connection("default_test_conn")
        
        # Set up test databases and collections
        self._setup_test_data()

    def tearDown(self):
        """Clean up test environment after each test."""
        super().tearDown()
        # Reset DB to clean state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None

    def _setup_test_data(self):
        """Set up test data for various test scenarios."""
        # Database: prod_db
        DB.use_database("prod_db")
        
        # Collection: users
        users_collection = DB.connections[DB.current_conn][DB.current_db]["users"]
        users_collection.insert_many([
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "Los Angeles"},
            {"name": "Charlie", "age": 35, "city": "Chicago"}
        ])
        
        # Collection: products
        products_collection = DB.connections[DB.current_conn][DB.current_db]["products"]
        products_collection.insert_many([
            {"name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"name": "Book", "price": 19.99, "category": "Education"},
            {"name": "Chair", "price": 149.99, "category": "Furniture"}
        ])
        
        # Collection: orders
        orders_collection = DB.connections[DB.current_conn][DB.current_db]["orders"]
        orders_collection.insert_many([
            {"user_id": 1, "product_id": 1, "quantity": 2, "total": 1999.98},
            {"user_id": 2, "product_id": 2, "quantity": 1, "total": 19.99},
            {"user_id": 3, "product_id": 3, "quantity": 1, "total": 149.99}
        ])
        
        # Database: test_db
        DB.use_database("test_db")
        
        # Collection: employees
        employees_collection = DB.connections[DB.current_conn][DB.current_db]["employees"]
        employees_collection.insert_many([
            {"name": "John", "department": "Engineering", "salary": 75000},
            {"name": "Jane", "department": "Marketing", "salary": 65000},
            {"name": "Mike", "department": "Sales", "salary": 55000}
        ])
        
        # Collection: departments
        departments_collection = DB.connections[DB.current_conn][DB.current_db]["departments"]
        departments_collection.insert_many([
            {"name": "Engineering", "budget": 500000, "head": "Alice"},
            {"name": "Marketing", "budget": 300000, "head": "Bob"},
            {"name": "Sales", "budget": 200000, "head": "Charlie"}
        ])
        
        # Database: analytics_db
        DB.use_database("analytics_db")
        
        # Collection: metrics
        metrics_collection = DB.connections[DB.current_conn][DB.current_db]["metrics"]
        metrics_collection.insert_many([
            {"metric": "page_views", "value": 1000, "date": "2023-01-01"},
            {"metric": "unique_visitors", "value": 500, "date": "2023-01-01"},
            {"metric": "conversion_rate", "value": 0.05, "date": "2023-01-01"}
        ])
        
        # Collection: reports
        reports_collection = DB.connections[DB.current_conn][DB.current_db]["reports"]
        reports_collection.insert_many([
            {"report_name": "Monthly Sales", "generated_date": "2023-01-31", "status": "completed"},
            {"report_name": "User Analytics", "generated_date": "2023-01-31", "status": "completed"},
            {"report_name": "Performance Metrics", "generated_date": "2023-01-31", "status": "pending"}
        ])

        # Database: empty_db (create a database that exists but has no collections)
        # Due to mongomock limitations, we'll create this database with a collection that stays
        DB.use_database("empty_db")
        # Create a placeholder collection to ensure database exists
        placeholder_collection = DB.connections[DB.current_conn][DB.current_db]["placeholder"]
        placeholder_collection.insert_one({"placeholder": True})

    def test_list_collections_success_prod_db(self):
        """Test successful listing of collections in prod_db."""
        result = list_collections(database="prod_db")
        
        # Verify the result structure - should be a list of strings
        self.assertIsInstance(result, list)
        
        # Verify expected collections are present
        expected_collections = {"users", "products", "orders"}
        actual_collections = set(result)
        self.assertTrue(expected_collections.issubset(actual_collections))
        
        # Verify all items are strings
        for collection_name in result:
            self.assertIsInstance(collection_name, str)

    def test_list_collections_success_test_db(self):
        """Test successful listing of collections in test_db."""
        result = list_collections(database="test_db")
        
        # Verify the result structure - should be a list of strings
        self.assertIsInstance(result, list)
        
        # Verify expected collections are present
        expected_collections = {"employees", "departments"}
        actual_collections = set(result)
        self.assertTrue(expected_collections.issubset(actual_collections))
        
        # Verify all items are strings
        for collection_name in result:
            self.assertIsInstance(collection_name, str)

    def test_list_collections_success_analytics_db(self):
        """Test successful listing of collections in analytics_db."""
        result = list_collections(database="analytics_db")
        
        # Verify the result structure - should be a list of strings
        self.assertIsInstance(result, list)
        
        # Verify expected collections are present
        expected_collections = {"metrics", "reports"}
        actual_collections = set(result)
        self.assertTrue(expected_collections.issubset(actual_collections))
        
        # Verify all items are strings
        for collection_name in result:
            self.assertIsInstance(collection_name, str)

    def test_list_collections_empty_database(self):
        """Test listing collections in a database with minimal collections."""
        # Test the empty_db which has only a placeholder collection
        result = list_collections(database="empty_db")
        
        # Should return list with only the placeholder collection
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn("placeholder", result)

    def test_list_collections_nonexistent_database(self):
        """Test listing collections in a nonexistent database."""
        self.assert_error_behavior(
            lambda: list_collections(database="nonexistent_db"),
            custom_errors.DatabaseNotFoundError,
            "Database 'nonexistent_db' not found on connection 'default_test_conn'."
        )

    def test_list_collections_collection_metadata(self):
        """Test that collection names are returned correctly."""
        result = list_collections(database="prod_db")

        # Verify we get collection names as strings
        self.assertIsInstance(result, list)
        self.assertIn("users", result)
        self.assertIn("products", result)
        self.assertIn("orders", result)

    def test_list_collections_multiple_databases_isolation(self):
        """Test that collections from different databases are properly isolated."""
        # Get collections from prod_db
        prod_result = list_collections(database="prod_db")
        prod_collections = set(prod_result)
        
        # Get collections from test_db
        test_result = list_collections(database="test_db")
        test_collections = set(test_result)
        
        # Get collections from analytics_db
        analytics_result = list_collections(database="analytics_db")
        analytics_collections = set(analytics_result)
        
        # Verify isolation - collections should be different
        self.assertNotEqual(prod_collections, test_collections)
        self.assertNotEqual(prod_collections, analytics_collections)
        self.assertNotEqual(test_collections, analytics_collections)
        
        # Verify expected collections in each database
        self.assertTrue({"users", "products", "orders"}.issubset(prod_collections))
        self.assertTrue({"employees", "departments"}.issubset(test_collections))
        self.assertTrue({"metrics", "reports"}.issubset(analytics_collections))

    def test_list_collections_result_consistency(self):
        """Test that multiple calls return consistent results."""
        # Call list_collections multiple times
        result1 = list_collections(database="prod_db")
        result2 = list_collections(database="prod_db")
        result3 = list_collections(database="prod_db")
        
        # Verify results are consistent
        self.assertEqual(set(result1), set(result2))
        self.assertEqual(set(result2), set(result3))

    def test_list_collections_case_sensitivity(self):
        """Test database name case sensitivity."""
        # Test with different cases (should be case-sensitive)
        result_lower = list_collections(database="prod_db")
        
        # This should fail because PROD_DB doesn't exist (case sensitive)
        self.assert_error_behavior(
            lambda: list_collections(database="PROD_DB"),
            custom_errors.DatabaseNotFoundError,
            "Database 'PROD_DB' not found on connection 'default_test_conn'."
        )

    def test_list_collections_special_characters_in_database_name(self):
        """Test database names with special characters."""
        # Create a database with special characters
        special_db_name = "test_db_with_underscores_123"
        DB.use_database(special_db_name)
        
        # Add a collection to the special database
        special_collection = DB.connections[DB.current_conn][DB.current_db]["special_collection"]
        special_collection.insert_one({"test": "data"})
        
        # Test listing collections
        result = list_collections(database=special_db_name)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertIn("special_collection", result)

    def test_list_collections_large_number_of_collections(self):
        """Test listing a large number of collections."""
        # Create a database with many collections
        large_db_name = "large_db"
        DB.use_database(large_db_name)
        
        # Create multiple collections
        num_collections = 50
        expected_collections = []
        for i in range(num_collections):
            collection_name = f"collection_{i:03d}"
            expected_collections.append(collection_name)
            collection = DB.connections[DB.current_conn][DB.current_db][collection_name]
            collection.insert_one({"index": i, "data": f"test_data_{i}"})
        
        # Test listing collections
        result = list_collections(database=large_db_name)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), num_collections)
        
        # Verify all expected collections are present
        result_set = set(result)
        expected_set = set(expected_collections)
        self.assertEqual(result_set, expected_set)

    def test_list_collections_with_indexes(self):
        """Test listing collections that have indexes."""
        # Create a collection with indexes
        DB.use_database("indexed_db")
        indexed_collection = DB.connections[DB.current_conn][DB.current_db]["indexed_collection"]
        
        # Insert some data
        indexed_collection.insert_many([
            {"name": "Alice", "email": "alice@example.com", "age": 30},
            {"name": "Bob", "email": "bob@example.com", "age": 25}
        ])
        
        # Create indexes
        indexed_collection.create_index("name")
        indexed_collection.create_index("email", unique=True)
        indexed_collection.create_index([("name", 1), ("age", -1)])
        
        # Test listing collections
        result = list_collections(database="indexed_db")
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertIn("indexed_collection", result)

    def test_list_collections_with_capped_collections(self):
        """Test listing capped collections."""
        # Note: mongomock may not fully support capped collections,
        # but we can test the basic structure
        DB.use_database("capped_db")
        
        # Create a regular collection (mongomock limitation)
        capped_collection = DB.connections[DB.current_conn][DB.current_db]["capped_collection"]
        capped_collection.insert_many([
            {"message": "log entry 1", "timestamp": "2023-01-01T10:00:00Z"},
            {"message": "log entry 2", "timestamp": "2023-01-01T10:01:00Z"}
        ])
        
        # Test listing collections
        result = list_collections(database="capped_db")
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertIn("capped_collection", result)

    def test_list_collections_performance_with_many_documents(self):
        """Test performance when collections have many documents."""
        # Create a database with collections containing many documents
        perf_db_name = "performance_db"
        DB.use_database(perf_db_name)
        
        # Create collections with many documents
        large_collection = DB.connections[DB.current_conn][DB.current_db]["large_collection"]
        
        # Insert many documents
        batch_size = 1000
        documents = [{"index": i, "data": f"data_{i}"} for i in range(batch_size)]
        large_collection.insert_many(documents)
        
        # Test listing collections (should be fast regardless of document count)
        result = list_collections(database=perf_db_name)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertIn("large_collection", result)

    # Test input validation
    def test_list_collections_raises_ValidationError_empty_database_name(self):
        """Test that empty database name raises validation error."""
        self.assert_error_behavior(
            lambda: list_collections(database=""),
            custom_errors.ValidationError,
            "Input 'database' cannot be an empty string."
        )

    def test_list_collections_raises_ValidationError_non_string_database_name(self):
        """Test that non-string database name raises validation error."""
        self.assert_error_behavior(
            lambda: list_collections(database=123),
            custom_errors.ValidationError,
            "Input 'database' must be a string."
        )


if __name__ == '__main__':
    unittest.main()