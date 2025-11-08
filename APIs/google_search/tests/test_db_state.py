import unittest
import os
import json
import shutil
from ..SimulationEngine import db

class TestDBState(unittest.TestCase):
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
        original_db = db.DB.copy()
        db.DB["recent_searches"] = [{"query": "test", "result": "test"}]
        db.save_state(self.state_file)
        
        db.reset_db()
        self.assertEqual(db.DB, original_db)
        
        db.load_state(self.state_file)
        self.assertEqual(db.DB["recent_searches"], [{"query": "test", "result": "test"}])

    def test_load_nonexistent_state(self):
        """Test loading a non-existent state file."""
        original_db = db.DB.copy()
        db.load_state("nonexistent.json")
        self.assertEqual(db.DB, original_db)

    def test_load_invalid_json(self):
        """Test loading a state file with invalid JSON."""
        original_db = db.DB.copy()
        invalid_json_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_file, "w") as f:
            f.write("{'invalid': json}")
        
        db.load_state(invalid_json_file)
        self.assertEqual(db.DB, original_db)

if __name__ == '__main__':
    unittest.main()
