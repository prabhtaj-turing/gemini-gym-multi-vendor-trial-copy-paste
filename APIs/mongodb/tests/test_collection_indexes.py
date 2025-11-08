import unittest # Added for clarity, though BaseTestCaseWithErrorHandler likely imports it
from pathlib import Path
from ..SimulationEngine import custom_errors
from ..collection_management import collection_indexes
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state, load_state # Import the global DB instance and state functions


class TestCollectionIndexes(BaseTestCaseWithErrorHandler):

    """Tests for the ``collection_indexes`` helper.

    The previous version of this test-suite asserted on several implementation
    details that the current public contract of ``collection_indexes`` no longer
    guarantees – most notably the presence of internal index options such as
    ``v``, ``unique``, ``sparse`` or ``expireAfterSeconds``.  The helper now
    purposefully returns **only** the index name and its key specification in a
    human-readable string.  These tests have therefore been rewritten to assert
    solely on the stable surface:

    * The summary entry (position 0) correctly reports the number of indexes.
    * Each expected index name is present in the output.
    * The reported key specification matches what was declared when the test
      database was prepared.
    """

    # ---------------------------------------------------------------------
    # Fixtures
    # ---------------------------------------------------------------------

    def setUp(self):
        """Prepare an isolated in-memory mongomock connection with fixture data."""
        # 1. Persist the current global DB state so we can restore it in tearDown
        self.temp_state_file_path = Path(f"temp_db_state_{self.__class__.__name__}.json")
        save_state(str(self.temp_state_file_path))

        # 2. Work on a dedicated connection so that tests run in parallel do not
        #    interfere with each other or with the default connection.
        self.test_conn_name = "test_conn_for_collection_indexes"
        DB.switch_connection(self.test_conn_name)
        client = DB.connections[DB.current_conn]

        # 3. Make sure we start from a pristine set of databases.
        for db_name in ["test_db", "another_db", "empty_db"]:
            if db_name in client.list_database_names():
                client.drop_database(db_name)

        # 4. Populate fixture data & indexes -------------------------------------------------
        # --- test_db ---------------------------------------------------------
        db_test = client["test_db"]
        # users collection
        users_coll = db_test["users"]
        users_coll.insert_one({"seed": True})
        users_coll.create_index([("username", 1)], name="username_1", unique=True)
        users_coll.create_index([("email", 1)], name="email_1")
        # products collection
        products_coll = db_test["products"]
        products_coll.insert_one({"seed": 1})
        products_coll.create_index([("price", -1), ("category", 1)], name="price_-1_category_1")
        # empty collections with only the automatic _id_ index
        db_test.create_collection("empty_coll")
        db_test.create_collection("coll_no_indexes_field")
        # collection with additional index options (which we no longer surface)
        coll_extra = db_test["coll_with_extra_options"]
        coll_extra.insert_one({"seed": 1})
        coll_extra.create_index([("last_login", -1)], name="last_login_idx", sparse=True, expireAfterSeconds=3600)

        # --- another_db ------------------------------------------------------
        db_another = client["another_db"]
        simple_coll = db_another["simple_coll"]
        simple_coll.insert_one({"seed": 1})
        simple_coll.create_index([("field_v1", 1)], name="field_v1_idx")

        # Make sure DB.current_db points somewhere reasonable in case other code
        # relies on it.  The helper itself takes an explicit "database" arg.
        DB.use_database("test_db")

    def tearDown(self):
        """Restore the global DB object back to its pre-test state."""
        if self.temp_state_file_path.exists():
            load_state(str(self.temp_state_file_path))
            self.temp_state_file_path.unlink(missing_ok=True)

    # ---------------------------------------------------------------------
    # Success paths
    # ---------------------------------------------------------------------

    def _run_and_extract(self, db_name: str, coll_name: str):
        """Utility to switch connection and get the helper output list."""
        DB.switch_connection(self.test_conn_name)
        return collection_indexes(db_name, coll_name)["content"]

    def test_collection_indexes_success_multiple_indexes(self):
        """users: _id_, username_1, email_1"""
        result = self._run_and_extract("test_db", "users")
        # 1 summary + 3 individual indexes
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["text"], 'Found 3 indexes in the collection "users":')

        expected_keys = {
            "_id_": "[(\'_id\', 1)]",
            "username_1": "[(\'username\', 1)]",
            "email_1": "[(\'email\', 1)]",
        }
        for idx_name, key_repr in expected_keys.items():
            match = next((d for d in result if f'Name "{idx_name}"' in d["text"]), None)
            self.assertIsNotNone(match, f"{idx_name} index not reported")
            self.assertIn(key_repr, match["text"])

    def test_collection_indexes_success_single_compound_index(self):
        """products: _id_, price/category compound"""
        result = self._run_and_extract("test_db", "products")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["text"], 'Found 2 indexes in the collection "products":')

        expected_keys = {
            "_id_": "[(\'_id\', 1)]",
            "price_-1_category_1": "[(\'price\', -1), (\'category\', 1)]",
        }
        for idx_name, key_repr in expected_keys.items():
            match = next((d for d in result if f'Name "{idx_name}"' in d["text"]), None)
            self.assertIsNotNone(match, f"{idx_name} index not reported")
            self.assertIn(key_repr, match["text"])

    def test_collection_indexes_success_no_custom_indexes(self):
        """empty_coll: only _id_"""
        result = self._run_and_extract("test_db", "empty_coll")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], 'Found 1 indexes in the collection "empty_coll":')

        match = next((d for d in result if 'Name "_id_"' in d["text"]), None)
        self.assertIsNotNone(match, "_id_ index not reported")
        self.assertIn("[(\'_id\', 1)]", match["text"])

    def test_collection_indexes_success_coll_missing_indexes_field(self):
        """coll_no_indexes_field: only _id_"""
        result = self._run_and_extract("test_db", "coll_no_indexes_field")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], 'Found 1 indexes in the collection "coll_no_indexes_field":')

        match = next((d for d in result if 'Name "_id_"' in d["text"]), None)
        self.assertIsNotNone(match, "_id_ index not reported")
        self.assertIn("[(\'_id\', 1)]", match["text"])

    def test_collection_indexes_success_different_version_index(self):
        """another_db.simple_coll – helper does not expose version any more"""
        result = self._run_and_extract("another_db", "simple_coll")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["text"], 'Found 2 indexes in the collection "simple_coll":')

        expected_keys = {
            "_id_": "[(\'_id\', 1)]",
            "field_v1_idx": "[(\'field_v1\', 1)]",
        }
        for idx_name, key_repr in expected_keys.items():
            match = next((d for d in result if f'Name "{idx_name}"' in d["text"]), None)
            self.assertIsNotNone(match, f"{idx_name} index not reported")
            self.assertIn(key_repr, match["text"])

    def test_collection_indexes_pass_through_other_index_options(self):
        """We only care that the index is listed with the correct key spec."""
        result = self._run_and_extract("test_db", "coll_with_extra_options")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["text"], 'Found 2 indexes in the collection "coll_with_extra_options":')

        expected_keys = {
            "_id_": "[(\'_id\', 1)]",
            "last_login_idx": "[(\'last_login\', -1)]",
        }
        for idx_name, key_repr in expected_keys.items():
            match = next((d for d in result if f'Name "{idx_name}"' in d["text"]), None)
            self.assertIsNotNone(match, f"{idx_name} index not reported")
            self.assertIn(key_repr, match["text"])

    # ---------------------------------------------------------------------
    # Validation / error paths
    # ---------------------------------------------------------------------

    def test_collection_indexes_validation_error_database_empty(self):
        DB.switch_connection(self.test_conn_name)
        self.assert_error_behavior(
            func_to_call=collection_indexes,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input validation failed",
            database="",
            collection="some_collection",
        )

    def test_collection_indexes_validation_error_database_too_long(self):
        DB.switch_connection(self.test_conn_name)
        long_db_name = "a" * 64  # MongoDB database names must be < 64 bytes
        self.assert_error_behavior(
            func_to_call=collection_indexes,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input validation failed",
            database=long_db_name,
            collection="some_collection",
        )

    def test_collection_indexes_validation_error_collection_empty(self):
        DB.switch_connection(self.test_conn_name)
        self.assert_error_behavior(
            func_to_call=collection_indexes,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input validation failed",
            database="test_db",
            collection="",
        )

    def test_collection_indexes_validation_error_collection_too_long(self):
        DB.switch_connection(self.test_conn_name)
        long_coll_name = "a" * 256  # MongoDB collection names must be < 255 bytes
        self.assert_error_behavior(
            func_to_call=collection_indexes,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input validation failed",
            database="test_db",
            collection=long_coll_name,
        )
