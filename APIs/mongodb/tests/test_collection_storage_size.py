import unittest
import copy
from pathlib import Path # For managing temp state file
from typing import Any, Dict, Optional, List 
import json
from unittest.mock import patch, MagicMock

# Assuming relative imports are correct for your project structure
from ..SimulationEngine import custom_errors 
from ..collection_management import collection_storage_size # Function under test
from ..SimulationEngine.db import DB, MongoDB, save_state, load_state # Import MongoDB class and state functions
from common_utils.base_case import BaseTestCaseWithErrorHandler # For assert_error_behavior
from pydantic import ValidationError as PydanticValidationError

class TestCollectionStorageSize(BaseTestCaseWithErrorHandler):
    """
    Test suite for collection_storage_size function with comprehensive coverage.
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

        # Set up test databases and collections for various test scenarios
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
        # Database 1: test_db1 with various collections
        db1 = DB.use_database("test_db1") 
        
        # Small collection with basic documents
        db1["small_collection"].insert_many([
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "Los Angeles"},
            {"name": "Charlie", "age": 35, "city": "Chicago"},
            {"name": "David", "age": 28, "city": "Miami"},
            {"name": "Eve", "age": 32, "city": "Seattle"},
            {"name": "Frank", "age": 27, "city": "Boston"}
        ])
        
        # Medium collection with complex documents
        medium_docs = []
        for i in range(50):
            doc = {
                "id": i,
                "user_info": {
                    "name": f"User_{i}",
                    "email": f"user{i}@example.com",
                    "preferences": {
                        "theme": "dark" if i % 2 == 0 else "light",
                        "notifications": True,
                        "language": "en"
                    }
                },
                "activity": {
                    "last_login": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    "login_count": i * 3,
                    "sessions": [f"session_{j}" for j in range(i % 5)]
                },
                "metadata": {
                    "created_at": f"2023-01-{(i % 28) + 1:02d}",
                    "tags": [f"tag_{j}" for j in range(i % 3)],
                    "score": i * 1.5
                }
            }
            medium_docs.append(doc)
        db1["medium_collection"].insert_many(medium_docs)
        
        # Varied size collection with documents of different sizes
        varied_docs = []
        for i in range(20):
            if i % 3 == 0:
                # Small documents
                doc = {"id": i, "type": "small", "data": "x" * 10}
            elif i % 3 == 1:
                # Medium documents
                doc = {"id": i, "type": "medium", "data": "y" * 100, "extra": {"field": "value"}}
            else:
                # Large documents
                doc = {"id": i, "type": "large", "data": "z" * 1000, "nested": {"deep": {"field": "x" * 500}}}
            varied_docs.append(doc)
        db1["varied_size_collection"].insert_many(varied_docs)
        
        # Database 2: test_db2 with specialized collections
        db2 = DB.use_database("test_db2")
        
        # Complex nested collection
        complex_docs = []
        for i in range(15):
            doc = {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "data": f"nested_data_{i}",
                                "array": [{"item": j, "value": j * i} for j in range(3)],
                                "metadata": {
                                    "timestamp": f"2023-{(i % 12) + 1:02d}-01",
                                    "flags": [True, False, True][i % 3]
                                }
                            }
                        }
                    }
                }
            }
            complex_docs.append(doc)
        db2["complex_collection"].insert_many(complex_docs)
        
        # Binary-like collection (simulating binary data with base64-like strings)
        binary_docs = []
        for i in range(10):
            doc = {
                "file_id": f"file_{i}",
                "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" * (i + 1),
                "metadata": {
                    "size": (i + 1) * 1024,
                    "type": "image/png",
                    "encoding": "base64"
                }
            }
            binary_docs.append(doc)
        db2["binary_collection"].insert_many(binary_docs)

    def test_small_collection_basic(self):
        """Test storage size calculation for a small collection."""
        result = collection_storage_size(database="test_db1", collection="small_collection")
        
        # Verify result structure - check actual return format
        self.assertIsInstance(result, dict)
        self.assertIn("ns", result)
        self.assertIn("size", result)
        self.assertIn("count", result)
        self.assertIn("storage_size", result)
        self.assertIn("avg_obj_size", result)
        self.assertIn("num_indexes", result)
        self.assertIn("total_index_size", result)
        
        # Verify values
        self.assertEqual(result["ns"], "test_db1.small_collection")
        self.assertEqual(result["count"], 6)  # We inserted 6 documents
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["storage_size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)
        self.assertGreaterEqual(result["num_indexes"], 1)  # At least _id index
        
        # Verify data types
        self.assertIsInstance(result["ns"], str)
        self.assertIsInstance(result["size"], (int, float))
        self.assertIsInstance(result["count"], int)
        self.assertIsInstance(result["storage_size"], (int, float))
        self.assertIsInstance(result["avg_obj_size"], (int, float))
        self.assertIsInstance(result["num_indexes"], int)
        self.assertIsInstance(result["total_index_size"], (int, float))

    def test_medium_collection_complex_documents(self):
        """Test storage size calculation for medium collection with complex documents."""
        result = collection_storage_size(database="test_db1", collection="medium_collection")
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ns"], "test_db1.medium_collection")
        self.assertEqual(result["count"], 50)  # We inserted 50 documents
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)

    def test_varied_size_collection(self):
        """Test storage size calculation for collection with varied document sizes."""
        result = collection_storage_size(database="test_db1", collection="varied_size_collection")
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ns"], "test_db1.varied_size_collection")
        self.assertEqual(result["count"], 20)  # We inserted 20 documents
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)

    def test_complex_nested_collection(self):
        """Test storage size calculation for collection with complex nested structures."""
        result = collection_storage_size(database="test_db2", collection="complex_collection")
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ns"], "test_db2.complex_collection")
        self.assertEqual(result["count"], 15)  # We inserted 15 documents
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)

    def test_binary_like_collection(self):
        """Test storage size calculation for collection with binary-like data."""
        result = collection_storage_size(database="test_db2", collection="binary_collection")
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ns"], "test_db2.binary_collection")
        self.assertEqual(result["count"], 10)  # We inserted 10 documents
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)

    def test_nonexistent_database(self):
        """Test storage size calculation for nonexistent database."""
        self.assert_error_behavior(
            lambda: collection_storage_size(database="nonexistent_db", collection="any_collection"),
            custom_errors.DatabaseNotFoundError,
            "Database 'nonexistent_db' not found on connection 'default_test_conn'."
        )

    def test_nonexistent_collection(self):
        """Test storage size calculation for nonexistent collection in existing database."""
        self.assert_error_behavior(
            lambda: collection_storage_size(database="test_db1", collection="nonexistent_collection"),
            custom_errors.CollectionNotFoundError,
            "Collection 'nonexistent_collection' not found in database 'test_db1' on connection 'default_test_conn'."
        )
    
    def test_empty_collection(self):
        """Test collection with no documents"""
        db_name = "test_db1"
        coll_name = "empty_collection_test"
        
        # Create a collection with documents first
        db1 = DB.use_database(db_name)
        db1[coll_name].insert_many([
            {"item": "temp1", "value": 1},
            {"item": "temp2", "value": 2}
        ])
        
        # Delete all documents to make it empty (collection will be dropped)
        db1[coll_name].delete_many({})
        
        # Now, collection_storage_size should raise CollectionNotFoundError
        from ..SimulationEngine import custom_errors
        self.assert_error_behavior(
            lambda: collection_storage_size(database=db_name, collection=coll_name),
            custom_errors.CollectionNotFoundError,
            "Collection 'empty_collection_test' not found in database 'test_db1' on connection 'default_test_conn'."
        )

    def test_large_collection_sampling(self):
        """Test collection with more than 1000 documents (sampling logic)"""
        db_name = "test_db1"
        coll_name = "large_collection"
        
        # Create a large collection with more than 1000 documents
        db1 = DB.use_database(db_name)
        large_docs = [{"item": f"item_{i}", "value": i, "data": "x" * 100} for i in range(1500)]
        db1[coll_name].insert_many(large_docs)
        
        result = collection_storage_size(database=db_name, collection=coll_name)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ns"], f"{db_name}.{coll_name}")
        self.assertEqual(result["count"], 1500)  # Should have exact count
        self.assertGreater(result["size"], 0)  # Should have estimated size
        self.assertGreater(result["avg_obj_size"], 0)

    def test_storage_size_consistency(self):
        """Test that multiple calls return consistent results."""
        # Call the function multiple times
        result1 = collection_storage_size(database="test_db1", collection="small_collection")
        result2 = collection_storage_size(database="test_db1", collection="small_collection")
        result3 = collection_storage_size(database="test_db1", collection="small_collection")
        
        # Results should be identical (no randomness in small collections)
        self.assertEqual(result1["count"], result2["count"])
        self.assertEqual(result2["count"], result3["count"])
        self.assertEqual(result1["size"], result2["size"])
        self.assertEqual(result2["size"], result3["size"])

    def test_storage_size_calculation_accuracy(self):
        """Test accuracy of storage size calculations."""
        # Create a collection with known document sizes
        db_name = "test_accuracy_db"
        coll_name = "accuracy_test_collection"
        
        db = DB.use_database(db_name)
        
        # Insert documents with predictable sizes
        test_docs = [
            {"id": 1, "data": "x" * 1000},  # ~1KB
            {"id": 2, "data": "y" * 2000},  # ~2KB
            {"id": 3, "data": "z" * 3000},  # ~3KB
        ]
        db[coll_name].insert_many(test_docs)
        
        result = collection_storage_size(database=db_name, collection=coll_name)
        
        # Verify calculations
        self.assertEqual(result["count"], 3)
        self.assertGreater(result["size"], 6000)  # Should be at least 6KB
        self.assertGreater(result["avg_obj_size"], 2000)  # Average should be > 2KB

    # Test input validation
    def test_pydantic_validation_empty_database_name(self):
        """Test that empty database name raises validation error."""
        self.assert_error_behavior(
            lambda: collection_storage_size(database="", collection="test_collection"),
            PydanticValidationError,
            "String should have at least 1 character"
        )

    def test_pydantic_validation_empty_collection_name(self):
        """Test that empty collection name raises validation error."""
        self.assert_error_behavior(
            lambda: collection_storage_size(database="test_db", collection=""),
            PydanticValidationError,
            "String should have at least 1 character"
        )

    def test_result_format_completeness(self):
        """Test that all expected fields are present in the result."""
        result = collection_storage_size(database="test_db1", collection="small_collection")
        
        # Check all required fields are present (actual format)
        required_fields = [
            "ns", "size", "count", "storage_size", 
            "avg_obj_size", "num_indexes", "total_index_size"
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing required field: {field}")

    def test_result_data_types(self):
        """Test that result fields have correct data types."""
        result = collection_storage_size(database="test_db1", collection="small_collection")
        
        # Check data types (actual format)
        self.assertIsInstance(result["ns"], str)
        self.assertIsInstance(result["size"], (int, float))
        self.assertIsInstance(result["count"], int)
        self.assertIsInstance(result["storage_size"], (int, float))
        self.assertIsInstance(result["avg_obj_size"], (int, float))
        self.assertIsInstance(result["num_indexes"], int)
        self.assertIsInstance(result["total_index_size"], (int, float))

    def test_edge_case_single_document(self):
        """Test collection with exactly one document."""
        db_name = "edge_case_db"
        coll_name = "single_doc_collection"
        
        db = DB.use_database(db_name)
        db[coll_name].insert_one({"single": "document", "data": "test"})
        
        result = collection_storage_size(database=db_name, collection=coll_name)
        
        # Verify result
        self.assertEqual(result["count"], 1)
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)
        self.assertEqual(result["size"], result["avg_obj_size"])  # For single doc, size == avg_obj_size

    def test_edge_case_exactly_1000_documents(self):
        """Test collection with exactly 1000 documents (boundary case)."""
        db_name = "boundary_db"
        coll_name = "thousand_docs_collection"
        
        db = DB.use_database(db_name)
        docs = [{"id": i, "data": f"document_{i}"} for i in range(1000)]
        db[coll_name].insert_many(docs)
        
        result = collection_storage_size(database=db_name, collection=coll_name)
        
        # Verify result
        self.assertEqual(result["count"], 1000)
        self.assertGreater(result["size"], 0)
        self.assertGreater(result["avg_obj_size"], 0)


if __name__ == '__main__':
    unittest.main()
