import unittest
import os
import shutil
import json
from ..SimulationEngine import db

class TestDB(unittest.TestCase):
    """Test suite for database state management."""

    def setUp(self):
        """Set up a test state file."""
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.state_file = os.path.join(self.test_dir, "state.json")
        db.reset_db()

    def tearDown(self):
        """Clean up the test state file."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_state(self):
        """Test saving and loading the database state."""
        # Set a known state
        db.DB["entities"] = {"test_id": {"name": "test_entity"}}
        
        # Save the state
        db.save_state(self.state_file)
        
        # Reset the DB
        db.reset_db()
        self.assertEqual(db.DB["entities"], {})
        
        # Load the state
        db.load_state(self.state_file)
        
        # Check if the state was restored
        self.assertEqual(db.DB["entities"], {"test_id": {"name": "test_entity"}})

    def test_load_nonexistent_state(self):
        """Test loading a non-existent state file."""
        db.load_state("nonexistent.json")
        # No error should be raised, and the DB should be in its default state
        self.assertEqual(db.DB["entities"], {})

    def test_load_invalid_json(self):
        """Test loading a state file with invalid JSON."""
        invalid_json_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_file, "w") as f:
            f.write("{'invalid': json}")
        
        db.load_state(invalid_json_file)
        # No error should be raised, and the DB should be in its default state
        self.assertEqual(db.DB["entities"], {})
        
        os.remove(invalid_json_file)

if __name__ == '__main__':
    unittest.main()
