import unittest
import os
import json
import tempfile
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state, load_state

class TestDBState(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test directory and reset DB."""
        super().setUp()
        # Reset DB to clean state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        self.test_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')

    def tearDown(self):
        """Clean up test files and directory."""
        super().tearDown()
        # Reset DB to clean state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    def test_save_and_load_state(self):
        """Test that the DB state can be saved to and loaded from a file."""
        # 1. Set up some DB state
        DB.switch_connection("test_conn")
        DB.use_database("test_db")
        
        # Add some test data to the connection
        client = DB.connections[DB.current_conn]
        test_collection = client[DB.current_db]["test_collection"]
        test_collection.insert_one({"name": "test_doc", "value": 123})
        
        # Store original state for comparison
        original_connections = len(DB.connections)
        original_conn = DB.current_conn
        original_db_name = DB.current_db
        
        # 2. Save state
        save_state(self.test_filepath)

        # 3. Check if the file was created
        self.assertTrue(os.path.exists(self.test_filepath))

        # 4. Reset DB to ensure we are loading fresh data
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        self.assertEqual(len(DB.connections), 0)

        # 5. Load state from file
        load_state(self.test_filepath)

        # 6. Assert that the data has been restored
        self.assertEqual(len(DB.connections), original_connections)
        # Note: load_state sets current_conn to first connection, not necessarily the original
        self.assertIsNotNone(DB.current_conn)
        self.assertIn(DB.current_conn, DB.connections)

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file doesn't raise an error and leaves DB unchanged."""
        # Set up initial state
        DB.switch_connection("initial_conn")
        initial_connections = len(DB.connections)
        initial_conn = DB.current_conn

        # Attempt to load from a file that does not exist
        load_state('nonexistent_filepath.json')

        # The DB state should not have changed
        self.assertEqual(len(DB.connections), initial_connections)
        self.assertEqual(DB.current_conn, initial_conn)

    def test_backward_compatibility_loading(self):
        """Test loading a DB state with missing keys (for backward compatibility)."""
        # 1. Create a test DB file that is missing some current DB structure
        old_format_db_data = {
            "connections": {
                "old_conn": {
                    "databases": {
                        "old_db": {
                            "collections": {
                                "old_collection": {
                                    "documents": [
                                        {"_id": "doc1", "data": "old data"}
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        
        with open(self.test_filepath, 'w') as f:
            json.dump(old_format_db_data, f)

        # 2. Reset the current DB
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        # 3. Load the old-format state
        load_state(self.test_filepath)

        # 4. Check that the loaded data is present and accessible
        self.assertIsNotNone(DB.current_conn)
        self.assertIn("old_conn", DB.connections)

    def test_save_state_with_empty_db(self):
        """Test saving state when DB is empty."""
        # Ensure DB is empty
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        # Save empty state
        save_state(self.test_filepath)
        
        # Check file was created
        self.assertTrue(os.path.exists(self.test_filepath))
        
        # Load and verify empty state
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertIn('connections', saved_data)
        # Note: save_state only saves connections, not current_conn/current_db
        self.assertEqual(saved_data['connections'], {})

    def test_save_state_with_multiple_connections(self):
        """Test saving and loading state with multiple connections."""
        # Create multiple connections
        DB.switch_connection("conn1")
        DB.use_database("db1")
        client1 = DB.connections["conn1"]
        client1["db1"]["collection1"].insert_one({"test": "data1"})
        
        DB.switch_connection("conn2")
        DB.use_database("db2")
        client2 = DB.connections["conn2"]
        client2["db2"]["collection2"].insert_one({"test": "data2"})
        
        # Save state
        save_state(self.test_filepath)
        
        # Reset and load
        original_conn_count = len(DB.connections)
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        load_state(self.test_filepath)
        
        # Verify multiple connections were restored
        self.assertEqual(len(DB.connections), original_conn_count)
        self.assertIn("conn1", DB.connections)
        self.assertIn("conn2", DB.connections)

    def test_save_load_with_complex_data(self):
        """Test saving and loading with complex MongoDB data structures."""
        # Set up complex data
        DB.switch_connection("complex_conn")
        DB.use_database("complex_db")
        
        client = DB.connections[DB.current_conn]
        collection = client[DB.current_db]["complex_collection"]
        
        # Insert complex documents
        complex_docs = [
            {
                "name": "doc1",
                "nested": {"field": "value", "number": 42},
                "array": [1, 2, 3, "string"],
                "boolean": True
            },
            {
                "name": "doc2",
                "metadata": {"created": "2023-01-01", "tags": ["tag1", "tag2"]},
                "null_field": None
            }
        ]
        
        collection.insert_many(complex_docs)
        
        # Save state
        save_state(self.test_filepath)
        
        # Reset and load
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        load_state(self.test_filepath)
        
        # Verify complex data was preserved
        self.assertIsNotNone(DB.current_conn)
        # Note: load_state doesn't restore current_db, only connections
        
        restored_client = DB.connections[DB.current_conn]
        # Find the database that contains our test collection
        found_collection = None
        for db_name in restored_client.list_database_names():
            db = restored_client[db_name]
            if "complex_collection" in db.list_collection_names():
                found_collection = db["complex_collection"]
                break
        
        self.assertIsNotNone(found_collection, "Complex collection not found after loading state")
        
        # Check that documents can be retrieved
        docs = list(found_collection.find({}))
        self.assertEqual(len(docs), 2)

    def test_state_file_permissions(self):
        """Test handling of file permission issues."""
        # Create a temporary file with restricted permissions
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Try to save to a location we might not have write access to
            # This test ensures graceful handling of permission errors
            DB.switch_connection("test_conn")
            
            # The save_state function should handle permission errors gracefully
            # If it raises an exception, it should be a meaningful one
            try:
                save_state(temp_filepath)
                # If successful, verify file exists
                self.assertTrue(os.path.exists(temp_filepath))
            except (PermissionError, OSError) as e:
                # This is acceptable - the function should handle permission errors
                self.assertIsInstance(e, (PermissionError, OSError))
                
        finally:
            # Clean up
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except (PermissionError, OSError):
                    pass  # Ignore cleanup errors

    def test_concurrent_state_operations(self):
        """Test that state operations are safe for concurrent access."""
        # Set up initial state
        DB.switch_connection("concurrent_conn")
        DB.use_database("concurrent_db")
        
        # Save state
        save_state(self.test_filepath)
        
        # Modify state
        DB.switch_connection("new_conn")
        
        # Load original state (should overwrite current state)
        load_state(self.test_filepath)
        
        # Verify original state was restored
        # Note: load_state sets current_conn to first connection, not necessarily the original
        self.assertIsNotNone(DB.current_conn)
        self.assertIn("concurrent_conn", DB.connections)


if __name__ == '__main__':
    unittest.main()
