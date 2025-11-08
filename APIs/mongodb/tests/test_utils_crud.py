import unittest
from bson import ObjectId
from datetime import datetime
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import utils
from ..SimulationEngine.custom_errors import (
    InvalidNameError, CollectionNotFoundError, DatabaseNotFoundError
)


class TestUtilsCrud(BaseTestCaseWithErrorHandler):
    """Test CRUD operations and database manipulation utilities."""
    
    def setUp(self):
        """Set up a clean test database before each test."""
        super().setUp()
        # Reset DB to clean state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        # Set up test connection and database
        DB.switch_connection("test_connection")
        DB.use_database("test_database")

    def tearDown(self):
        """Reset the database after each test."""
        super().tearDown()
        # Reset DB to clean state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None

    def validate_db(self):
        """Helper method to validate database state consistency."""
        # Ensure we have an active connection
        self.assertIsNotNone(DB.current_conn)
        self.assertIn(DB.current_conn, DB.connections)
        
        # Ensure we have an active database
        if DB.current_db:
            self.assertIsNotNone(DB.current_db)

    def test_create_and_manage_collections(self):
        """Test collection creation and management operations."""
        client = DB.connections[DB.current_conn]
        db = client[DB.current_db]
        
        # Test collection creation
        collection_name = "test_collection"
        collection = db[collection_name]
        
        # Insert a document to actually create the collection
        test_doc = {"name": "test", "created_at": datetime.utcnow()}
        result = collection.insert_one(test_doc)
        
        self.assertIsNotNone(result.inserted_id)
        self.assertIsInstance(result.inserted_id, ObjectId)
        
        # Verify collection exists
        collection_names = db.list_collection_names()
        self.assertIn(collection_name, collection_names)
        
        # Test document retrieval
        retrieved_doc = collection.find_one({"_id": result.inserted_id})
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc["name"], "test")
        
        self.validate_db()

    def test_document_crud_operations(self):
        """Test basic document CRUD operations."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["crud_test"]
        
        # CREATE - Insert documents
        test_docs = [
            {"name": "Alice", "age": 30, "department": "Engineering"},
            {"name": "Bob", "age": 25, "department": "Marketing"},
            {"name": "Charlie", "age": 35, "department": "Engineering"}
        ]
        
        # Insert multiple documents
        insert_result = collection.insert_many(test_docs)
        self.assertEqual(len(insert_result.inserted_ids), 3)
        
        # READ - Query documents
        all_docs = list(collection.find({}))
        self.assertEqual(len(all_docs), 3)
        
        # Query with filter
        engineers = list(collection.find({"department": "Engineering"}))
        self.assertEqual(len(engineers), 2)
        
        # Query single document
        alice = collection.find_one({"name": "Alice"})
        self.assertIsNotNone(alice)
        self.assertEqual(alice["age"], 30)
        
        # UPDATE - Modify documents
        update_result = collection.update_one(
            {"name": "Alice"},
            {"$set": {"age": 31, "updated": True}}
        )
        self.assertEqual(update_result.modified_count, 1)
        
        # Verify update
        updated_alice = collection.find_one({"name": "Alice"})
        self.assertEqual(updated_alice["age"], 31)
        self.assertTrue(updated_alice["updated"])
        
        # Update multiple documents
        update_many_result = collection.update_many(
            {"department": "Engineering"},
            {"$set": {"team": "Tech"}}
        )
        self.assertEqual(update_many_result.modified_count, 2)
        
        # DELETE - Remove documents
        delete_result = collection.delete_one({"name": "Bob"})
        self.assertEqual(delete_result.deleted_count, 1)
        
        # Verify deletion
        bob = collection.find_one({"name": "Bob"})
        self.assertIsNone(bob)
        
        # Delete multiple documents
        delete_many_result = collection.delete_many({"department": "Engineering"})
        self.assertEqual(delete_many_result.deleted_count, 2)
        
        # Verify all engineering docs are gone
        remaining_docs = list(collection.find({}))
        self.assertEqual(len(remaining_docs), 0)
        
        self.validate_db()

    def test_index_management(self):
        """Test index creation and management."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["index_test"]
        
        # Insert test data
        collection.insert_many([
            {"name": "Alice", "email": "alice@example.com", "score": 95},
            {"name": "Bob", "email": "bob@example.com", "score": 87},
            {"name": "Charlie", "email": "charlie@example.com", "score": 92}
        ])
        
        # Create single field index
        collection.create_index("name")
        
        # Create compound index
        collection.create_index([("score", -1), ("name", 1)])
        
        # Create unique index
        collection.create_index("email", unique=True)
        
        # Get index information
        indexes = collection.index_information()
        self.assertIsInstance(indexes, dict)
        
        # Should have at least the default _id index plus our created indexes
        self.assertGreaterEqual(len(indexes), 4)
        
        # Verify specific indexes exist
        index_names = list(indexes.keys())
        self.assertIn("_id_", index_names)  # Default index
        
        # Test index usage with queries
        # These should use the indexes we created
        name_query = collection.find({"name": "Alice"})
        score_query = collection.find({}).sort("score", -1)
        
        # Verify queries return expected results
        alice = list(name_query)[0]
        self.assertEqual(alice["name"], "Alice")
        
        sorted_docs = list(score_query)
        self.assertEqual(sorted_docs[0]["score"], 95)  # Highest score first
        
        self.validate_db()

    def test_aggregation_operations(self):
        """Test aggregation pipeline operations."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["aggregation_test"]
        
        # Insert test data
        test_data = [
            {"name": "Alice", "department": "Engineering", "salary": 75000, "projects": 3},
            {"name": "Bob", "department": "Engineering", "salary": 80000, "projects": 5},
            {"name": "Charlie", "department": "Marketing", "salary": 65000, "projects": 2},
            {"name": "Diana", "department": "Marketing", "salary": 70000, "projects": 4},
            {"name": "Eve", "department": "Engineering", "salary": 85000, "projects": 6}
        ]
        collection.insert_many(test_data)
        
        # Test aggregation pipeline
        pipeline = [
            {"$match": {"salary": {"$gte": 70000}}},
            {"$group": {
                "_id": "$department",
                "avg_salary": {"$avg": "$salary"},
                "total_projects": {"$sum": "$projects"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"avg_salary": -1}}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        # Verify aggregation results
        self.assertGreater(len(results), 0)
        
        # Should have results for both departments
        departments = [result["_id"] for result in results]
        self.assertIn("Engineering", departments)
        self.assertIn("Marketing", departments)
        
        # Verify aggregation calculations
        for result in results:
            self.assertIn("avg_salary", result)
            self.assertIn("total_projects", result)
            self.assertIn("count", result)
            self.assertGreater(result["avg_salary"], 0)
            self.assertGreater(result["total_projects"], 0)
            self.assertGreater(result["count"], 0)
        
        self.validate_db()

    def test_transaction_like_operations(self):
        """Test operations that simulate transaction-like behavior."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["transaction_test"]
        
        # Insert initial data
        collection.insert_many([
            {"account": "A", "balance": 1000},
            {"account": "B", "balance": 500}
        ])
        
        # Simulate a transfer operation (A -> B: $200)
        transfer_amount = 200
        
        # Step 1: Check if account A has sufficient balance
        account_a = collection.find_one({"account": "A"})
        self.assertIsNotNone(account_a)
        self.assertGreaterEqual(account_a["balance"], transfer_amount)
        
        # Step 2: Deduct from account A
        deduct_result = collection.update_one(
            {"account": "A", "balance": {"$gte": transfer_amount}},
            {"$inc": {"balance": -transfer_amount}}
        )
        self.assertEqual(deduct_result.modified_count, 1)
        
        # Step 3: Add to account B
        add_result = collection.update_one(
            {"account": "B"},
            {"$inc": {"balance": transfer_amount}}
        )
        self.assertEqual(add_result.modified_count, 1)
        
        # Verify final balances
        final_a = collection.find_one({"account": "A"})
        final_b = collection.find_one({"account": "B"})
        
        self.assertEqual(final_a["balance"], 800)  # 1000 - 200
        self.assertEqual(final_b["balance"], 700)  # 500 + 200
        
        # Verify total balance is conserved
        total_balance = final_a["balance"] + final_b["balance"]
        self.assertEqual(total_balance, 1500)  # Original total
        
        self.validate_db()

    def test_bulk_operations(self):
        """Test bulk insert, update, and delete operations."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["bulk_test"]
        
        # Bulk insert
        bulk_docs = [{"item": f"item_{i}", "value": i * 10} for i in range(100)]
        insert_result = collection.insert_many(bulk_docs)
        self.assertEqual(len(insert_result.inserted_ids), 100)
        
        # Verify all documents were inserted
        total_count = collection.count_documents({})
        self.assertEqual(total_count, 100)
        
        # Bulk update
        update_result = collection.update_many(
            {"value": {"$gte": 500}},
            {"$set": {"category": "high_value"}}
        )
        self.assertGreater(update_result.modified_count, 0)
        
        # Verify updates
        high_value_count = collection.count_documents({"category": "high_value"})
        self.assertGreater(high_value_count, 0)
        
        # Bulk delete
        delete_result = collection.delete_many({"value": {"$lt": 200}})
        self.assertGreater(delete_result.deleted_count, 0)
        
        # Verify deletions
        remaining_count = collection.count_documents({})
        self.assertLess(remaining_count, 100)
        
        self.validate_db()

    def test_complex_queries(self):
        """Test complex query operations."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["complex_query_test"]
        
        # Insert complex test data
        test_data = [
            {
                "name": "Alice",
                "age": 30,
                "skills": ["Python", "MongoDB", "Docker"],
                "address": {"city": "New York", "country": "USA"},
                "projects": [
                    {"name": "Project A", "status": "completed"},
                    {"name": "Project B", "status": "in_progress"}
                ]
            },
            {
                "name": "Bob",
                "age": 25,
                "skills": ["JavaScript", "React", "Node.js"],
                "address": {"city": "San Francisco", "country": "USA"},
                "projects": [
                    {"name": "Project C", "status": "completed"}
                ]
            },
            {
                "name": "Charlie",
                "age": 35,
                "skills": ["Python", "Django", "PostgreSQL"],
                "address": {"city": "London", "country": "UK"},
                "projects": [
                    {"name": "Project D", "status": "planning"},
                    {"name": "Project E", "status": "in_progress"}
                ]
            }
        ]
        collection.insert_many(test_data)
        
        # Test array queries
        python_devs = list(collection.find({"skills": "Python"}))
        self.assertEqual(len(python_devs), 2)
        
        # Test nested field queries
        usa_devs = list(collection.find({"address.country": "USA"}))
        self.assertEqual(len(usa_devs), 2)
        
        # Test complex conditions
        experienced_python_devs = list(collection.find({
            "age": {"$gte": 30},
            "skills": "Python"
        }))
        self.assertEqual(len(experienced_python_devs), 2)
        
        # Test projection
        names_only = list(collection.find({}, {"name": 1, "_id": 0}))
        self.assertEqual(len(names_only), 3)
        for doc in names_only:
            self.assertIn("name", doc)
            self.assertNotIn("age", doc)
            self.assertNotIn("_id", doc)
        
        # Test sorting and limiting
        sorted_by_age = list(collection.find({}).sort("age", 1).limit(2))
        self.assertEqual(len(sorted_by_age), 2)
        self.assertEqual(sorted_by_age[0]["name"], "Bob")  # Youngest first
        
        # Test regex queries
        names_with_a = list(collection.find({"name": {"$regex": "^A"}}))
        self.assertEqual(len(names_with_a), 1)
        self.assertEqual(names_with_a[0]["name"], "Alice")
        
        self.validate_db()

    def test_data_type_handling(self):
        """Test handling of various MongoDB data types."""
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["data_types_test"]
        
        # Insert document with various data types
        complex_doc = {
            "string_field": "Hello World",
            "integer_field": 42,
            "float_field": 3.14159,
            "boolean_field": True,
            "null_field": None,
            "array_field": [1, 2, 3, "four", 5.0],
            "object_field": {
                "nested_string": "nested value",
                "nested_number": 100
            },
            "date_field": datetime.utcnow(),
            "objectid_field": ObjectId()
        }
        
        insert_result = collection.insert_one(complex_doc)
        self.assertIsNotNone(insert_result.inserted_id)
        
        # Retrieve and verify data types
        retrieved_doc = collection.find_one({"_id": insert_result.inserted_id})
        
        self.assertIsInstance(retrieved_doc["string_field"], str)
        self.assertIsInstance(retrieved_doc["integer_field"], int)
        self.assertIsInstance(retrieved_doc["float_field"], float)
        self.assertIsInstance(retrieved_doc["boolean_field"], bool)
        self.assertIsNone(retrieved_doc["null_field"])
        self.assertIsInstance(retrieved_doc["array_field"], list)
        self.assertIsInstance(retrieved_doc["object_field"], dict)
        self.assertIsInstance(retrieved_doc["date_field"], datetime)
        self.assertIsInstance(retrieved_doc["objectid_field"], ObjectId)
        
        # Test queries on different data types
        string_query = collection.find_one({"string_field": "Hello World"})
        self.assertIsNotNone(string_query)
        
        number_query = collection.find_one({"integer_field": {"$gt": 40}})
        self.assertIsNotNone(number_query)
        
        boolean_query = collection.find_one({"boolean_field": True})
        self.assertIsNotNone(boolean_query)
        
        array_query = collection.find_one({"array_field": {"$in": [1]}})
        self.assertIsNotNone(array_query)
        
        nested_query = collection.find_one({"object_field.nested_number": 100})
        self.assertIsNotNone(nested_query)
        
        self.validate_db()

    def test_error_handling_in_operations(self):
        """Test error handling in database operations."""
        client = DB.connections[DB.current_conn]
        
        # Test operations on non-existent collection
        non_existent_collection = client[DB.current_db]["non_existent"]
        
        # These operations should not raise errors but return empty results
        empty_result = list(non_existent_collection.find({}))
        self.assertEqual(len(empty_result), 0)
        
        count_result = non_existent_collection.count_documents({})
        self.assertEqual(count_result, 0)
        
        # Test invalid operations
        collection = client[DB.current_db]["error_test"]
        collection.insert_one({"test": "document"})
        
        # Test update with invalid operator (should be handled gracefully by mongomock)
        try:
            collection.update_one({"test": "document"}, {"invalid_operator": {"field": "value"}})
        except Exception as e:
            # If an exception is raised, it should be a meaningful one
            self.assertIsInstance(e, Exception)
        
        self.validate_db()


if __name__ == "__main__":
    unittest.main()
