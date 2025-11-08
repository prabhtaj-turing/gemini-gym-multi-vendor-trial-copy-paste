import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..data_operations import delete_many
from pydantic import ValidationError as PydanticValidationError

class TestDeleteMany(BaseTestCaseWithErrorHandler):

    def setUp(self):
        # 1. Reset the global DB instance's internal state for a clean slate.
        #    This ensures no data or connection state leaks from previous tests or test classes.
        DB.connections = {}  # Clear any existing mongomock client instances
        DB.current_conn = None
        DB.current_db = None # Your MongoDB class stores current_db as a string name

        # 2. Establish and activate a consistent connection for all tests in this class.
        #    This will create a new, empty mongomock.MongoClient for 'test_fixture_conn'.
        DB.switch_connection("test_fixture_conn") 
        
        # 3. Get a direct handle to the mongomock client for this active connection.
        #    This client will be used to populate data.
        client = DB.connections[DB.current_conn]

        # 4. Populate the 'test_fixture_conn' client with specific databases and collections.
        
        # --- Setup for "test_db" ---
        self.db_test = client["test_db"] # Get/create the 'test_db' database object
        
        coll_test_1 = self.db_test["test_collection_1"] # Get/create 'test_collection_1'
        coll_test_1.insert_many([
            {"_id": "doc1", "name": "Alice", "age": 30, "city": "New York"},
            {"_id": "doc2", "name": "Bob", "age": 24, "city": "Paris"},
            {"_id": "doc3", "name": "Alice", "age": 35, "city": "London"},
            {"_id": "doc4", "name": "Charlie", "age": 30, "city": "New York"},
            {"_id": "doc5", "name": "Alice", "age": 30, "city": "Paris"},
        ])
        
        # 'empty_collection' will be created when accessed if it doesn't exist,
        # or you can explicitly create it if your function under test needs it listed.
        # For many tests, simply having the db_test object is enough.
        # If tests need to confirm it's listed but empty:
        self.db_test.create_collection("empty_collection") 
        
        coll_for_delete_all = self.db_test["collection_for_delete_all"]
        coll_for_delete_all.insert_many([
            {"_id": "dela1", "data": "x"},
            {"_id": "dela2", "data": "y"},
        ])

        # --- Setup for "another_db" ---
        self.db_another = client["another_db"] # Get/create 'another_db'
        
        coll_another = self.db_another["another_collection"]
        coll_another.insert_many([ # Use insert_many for consistency, even for one doc
            {"_id": "adoc1", "value": 100}
        ])


    def tearDown(self):
        # Clean up by dropping the databases created specifically for tests on the active connection.
        # This provides good isolation between test method runs and between test classes.
        if DB.current_conn and DB.current_conn in DB.connections:
            client_to_clean = DB.connections[DB.current_conn]
            
            # List of DBs created or significantly used in setUp that should be dropped
            dbs_to_drop_if_exist = ["test_db", "another_db"] 
            
            for db_name_to_drop in dbs_to_drop_if_exist:
                # Check if DB exists in mongomock client before trying to drop
                # (list_database_names() only shows non-empty DBs, but drop_database works by name)
                try:
                    client_to_clean.drop_database(db_name_to_drop)
                except Exception:
                    # Mongomock's drop_database might not error if DB doesn't exist,
                    # but good to be safe or log if needed.
                    pass
        
        # Fully reset the global DB object's state to be absolutely sure for the next test class.
        DB.connections = {}
        DB.current_conn = None
        DB.current_db = None

    # Success Cases
    def test_delete_many_with_filter_matching_multiple_docs(self):
        result = delete_many(database="test_db", collection="test_collection_1", filter={"name": "Alice"})
        self.assertEqual(result, {"deleted_count": 3, "acknowledged": True})
        remaining_docs = self.db_test["test_collection_1"]
        self.assertEqual(remaining_docs.count_documents({}), 2) 
        for doc in list(remaining_docs.find({})):
            self.assertNotEqual(doc["name"], "Alice")

    def test_delete_many_with_filter_matching_one_doc(self):
        result = delete_many(database="test_db", collection="test_collection_1", filter={"name": "Bob"})
        self.assertEqual(result, {"deleted_count": 1, "acknowledged": True})
        remaining_docs = self.db_test["test_collection_1"]
        self.assertEqual(remaining_docs.count_documents({}), 4) 
        self.assertFalse(any(doc["name"] == "Bob" for doc in list(remaining_docs.find({}))))

    def test_delete_many_with_compound_filter(self):
        result = delete_many(database="test_db", collection="test_collection_1", filter={"name": "Alice", "age": 30})
        self.assertEqual(result, {"deleted_count": 2, "acknowledged": True})
        remaining_docs = self.db_test["test_collection_1"]
        self.assertEqual(remaining_docs.count_documents({}), 3) 
        self.assertTrue(any(doc["name"] == "Alice" and doc["age"] == 35 for doc in list(remaining_docs.find({}))))
        self.assertFalse(any(doc["name"] == "Alice" and doc["age"] == 30 for doc in list(remaining_docs.find({}))))

    def test_delete_many_with_id_filter(self):
        result = delete_many(database="test_db", collection="test_collection_1", filter={"_id": "doc1"})
        self.assertEqual(result, {"deleted_count": 1, "acknowledged": True})
        remaining_docs = self.db_test["test_collection_1"]
        self.assertEqual(remaining_docs.count_documents({}), 4)
        self.assertFalse(any(doc["_id"] == "doc1" for doc in list(remaining_docs.find({}))))

    def test_delete_many_with_empty_filter_deletes_all(self):
        collection_name = "collection_for_delete_all"
        initial_count = self.db_test[collection_name].count_documents({})
        self.assertTrue(initial_count > 0, "Test setup error: collection_for_delete_all should not be empty.")

        result = delete_many(database="test_db", collection=collection_name, filter={})
        self.assertEqual(result, {"deleted_count": initial_count, "acknowledged": True})
        remaining_docs = self.db_test[collection_name]
        self.assertEqual(remaining_docs.count_documents({}), 0)

    def test_delete_many_with_none_filter_deletes_all(self):
        collection_name = "collection_for_delete_all"
        initial_count = self.db_test[collection_name].count_documents({})
        self.assertTrue(initial_count > 0, "Test setup error: collection_for_delete_all should not be empty.")

        result = delete_many(database="test_db", collection=collection_name, filter=None)
        self.assertEqual(result, {"deleted_count": initial_count, "acknowledged": True})
        remaining_docs = self.db_test[collection_name]
        self.assertEqual(remaining_docs.count_documents({}), 0)

    def test_delete_many_filter_matches_no_documents(self):
        initial_doc_count = self.db_test["test_collection_1"].count_documents({})
        result = delete_many(database="test_db", collection="test_collection_1", filter={"name": "DoesNotExist"})
        self.assertEqual(result, {"deleted_count": 0, "acknowledged": True})
        remaining_docs = self.db_test["test_collection_1"]
        self.assertEqual(remaining_docs.count_documents({}), initial_doc_count)

    def test_delete_many_from_empty_collection_with_filter(self):
        result = delete_many(database="test_db", collection="empty_collection", filter={"name": "Any"})
        initial_count_for_debug = self.db_test["empty_collection"].find({})
        print(f"DEBUG: Count in 'empty_collection' at start of test: {initial_count_for_debug}")
        self.assertEqual(result, {"deleted_count": 0, "acknowledged": True})
        remaining_docs = self.db_test["empty_collection"]
        self.assertEqual(remaining_docs.count_documents({}), 0)

    def test_delete_many_from_empty_collection_with_empty_filter(self):
        result = delete_many(database="test_db", collection="empty_collection", filter={})
        self.assertEqual(result, {"deleted_count": 0, "acknowledged": True})
        remaining_docs = self.db_test["empty_collection"]
        self.assertEqual(remaining_docs.count_documents({}), 0)

    def test_delete_many_with_in_operator_filter(self):
        initial_docs_count = self.db_test["test_collection_1"].count_documents({}) 
        
        result = delete_many(
            database="test_db",
            collection="test_collection_1",
            filter={"city": {"$in": ["Paris", "London"]}}
        )
        self.assertEqual(result, {"deleted_count": 3, "acknowledged": True})
        
        remaining_docs = self.db_test["test_collection_1"]
        self.assertEqual(remaining_docs.count_documents({}), initial_docs_count - 3)
        remaining_documents_list = list(remaining_docs.find({}))
        for doc in remaining_documents_list:
            self.assertNotIn(doc["city"], ["Paris", "London"])
        
        self.assertTrue(any(doc["_id"] == "doc1" for doc in remaining_documents_list))
        self.assertTrue(any(doc["_id"] == "doc4" for doc in remaining_documents_list))


    def test_delete_many_invalid_query_filter(self):
        initial_doc_count = self.db_test["test_collection_1"].count_documents({})
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=custom_errors.InvalidQueryError,
            expected_message="Error during delete_many operation: unknown operator: $unsupportedOperator",
            database="test_db",
            collection="test_collection_1",
            filter={"field": {"$unsupportedOperator": 1}}
        )
        self.assertEqual(self.db_test["test_collection_1"].count_documents({}), initial_doc_count)

    # ValidationError Cases
    def test_delete_many_invalid_database_name_type(self):
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database=123,
            collection="test_collection_1",
            filter={}
        )

    def test_delete_many_database_name_empty(self):
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="",
            collection="test_collection_1",
            filter={}
        )

    def test_delete_many_database_name_too_long(self):
        long_name = "a" * 64
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 63 characters",
            database=long_name,
            collection="test_collection_1",
            filter={}
        )

    def test_delete_many_invalid_collection_name_type(self):
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database="test_db",
            collection=123,
            filter={}
        )

    def test_delete_many_collection_name_empty(self):
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="test_db",
            collection="",
            filter={}
        )

    def test_delete_many_collection_name_too_long(self):
        long_name = "a" * 256
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 255 characters",
            database="test_db",
            collection=long_name,
            filter={}
        )

    def test_delete_many_invalid_filter_type(self):
        self.assert_error_behavior(
            func_to_call=delete_many,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid dictionary",
            database="test_db",
            collection="test_collection_1",
            filter="not_a_dictionary"
        )

if __name__ == '__main__':
    unittest.main()