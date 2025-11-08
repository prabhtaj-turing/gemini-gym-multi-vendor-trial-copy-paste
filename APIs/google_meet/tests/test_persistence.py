import unittest
import os

from google_meet.tests.common import reset_db
from google_meet import DB
from google_meet.SimulationEngine.db import save_state, load_state
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestPersistence(BaseTestCaseWithErrorHandler):

    def setUp(self):
        reset_db()

    def test_save_and_load_state(self):
        # Add some test data to the DB
        DB["spaces"]["test_space"] = {"id": "test_space", "name": "Test Space"}
        DB["conferenceRecords"]["conf1"] = {"id": "conf1", "start_time": "10:00"}

        # Save the state to a test file
        save_state("test_meet_state.json")

        # Clear the DB
        DB.clear()

        # Ensure the DB is empty
        self.assertEqual(len(DB), 0)

        # Load the saved state
        load_state("test_meet_state.json")

        # Verify the data was restored
        self.assertIn("spaces", DB)
        self.assertIn("test_space", DB["spaces"])
        self.assertEqual(DB["spaces"]["test_space"]["name"], "Test Space")

        self.assertIn("conferenceRecords", DB)
        self.assertIn("conf1", DB["conferenceRecords"])
        self.assertEqual(DB["conferenceRecords"]["conf1"]["start_time"], "10:00")

        # Clean up test file
        os.remove("test_meet_state.json")


if __name__ == "__main__":
    unittest.main()
