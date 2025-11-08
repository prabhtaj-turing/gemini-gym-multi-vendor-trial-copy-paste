import os
import unittest
import sys
from unittest.mock import patch

# Add the parent directory to the path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine import db
from ces_flights.SimulationEngine.custom_errors import DatabaseError

TEST_DB_PATH = "test_state.json"


class TestDatabase(BaseTestCaseWithErrorHandler):
    """Test database functionality."""

    def setUp(self):
        """Set up test database."""
        # Mock the automatic save to default DB file
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
        
        db.DB.clear()
        db.DB.update({"flight_bookings": {}, "_end_of_conversation_status": {}})

    def tearDown(self):
        """Clean up test files."""
        self.save_patcher.stop()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_new_record_id_format(self):
        record_id = db.new_record_id("search")
        self.assertTrue(record_id.startswith("search_"))

    def test_save_and_load_state(self):
        """Test saving and loading database state."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "state.json")
            db.DB["flight_bookings"]["id1"] = {
                "booking_id": "id1",
                "flight_id": "TEST123",
                "travelers": [],
                "status": "confirmed"
            }
            db.save_state(str(path))
            db.DB.clear()
            db.load_state(str(path))
            self.assertIn("id1", db.DB["flight_bookings"])

    def test_load_state_invalid_file(self):
        """Test loading from invalid/corrupt file."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "corrupt.json")
            with open(path, 'w') as f:
                f.write("{not-valid-json}")
            with self.assertRaises(DatabaseError):
                db.load_state(str(path))

    def test_get_minified_state_counts(self):
        db.DB["flight_bookings"]["a"] = {"test": 1}
        summary = db.get_minified_state()
        self.assertEqual(summary["flight_bookings"], 1)


if __name__ == "__main__":
    unittest.main()