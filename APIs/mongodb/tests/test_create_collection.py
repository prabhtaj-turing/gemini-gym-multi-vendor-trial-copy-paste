import unittest
import copy
import json
from pathlib import Path
from bson import json_util

from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state # Import DB and persistence functions
from ..collection_management import create_collection
from pydantic import ValidationError as PydanticValidationError

# Define a path for test-specific state files
TEST_STATE_DIR = Path(__file__).resolve().parent / "test_states_temp" # Use resolve for robustness
TEST_STATE_DIR.mkdir(parents=True, exist_ok=True) # Ensure directory exists, create parents if needed

class TestCreateCollection(BaseTestCaseWithErrorHandler):

    def _get_current_test_state_file_path(self) -> Path:
        """Generates a state file path based on the current test method name."""
        # To get the test method name, unittest provides it via self.id()
        # self.id() is usually something like 'your_module.YourClass.test_method_name'
        test_method_name = self.id().split('.')[-1]
        return TEST_STATE_DIR / f"{test_method_name}_mongodb_state.json"

    def _write_json_state(self, file_path: Path, state_dict: dict):
        """Helper to write a dictionary to a JSON file for test setup."""
        file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        with open(file_path, "w") as f:
            json.dump(state_dict, f, default=json_util.default, indent=2)

    def _read_json_state(self, file_path: Path) -> dict:
        """Helper to read a JSON file into a dictionary for assertions."""
        if not file_path.exists():
            # Return a structure that load_state would expect for an empty DB
            return {"connections": {"test_conn": {"databases": {}}}} 
        with open(file_path, "r") as f:
            try:
                return json.load(f, object_hook=json_util.object_hook)
            except json.JSONDecodeError: # Handle case where file might be empty or malformed
                return {"connections": {"test_conn": {"databases": {}}}}


    def setUp(self):
        self.current_test_state_file = self._get_current_test_state_file_path()
        
        # Define a base "empty" state for most tests for the active connection
        self.base_empty_state_dict = {
            "connections": {
                "test_conn": { # Ensure our test connection exists in the state
                    "databases": {}
                }
            }
        }
        
        # Ensure a clean start by writing an empty state and loading it
        self._write_json_state(self.current_test_state_file, self.base_empty_state_dict)
        load_state(str(self.current_test_state_file)) # Load this minimal state into global DB
        
        # Ensure a connection is active and it's the one we expect from the state file
        if not DB.current_conn or DB.current_conn not in DB.connections:
            DB.switch_connection("test_conn")
        elif DB.current_conn != "test_conn": # If a different conn was loaded, switch
            DB.switch_connection("test_conn")

    def tearDown(self):
        # Clean up the temporary state file used by the test
        if self.current_test_state_file.exists():
            try:
                self.current_test_state_file.unlink()
            except OSError: # Handle potential issues if file is locked, though unlikely in tests
                pass 
        # Clean up the directory if it's empty, optional
        # try:
        #     TEST_STATE_DIR.rmdir() # Only if empty
        # except OSError:
        #     pass

    
    def test_create_collection_new_db_new_collection_success(self):
        db_name = "new_database"
        coll_name = "new_collection"
        
        result = create_collection(database=db_name, collection=coll_name)
        
        expected_response = {"status": "success", "message": "Collection created successfully"}
        self.assertEqual(result, expected_response)
        
        client = DB.connections[DB.current_conn]
        self.assertIn(db_name, client.list_database_names())
        mongo_db_instance = client[db_name]
        self.assertIn(coll_name, mongo_db_instance.list_collection_names())
        self.assertEqual(mongo_db_instance[coll_name].count_documents({}), 0)

        save_state(str(self.current_test_state_file))
        persisted_state = self._read_json_state(self.current_test_state_file)
        self.assertIn(DB.current_conn, persisted_state["connections"])
        conn_data = persisted_state["connections"][DB.current_conn]
        self.assertIn(db_name, conn_data["databases"])
        db_data = conn_data["databases"][db_name]
        self.assertIn(coll_name, db_data["collections"])
        self.assertEqual(db_data["collections"][coll_name]["documents"], [])

    def test_create_collection_existing_db_new_collection_success(self):
        existing_db_name = "existing_db_for_test"
        existing_coll_name = "old_collection"
        new_coll_name = "new_collection_in_existing_db"
        sample_doc_id = "doc1"
        sample_doc_data = "sample_document"
        
        initial_state_dict = {
            "connections": {
                "test_conn": {
                    "databases": {
                        existing_db_name: {
                            "collections": {
                                existing_coll_name: {
                                    "documents": [{"_id": sample_doc_id, "data": sample_doc_data}],
                                    "indexes": [] 
                                }
                            }
                        }
                    }
                }
            }
        }
        self._write_json_state(self.current_test_state_file, initial_state_dict)
        load_state(str(self.current_test_state_file))
        DB.switch_connection("test_conn")

        result = create_collection(database=existing_db_name, collection=new_coll_name)
        
        expected_response = {"status": "success", "message": "Collection created successfully"}
        self.assertEqual(result, expected_response)

        client = DB.connections[DB.current_conn]
        mongo_db_instance = client[existing_db_name]
        self.assertIn(existing_coll_name, mongo_db_instance.list_collection_names())
        self.assertEqual(mongo_db_instance[existing_coll_name].count_documents({"_id": sample_doc_id}), 1)
        self.assertIn(new_coll_name, mongo_db_instance.list_collection_names())
        self.assertEqual(mongo_db_instance[new_coll_name].count_documents({}), 0)
        self.assertEqual(len(mongo_db_instance.list_collection_names()), 2)

        save_state(str(self.current_test_state_file))
        persisted_state = self._read_json_state(self.current_test_state_file)
        conn_data = persisted_state["connections"][DB.current_conn]
        db_data = conn_data["databases"][existing_db_name]
        self.assertIn(existing_coll_name, db_data["collections"])
        self.assertEqual(len(db_data["collections"][existing_coll_name]["documents"]), 1)
        self.assertIn(new_coll_name, db_data["collections"])
        self.assertEqual(db_data["collections"][new_coll_name]["documents"], [])

    def test_create_collection_already_exists_error(self):
        db_name = "test_db_exists"
        coll_name = "test_coll_exists"
        
        initial_state_dict = {
            "connections": {
                "test_conn": {
                    "databases": {
                        db_name: {"collections": {coll_name: {"documents": [], "indexes": []}}}
                    }
                }
            }
        }
        self._write_json_state(self.current_test_state_file, initial_state_dict)
        
        load_state(str(self.current_test_state_file))
        DB.switch_connection("test_conn")
        
        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=custom_errors.CollectionExistsError,
            expected_message=f"Collection '{db_name}.{coll_name}' already exists.",
            database=db_name,
            collection=coll_name
        )

        persisted_state_after_error = self._read_json_state(self.current_test_state_file)
        # Check that the persisted state reflects the initial setup, not something new
        self.assertIn(db_name, persisted_state_after_error["connections"]["test_conn"]["databases"])
        self.assertIn(coll_name, persisted_state_after_error["connections"]["test_conn"]["databases"][db_name]["collections"])
        self.assertEqual(len(persisted_state_after_error["connections"]["test_conn"]["databases"][db_name]["collections"]), 1)

    # --- New tests for 100% coverage ---
    
    def test_create_collection_no_current_connection(self):
        """Test when no current connection exists"""
        # Clear the current connection
        original_conn = DB.current_conn
        DB.current_conn = None
        
        try:
            result = create_collection(database="test_db", collection="test_coll")
            expected_response = {"status": "success", "message": "Collection created successfully"}
            self.assertEqual(result, expected_response)
        finally:
            # Restore the original connection
            DB.current_conn = original_conn

    def _run_error_test_and_check_state_unchanged(self, expected_exception, expected_message_part, **kwargs_for_create_collection):
        """Helper for boilerplate in validation/name error tests checking state."""
        initial_json_state_before_call = self._read_json_state(self.current_test_state_file)
        
        initial_in_memory_snapshot = {}
        if DB.current_conn and DB.current_conn in DB.connections:
            client = DB.connections[DB.current_conn]
            for db_name_snap in client.list_database_names():
                initial_in_memory_snapshot[db_name_snap] = sorted(client[db_name_snap].list_collection_names())

        self.assert_error_behavior(
            func_to_call=create_collection,
            expected_exception_type=expected_exception,
            expected_message=expected_message_part,
            **kwargs_for_create_collection
        )

        current_in_memory_snapshot = {}
        if DB.current_conn and DB.current_conn in DB.connections:
            client_after = DB.connections[DB.current_conn]
            for db_name_snap_after in client_after.list_database_names():
                current_in_memory_snapshot[db_name_snap_after] = sorted(client_after[db_name_snap_after].list_collection_names())
        self.assertEqual(current_in_memory_snapshot, initial_in_memory_snapshot, "In-memory DB structure changed on error.")

        # If create_collection does NOT save state on early validation error, JSON should be unchanged.
        # If it DOES save state (even an unchanged one), this assertion might need adjustment
        # or you'd check that the content of the saved state is logically equivalent to the initial.
        final_json_state = self._read_json_state(self.current_test_state_file)
        self.assertEqual(final_json_state, initial_json_state_before_call, "JSON state file changed on error.")

    # --- ValidationError Tests ---
    def test_create_collection_database_name_not_string_validation_error(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "Input should be a valid string",
            database=123, collection="valid_collection_name"
        )

    def test_create_collection_collection_name_not_string_validation_error(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "Input should be a valid string", 
            database="valid_database_name", collection=None
        )

    def test_create_collection_empty_database_name_validation_error(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at least 1 character",
            database="", collection="valid_collection"
        )

    def test_create_collection_database_name_too_long_validation_error(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at most 63 characters",
            database="a" * 64, collection="valid_collection"
        )

    def test_create_collection_empty_collection_name_validation_error(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at least 1 character",
            database="valid_database", collection=""
        )

    def test_create_collection_collection_name_too_long_validation_error(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at most 255 characters",
            database="valid_database", collection="a" * 256
        )

    # --- InvalidNameError Tests ---
    def test_create_collection_database_name_with_null_char_invalid_name_error(self):
        db_name = "db\0name"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Database name 'db\x00name' contains an illegal null character.",
            database=db_name, collection="valid_collection"
        )
        
    def test_create_collection_collection_name_with_dollar_invalid_name_error(self):
        coll_name = "coll$name"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Collection name '{coll_name}' contains illegal characters.",
            database="valid_database", collection=coll_name
        )

    def test_create_collection_collection_name_with_null_char_invalid_name_error(self):
        coll_name = "coll\0name"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Collection name '{coll_name}' contains illegal characters.",
            database="valid_database", collection=coll_name
        )

    def test_create_collection_collection_name_starts_with_system_invalid_name_error(self):
        coll_name = "system.coll"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Collection name '{coll_name}' cannot start with 'system.' or contain '.system.'.",
            database="valid_database", collection=coll_name
        )

    # --- Valid names (edge cases, boundary lengths, allowed characters) ---
    def _run_success_test_and_check_persisted_state(self, db_name_to_create: str, coll_name_to_create: str):
        result = create_collection(database=db_name_to_create, collection=coll_name_to_create)
        self.assertEqual(result["status"], "success", f"Failed for DB: {db_name_to_create}, Coll: {coll_name_to_create}")

        # In-memory check
        client = DB.connections[DB.current_conn]
        self.assertIn(db_name_to_create, client.list_database_names())
        self.assertIn(coll_name_to_create, client[db_name_to_create].list_collection_names())
        
        # Persisted state check
        save_state(str(self.current_test_state_file))
        persisted_state = self._read_json_state(self.current_test_state_file)
        self.assertIn(DB.current_conn, persisted_state["connections"])
        conn_data = persisted_state["connections"][DB.current_conn]
        self.assertIn(db_name_to_create, conn_data["databases"])
        db_data = conn_data["databases"][db_name_to_create]
        self.assertIn(coll_name_to_create, db_data["collections"])
        self.assertIn("documents", db_data["collections"][coll_name_to_create]) # Check documents key exists

    def test_create_collection_database_name_min_length_success(self):
        self._run_success_test_and_check_persisted_state("d", "my_collection_min_db")

    def test_create_collection_database_name_max_length_success(self):
        self._run_success_test_and_check_persisted_state("a" * 63, "my_collection_max_db")

    def test_create_collection_collection_name_min_length_success(self):
        self._run_success_test_and_check_persisted_state("my_database_min_coll", "c")

    def test_create_collection_collection_name_max_length_success(self):
        self._run_success_test_and_check_persisted_state("my_database_max_coll", "a" * 255)

    def test_create_collection_valid_names_with_underscore_success(self):
        self._run_success_test_and_check_persisted_state("my_db_underscore", "my_coll_underscore")

    def test_create_collection_valid_names_with_hyphen_success(self):
        self._run_success_test_and_check_persisted_state("my-db-hyphen", "my-coll-hyphen")

    def test_create_collection_valid_names_with_numbers_success(self):
        self._run_success_test_and_check_persisted_state("db123numbers", "coll456numbers")
        
    def test_create_collection_valid_name_with_dot_in_collection_success(self):
        self._run_success_test_and_check_persisted_state("mydb_for_dot_coll", "collection.with.dots")

    def test_create_collection_valid_database_name_with_dot_success(self):
        # This test assumes your _validate_database_name_conventions allows dots
        # and your Pydantic model for database name also allows dots.
        self._run_success_test_and_check_persisted_state("my.db.with.dots", "mycoll_for_dot_db")

if __name__ == '__main__':
    unittest.main()