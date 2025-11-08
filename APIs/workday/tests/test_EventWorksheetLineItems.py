import unittest
import workday as WorkdayStrategicSourcingAPI
from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine.custom_errors import NotFoundError, ValidationError, ConflictError
from workday.SimulationEngine.models import LineItemInput
from pydantic import ValidationError as PydanticValidationError

class TestEventsAPIPostMultipleLineItem(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up a fresh, predictable database state before each test."""
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB = {
            "attachments": {},
            "awards": {"award_line_items": [], "awards": []},
            "contracts": {
                "award_line_items": [],
                "awards": {},
                "contract_types": {},
                "contracts": {},
            },
            "events": {
                "event_templates": {1: {"name": "Template 1"}},
                "events": {
                    "1": {"id": "1", "name": "Event 1", "type": "RFP", "external_id": "event_ext_1", "title_contains": "RFP"},
                    "2": {"id": "2", "name": "Event 2", "type": "Other"},
                    "3": {"id": "3", "name": "Event 3", "external_id": "event_ext_2"},
                },
                "worksheets": {1: {"event_id": 1, "name": "Worksheet 1"}},
                "line_items": {
                    1: {"event_id": "1", "worksheet_id": 1, "name": "Line Item 1"}
                },
                "bids": {1: {"event_id": 1, "supplier_id": 1, "status": "submitted"}},
                "bid_line_items": {
                    1: {"bid_id": 1, "item_name": "Bid Line Item 1", "price": 100}
                },
            },
            "fields": {"field_groups": {}, "field_options": {}, "fields": {}},
            "payments": {
                "payment_currencies": [],
                "payment_currency_id_counter": "",
                "payment_term_id_counter": "",
                "payment_terms": [],
                "payment_type_id_counter": "",
                "payment_types": [],
            },
            "projects": {"project_types": {}, "projects": {}},
            "reports": {
                "contract_milestone_reports_entries": [],
                "contract_milestone_reports_schema": {},
                "contract_reports_entries": [],
                "contract_reports_schema": {},
                "event_reports": [],
                "event_reports_1_entries": [],
                "event_reports_entries": [],
                "event_reports_schema": {},
                "performance_review_answer_reports_entries": [],
                "performance_review_answer_reports_schema": {},
                "performance_review_reports_entries": [],
                "performance_review_reports_schema": {},
                "project_milestone_reports_entries": [],
                "project_milestone_reports_schema": {},
                "project_reports_1_entries": [],
                "project_reports_entries": [],
                "project_reports_schema": {},
                "savings_reports_entries": [],
                "savings_reports_schema": {},
                "supplier_reports_entries": [],
                "supplier_reports_schema": {},
                "supplier_review_reports_entries": [],
                "supplier_review_reports_schema": {},
                "suppliers": [],
            },
            "scim": {
                "resource_types": [],
                "schemas": [],
                "service_provider_config": {},
                "users": [],
            },
            "spend_categories": {},
            "suppliers": {
                "contact_types": {},
                "supplier_companies": {},
                "supplier_company_segmentations": {},
                "supplier_contacts": {},
            },
        }

    def test_post_multiple_success(self):
        """Test creating multiple valid line items successfully."""
        valid_payload = [
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
            },
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "B"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
            }
        ]
        result = WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, valid_payload)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['attributes']['data']['col1']['value'], 'A')
        self.assertEqual(result[1]['id'], 3)
        self.assertEqual(len(WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"]), 3)

    def test_post_multiple_nonexistent_event(self):
        """Test error when the event_id does not exist."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple,
            NotFoundError,
            "Event with id '999' not found.",
            None,
            999, 1, []
        )

    def test_post_multiple_nonexistent_worksheet(self):
        """Test error when the worksheet_id does not exist."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple,
            NotFoundError,
            "Worksheet with id '999' not found.",
            None,
            1, 999, []
        )

    def test_post_multiple_payload_is_none(self):
        """Test error when the data payload is None."""
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple,
            ValueError,
            "Request body cannot be null.",
            None,
            1, 1, None
        )

    def test_post_multiple_empty_list(self):
        """Test that passing an empty list results in no change."""
        result = WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, [])
        self.assertEqual(result, [])
        self.assertEqual(len(WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"]), 1)

    def test_post_multiple_payload_worksheet_id_mismatch(self):
        """Test error when an item's worksheet_id doesn't match the URL."""
        mismatched_payload = [
            {"type": "line_items", "attributes": {"data": {}}, "relationships": {"worksheet": {"type": "worksheets", "id": 2}}}
        ]
        expected_msg = "Validation failed for line item at index 0: Payload worksheet id (2) does not match URL worksheet id (1)."
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple,
            ValueError,
            expected_msg,
            None,
            1, 1, mismatched_payload
        )

    def test_post_multiple_payload_missing_required_field(self):
        """Test Pydantic validation error for a missing field."""
        # FIX: Use with self.assertRaises to allow for flexible substring checking.
        invalid_payload = [{"attributes": {"data": {}}, "relationships": {"worksheet": {"type": "worksheets", "id": 1}}}]
        
        with self.assertRaises(ValueError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, invalid_payload)

        self.assertIn("Validation failed for line item at index 0", str(context.exception))
        self.assertIn("Field required", str(context.exception))


    def test_post_multiple_payload_with_extra_field(self):
        """Test Pydantic validation error for an unexpected field."""
        # FIX: Use with self.assertRaises to allow for flexible substring checking.
        invalid_payload = [
            {"type": "line_items", "attributes": {"data": {}}, "relationships": {"worksheet": {"type": "worksheets", "id": 1}}, "unexpected_field": "some_value"}
        ]

        with self.assertRaises(ValueError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, invalid_payload)
        
        self.assertIn("Validation failed for line item at index 0", str(context.exception))
        self.assertIn("Extra inputs are not permitted", str(context.exception))

    def test_post_multiple_event_id_not_integer(self):
        """Test TypeError when event_id is not an integer."""
        valid_payload = [
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
            }
        ]
        
        # Test with string
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple("1", 1, valid_payload)
        self.assertEqual(str(context.exception), "event_id must be an integer, got str")
        
        # Test with float
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1.5, 1, valid_payload)
        self.assertEqual(str(context.exception), "event_id must be an integer, got float")
        
        # Test with None
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(None, 1, valid_payload)
        self.assertEqual(str(context.exception), "event_id must be an integer, got NoneType")

    def test_post_multiple_worksheet_id_not_integer(self):
        """Test TypeError when worksheet_id is not an integer."""
        valid_payload = [
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
            }
        ]
        
        # Test with string
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, "1", valid_payload)
        self.assertEqual(str(context.exception), "worksheet_id must be an integer, got str")
        
        # Test with float
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1.5, valid_payload)
        self.assertEqual(str(context.exception), "worksheet_id must be an integer, got float")
        
        # Test with None
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, None, valid_payload)
        self.assertEqual(str(context.exception), "worksheet_id must be an integer, got NoneType")

    def test_post_multiple_data_not_list(self):
        """Test TypeError when data is not a list."""
        valid_item = {
            "type": "line_items",
            "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }
        
        # Test with dict
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, valid_item)
        self.assertEqual(str(context.exception), "data must be a list, got dict")
        
        # Test with string
        with self.assertRaises(TypeError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, "not a list")
        self.assertEqual(str(context.exception), "data must be a list, got str")
        
        # Test with None (this should raise ValueError for null check, not TypeError)
        with self.assertRaises(ValueError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, 1, None)
        self.assertEqual(str(context.exception), "Request body cannot be null.")

    def test_post_multiple_negative_event_id(self):
        """Test ValueError when event_id is negative."""
        valid_payload = [
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
            }
        ]
        
        with self.assertRaises(ValueError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(-1, 1, valid_payload)
        self.assertEqual(str(context.exception), "event_id must be non-negative, got -1")

    def test_post_multiple_negative_worksheet_id(self):
        """Test ValueError when worksheet_id is negative."""
        valid_payload = [
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
            }
        ]
        
        with self.assertRaises(ValueError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(1, -1, valid_payload)
        self.assertEqual(str(context.exception), "worksheet_id must be non-negative, got -1")

    def test_post_multiple_zero_ids_valid(self):
        """Test that zero values for event_id and worksheet_id are valid (non-negative)."""
        valid_payload = [
            {
                "type": "line_items",
                "attributes": {"data": {"col1": {"data_identifier": "col1", "value": "A"}}},
                "relationships": {"worksheet": {"type": "worksheets", "id": 0}}
            }
        ]
        
        # This should pass the non-negative validation but fail the existence check
        with self.assertRaises(NotFoundError) as context:
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post_multiple(0, 0, valid_payload)
        self.assertEqual(str(context.exception), "Event with id '0' not found.")

class TestEventsAPIPostLineItem(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up a fresh, populated in-memory database for each test."""
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB = {
            "events": {
                "events": {
                    "1": {"id": "1", "name": "Event 1"},
                    "2": {"id": "2", "name": "Event 2"},
                },
                "worksheets": {
                    1: {"event_id": 1, "name": "Worksheet 1"}
                },
                "line_items": {
                    1: {"event_id": "1", "worksheet_id": 1, "name": "Existing Line Item"}
                },
                # Other event-related data...
            },
            # ... other top-level keys
        }
        # To simplify, ensure other keys exist but are empty if not needed
        for key in ['attachments', 'awards', 'contracts', 'fields', 'payments', 'projects', 'reports', 'scim', 'spend_categories', 'suppliers']:
            if key not in WorkdayStrategicSourcingAPI.SimulationEngine.db.DB:
                WorkdayStrategicSourcingAPI.SimulationEngine.db.DB[key] = {}


    def test_post_line_item_success(self):
        """Test successful creation of a line item with a valid payload."""
        valid_payload = {
            "type": "line_items",
            "attributes": {
                "data": {
                    "item_name": {"data_identifier": "item_name", "value": "New Laptop"},
                    "quantity": {"data_identifier": "quantity", "value": 10}
                }
            },
            "relationships": {
                "worksheet": {
                    "type": "worksheets",
                    "id": 1
                }
            }
        }
        
        initial_item_count = len(WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"])
        
        # ACT
        new_item = WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post(1, 1, valid_payload)

        # ASSERT
        self.assertIsInstance(new_item, dict)
        self.assertEqual(new_item['id'], 2) # First ID is 1 from setUp
        self.assertEqual(new_item['event_id'], "1")
        self.assertEqual(new_item['attributes']['data']['item_name']['value'], "New Laptop")
        
        final_item_count = len(WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"])
        self.assertEqual(final_item_count, initial_item_count + 1)
        self.assertIn(new_item['id'], WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"])

    
    def test_post_line_item_empty_db_first_id(self):
        """Test that the first item created gets ID 1 when the DB is empty."""
        # ARRANGE: Start with an empty line_items table
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB["events"]["line_items"] = {}
        
        valid_payload = {
            "type": "line_items",
            "attributes": {"data": {}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }

        # ACT
        new_item = WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post(1, 1, valid_payload)

        # ASSERT
        self.assertEqual(new_item['id'], 1)

    
    def test_post_line_item_nonexistent_event(self):
        """Test error when creating a line item for a non-existent event."""
        # ARRANGE
        valid_payload = {"type": "line_items", "attributes": {"data": {}}, "relationships": {"worksheet": {"type": "worksheets", "id": 1}}}
        non_existent_event_id = 999

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            NotFoundError,
            f"Event with id '{non_existent_event_id}' not found.",
            None,
            non_existent_event_id, 1, valid_payload
        )


    def test_post_line_item_nonexistent_worksheet(self):
        """Test error when creating a line item for a non-existent worksheet."""
        # ARRANGE
        valid_payload = {"type": "line_items", "attributes": {"data": {}}, "relationships": {"worksheet": {"type": "worksheets", "id": 999}}}
        non_existent_worksheet_id = 999

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            NotFoundError,
            f"Worksheet with id '{non_existent_worksheet_id}' not found.",
            None,
            1, non_existent_worksheet_id, valid_payload
        )

    
    def test_post_line_item_id_mismatch(self):
        """Test error when worksheet ID in URL and payload conflict."""
        # ARRANGE
        payload_with_mismatch = {
            "type": "line_items",
            "attributes": {"data": {}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 2}} # ID is 2
        }
        worksheet_id_in_url = 1 # URL has ID 1

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ConflictError,
            "Worksheet ID in URL (1) does not match ID in payload (2).",
            None,
            1, worksheet_id_in_url, payload_with_mismatch
        )

    
    def test_post_line_item_invalid_payload(self):
        """Test validation error for a malformed payload (missing attributes)."""
        # ARRANGE
        invalid_payload = {
            "type": "line_items",
            # 'attributes' key is missing
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }

        # MODIFIED: Determine the exact Pydantic error message first
        expected_full_message = ""
        try:
            LineItemInput.parse_obj(invalid_payload)
        except PydanticValidationError as e:
            # Construct the exact message that the 'post' function will generate
            expected_full_message = f"Invalid input data format: {e}"

        # ACT & ASSERT
        # Use the full, exact message in the assertion
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError, # The custom error
            expected_full_message,
            None,
            1, 1, invalid_payload
        )

    def test_post_line_item_invalid_event_id_type(self):
        """Test validation error when event_id is not an integer."""
        # ARRANGE
        valid_payload = {
            "type": "line_items",
            "attributes": {"data": {}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }
        invalid_event_id = "1"  # String instead of int

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError,
            "event_id must be an integer, got str",
            None,
            invalid_event_id, 1, valid_payload
        )

    def test_post_line_item_negative_event_id(self):
        """Test validation error when event_id is negative."""
        # ARRANGE
        valid_payload = {
            "type": "line_items",
            "attributes": {"data": {}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }
        negative_event_id = -1

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError,
            "event_id must be non-negative, got -1",
            None,
            negative_event_id, 1, valid_payload
        )

    def test_post_line_item_invalid_worksheet_id_type(self):
        """Test validation error when worksheet_id is not an integer."""
        # ARRANGE
        valid_payload = {
            "type": "line_items",
            "attributes": {"data": {}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }
        invalid_worksheet_id = 1.5  # Float instead of int

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError,
            "worksheet_id must be an integer, got float",
            None,
            1, invalid_worksheet_id, valid_payload
        )

    def test_post_line_item_negative_worksheet_id(self):
        """Test validation error when worksheet_id is negative."""
        # ARRANGE
        valid_payload = {
            "type": "line_items",
            "attributes": {"data": {}},
            "relationships": {"worksheet": {"type": "worksheets", "id": 1}}
        }
        negative_worksheet_id = -5

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError,
            "worksheet_id must be non-negative, got -5",
            None,
            1, negative_worksheet_id, valid_payload
        )

    def test_post_line_item_invalid_data_type(self):
        """Test validation error when data is not a dictionary."""
        # ARRANGE
        invalid_data = "not a dict"  # String instead of dict
        valid_event_id = 1
        valid_worksheet_id = 1

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError,
            "data must be a dictionary, got str",
            None,
            valid_event_id, valid_worksheet_id, invalid_data
        )

    def test_post_line_item_empty_data(self):
        """Test validation error when data is empty."""
        # ARRANGE
        empty_data = {}  # Empty dict
        valid_event_id = 1
        valid_worksheet_id = 1

        # ACT & ASSERT
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventWorksheetLineItems.post,
            ValidationError,
            "data cannot be empty",
            None,
            valid_event_id, valid_worksheet_id, empty_data
        )

if __name__ == "__main__":
    unittest.main()
