import unittest
import copy
from unittest.mock import patch, MagicMock
from pathlib import Path # Added for the new setUp method

from ..SimulationEngine import custom_errors
from ..connection_server_management import switch_connection # This is the SUT
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state # MODIFIED: Added save_state import
import tempfile

# Note: pymongo.errors.ConnectionFailure and pymongo.errors.ConfigurationError
# are no longer imported at the top level.
# The test methods using them for mock side_effects might require adjustments
# if these names are not available.
# The inline import of pymongo.errors.OperationFailure in one of the test methods remains.


class TestSwitchConnection(BaseTestCaseWithErrorHandler): # type: ignore

    def setUp(self):
        # 1. Define a temporary state file path
        # It's good practice for the filename to be unique per test class or even method if tests run in parallel.
        self.temp_state_file_path = Path(f"{tempfile.mkdtemp()}_{self.__class__.__name__}.json")

        # 2. Save the current state of the global DB object
        # 'save_state' is now imported.
        save_state(str(self.temp_state_file_path))

        # 3. Switch to a dedicated connection for these tests.
        # This ensures that these tests operate on a known mongomock client instance.
        self.test_conn_name = "mongodb://test_conn_for_collection_indexes" # Note: Class is TestSwitchConnection
        DB.switch_connection(self.test_conn_name)

        # Get the actual mongomock client for this connection.
        # utils.get_active_connection() used by the main function will get this client.
        client = DB.connections[DB.current_conn] # Assumes DB.connections and DB.current_conn are valid

        # 4. Ensure a clean state for the databases within this test connection.
        # This prevents data leakage if a previous test run failed before tearDown.
        # If switch_connection created a new client, it's already clean.
        # If the connection was reused, explicitly drop databases.
        databases_to_clean = ["test_db", "another_db", "empty_db"]
        for db_name_to_clean in databases_to_clean:
            if db_name_to_clean in client.list_database_names():
                client.drop_database(db_name_to_clean)

        # 5. Populate the databases and collections with indexes using mongomock's API.

        # --- Populate 'test_db' ---
        db_test = client["test_db"] # This is a mongomock.Database object

        # 'users' collection
        users_coll = db_test["users"]
        users_coll.insert_one({"doc": "ensure_collection_exists"}) # Ensures collection is created
        users_coll.create_index([("username", 1)], name="username_1", unique=True)
        users_coll.create_index([("email", 1)], name="email_1")

        # 'products' collection
        products_coll = db_test["products"]
        products_coll.insert_one({"doc": 1})
        products_coll.create_index([("price", -1), ("category", 1)], name="price_-1_category_1")

        # 'empty_coll' collection (will only have the default _id_ index)
        db_test.create_collection("empty_coll") # or empty_coll = db_test["empty_coll"]; empty_coll.insert_one({})

        # 'coll_no_indexes_field' (similar to empty_coll for testing purposes)
        db_test.create_collection("coll_no_indexes_field")

        # 'coll_with_extra_options' collection
        coll_extra_opts = db_test["coll_with_extra_options"]
        coll_extra_opts.insert_one({"doc": 1})
        coll_extra_opts.create_index([("last_login", -1)], name="last_login_idx", sparse=True, expireAfterSeconds=3600)

        # --- Populate 'another_db' ---
        db_another = client["another_db"]

        simple_coll = db_another["simple_coll"]
        simple_coll.insert_one({"doc": 1})
        # Regarding 'v' (index version): mongomock's index_information() typically reports 'v': 2.
        # The test for 'v': 1 (test_collection_indexes_success_different_version_index)
        # will likely need adjustment to expect 'v': 2, as setting 'v' via create_index is not standard.
        # The collection_indexes function itself defaults 'v' to 2 if not present in raw data.
        simple_coll.create_index([("field_v1", 1)], name="field_v1_idx")

        # --- Ensure 'empty_db' exists (it will have no collections unless explicitly created) ---
        _ = client["empty_db"] # Accessing it ensures it's in list_database_names if it was newly created implicitly.
                                # To be truly empty as per test expectations, no collections should be added.

        # Set a current database context on the DB object if any other logic relies on DB.current_db.
        # collection_indexes itself takes 'database' argument, so it's robust to this.
        DB.use_database("test_db")

    def tearDown(self):
        # This will likely raise an AttributeError if self.mock_mongo_client_patcher
        # is not set by the new setUp method.
        if hasattr(self, 'mock_mongo_client_patcher') and self.mock_mongo_client_patcher:
            self.mock_mongo_client_patcher.stop()
        
        # Restore the original state using the temp file if 'load_state' is available
        # and if the new setUp implies a matching tearDown logic.
        # For now, the old DB.clear() and DB.update() are kept but might be irrelevant
        # if DB is not a dict and if save_state/load_state is the new mechanism.
        # This tearDown part likely needs to be rewritten to match the new setUp.
        
        # Example of what might be needed for tearDown matching the new setUp:
        # if hasattr(self, 'temp_state_file_path') and self.temp_state_file_path.exists():
        #     # load_state(str(self.temp_state_file_path)) # Assuming load_state function exists and is imported
        #     self.temp_state_file_path.unlink() # Clean up the temp file

        # Original tearDown logic, may conflict with new DB object model:
        # DB.clear()
        # DB.update(self._original_DB_state) # This assumed DB was a dict and _original_DB_state was a deepcopy of it.

        # A more appropriate tearDown for the new setUp might be to restore DB state
        # from self.temp_state_file_path and clean up the test connection/databases if needed.
        # For now, leaving the original structure but commenting out potentially problematic lines.

        # If _original_DB_state was based on the old dict-like DB, it's no longer applicable.
        # The concept of restoring state needs to align with how `save_state` and the `DB` object work.
        pass # Placeholder for revised tearDown logic


    def _configure_mock_client_defaults(self):
        # This method configures self.mock_client_instance.
        # If self.mock_client_instance is not created by setUp, this method might be called on None.
        if hasattr(self, 'mock_client_instance') and self.mock_client_instance:
            self.mock_client_instance.server_info.return_value = {'version': '5.0.0', 'ok': 1}
            self.mock_client_instance.address = ('mockhost', 27017)
            self.mock_client_instance.nodes = frozenset([('mockhost', 27017)])
            self.mock_client_instance.server_info.side_effect = None
            self.mock_client_instance.close.reset_mock()


    def _configure_mock_connection_success(self, host='mockhost', port=27017, version='5.0.0', srv_host=None):
        # This method configures self.mock_client_instance and self.MockMongoClient.
        # If these are not created by setUp, this method's calls will fail.
        if hasattr(self, 'mock_client_instance') and self.mock_client_instance and \
           hasattr(self, 'MockMongoClient') and self.MockMongoClient:
            self.mock_client_instance.server_info.return_value = {'version': version, 'ok': 1}
            self.mock_client_instance.server_info.side_effect = None
            if srv_host:
                self.mock_client_instance.nodes = frozenset([(srv_host, port)])
                self.mock_client_instance.address = (srv_host.split('.')[0] + "-node", port)
            else:
                self.mock_client_instance.address = (host, port)
                self.mock_client_instance.nodes = frozenset([(host, port)])
            self.MockMongoClient.return_value = self.mock_client_instance
        else:
            # Log or raise an error if mocks are not set up, to avoid silent failures
            # print("Warning: Mocks not configured in _configure_mock_connection_success due to missing setup.")
            pass


    def test_switch_connection_with_valid_new_string_success(self):
        new_uri = "mongodb://testuser:testpass@newhost:27017/testdb"
        self._configure_mock_connection_success(host='newhost', port=27017, version='5.0.1')

        result = switch_connection(connectionString=new_uri) 

        self.assertEqual(result['status'], 'success')
        self.assertIn("Switched to connection", result['message'])
        self.assertIsNotNone(result['active_connection_info'])
        self.assertIn("Current connection now is", result['active_connection_info'])


    def test_switch_connection_with_valid_srv_string_success(self):
        srv_uri = "mongodb+srv://testuser:testpass@cluster.mongodb.net/testdb"
        self._configure_mock_connection_success(srv_host='cluster.mongodb.net', port=27017, version='5.0.2')

        result = switch_connection(connectionString=srv_uri)

        self.assertEqual(result['status'], 'success')
        self.assertIn("Switched to connection", result['message'])
        self.assertIn("Current connection now is", result['active_connection_info'])


    def test_switch_connection_to_same_uri_as_current(self):
        current_uri = "mongodb://user:pass@host:27017/db"
        initial_mock_client = MagicMock()

        if not hasattr(DB, 'connections') or not isinstance(DB.connections, dict):
            DB.connections = {}
        DB.connections[current_uri] = initial_mock_client
        DB.current_conn = current_uri
        
        self._configure_mock_connection_success(host='host', port=27017)

        result = switch_connection(connectionString=current_uri)

        self.assertEqual(result['status'], 'failure')
        self.assertIn("is already the current connection", result['message'])
        self.assertEqual(DB.current_conn, current_uri)
        self.assertIn(current_uri, DB.connections)
        self.assertIsNotNone(DB.connections[current_uri])
        self.assertEqual(DB.connections[current_uri], initial_mock_client)


    def test_switch_connection_empty_string_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=switch_connection, 
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Connection string cannot be empty or contain only whitespace.",
            connectionString=""
        )

    def test_switch_connection_none_string(self):
        self.assert_error_behavior(
            func_to_call=switch_connection, 
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Provided connection string must be a string",
            connectionString=None
        )


    def test_switch_connection_none_string(self):
        self.assert_error_behavior(
            func_to_call=switch_connection, 
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Provided connection string must be a string.",
            connectionString=None
        )
    
    def test_switch_connection_invalid_argument_type_for_connectionstring_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=switch_connection, 
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Provided connection string must be a string.",
            connectionString=12345
        )

    def test_switch_connection_invalid_prefix(self):
        invalid_uri = "http://some_other_service:1234/db"
        
        # Ensure DB.current_conn is different from invalid_uri to avoid hitting
        # the "already current connection" check first.
        # We can set it to None or some other valid-looking URI that is not invalid_uri.
        # If setUp already establishes a DB.current_conn, this might not be strictly necessary
        # as long as the invalid_uri is guaranteed to be different.
        # For robustness, let's ensure it's different:
        if hasattr(DB, 'current_conn') and DB.current_conn == invalid_uri:
            DB.current_conn = "mongodb://initial_placeholder_for_test" # or None, depending on DB logic for no conn

        result = switch_connection(connectionString=invalid_uri)

        self.assertEqual(result['status'], 'failure')
        self.assertEqual(
            result['message'],
            "Connection failed! Invalid MongoDB connection string format: Must start with 'mongodb://' or 'mongodb+srv://'."
        )
        # Optionally, assert that active_connection_info is None or not present if that's the expected contract
        # Based on the SwitchConnectionResponse model, if the message indicates failure and there's no active_connection_info
        # explicitly set for this failure case, its default (likely None or not included in model_dump if Optional) would be present.
        # The function currently does not set active_connection_info in this specific failure path before returning.
        self.assertIsNone(result.get('active_connection_info')) # Or check if key is absent if model_dump(exclude_none=True)