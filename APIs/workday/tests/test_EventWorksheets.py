from ..SimulationEngine.custom_errors import InvalidInputError, DatabaseStructureError
from common_utils.base_case import BaseTestCaseWithErrorHandler
import workday as WorkdayStrategicSourcingAPI

class TestEventsAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Base setup with one event and one worksheet
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB = {
            "events": {
                "worksheets": {
                    1: {"id": 1, "name": "Worksheet 1", "event_id": 1},
                    2: {"id": 2, "name": "Worksheet 2", "event_id": 1},
                    3: {"id": 3, "name": "Worksheet 3", "event_id": 2},
                    4: {"id": 4, "name": "Malformed Worksheet"}, # No event_id key
                    5: {"id": 5, "name": "Worksheet with None event_id", "event_id": None},
                }
            }
        }
        # Save a clean state to reset to in tearDown
        WorkdayStrategicSourcingAPI.SimulationEngine.db.save_state("test_db.json")

    def tearDown(self):
        # Restore the original state after each test
        WorkdayStrategicSourcingAPI.SimulationEngine.db.load_state("test_db.json")

    # --- Success and Edge Case Tests ---

    def test_event_worksheets_get_multiple(self):
        """
        Tests retrieving all worksheets for an event that has more than one.
        """
        worksheets = WorkdayStrategicSourcingAPI.EventWorksheets.get(1)
        self.assertEqual(len(worksheets), 2)
        # Verify the correct worksheets were returned
        worksheet_ids = {ws['id'] for ws in worksheets}
        self.assertEqual(worksheet_ids, {1, 2})

    def test_event_worksheets_get_for_event_with_no_worksheets(self):
        """
        Tests that an empty list is returned for a valid event ID that has no worksheets.
        """
        worksheets = WorkdayStrategicSourcingAPI.EventWorksheets.get(3)
        self.assertEqual(len(worksheets), 0)
        self.assertIsInstance(worksheets, list)

    def test_get_worksheets_ignores_malformed_data(self):
        """
        Tests that the function correctly ignores worksheet entries that are
        missing an 'event_id' key and does not crash.
        """
        # The setUp data already includes malformed entries.
        # Calling get(1) should still succeed and return only the valid worksheets.
        worksheets = WorkdayStrategicSourcingAPI.EventWorksheets.get(1)
        self.assertEqual(len(worksheets), 2)


    # --- Error Condition Tests ---

    def test_get_worksheets_with_invalid_id_zero(self):
        """
        Tests that get() raises InvalidInputError for an event_id of 0.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheets.get,
            InvalidInputError,
            "Input 'event_id' must be a positive integer.",
            event_id=0  # Argument to pass to get()
        )

    def test_get_worksheets_with_invalid_id_negative(self):
        """
        Tests that get() raises InvalidInputError for a negative event_id.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheets.get,
            InvalidInputError,
            "Input 'event_id' must be a positive integer.",
            event_id=-5
        )

    def test_get_worksheets_with_invalid_id_type_string(self):
        """
        Tests that get() raises InvalidInputError for a non-integer event_id.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheets.get,
            InvalidInputError,
            "Input 'event_id' must be a positive integer.",
            event_id="1"
        )

    def test_get_worksheets_with_missing_table(self):
        """
        Tests that get() raises DatabaseStructureError if the 'worksheets' table is missing.
        """
        # Modify the DB for this specific test
        del WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["worksheets"]

        # FIX: The expected message must exactly match the string representation
        # of the KeyError, which includes being wrapped in single quotes.
        expected_message = '\'Could not find "worksheets" in the event database.\''

        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheets.get,
            DatabaseStructureError,
            expected_message,
            event_id=1
        )