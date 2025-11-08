import unittest
from unittest.mock import patch, MagicMock

from pydantic import ValidationError
from bson import ObjectId
from pymongo.errors import (
    OperationFailure,
    BulkWriteError as PyMongoBulkWriteError,
    InvalidOperation,
    AutoReconnect,
    WriteError
)
from pymongo.results import InsertManyResult, UpdateResult

from ..data_operations import insert_many, update_many, count
from ..SimulationEngine.custom_errors import (
    DatabaseNotFoundError,
    BulkWriteError,
    InvalidDocumentError,
    CollectionNotFoundError,
    InvalidQueryError,
    InvalidUpdateError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from mongomock import MongoClient

class TestCountOperation(BaseTestCaseWithErrorHandler):
    TEST_DATABASE_NAME = "py_test_count_db"      # Test database name

    _test_client_instance = None # To hold the client created for testing

    @classmethod
    def setUpClass(cls):
        # Create a single client instance for all tests in this class
        cls.mongo_client_for_tests = MongoClient()

        # Patch 'utils.get_active_connection' to return our test client
        # This ensures the 'count' function uses our controlled MongoDB connection
        cls.patcher = patch("mongodb.SimulationEngine.utils.get_active_connection")
        cls.mock_get_active_connection = cls.patcher.start()
        cls.mock_get_active_connection.return_value = cls.mongo_client_for_tests
        
        # Store the client instance that the mocked get_active_connection will return
        # This is the client we will use in setUp/tearDown to manage data
        TestCountOperation._test_client_instance = cls.mongo_client_for_tests


    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop() # Stop the patch
        if cls.mongo_client_for_tests:
            cls.mongo_client_for_tests.close()

    def setUp(self):
        # Ensure we have the client instance
        self.assertTrue(TestCountOperation._test_client_instance, "Test client not initialized")
        self.client = TestCountOperation._test_client_instance
        self.db = self.client[self.TEST_DATABASE_NAME]
        # Clean up collections from previous (potentially failed) tests in this DB
        for coll_name in self.db.list_collection_names():
            self.db[coll_name].drop()

    def tearDown(self):
        # Clean up the test database by dropping all its collections after each test
        if self.db:
            for coll_name in self.db.list_collection_names():
                self.db[coll_name].drop()
        # Alternatively, to drop the entire database (might be slower if many tests):
        # self.client.drop_database(self.TEST_DATABASE_NAME)


    # --- Input Validation Error Tests (No DB interaction, Pydantic-driven) ---
    def test_validation_error_empty_database_string(self):
        self.assert_error_behavior(
            func_to_call=count,
            expected_exception_type=ValidationError,
            expected_message="database",
            database="",
            collection="mycollection"
        )

    def test_validation_error_empty_collection_string(self):
        self.assert_error_behavior(
            func_to_call=count,
            expected_exception_type=ValidationError,
            expected_message="collection",
            database="mydatabase",
            collection=""
        )

    def test_validation_error_invalid_query_type(self):
        self.assert_error_behavior(
            func_to_call=count,
            expected_exception_type=ValidationError,
            expected_message="query",
            database="mydatabase",
            collection="mycollection",
            query="this is not a dict"
        )

    # --- Query Execution Error Test (Uses real DB) ---
    def test_invalid_query_on_operation_failure(self):
        coll_name = "test_op_failure_coll"
        # A query that MongoDB should reject (e.g., invalid field name starting with '$')
        bad_query = {"$invalidFieldName": 1}

        # The collection doesn't even need to exist for this type of query error
        self.assert_error_behavior(
            func_to_call=count,
            expected_exception_type=InvalidQueryError,
            expected_message=f"Invalid query for collection '{coll_name}' in database '{self.TEST_DATABASE_NAME}': unknown top level operator: $invalidFieldName",
            database=self.TEST_DATABASE_NAME,
            collection=coll_name,
            query=bad_query
        )

    # --- Success Path Tests (Uses real DB) ---
    def test_success_no_query_provided(self):
        coll_name = "success_coll_no_query"
        self.db[coll_name].insert_many([
            {"name": "doc1"}, {"name": "doc2"}, {"name": "doc3"}
        ])
        
        result = count(database=self.TEST_DATABASE_NAME, collection=coll_name, query=None)
        
        expected_result = {
            "content": [
                {"text": f'Found 3 documents in the collection "{coll_name}"', "type": "text"}
            ]
        }
        self.assertEqual(result, expected_result)

    def test_success_with_valid_query(self):
        coll_name = "success_coll_with_query"
        self.db[coll_name].insert_many([
            {"type": "widget", "active": True, "name": "w1"},
            {"type": "gadget", "active": True, "name": "g1"},
            {"type": "widget", "active": False, "name": "w2"},
            {"type": "widget", "active": True, "name": "w3"},
        ])
        
        specific_query = {"type": "widget", "active": True}
        result = count(database=self.TEST_DATABASE_NAME, collection=coll_name, query=specific_query)
        
        expected_result = {
            "content": [
                {"text": f'Found 2 documents in the collection "{coll_name}"', "type": "text"}
            ]
        }
        self.assertEqual(result, expected_result)

    def test_success_with_empty_dict_query(self):
        coll_name = "success_coll_empty_query"
        self.db[coll_name].insert_many([{"item": "A"}, {"item": "B"}])
        
        result = count(database=self.TEST_DATABASE_NAME, collection=coll_name, query={})
        
        expected_result = {
            "content": [
                {"text": f'Found 2 documents in the collection "{coll_name}"', "type": "text"}
            ]
        }
        self.assertEqual(result, expected_result)

    def test_success_collection_is_empty(self):
        coll_name = "empty_coll_for_count"
        # Ensure collection exists but is empty (count_documents on non-existent also returns 0)
        self.db.create_collection(coll_name) 

        result = count(database=self.TEST_DATABASE_NAME, collection=coll_name, query={})
        
        expected_result = {
            "content": [
                {"text": f'Found 0 documents in the collection "{coll_name}"', "type": "text"}
            ]
        }
        self.assertEqual(result, expected_result)

    def test_success_collection_does_not_exist(self):
        coll_name = "non_existent_coll_for_count"
        # Do not create this collection. PyMongo's count_documents returns 0.

        result = count(database=self.TEST_DATABASE_NAME, collection=coll_name, query={})
        
        expected_result = {
            "content": [
                {"text": f'Found 0 documents in the collection "{coll_name}"', "type": "text"}
            ]
        }
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()