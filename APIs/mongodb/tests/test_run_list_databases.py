import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from mongomock import MongoClient

from ..database_operations import list_databases # Function under test
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import ConnectionError

class TestListDatabases(BaseTestCaseWithErrorHandler):

    def setUp(self):
        # Ensure a clean state for the global DB object for each test
        DB.connections = {}
        DB.current_conn = None 
        DB.current_db = None # This is a string name in your MongoDB class

        # Establish a consistent active connection
        DB.switch_connection("mock_conn") # This creates/switches to the MongoClient for 'mock_conn'
        
        # Get a direct handle to the mongomock client for this active connection.
        # self.active_connection is the MongoClient instance
        self.active_connection = DB.connections[DB.current_conn] 

    def tearDown(self):
        # Clean up by dropping databases created during tests on the active connection
        if DB.current_conn and DB.current_conn in DB.connections:
            client_to_clean = DB.connections[DB.current_conn]
            # List all dbs and drop them (safer than hardcoding names if tests add more)
            # Be careful not to drop system dbs if mongomock actually creates them,
            # though typically list_database_names for mongomock doesn't show them unless content is added.
            db_names = client_to_clean.list_database_names()
            for db_name in db_names:
                if db_name not in ["admin", "local", "config"]: # Standard system DBs
                    client_to_clean.drop_database(db_name)
        
        # Reset global DB for next test class
        DB.connections = {}
        DB.current_conn = None
        DB.current_db = None

    def test_list_databases_success_basic(self):
        # Arrange: Create some databases with collections and data
        self.active_connection["test_db1"].create_collection("coll1").insert_one({"x": 1})
        self.active_connection["test_db2"].create_collection("coll2").insert_one({"y": 2})

        # Act
        result = list_databases()

        # Assert
        self.assertEqual(len(result), 2)
        # Sort results by name for consistent assertion order
        result.sort(key=lambda db_info: db_info["name"])

        self.assertEqual(result[0]["name"], "test_db1")
        self.assertEqual(result[1]["name"], "test_db2")
        self.assertIn("size_on_disk", result[0])
        self.assertIn("size_on_disk", result[1])
        # For mongomock, size_on_disk will be an estimate or potentially 0.
        self.assertIsInstance(result[0]["size_on_disk"], (int, float))
        self.assertGreaterEqual(result[0]["size_on_disk"], 0)
        self.assertIsInstance(result[1]["size_on_disk"], (int, float))
        self.assertGreaterEqual(result[1]["size_on_disk"], 0)

    def test_list_databases_includes_db_with_empty_collection(self):
        # Arrange
        self.active_connection["db_with_data"].create_collection("data_coll").insert_one({"a": 1})
        self.active_connection["db_with_empty_coll"].create_collection("empty_coll") # Collection exists but is empty

        # Act
        result = list_databases()

        # Assert
        self.assertEqual(len(result), 2)
        result.sort(key=lambda db_info: db_info["name"])
        
        db_names_found = [item["name"] for item in result]
        self.assertIn("db_with_data", db_names_found)
        self.assertIn("db_with_empty_coll", db_names_found) # MongoDB lists DBs if they contain ANY collection

    def test_list_databases_does_not_include_truly_empty_db_without_collections(self):
        # Arrange
        self.active_connection["db_with_data1"].create_collection("data_coll1").insert_one({"a": 1})
        # "truly_empty_db" is accessed but no collections are created in it
        _ = self.active_connection["truly_empty_db"] 

        # Act
        result = list_databases()

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "db_with_data1")
        db_names_found = [item["name"] for item in result]
        self.assertNotIn("truly_empty_db", db_names_found)

    def test_list_databases_with_varied_names(self):
        # Arrange
        self.active_connection["my-db-1"].create_collection("c1").insert_one({"id": 1})
        self.active_connection["db_with_numbers_123"].create_collection("c2").insert_one({"id": 2})
        self.active_connection["db.with.dots"].create_collection("c3").insert_one({"id": 3}) # Dots are allowed in DB names

        # Act
        result = list_databases()

        # Assert
        self.assertEqual(len(result), 3)
        db_names_found = sorted([item["name"] for item in result])
        expected_db_names = sorted(["my-db-1", "db_with_numbers_123", "db.with.dots"])
        self.assertListEqual(db_names_found, expected_db_names)

    def test_list_databases_excludes_standard_system_dbs_if_empty(self):
        # Arrange: Create a user DB to ensure list_databases doesn't return empty solely due to no user DBs
        self.active_connection["user_db"].create_collection("user_coll").insert_one({"u":1})
        
        # Mongomock might not create admin, local, config by default, or list_database_names might filter them
        # if they are empty. Real MongoDB always has them, but listDatabases might filter based on content/privs.
        # This test checks that IF they are present but empty (or not created by default by mongomock),
        # they are not included in a typical user-level list_databases call.

        # Act
        result = list_databases() # Assuming your function calls client.list_databases() or similar

        # Assert
        db_names_found = [item["name"] for item in result]
        self.assertIn("user_db", db_names_found)
        self.assertNotIn("admin", db_names_found, "Empty 'admin' DB should generally not be listed for users unless explicitly queried or has user data.")
        self.assertNotIn("local", db_names_found, "Empty 'local' DB should not be listed.")
        self.assertNotIn("config", db_names_found, "Empty 'config' DB should not be listed (relevant for sharded setups).")
        self.assertEqual(len(db_names_found), 1) # Only user_db should be listed

    def test_list_databases_size_on_disk_estimation(self):
        # This test is more about acknowledging the field's presence, as accurate size
        # is hard to get from mongomock.
        # Arrange
        db1 = self.active_connection["size_test_db1"]
        db1["small_coll"].insert_one({"a": "short string"})
        
        db2 = self.active_connection["size_test_db2"]
        big_string = "a" * 1024 # 1KB string
        db2["large_coll"].insert_many([{"data": big_string} for _ in range(5)]) # 5KB of data

        # Act
        result = list_databases()
        result.sort(key=lambda db_info: db_info["name"])

        # Assert
        self.assertEqual(len(result), 2)
        db1_info = next(item for item in result if item["name"] == "size_test_db1")
        db2_info = next(item for item in result if item["name"] == "size_test_db2")

        self.assertIn("size_on_disk", db1_info)
        self.assertIn("size_on_disk", db2_info)
        self.assertIsInstance(db1_info["size_on_disk"], (int, float))
        self.assertIsInstance(db2_info["size_on_disk"], (int, float))
        self.assertGreaterEqual(db1_info["size_on_disk"], 0)
        self.assertGreaterEqual(db2_info["size_on_disk"], 0)


    # --- Error Handling Tests (already present in your example) ---
    def test_list_databases_no_active_connection(self):
        DB.current_conn = None # Simulate no active connection in the wrapper
        self.assert_error_behavior(
            list_databases, 
            ConnectionError, 
            "No active MongoDB connection."
        )

    def test_list_databases_invalid_connection(self):
        DB.current_conn = "nonexistent_conn_name" # Simulate an invalid current_conn name
        # DB.connections.clear() # Not strictly needed if setUp clears, but good for isolation
        if "nonexistent_conn_name" in DB.connections: # Ensure it's really not there
            del DB.connections["nonexistent_conn_name"]

        self.assert_error_behavior(
            list_databases, 
            ConnectionError, 
            "Invalid MongoDB connection." # Or "Connection 'nonexistent_conn_name' not found."
        )
    
    def test_empty_list_databases_when_no_user_dbs_exist(self):
        result = list_databases()
        self.assertEqual(len(result), 0, "Expected empty list when no user databases with collections exist.")


if __name__ == '__main__':
    unittest.main()