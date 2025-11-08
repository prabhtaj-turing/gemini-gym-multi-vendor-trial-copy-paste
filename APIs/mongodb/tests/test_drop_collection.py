import unittest
import copy
from ..SimulationEngine import custom_errors

from ..SimulationEngine.db import DB
from mongodb import drop_collection
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError
from bson import ObjectId
import unittest.mock

class TestDropCollection(BaseTestCaseWithErrorHandler):

    def setUp(self):
        DB.connections = {}  # Clears any existing mongomock clients
        DB.current_conn = None
        DB.current_db = None # Your MongoDB class stores current_db as a string name

        # 2. Establish and activate a consistent connection for all tests in this class.
        #    This will create a new, empty mongomock.MongoClient for 'test_conn'.
        DB.switch_connection("test_conn") 
        
        # 3. Get a direct handle to the mongomock client for this connection.
        self.client = DB.connections[DB.current_conn]

        # 4. Populate the 'test_conn' client with specific databases and collections
        #    needed for the tests. This is done directly using mongomock methods.
        
        # For tests like test_drop_existing_collection_success, etc.
        self.db_existing_name = "existing_db"
        db_instance_existing = self.client[self.db_existing_name] # Get/create database
        
        self.coll_to_drop_name = "collection_to_drop"
        coll_to_drop = db_instance_existing[self.coll_to_drop_name]
        coll_to_drop.insert_many([
            {"_id": ObjectId("111111111111111111111101"), "item": "A"},
            {"_id": ObjectId("111111111111111111111102"), "item": "B"}
        ])

        self.view_to_drop_name = "view_to_drop"
        # For mongomock, views are created using create_collection with options
        try:
            db_instance_existing.create_collection(
                self.view_to_drop_name,
                viewOn=self.coll_to_drop_name, # Example: view on the collection we just made
                pipeline=[{"$match": {"item": "A"}}]
            )
        except Exception as e:
            print(f"Warning: Could not create view '{self.view_to_drop_name}' during setUp, creating as normal collection: {e}")
            db_instance_existing[self.view_to_drop_name].insert_one({"_id": "view_placeholder"})


        self.another_coll_name = "another_collection"
        another_coll = db_instance_existing[self.another_coll_name]
        another_coll.insert_one({"_id": ObjectId("111111111111111111111103"), "data": "other data"})

        # For test_drop_collection_from_existing_empty_database_success
        self.db_empty_name = "empty_db"
        _ = self.client[self.db_empty_name]

    def tearDown(self):
        # Restore the original DB state by clearing and updating
        if DB.current_conn and DB.current_conn in DB.connections:
            client_to_clean = DB.connections[DB.current_conn]
            # List of DBs created in setUp that should be dropped
            dbs_to_drop_if_exist = [self.db_existing_name, self.db_empty_name]
            for db_name_to_drop in dbs_to_drop_if_exist:
                if db_name_to_drop in client_to_clean.list_database_names():
                    client_to_clean.drop_database(db_name_to_drop)

    # Success Scenarios
    def test_drop_existing_collection_success(self):
        db_name = "existing_db"
        collection_name = "collection_to_drop"

        self.assertIn(db_name, self.client.list_database_names())
        self.assertIn(collection_name, self.client[db_name].list_collection_names())
        
        result = drop_collection(database=db_name, collection=collection_name)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("message"), "Collection dropped successfully.")
        self.assertNotIn(collection_name, self.client[db_name].list_collection_names())
        self.assertIn("another_collection", self.client[db_name].list_collection_names()) # Ensure other collections are untouched

    def test_drop_existing_view_success(self):
        db_name = "existing_db"
        view_name = "view_to_drop" 

        self.assertIn(db_name, self.client.list_database_names())
        self.assertIn(view_name, self.client[db_name].list_collection_names())
        
        result = drop_collection(database=db_name, collection=view_name)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("message"), "Collection dropped successfully.")
        self.assertNotIn(view_name, self.client[db_name].list_collection_names())

    def test_drop_non_existent_collection_in_existing_database_success(self):
        db_name = "existing_db"
        collection_name = "non_existent_collection"

        self.assertIn(db_name, self.client.list_database_names())
        self.assertNotIn(collection_name, self.client[db_name].list_collection_names())

        result = drop_collection(database=db_name, collection=collection_name)
        
        self.assertEqual(result.get("status"), "success") 
        self.assertEqual(result.get("message"), "Collection not found.")
        self.assertNotIn(collection_name, self.client[db_name].list_collection_names())


    # Error Scenarios: Validation Errors for 'database' argument
    def test_drop_collection_database_name_empty_raises_ValidationError(self):
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="", 
            collection="any_collection"
        )

    def test_drop_collection_database_name_too_long_raises_ValidationError(self):
        long_db_name = "a" * 64 
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 63 characters",
            database=long_db_name,
            collection="any_collection"
        )
        
    def test_drop_collection_database_name_none_raises_ValidationError(self):
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database=None,
            collection="any_collection"
        )

    def test_drop_collection_database_name_invalid_type_raises_ValidationError(self):
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database=123, 
            collection="any_collection"
        )

    # Error Scenarios: Validation Errors for 'collection' argument
    def test_drop_collection_collection_name_empty_raises_ValidationError(self):
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="existing_db",
            collection=""
        )

    def test_drop_collection_collection_name_too_long_raises_ValidationError(self):
        long_collection_name = "a" * 256 
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 255 characters",
            database="existing_db",
            collection=long_collection_name
        )

    def test_drop_collection_collection_name_none_raises_ValidationError(self):
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database="existing_db",
            collection=None
        )

    def test_drop_collection_collection_name_invalid_type_raises_ValidationError(self):
        self.assert_error_behavior(
            func_to_call=drop_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database="existing_db",
            collection=123 
        )
        
        
     # Exception Handling Test - This covers lines 535-538
    def test_drop_collection_exception_handling(self):
        """Test the exception handling path that raises ApiError"""
        db_name = "existing_db"
        collection_name = "collection_to_drop"

        # Create a collection that exists
        self.assertIn(db_name, self.client.list_database_names())
        self.assertIn(collection_name, self.client[db_name].list_collection_names())

        # Mock the database object's drop_collection method to raise an exception
        with unittest.mock.patch.object(
            self.client[db_name], 'drop_collection', side_effect=Exception("Test exception")
        ):
            
            self.assert_error_behavior(
                func_to_call=drop_collection,
                expected_exception_type=custom_errors.ApiError,
                expected_message="An error occurred during the drop operation: Test exception",
                database=db_name, collection=collection_name
            )
                

    # Exception Handling Test - This covers lines 535-538
    def test_drop_collection_exception_handling(self):
        """Test the exception handling path that raises ApiError"""
        db_name = "existing_db"
        collection_name = "collection_to_drop"
        
        # Create a collection that exists
        self.assertIn(db_name, self.client.list_database_names())
        self.assertIn(collection_name, self.client[db_name].list_collection_names())
        
        # Mock the database object's drop_collection method to raise an exception
        with unittest.mock.patch.object(
            self.client[db_name], 'drop_collection', side_effect=Exception("Test exception")
        ):
            self.assert_error_behavior(
                func_to_call=drop_collection,
                expected_exception_type=custom_errors.ApiError,
                expected_message="An error occurred during the drop operation: Test exception",
                database=db_name, collection=collection_name
            )

if __name__ == '__main__':
    unittest.main()