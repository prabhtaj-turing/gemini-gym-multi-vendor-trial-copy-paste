
from ..SimulationEngine.custom_errors import InvalidInputError, LineItemNotFound, LineItemMismatchError
from ..SimulationEngine.custom_errors import DataIntegrityError
from common_utils.base_case import BaseTestCaseWithErrorHandler
import workday as WorkdayStrategicSourcingAPI
import copy

class TestDeleteLineItem(BaseTestCaseWithErrorHandler):
    """
    Dedicated test suite for the EventWorksheetLineItemById.delete function.
    """

    def setUp(self):
        """
        Set up a clean, known database state before each test.
        """
        # A minimal DB state required for these specific tests
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB = {
            'events': {
                'line_items': {
                    100: {"event_id": "10", "worksheet_id": 1, "name": "Test Line Item"}
                }
            }
        }
        # Set the error mode to RAISE for testing exceptions directly
        # Ensure your test runner or setup configures this appropriately.
        # For this example, we'll assume it's set to "RAISE".
        # if WorkdayStrategicSourcingAPI.SimulationEngine.error_handling.get_package_error_mode() != "RAISE":
        #     print("\nWarning: These tests are designed for ERROR_MODE='RAISE'")


    def test_delete_line_item_success(self):
        """
        Tests the successful deletion of a line item and asserts a True return value.
        """
        # Arrange: Confirm the item exists
        self.assertIn(100, WorkdayStrategicSourcingAPI.SimulationEngine.db.DB['events']['line_items'])

        # Act
        result = WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete(event_id=10, worksheet_id=1, id=100)

        # Assert
        self.assertTrue(result)
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=LineItemNotFound,
            expected_message="Line item with id '100' not found.",
            event_id=10,
            worksheet_id=1,
            id=100
        )

    def test_delete_raises_line_item_not_found(self):
        """
        Tests that LineItemNotFound is raised for a non-existent ID.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=LineItemNotFound,
            expected_message="Line item with id '999' not found.",
            event_id=10,
            worksheet_id=1,
            id=999
        )


    def test_delete_raises_mismatch_error_for_wrong_event_id(self):
        """
        Tests that LineItemMismatchError is raised for an incorrect event_id.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=LineItemMismatchError,
            expected_message="Line item '100' does not belong to the specified event '99' and worksheet '1'.",
            event_id=99, # Incorrect event_id
            worksheet_id=1,
            id=100
        )


    def test_delete_raises_mismatch_error_for_wrong_worksheet_id(self):
        """
        Tests that LineItemMismatchError is raised for an incorrect worksheet_id.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=LineItemMismatchError,
            expected_message="Line item '100' does not belong to the specified event '10' and worksheet '99'.",
            event_id=10,
            worksheet_id=99, # Incorrect worksheet_id
            id=100
        )


    def test_delete_raises_invalid_input_for_zero_id(self):
        """
        Tests that InvalidInputError is raised for a zero value ID.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=InvalidInputError,
            expected_message="All IDs must be positive integers.",
            event_id=10,
            worksheet_id=1,
            id=0 # Invalid ID
        )

    def test_delete_raises_invalid_input_for_negative_id(self):
        """
        Tests that InvalidInputError is raised for a negative value ID.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=InvalidInputError,
            expected_message="All IDs must be positive integers.",
            event_id=10,
            worksheet_id=1,
            id=-5 # Invalid ID
        )

    def test_delete_raises_invalid_input_for_string_id(self):
        """
        Tests that InvalidInputError is raised for a non-integer ID.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=InvalidInputError,
            expected_message="All IDs must be positive integers.",
            event_id=10,
            worksheet_id=1,
            id="abc" # Invalid ID
        )


    def test_delete_raises_invalid_input_for_none_event_id(self):
        """
        Tests that InvalidInputError is raised for a None value event_id.
        """
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItemById.delete,
            expected_exception_type=InvalidInputError,
            expected_message="All IDs must be positive integers.",
            event_id=None, # Invalid event_id
            worksheet_id=1,
            id=100
        )


class TestEventWorksheetLineItemsGet(BaseTestCaseWithErrorHandler):
    """
    Test suite for WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get()
    focusing on edge cases and error handling.
    """

    def setUp(self):
        """Set up a fresh, consistent database state before each test."""
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB = {
            "events": {
                "line_items": {
                    1: {"id": 1, "event_id": "1", "worksheet_id": 1, "name": "Line Item 1"},
                    2: {"id": 2, "event_id": "1", "worksheet_id": 2, "name": "Line Item 2"},
                    3: {"id": 3, "event_id": "99", "worksheet_id": 99, "name": "Another Line Item"},
                }
            }
        }
        self.initial_db_state = WorkdayStrategicSourcingAPI.SimulationEngine.db.DB.copy()

    def tearDown(self):
        """Restore the database to its initial state after each test."""
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB = self.initial_db_state

    def test_get_line_items_success(self):
        """Test retrieving line items successfully for a valid event and worksheet."""
        line_items = WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get(1, 1)
        self.assertEqual(len(line_items), 1)
        self.assertEqual(line_items[0]["name"], "Line Item 1")

    def test_get_line_items_no_match(self):
        """Test that an empty list is returned for valid IDs with no matching line items."""
        line_items = WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get(1, 999)
        self.assertEqual(len(line_items), 0)

    def test_get_line_items_invalid_event_id_type(self):
        """Test that a TypeError is raised for a non-integer event_id."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get,
            expected_exception_type=TypeError,
            expected_message="Parameter 'event_id' must be an integer, but received type str.",
            # FIX: Pass arguments directly
            event_id="not-an-int", worksheet_id=1
        )

    def test_get_line_items_invalid_worksheet_id_type(self):
        """Test that a TypeError is raised for a non-integer worksheet_id."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get,
            expected_exception_type=TypeError,
            expected_message="Parameter 'worksheet_id' must be an integer, but received type list.",
            # FIX: Pass arguments directly
            event_id=1, worksheet_id=[2]
        )

    def test_get_line_items_non_positive_event_id(self):
        """Test that a ValueError is raised for a non-positive event_id."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get,
            expected_exception_type=ValueError,
            expected_message="Parameter 'event_id' must be a positive integer, but was 0.",
            # FIX: Pass arguments directly
            event_id=0, worksheet_id=1
        )

    def test_get_line_items_non_positive_worksheet_id(self):
        """Test that a ValueError is raised for a negative worksheet_id."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get,
            expected_exception_type=ValueError,
            expected_message="Parameter 'worksheet_id' must be a positive integer, but was -50.",
            # FIX: Pass arguments directly
            event_id=1, worksheet_id=-50
        )

    def test_get_line_items_data_integrity_error_missing_key(self):
        """Test that DataIntegrityError is raised for a malformed record in the database."""
        # Introduce a malformed record into the test DB
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"][4] = {
            "id": 4,
            "worksheet_id": 99,
            "name": "Malformed Item, missing event_id"
        }
        
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.get,
            expected_exception_type=DataIntegrityError,
            expected_message="Data integrity issue in line_item '4': missing required key 'event_id'.",
            # FIX: Pass arguments directly
            event_id=99, worksheet_id=99
        )