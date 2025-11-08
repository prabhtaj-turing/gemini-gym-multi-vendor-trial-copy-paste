import unittest
import copy
import json
from pathlib import Path
from bson import json_util, ObjectId
from typing import Dict

from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state, MongoDB
from mongodb import rename_collection 
from pydantic import ValidationError as PydanticValidationError

# Define a path for test-specific state files
TEST_STATE_DIR = Path(__file__).resolve().parent / "test_states_temp_rename"
TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)

class TestRenameCollection(BaseTestCaseWithErrorHandler):

    def _get_current_test_state_file_path(self) -> Path:
        test_method_name = self.id().split('.')[-1]
        return TEST_STATE_DIR / f"{test_method_name}_mongodb_state.json"

    def _write_json_state(self, file_path: Path, state_dict: dict):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(state_dict, f, default=json_util.default, indent=2)

    def _read_json_state(self, file_path: Path) -> dict:
        if not file_path.exists():
            return {"connections": {"test_conn": {"databases": {}}}}
        with open(file_path, "r") as f:
            try:
                return json.load(f, object_hook=json_util.object_hook)
            except json.JSONDecodeError:
                return {"connections": {"test_conn": {"databases": {}}}}

    def setUp(self):
        self.current_test_state_file = self._get_current_test_state_file_path()
        
        # Base state for most tests: an active connection "test_conn" with no databases yet
        self.base_empty_state_with_connection = {
            "connections": {
                "test_conn": {"databases": {}}
            }
        }
        self._write_json_state(self.current_test_state_file, self.base_empty_state_with_connection)
        load_state(str(self.current_test_state_file))
        
        if not DB.current_conn or DB.current_conn != "test_conn":
            DB.switch_connection("test_conn")

        # Common names used in tests, set them up here if they are part of a common initial state
        self.db_name_for_tests = "test_db_rename"
        self.source_coll_for_tests = "source_coll_rename"
        self.existing_target_coll_for_tests = "target_coll_exists_rename"
        self.source_data_for_tests = [
            {"_id": ObjectId(), "field": "value1_source_r"}, # Use ObjectId() for new unique IDs
            {"_id": ObjectId(), "field": "value2_source_r"}
        ]
        self.target_data_for_tests = [
            {"_id": ObjectId(), "field": "value1_target_r"}
        ]

    def tearDown(self):
        if self.current_test_state_file.exists():
            try:
                self.current_test_state_file.unlink()
            except OSError:
                pass

    def _setup_initial_state_for_rename_tests(self):
        """Sets up a common initial state for many rename tests."""
        initial_state = {
            "connections": {
                "test_conn": {
                    "databases": {
                        self.db_name_for_tests: {
                            "collections": {
                                self.source_coll_for_tests: {"documents": copy.deepcopy(self.source_data_for_tests), "indexes": []},
                                self.existing_target_coll_for_tests: {"documents": copy.deepcopy(self.target_data_for_tests), "indexes": []},
                                "another_coll_rename": {"documents": [{"_id": ObjectId(), "data": "misc_r"}], "indexes": []}
                            }
                        },
                        "empty_db_for_rename": {"collections": {}},
                        "other_db_for_rename": {
                            "collections": {
                                "other_coll_in_other_db": {"documents": [{"_id": ObjectId(), "data": "other data_r"}], "indexes": []}
                            }
                        }
                    }
                }
            }
        }
        self._write_json_state(self.current_test_state_file, initial_state)
        load_state(str(self.current_test_state_file))
        DB.switch_connection("test_conn") # Ensure connection is active after load

    def _assert_db_and_collection_state(self, db_name_to_check: str, expected_collections: Dict[str, list]):
        """Asserts in-memory and persisted state of a database's collections."""
        # In-memory check
        client = DB.connections[DB.current_conn]
        self.assertIn(db_name_to_check, client.list_database_names())
        db_instance = client[db_name_to_check]
        actual_collection_names = sorted(db_instance.list_collection_names())
        self.assertEqual(actual_collection_names, sorted(expected_collections.keys()))
        for coll_name, expected_docs in expected_collections.items():
            # Comparing ObjectId requires care if they are regenerated or stringified.
            # For simplicity, if docs are complex, consider comparing counts or key fields.
            # Here, assuming docs are simple enough for direct comparison after fetching.
            actual_docs = list(db_instance[coll_name].find({}, {"_id": 0})) # Exclude _id for simpler comparison if variable
            expected_docs_no_id = [copy.deepcopy(doc) for doc in expected_docs]
            for doc in expected_docs_no_id: doc.pop("_id", None)
            self.assertEqual(actual_docs, expected_docs_no_id, f"Documents mismatch in {db_name_to_check}.{coll_name}")

        # Persisted state check
        save_state(str(self.current_test_state_file))
        persisted = self._read_json_state(self.current_test_state_file)
        conn_data = persisted["connections"][DB.current_conn]
        self.assertIn(db_name_to_check, conn_data["databases"])
        db_data = conn_data["databases"][db_name_to_check]
        self.assertEqual(sorted(db_data["collections"].keys()), sorted(expected_collections.keys()))
        for coll_name, expected_docs in expected_collections.items():
            persisted_docs = db_data["collections"][coll_name]["documents"]
            persisted_docs_no_id = [copy.deepcopy(doc) for doc in persisted_docs]
            for doc in persisted_docs_no_id: doc.pop("_id", None) # Assuming _id might be ObjectId
            expected_docs_no_id_compare = [copy.deepcopy(doc) for doc in expected_docs]
            for doc in expected_docs_no_id_compare: doc.pop("_id", None)
            self.assertEqual(persisted_docs_no_id, expected_docs_no_id_compare, f"Persisted documents mismatch in {db_name_to_check}.{coll_name}")

    def _run_error_test_and_check_state_unchanged(self, expected_exception, expected_message_part, **kwargs_for_rename_collection):
        """Helper for error tests where DB/JSON state shouldn't change."""
        self._setup_initial_state_for_rename_tests() # Ensure a known state before error test
        
        initial_json_state_before_call = self._read_json_state(self.current_test_state_file)
        initial_in_memory_snapshot = {}
        client = DB.connections[DB.current_conn]
        for db_name_snap in client.list_database_names():
            initial_in_memory_snapshot[db_name_snap] = sorted(client[db_name_snap].list_collection_names())

        self.assert_error_behavior(
            func_to_call=rename_collection,
            expected_exception_type=expected_exception,
            expected_message=expected_message_part,
            **kwargs_for_rename_collection
        )

        current_in_memory_snapshot = {}
        client_after = DB.connections[DB.current_conn]
        for db_name_snap_after in client_after.list_database_names():
            current_in_memory_snapshot[db_name_snap_after] = sorted(client_after[db_name_snap_after].list_collection_names())
        self.assertEqual(current_in_memory_snapshot, initial_in_memory_snapshot, "In-memory DB structure changed on error.")

        # If rename_collection does NOT save state on early validation error, JSON should be unchanged.
        final_json_state = self._read_json_state(self.current_test_state_file)
        self.assertEqual(final_json_state, initial_json_state_before_call, "JSON state file changed on error.")

    def test_rename_collection_success_no_target_exists(self):
        self._setup_initial_state_for_rename_tests()
        new_name = "renamed_coll_no_target"
        
        result = rename_collection(
            database=self.db_name_for_tests,
            collection=self.source_coll_for_tests,
            newName=new_name
        )
        self.assertEqual(result, {"status": "success", "message": f"Collection '{self.source_coll_for_tests}' was successfully renamed to '{new_name}' in database '{self.db_name_for_tests}'."})

        expected_collections_in_db = {
            new_name: self.source_data_for_tests,
            self.existing_target_coll_for_tests: self.target_data_for_tests,
            "another_coll_rename": [{"_id": "ac1_r", "data": "misc_r"}] # Assuming ac1_r is ObjectId compatible
        }
        # Adjust _id in "another_coll_rename" if it's a string and your comparison needs ObjectId
        # For simplicity, I'm assuming a more direct comparison might be needed or data setup adjusts _ids
        # Re-fetch the actual data for another_coll_rename for comparison
        client = DB.connections[DB.current_conn]
        another_coll_data_actual = list(client[self.db_name_for_tests]["another_coll_rename"].find({}))
        expected_collections_in_db["another_coll_rename"] = another_coll_data_actual


        self._assert_db_and_collection_state(self.db_name_for_tests, expected_collections_in_db)
        
        # Check other DBs are unaffected (example)
        persisted_state = self._read_json_state(self.current_test_state_file)
        self.assertIn("other_db_for_rename", persisted_state["connections"][DB.current_conn]["databases"])

    def test_rename_collection_success_target_exists_drop_target_true(self):
        self._setup_initial_state_for_rename_tests()
        
        result = rename_collection(
            database=self.db_name_for_tests,
            collection=self.source_coll_for_tests,
            newName=self.existing_target_coll_for_tests,
            dropTarget=True
        )
        self.assertEqual(result, {"status": "success", "message": f"Collection '{self.source_coll_for_tests}' was successfully renamed to '{self.existing_target_coll_for_tests}' in database '{self.db_name_for_tests}'."})

        client = DB.connections[DB.current_conn] # For fetching 'another_coll_rename' data
        another_coll_data_actual = list(client[self.db_name_for_tests]["another_coll_rename"].find({}))

        expected_collections_in_db = {
            self.existing_target_coll_for_tests: self.source_data_for_tests, # Now contains source data
            "another_coll_rename": another_coll_data_actual
        }
        self._assert_db_and_collection_state(self.db_name_for_tests, expected_collections_in_db)


    def test_rename_collection_error_database_not_found(self):
        db_not_found_name = "non_existent_db_rename"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.DatabaseNotFoundError,
            f"Database '{db_not_found_name}' not found.",
            database=db_not_found_name, collection="any_coll", newName="any_new_name"
        )

    def test_rename_collection_error_source_collection_not_found(self):
        coll_not_found_name = "non_existent_source_coll_rename"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.CollectionNotFoundError,
            f"Source collection '{coll_not_found_name}' not found in database '{self.db_name_for_tests}'.",
            database=self.db_name_for_tests, collection=coll_not_found_name, newName="any_new_name"
        )

    def test_rename_collection_error_target_collection_exists_drop_target_false(self):
        self._run_error_test_and_check_state_unchanged(
            custom_errors.TargetCollectionExistsError,
            f"Target collection '{self.existing_target_coll_for_tests}' already exists in database '{self.db_name_for_tests}', and 'dropTarget' is false.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests,
            newName=self.existing_target_coll_for_tests, dropTarget=False
        )

    def test_rename_collection_error_target_collection_exists_drop_target_default_is_false(self):
        self._run_error_test_and_check_state_unchanged(
            custom_errors.TargetCollectionExistsError,
            f"Target collection '{self.existing_target_coll_for_tests}' already exists in database '{self.db_name_for_tests}', and 'dropTarget' is false.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests,
            newName=self.existing_target_coll_for_tests
        )

    def test_rename_collection_error_invalid_new_name_starts_with_system(self):
        invalid_name = "system.core"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Collection name '{invalid_name}' cannot start with 'system.' or contain '.system.'.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests, newName=invalid_name
        )
    
    def test_rename_collection_error_invalid_new_name_contains_dollar(self):
        invalid_name = "coll$with_dollar"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Collection name '{invalid_name}' contains illegal characters.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests, newName=invalid_name
        )
    
    def test_rename_collection_error_invalid_new_name_contains_null_char(self):
        invalid_name = "coll\0with_null"
        self._run_error_test_and_check_state_unchanged(
            custom_errors.InvalidNameError,
            f"Collection name '{invalid_name}' contains illegal characters.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests, newName=invalid_name
        )

    # --- Pydantic or Built-in Validation Error Tests ---
    # These now expect PydanticValidationError directly if rename_collection doesn't wrap it.
    # The expected_message should be a substring of Pydantic's verbose error.

    def test_rename_collection_validation_error_empty_database_name(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError, # Expect Pydantic's own error
            "String should have at least 1 character", # Substring from Pydantic's error for database field
            database="", collection=self.source_coll_for_tests, newName="new_name_valid"
        )

    def test_rename_collection_validation_error_long_database_name(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at most 63 characters", # Substring for database field
            database="a" * 64, collection=self.source_coll_for_tests, newName="new_name_valid"
        )

    def test_rename_collection_validation_error_empty_collection_name(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at least 1 character", # Substring for collection field
            database=self.db_name_for_tests, collection="", newName="new_name_valid"
        )

    def test_rename_collection_validation_error_long_collection_name(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at most 255 characters", # Substring for collection field
            database=self.db_name_for_tests, collection="a" * 256, newName="new_name_valid"
        )

    def test_rename_collection_validation_error_empty_new_name(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at least 1 character", # Substring for newName field
            database=self.db_name_for_tests, collection=self.source_coll_for_tests, newName=""
        )

    def test_rename_collection_validation_error_long_new_name(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "String should have at most 255 characters", # Substring for newName field
            database=self.db_name_for_tests, collection=self.source_coll_for_tests, newName="a" * 256
        )

    def test_rename_collection_validation_error_invalid_drop_target_type(self):
        self._run_error_test_and_check_state_unchanged(
            PydanticValidationError,
            "Input should be a valid boolean", # Substring for dropTarget field (bool type error)
            database=self.db_name_for_tests, collection=self.source_coll_for_tests,
            newName="new_name_valid", dropTarget="true_string"
        )

    # --- More specific behavior tests ---
    def test_rename_collection_to_same_name_drop_target_false(self):
        # Renaming to itself when target exists and dropTarget is false should error
        self._run_error_test_and_check_state_unchanged(
            custom_errors.RenameToSameNameError,
            f"Source collection '{self.source_coll_for_tests}' is identical to the new name '{self.source_coll_for_tests}'. No rename operation was performed.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests,
            newName=self.source_coll_for_tests, dropTarget=False
        )
        # Additionally verify the original collection data is untouched
        client = DB.connections[DB.current_conn]
        db_instance = client[self.db_name_for_tests]
        self.assertIn(self.source_coll_for_tests, db_instance.list_collection_names())
        actual_docs = list(db_instance[self.source_coll_for_tests].find({}))
        # Need to compare content carefully, _id might cause issues if not handled
        self.assertEqual(len(actual_docs), len(self.source_data_for_tests))

    def test_rename_collection_to_same_name_drop_target_true(self):
        # Renaming to itself when target exists and dropTarget is true
        self._run_error_test_and_check_state_unchanged(
            custom_errors.RenameToSameNameError, # Or another error depending on exact mongo shell/driver behavior
            f"Source collection '{self.source_coll_for_tests}' is identical to the new name '{self.source_coll_for_tests}'. No rename operation was performed.",
            database=self.db_name_for_tests, collection=self.source_coll_for_tests,
            newName=self.source_coll_for_tests, dropTarget=True
        )

    def test_rename_collection_preserves_other_collections_in_same_db(self):
        self._setup_initial_state_for_rename_tests()
        new_name = "renamed_coll_others_preserved"
        
        rename_collection(
            database=self.db_name_for_tests,
            collection=self.source_coll_for_tests,
            newName=new_name
        )
        
        client = DB.connections[DB.current_conn]
        db_instance = client[self.db_name_for_tests]

        self.assertIn(new_name, db_instance.list_collection_names())
        self.assertNotIn(self.source_coll_for_tests, db_instance.list_collection_names())
        
        # Check other collections are still there and their data is intact
        self.assertIn(self.existing_target_coll_for_tests, db_instance.list_collection_names())
        target_docs_after = list(db_instance[self.existing_target_coll_for_tests].find({}, {"_id": 0}))
        expected_target_docs_no_id = [copy.deepcopy(doc) for doc in self.target_data_for_tests]
        for doc in expected_target_docs_no_id: doc.pop("_id", None)
        self.assertEqual(target_docs_after, expected_target_docs_no_id)

        self.assertIn("another_coll_rename", db_instance.list_collection_names())
        # Fetch actual data for comparison as _id might be an issue with simple list compare
        # For this test, just checking existence might be enough or count.
        self.assertTrue(db_instance["another_coll_rename"].count_documents({}) > 0)

    def test_rename_collection_preserves_other_databases_and_their_content(self):
        self._setup_initial_state_for_rename_tests() # This sets up other_db_for_rename
        new_name = "renamed_coll_other_dbs_preserved"

        # Snapshot content of other_db_for_rename before the operation
        client = DB.connections[DB.current_conn]
        original_other_db_coll_names = []
        original_other_db_coll_docs = {}
        if "other_db_for_rename" in client.list_database_names():
            other_db_instance = client["other_db_for_rename"]
            original_other_db_coll_names = sorted(other_db_instance.list_collection_names())
            for coll_n in original_other_db_coll_names:
                original_other_db_coll_docs[coll_n] = list(other_db_instance[coll_n].find({}, {"_id": 0}))
        
        original_empty_db_coll_names = []
        if "empty_db_for_rename" in client.list_database_names():
             original_empty_db_coll_names = sorted(client["empty_db_for_rename"].list_collection_names())


        rename_collection(
            database=self.db_name_for_tests,
            collection=self.source_coll_for_tests,
            newName=new_name
        )

        # Verify other_db_for_rename and its content are preserved
        self.assertIn("other_db_for_rename", client.list_database_names())
        other_db_instance_after = client["other_db_for_rename"]
        self.assertEqual(sorted(other_db_instance_after.list_collection_names()), original_other_db_coll_names)
        for coll_n_after in other_db_instance_after.list_collection_names():
            docs_after = list(other_db_instance_after[coll_n_after].find({}, {"_id": 0}))
            self.assertEqual(docs_after, original_other_db_coll_docs.get(coll_n_after, []))


if __name__ == '__main__':
    unittest.main()