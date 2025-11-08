from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import get_active_connection
from ..SimulationEngine.db import DB
from ..database_operations import drop_database
from mongomock import MongoClient

class TestDropDatabase(BaseTestCaseWithErrorHandler): # BaseTestCaseWithErrorHandler is assumed global

    def setUp(self):
        DB.connections = {}
        DB.current_db = None
        DB.current_conn = "mock_conn"
        DB.connections[DB.current_conn] = MongoClient()

        self.active_connection = get_active_connection()

    def test_drop_existing_database_successfully(self):
        # Add a database to the active connection
        db_name = "db_to_drop"
        db_name_to_keep = "another_existing_db"
        self.active_connection[db_name].create_collection("test_collection")
        self.active_connection[db_name_to_keep].create_collection("test_collection")
        self.assertTrue(db_name in self.active_connection.list_database_names(), "Database should exist before dropping.")
        
        result = drop_database(database=db_name) # drop_database function is assumed global

        expected_response = [{"text": f'Successfully dropped database "{db_name}"', "type": "text"}]
        self.assertEqual(result['content'], expected_response, "Response message mismatch.")
        self.assertNotIn(db_name, self.active_connection.list_database_names(), "Database should be removed from client.")
        self.assertTrue(db_name_to_keep in self.active_connection.list_database_names(), "Other databases should remain untouched.")

    def test_drop_non_existent_database_successfully(self):
        db_name = "non_existent_db"
        self.assertNotIn(db_name, self.active_connection.list_database_names(), "Database should not exist before 'dropping'.")

        result = drop_database(database=db_name)
        
        # MongoDB's drop_database typically doesn't error if the DB doesn't exist.
        expected_response = [{"text": f'Successfully dropped database "{db_name}"', "type": "text"}]
        self.assertEqual(result['content'], expected_response, "Response message for non-existent DB mismatch.")
        self.assertNotIn(db_name, self.active_connection.list_database_names(), "Non-existent database should still not be listed.")

    def test_drop_database_with_different_active_connection(self):
        DB.connections = {}
        DB.connections["another"] = MongoClient()
        DB.connections['mock_conn'] = MongoClient()

        db_name = "db_to_drop"
        DB.connections["another"][db_name].create_collection("test_collection")
        DB.connections["mock_conn"][db_name].create_collection("test_collection")

        DB.current_conn = "another"
        result = drop_database(database=db_name)
        print(result)

        expected_response = [{"text": f'Successfully dropped database "{db_name}"', "type": "text"}]
        self.assertEqual(result['content'], expected_response)
        self.assertNotIn(db_name, self.active_connection.list_database_names(), "DB should be removed from 'another' client.")

        DB.current_conn = "mock_conn"
        self.active_connection = get_active_connection()
        self.assertIn(db_name, self.active_connection.list_database_names(), "DB should not be removed from 'mock_conn' client.")

    def test_drop_current_database_resets_db_current_db(self):
        db_name = "cur_db"
        # Simulate this DB being the current one in the global DB state
        DB.current_db = db_name
        self.active_connection[db_name].create_collection("test_collection")
        self.assertIsNotNone(DB.current_db, "DB.current_db should be set for this test.")
        self.assertEqual(DB.current_db, db_name, "DB.current_db name mismatch.")
        
        result = drop_database(database=db_name)

        expected_response = [{"text": f'Successfully dropped database "{db_name}"', "type": "text"}]
        self.assertEqual(result['content'], expected_response)
        self.assertNotIn(db_name, self.active_connection.list_database_names(), "Dropped DB should be removed from client.")
        self.assertIsNone(DB.current_db, "DB.current_db should be reset to None if the dropped DB was current.")

    # # --- ConnectionError Scenarios ---
    # # These tests verify that ConnectionError is raised for various invalid connection states.
    # # The exact error message for ConnectionError is not specified, so not asserted.

    def test_drop_database_no_current_connection_key_raises_connectionerror(self):
        DB.current_conn = None # current_conn key missing from DB
        self.assert_error_behavior(
            func_to_call=drop_database,
            expected_exception_type=ConnectionError,
            expected_message="No active MongoDB connection.",
            database="any_db_name"
        )


    def test_drop_database_no_connections_key_in_connections_raises_connectionerror(self):
        DB.connections = {} # connections key missing from DB
        self.assert_error_behavior(
            func_to_call=drop_database,
            expected_exception_type=ConnectionError,
            expected_message="Invalid MongoDB connection.",
            database="any_db_name"
        )

    # # --- custom_errors.ValidationError Scenarios ---
    # # These tests assume input validation is performed (e.g., via a Pydantic model like DropDatabaseInput)
    # # and results in custom_errors.ValidationError.
    # # Error messages are checked for containment of key phrases.

    def test_drop_database_name_empty_raises_valueerror(self):
        self.assert_error_behavior(
            func_to_call=drop_database,
            expected_exception_type = ValueError,
            expected_message="Database name cannot be empty.",
            database=""
        )

    def test_drop_database_name_is_none_raises_valueerror(self):
        self.assert_error_behavior(
            func_to_call=drop_database,
            expected_exception_type=ValueError,
            expected_message="Database name cannot be empty.",
            database=None
        )

    def test_drop_database_name_is_integer_raises_typeerror(self):
        self.assert_error_behavior(
            func_to_call=drop_database,
            expected_exception_type=TypeError,
            expected_message="Database name must be a string.",
            database=123
        )

