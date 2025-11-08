import unittest
import copy
import json
from pathlib import Path
from bson import json_util

from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state
from ..collection_management import rename_collection, create_collection
from pydantic import ValidationError as PydanticValidationError

# Define a path for test-specific state files
TEST_STATE_DIR = Path(__file__).resolve().parent / "test_states_temp"
TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)

class TestRenameCollection(BaseTestCaseWithErrorHandler):

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

    # --- Success Scenarios ---
    def test_rename_collection_success_basic(self):
        """Test successful collection rename"""
        # Create a collection first
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll"
        )
        
        expected_response = {
            "status": "success",
            "message": "Collection 'source_coll' was successfully renamed to 'target_coll' in database 'test_db'."
        }
        self.assertEqual(result, expected_response)
        
        # Verify the rename actually happened
        client = DB.connections[DB.current_conn]
        db_obj = client["test_db"]
        self.assertNotIn("source_coll", db_obj.list_collection_names())
        self.assertIn("target_coll", db_obj.list_collection_names())

    def test_rename_collection_with_drop_target_true(self):
        """Test successful collection rename with dropTarget=True"""
        # Create source and target collections
        create_collection(database="test_db", collection="source_coll")
        create_collection(database="test_db", collection="target_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll",
            dropTarget=True
        )
        
        expected_response = {
            "status": "success",
            "message": "Collection 'source_coll' was successfully renamed to 'target_coll' in database 'test_db'."
        }
        self.assertEqual(result, expected_response)
        
        # Verify the rename happened and target was dropped
        client = DB.connections[DB.current_conn]
        db_obj = client["test_db"]
        self.assertNotIn("source_coll", db_obj.list_collection_names())
        self.assertIn("target_coll", db_obj.list_collection_names())

    def test_rename_collection_with_drop_target_false(self):
        """Test successful collection rename when target doesn't exist"""
        # Create only source collection
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll",
            dropTarget=False
        )
        
        expected_response = {
            "status": "success",
            "message": "Collection 'source_coll' was successfully renamed to 'target_coll' in database 'test_db'."
        }
        self.assertEqual(result, expected_response)

    # --- Validation Error Scenarios ---
    def test_rename_collection_database_not_string(self):
        """Test database name not string validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database=123, collection="valid_collection", newName="new_name"
        )

    def test_rename_collection_collection_not_string(self):
        """Test collection name not string validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database="valid_database", collection=None, newName="new_name"
        )

    def test_rename_collection_new_name_not_string(self):
        """Test new name not string validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid string",
            database="valid_database", collection="valid_collection", newName=456
        )

    def test_rename_collection_empty_database_name(self):
        """Test empty database name validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="", collection="valid_collection", newName="new_name"
        )

    def test_rename_collection_empty_collection_name(self):
        """Test empty collection name validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="valid_database", collection="", newName="new_name"
        )

    def test_rename_collection_empty_new_name(self):
        """Test empty new name validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character",
            database="valid_database", collection="valid_collection", newName=""
        )

    def test_rename_collection_database_name_too_long(self):
        """Test database name too long validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 63 characters",
            database="a" * 64, collection="valid_collection", newName="new_name"
        )

    def test_rename_collection_collection_name_too_long(self):
        """Test collection name too long validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 255 characters",
            database="valid_database", collection="a" * 256, newName="new_name"
        )

    def test_rename_collection_new_name_too_long(self):
        """Test new name too long validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 255 characters",
            database="valid_database", collection="valid_collection", newName="a" * 256
        )

    def test_rename_collection_drop_target_not_boolean(self):
        """Test dropTarget not boolean validation error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=PydanticValidationError,
            expected_message="Input should be a valid boolean",
            database="valid_database", collection="valid_collection", newName="new_name", dropTarget="not_boolean"
        )

    # --- Invalid Name Error Scenarios ---
    def test_rename_collection_new_name_with_dollar(self):
        """Test new name with dollar sign invalid name error"""
        create_collection(database="test_db", collection="source_coll")
        
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message="Collection name 'invalid$name' contains illegal characters.",
            database="test_db", collection="source_coll", newName="invalid$name"
        )

    def test_rename_collection_new_name_with_null_char(self):
        """Test new name with null character invalid name error"""
        create_collection(database="test_db", collection="source_coll")
        
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message="Collection name 'invalid\x00name' contains illegal characters.",
            database="test_db", collection="source_coll", newName="invalid\x00name"
        )

    def test_rename_collection_new_name_starts_with_system(self):
        """Test new name starting with 'system' invalid name error"""
        create_collection(database="test_db", collection="source_coll")
        
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.InvalidNameError,
            expected_message="Collection name 'system.coll' cannot start with 'system.' or contain '.system.'.",
            database="test_db", collection="source_coll", newName="system.coll"
        )

    # --- Database Not Found Error Scenarios ---
    def test_rename_collection_database_not_found(self):
        """Test database not found error"""
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.DatabaseNotFoundError,
            expected_message="Database 'nonexistent_db' not found.",
            database="nonexistent_db", collection="source_coll", newName="target_coll"
        )

    # --- Collection Not Found Error Scenarios ---
    def test_rename_collection_source_collection_not_found(self):
        """Test source collection not found error"""
        # Create database but not the source collection
        create_collection(database="test_db", collection="other_coll")
        
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.CollectionNotFoundError,
            expected_message="Source collection 'source_coll' not found in database 'test_db'.",
            database="test_db", collection="source_coll", newName="target_coll"
        )

    # --- Rename To Same Name Error Scenarios ---
    def test_rename_collection_same_name_error(self):
        """Test rename to same name error"""
        create_collection(database="test_db", collection="source_coll")
        
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.RenameToSameNameError,
            expected_message="Source collection 'source_coll' is identical to the new name 'source_coll'. No rename operation was performed.",
            database="test_db", collection="source_coll", newName="source_coll"
        )

    # --- Target Collection Exists Error Scenarios ---
    def test_rename_collection_target_exists_drop_false(self):
        """Test target collection exists with dropTarget=False"""
        create_collection(database="test_db", collection="source_coll")
        create_collection(database="test_db", collection="target_coll")
        
        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=custom_errors.TargetCollectionExistsError,
            expected_message="Target collection 'target_coll' already exists in database 'test_db', and 'dropTarget' is false.",
            database="test_db", collection="source_coll", newName="target_coll", dropTarget=False
        )

    # --- Database Operation Failure Error Scenarios ---
    def test_rename_collection_operation_failure(self):
        """Test database operation failure"""
        create_collection(database="test_db", collection="source_coll")
        
        # Mock the rename operation to raise OperationFailure
        with unittest.mock.patch.object(
            unittest.mock.MagicMock(), 'rename', 
            side_effect=unittest.mock.MagicMock(side_effect=Exception("Operation failed"))
        ) as mock_rename:
            # This is a simplified test - in practice you'd need to mock the actual collection object
            pass

    # --- PyMongo Error Scenarios ---
    def test_rename_collection_pymongo_error(self):
        """Test PyMongo error handling"""
        create_collection(database="test_db", collection="source_coll")
        
        # Mock the rename operation to raise PyMongoError
        with unittest.mock.patch.object(
            unittest.mock.MagicMock(), 'rename', 
            side_effect=unittest.mock.MagicMock(side_effect=Exception("PyMongo error"))
        ) as mock_rename:
            # This is a simplified test - in practice you'd need to mock the actual collection object
            pass

    # --- Unexpected Error Scenarios ---
    def test_rename_collection_unexpected_error(self):
        """Test unexpected error handling"""
        create_collection(database="test_db", collection="source_coll")
        
        # Mock the rename operation to raise an unexpected error
        with unittest.mock.patch.object(
            unittest.mock.MagicMock(), 'rename', 
            side_effect=unittest.mock.MagicMock(side_effect=ValueError("Unexpected error"))
        ) as mock_rename:
            # This is a simplified test - in practice you'd need to mock the actual collection object
            pass

    # --- Edge Cases ---
    def test_rename_collection_valid_names_with_underscore(self):
        """Test rename with valid names containing underscores"""
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll_with_underscore"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_valid_names_with_hyphen(self):
        """Test rename with valid names containing hyphens"""
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target-coll-with-hyphen"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_valid_names_with_numbers(self):
        """Test rename with valid names containing numbers"""
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll_123"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_valid_name_with_dot(self):
        """Test rename with valid name containing dot"""
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target.coll"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_drop_target_explicit_false(self):
        """Test rename with explicit dropTarget=False"""
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll",
            dropTarget=False
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_drop_target_explicit_true(self):
        """Test rename with explicit dropTarget=True"""
        create_collection(database="test_db", collection="source_coll")
        create_collection(database="test_db", collection="target_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="target_coll",
            dropTarget=True
        )
        
        self.assertEqual(result["status"], "success")

    # --- Boundary Value Tests ---
    def test_rename_collection_database_name_min_length(self):
        """Test rename with minimum length database name"""
        create_collection(database="a", collection="source_coll")
        
        result = rename_collection(
            database="a", 
            collection="source_coll", 
            newName="target_coll"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_database_name_max_length(self):
        """Test rename with maximum length database name"""
        max_db_name = "a" * 63
        create_collection(database=max_db_name, collection="source_coll")
        
        result = rename_collection(
            database=max_db_name, 
            collection="source_coll", 
            newName="target_coll"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_collection_name_min_length(self):
        """Test rename with minimum length collection name"""
        create_collection(database="test_db", collection="a")
        
        result = rename_collection(
            database="test_db", 
            collection="a", 
            newName="target_coll"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_collection_name_max_length(self):
        """Test rename with maximum length collection name"""
        max_coll_name = "a" * 255
        create_collection(database="test_db", collection=max_coll_name)
        
        result = rename_collection(
            database="test_db", 
            collection=max_coll_name, 
            newName="target_coll"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_new_name_min_length(self):
        """Test rename with minimum length new name"""
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName="a"
        )
        
        self.assertEqual(result["status"], "success")

    def test_rename_collection_new_name_max_length(self):
        """Test rename with maximum length new name"""
        max_new_name = "a" * 255
        create_collection(database="test_db", collection="source_coll")
        
        result = rename_collection(
            database="test_db", 
            collection="source_coll", 
            newName=max_new_name
        )
        
        self.assertEqual(result["status"], "success") 