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
        # Create valid calendar data that conforms to the schema
        db.DB["calendars"] = {
            "test_calendar": {
                "id": "test_calendar",
                "summary": "Test Calendar",
                "timeZone": "America/New_York",
                "primary": False
            }
        }
        db.save_state(self.state_file)
        
        db.reset_db()
        self.assertEqual(db.DB["calendars"], {})
        
        db.load_state(self.state_file)
        self.assertEqual(db.DB["calendars"]["test_calendar"]["id"], "test_calendar")

    def test_load_nonexistent_state(self):
        """Test loading a non-existent state file."""
        db.load_state("nonexistent.json")
        self.assertEqual(db.DB["calendars"], {})

    def test_load_invalid_json(self):
        """Test loading a state file with invalid JSON."""
        invalid_json_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_file, "w") as f:
            f.write("{'invalid': json}")
        
        db.load_state(invalid_json_file)
        self.assertEqual(db.DB["calendars"], {})

if __name__ == '__main__':
    unittest.main()
