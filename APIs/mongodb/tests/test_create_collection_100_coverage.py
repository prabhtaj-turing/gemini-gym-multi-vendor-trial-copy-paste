import unittest
import json
from pathlib import Path
from bson import json_util
from unittest.mock import patch, MagicMock

from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state
from ..collection_management import create_collection
from pydantic import ValidationError as PydanticValidationError
import pymongo.errors

# Define a path for test-specific state files
TEST_STATE_DIR = Path(__file__).resolve().parent / "test_states_temp"
TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)

class TestCreateCollection100Coverage(BaseTestCaseWithErrorHandler):

    def _get_current_test_state_file_path(self) -> Path:
        """Generates a state file path based on the current test method name."""
        test_method_name = self.id().split('.')[-1]
        return TEST_STATE_DIR / f"{test_method_name}_mongodb_state.json"

    def _write_json_state(self, file_path: Path, state_dict: dict):
        """Helper to write a dictionary to a JSON file for test setup."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(state_dict, f, default=json_util.default, indent=2)

    def _read_json_state(self, file_path: Path) -> dict:
        """Helper to read a JSON file into a dictionary for assertions."""
        if not file_path.exists():
            return {"connections": {"test_conn": {"databases": {}}}}
        with open(file_path, "r") as f:
            try:
                return json.load(f, object_hook=json_util.object_hook)
            except json.JSONDecodeError:
                return {"connections": {"test_conn": {"databases": {}}}}

    def setUp(self):
        self.current_test_state_file = self._get_current_test_state_file_path()
        
        # Define a base "empty" state for most tests
        self.base_empty_state_dict = {
            "connections": {
                "test_conn": {
                    "databases": {}
                }
            }
        }
        
        # Ensure a clean start
        self._write_json_state(self.current_test_state_file, self.base_empty_state_dict)
        load_state(str(self.current_test_state_file))
        
        # Ensure a connection is active
        if not DB.current_conn or DB.current_conn not in DB.connections:
            DB.switch_connection("test_conn")
        elif DB.current_conn != "test_conn":
            DB.switch_connection("test_conn")

    def tearDown(self):
        # Clean up the temporary state file
        if self.current_test_state_file.exists():
            try:
                self.current_test_state_file.unlink()
            except OSError:
                pass

    def test_create_collection_success_basic(self):
        """Test basic successful collection creation"""
        result = create_collection(database="test_db", collection="test_coll")
        
        expected_response = {"status": "success", "message": "Collection created successfully"}
        self.assertEqual(result, expected_response)
        
        # Verify in memory
        client = DB.connections[DB.current_conn]
        self.assertIn("test_db", client.list_database_names())
        mongo_db_instance = client["test_db"]
        self.assertIn("test_coll", mongo_db_instance.list_collection_names())

    def test_create_collection_success_with_save_state(self):
        """Test successful collection creation with state persistence"""
        result = create_collection(database="test_db", collection="test_coll")
        
        expected_response = {"status": "success", "message": "Collection created successfully"}
        self.assertEqual(result, expected_response)
        
        # Save and verify persisted state
        save_state(str(self.current_test_state_file))
        persisted_state = self._read_json_state(self.current_test_state_file)
        self.assertIn(DB.current_conn, persisted_state["connections"])
        conn_data = persisted_state["connections"][DB.current_conn]
        self.assertIn("test_db", conn_data["databases"])
        db_data = conn_data["databases"]["test_db"]
        self.assertIn("test_coll", db_data["collections"])

    def test_create_collection_already_exists(self):
        """Test collection already exists error"""
        # First create the collection
        create_collection(database="test_db", collection="test_coll")
        
        # Try to create it again
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=custom_errors.CollectionExistsError,
            expected_message="Collection 'test_db.test_coll' already exists.",
            database="test_db",
            collection="test_coll"
        )

    def test_create_collection_no_current_connection(self):
        """Test when no current connection exists"""
        # Clear the current connection
        original_conn = DB.current_conn
        DB.current_conn = None
        
        try:
            result = create_collection(database="no_conn_db", collection="no_conn_coll")
            expected_response = {"status": "success", "message": "Collection created successfully"}
            self.assertEqual(result, expected_response)
        finally:
            # Restore the original connection
            DB.current_conn = original_conn

    # --- Validation Error Tests ---
    def test_create_collection_database_name_not_string(self):
        """Test database name not string validation error"""
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database=123, collection="valid_collection_name"
        )

    def test_create_collection_collection_name_not_string(self):
        """Test collection name not string validation error"""
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database="valid_database_name", collection=None
        )

    def test_create_collection_empty_database_name(self):
        """Test empty database name validation error"""
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="", collection="valid_collection"
        )

    def test_create_collection_database_name_too_long(self):
        """Test database name too long validation error"""
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 63 characters",
            database="a" * 64, collection="valid_collection"
        )

    def test_create_collection_empty_collection_name(self):
        """Test empty collection name validation error"""
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="valid_database", collection=""
        )

    def test_create_collection_collection_name_too_long(self):
        """Test collection name too long validation error"""
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 255 characters",
            database="valid_database", collection="a" * 256
        )

    # --- Invalid Name Error Tests ---
    def test_create_collection_database_name_with_null_char(self):
        """Test database name with null character"""
        db_name = "db\0name"
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message=f"Database name 'db\x00name' contains an illegal null character.",
            database=db_name, collection="valid_collection"
        )

    def test_create_collection_collection_name_with_dollar(self):
        """Test collection name with dollar sign"""
        coll_name = "coll$name"
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message=f"Collection name '{coll_name}' contains illegal characters.",
            database="valid_database", collection=coll_name
        )

    def test_create_collection_collection_name_with_null_char(self):
        """Test collection name with null character"""
        coll_name = "coll\0name"
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message=f"Collection name '{coll_name}' contains illegal characters.",
            database="valid_database", collection=coll_name
        )

    def test_create_collection_collection_name_starts_with_system(self):
        """Test collection name starting with system"""
        coll_name = "system.coll"
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message=f"Collection name '{coll_name}' cannot start with 'system.' or contain '.system.'.",
            database="valid_database", collection=coll_name
        )

    # --- Exception Injection Tests for 100% Coverage ---
    
    def test_create_collection_collection_invalid_already_exists(self):
        """Test CollectionInvalid exception with 'already exists' message"""
        # Create a mock client that raises CollectionInvalid
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise CollectionInvalid with "already exists"
        mock_db_instance.create_collection.side_effect = pymongo.errors.CollectionInvalid(
            "Collection 'test_db.test_coll' already exists."
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.CollectionExistsError,
                expected_message="Collection 'test_db.test_coll' already exists.",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    def test_create_collection_collection_invalid_other_error(self):
        """Test CollectionInvalid exception with other invalid name messages"""
        # Create a mock client that raises CollectionInvalid
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise CollectionInvalid with other error
        mock_db_instance.create_collection.side_effect = pymongo.errors.CollectionInvalid(
            "Invalid collection name"
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.InvalidNameError,
                expected_message="Collection name 'test_coll' is invalid.",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    def test_create_collection_operation_failure_invalid_name(self):
        """Test OperationFailure exception with invalid name keywords"""
        # Create a mock client that raises OperationFailure
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise OperationFailure with invalid name
        mock_db_instance.create_collection.side_effect = pymongo.errors.OperationFailure(
            "Invalid collection name"
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.InvalidNameError,
                expected_message="Invalid name: Invalid collection name",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    def test_create_collection_operation_failure_database_not_found(self):
        """Test OperationFailure exception with database not found"""
        # Create a mock client that raises OperationFailure
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise OperationFailure with database not found
        mock_db_instance.create_collection.side_effect = pymongo.errors.OperationFailure(
            "Database not found"
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.DatabaseNotFoundError,
                expected_message="Database 'test_db' not found or cannot be accessed: Database not found",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    def test_create_collection_operation_failure_other_error(self):
        """Test OperationFailure exception with other database operation failures"""
        # Create a mock client that raises OperationFailure
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise OperationFailure with other error
        mock_db_instance.create_collection.side_effect = pymongo.errors.OperationFailure(
            "Some other database operation error"
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.ApiError,
                expected_message="Database operation failed: Some other database operation error",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    def test_create_collection_pymongo_error_database_not_found(self):
        """Test PyMongoError exception with database not found"""
        # Create a mock client that raises PyMongoError
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise PyMongoError with database not found
        mock_db_instance.create_collection.side_effect = pymongo.errors.PyMongoError(
            "Database does not exist"
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.DatabaseNotFoundError,
                expected_message="Database 'test_db' not found or cannot be accessed: Database does not exist",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    def test_create_collection_pymongo_error_other_error(self):
        """Test PyMongoError exception with other driver errors"""
        # Create a mock client that raises PyMongoError
        mock_client = MagicMock()
        mock_db_instance = MagicMock()
        mock_client.__getitem__.return_value = mock_db_instance
        
        # Mock the create_collection to raise PyMongoError with other error
        mock_db_instance.create_collection.side_effect = pymongo.errors.PyMongoError(
            "Some other driver error"
        )
        
        # Store original connections and replace with mock
        original_connections = DB.connections.copy()
        DB.connections["test_conn"] = mock_client
        
        try:
            self.assert_error_behavior(
                func_to_call=create_collection,
                expected_exception_type=custom_errors.ApiError,
                expected_message="Database driver error: Some other driver error",
                database="test_db",
                collection="test_coll"
            )
        finally:
            # Restore original connections
            DB.connections.update(original_connections)

    # --- Valid names (edge cases, boundary lengths, allowed characters) ---
    def test_create_collection_database_name_min_length_success(self):
        """Test database name with minimum length"""
        result = create_collection(database="d", collection="my_collection_min_db")
        self.assertEqual(result["status"], "success")

    def test_create_collection_database_name_max_length_success(self):
        """Test database name with maximum length"""
        result = create_collection(database="a" * 63, collection="my_collection_max_db")
        self.assertEqual(result["status"], "success")

    def test_create_collection_collection_name_min_length_success(self):
        """Test collection name with minimum length"""
        result = create_collection(database="my_database_min_coll", collection="c")
        self.assertEqual(result["status"], "success")

    def test_create_collection_collection_name_max_length_success(self):
        """Test collection name with maximum length"""
        result = create_collection(database="my_database_max_coll", collection="a" * 255)
        self.assertEqual(result["status"], "success")

    def test_create_collection_valid_names_with_underscore_success(self):
        """Test valid names with underscores"""
        result = create_collection(database="my_db_underscore", collection="my_coll_underscore")
        self.assertEqual(result["status"], "success")

    def test_create_collection_valid_names_with_hyphen_success(self):
        """Test valid names with hyphens"""
        result = create_collection(database="my-db-hyphen", collection="my-coll-hyphen")
        self.assertEqual(result["status"], "success")

    def test_create_collection_valid_names_with_numbers_success(self):
        """Test valid names with numbers"""
        result = create_collection(database="db123numbers", collection="coll456numbers")
        self.assertEqual(result["status"], "success")

    def test_create_collection_valid_name_with_dot_in_collection_success(self):
        """Test valid collection name with dots"""
        result = create_collection(database="mydb_for_dot_coll", collection="collection.with.dots")
        self.assertEqual(result["status"], "success")

    def test_create_collection_valid_database_name_with_dot_success(self):
        """Test valid database name with dots"""
        result = create_collection(database="my.db.with.dots", collection="mycoll_for_dot_db")
        self.assertEqual(result["status"], "success")

if __name__ == '__main__':
    unittest.main() 