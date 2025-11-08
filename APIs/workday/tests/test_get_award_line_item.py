from workday.SimulationEngine import db
from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.Awards import get_award_line_item
from workday.SimulationEngine.custom_errors import ResourceNotFoundError, ValidationError

class TestGetAwardLineItem(BaseTestCaseWithErrorHandler):
    """
    Test suite for the get_award_line_item function.
    """

    def setUp(self):
        """Sets up a mock database with test data before each test."""
        # Reset the database to a clean state
        db.DB.clear()
        db.DB.update({
            'awards': {
                'award_line_items': [
                    {
                        "id": 101,
                        "award_id": 1,
                        "description": "Line item with relationships",
                        "relationships": {
                            "supplier_company": {"id": 500},
                            "worksheet": {"id": 900}
                        }
                    },
                    {
                        "id": 102,
                        "award_id": 1,
                        "description": "Line item with no relationships"
                    },
                    {
                        "id": 103,
                        "award_id": 2,
                        "description": "Line item with a broken relationship link",
                        "relationships": {
                            "supplier_company": {"id": 9999} # This company does not exist
                        }
                    }
                ]
            },
            'suppliers': {
                'supplier_companies': {
                    "500": {"id": 500, "name": "Global Supplies Inc.", "tier": "1"}
                }
            },
            'events': {
                'worksheets': {
                    "900": {"id": 900, "name": "Q3 RFQ Worksheet", "type": "BID_SHEET"}
                }
            }
        })


    def test_success_get_item_without_include(self):
        """Tests successfully retrieving an item without embedding relationships."""
        line_item = get_award_line_item(id="101")
        self.assertIsNotNone(line_item)
        self.assertEqual(line_item["id"], 101)
        # Ensure relationships are just links, not the full embedded objects
        self.assertEqual(line_item["relationships"]["supplier_company"], {"id": 500})
        self.assertEqual(line_item["relationships"]["worksheet"], {"id": 900})

    def test_success_with_single_include(self):
        """Tests embedding a single related resource."""
        line_item = get_award_line_item(id="101", _include="supplier_company")
        self.assertEqual(line_item["id"], 101)
        # Supplier company should be the full object
        self.assertEqual(line_item["relationships"]["supplier_company"]["name"], "Global Supplies Inc.")
        # Worksheet should remain a link
        self.assertEqual(line_item["relationships"]["worksheet"], {"id": 900})

    def test_success_with_multiple_includes(self):
        """Tests embedding multiple related resources from a comma-separated string."""
        line_item = get_award_line_item(id="101", _include="worksheet,supplier_company")
        # Both relationships should be full objects
        self.assertEqual(line_item["relationships"]["supplier_company"]["name"], "Global Supplies Inc.")
        self.assertEqual(line_item["relationships"]["worksheet"]["name"], "Q3 RFQ Worksheet")

    def test_success_with_include_whitespace(self):
        """Tests that the _include parser correctly handles extra whitespace."""
        line_item = get_award_line_item(id="101", _include="  worksheet ,  supplier_company  ")
        self.assertEqual(line_item["relationships"]["supplier_company"]["name"], "Global Supplies Inc.")
        self.assertEqual(line_item["relationships"]["worksheet"]["name"], "Q3 RFQ Worksheet")

    def test_error_item_not_found(self):
        """Tests that a ResourceNotFoundError is raised for a non-existent ID."""
        self.assert_error_behavior(
            get_award_line_item,
            ResourceNotFoundError,
            "Award Line Item with ID '999' not found.",
            id="999"
        )

    def test_error_id_validation(self):
        """Tests various validation errors for the 'id' parameter."""
        # ID is not a string
        self.assert_error_behavior(get_award_line_item, TypeError, "URL parameter 'id' must be a string.", id=101)
        # ID is an empty string
        self.assert_error_behavior(get_award_line_item, ValidationError, "URL parameter 'id' cannot be empty.", id="")
        # ID is only whitespace
        self.assert_error_behavior(get_award_line_item, ValidationError, "URL parameter 'id' cannot be empty.", id="   ")

    def test_error_include_validation(self):
        """Tests various validation errors for the '_include' parameter."""
        self.assert_error_behavior(get_award_line_item, TypeError, "Query parameter '_include' must be a string.", id="101", _include=123)
        
        # FIX: The expected error message now uses a sorted list for deterministic order.
        expected_msg = "Unsupported value(s) in '_include' parameter: {'invalid_value'}. Supported values are: ['supplier_company', 'worksheet']."
        self.assert_error_behavior(
            get_award_line_item,
            ValidationError,
            expected_msg,
            id="101",
            _include="invalid_value"
        )
        
        # FIX: Also update the second assertion for consistency.
        expected_msg_mixed = "Unsupported value(s) in '_include' parameter: {'another_bad_one'}. Supported values are: ['supplier_company', 'worksheet']."
        self.assert_error_behavior(
            get_award_line_item,
            ValidationError,
            expected_msg_mixed,
            id="101",
            _include="worksheet,another_bad_one"
        )
        
    def test_edge_case_include_on_item_with_no_relationships(self):
        """Tests that requesting an include on an item with no relationships does not cause an error."""
        line_item = get_award_line_item(id="102", _include="supplier_company")
        self.assertEqual(line_item["id"], 102)
        # FIX: The function no longer adds a 'relationships' key if one doesn't exist.
        # This assertion is now correct.
        self.assertNotIn("relationships", line_item)

    def test_edge_case_include_with_broken_link(self):
        """Tests that a broken relationship link is handled gracefully."""
        line_item = get_award_line_item(id="103", _include="supplier_company")
        self.assertEqual(line_item["id"], 103)
        # FIX: The function logic was changed to preserve the original link if the lookup fails.
        # This assertion now correctly reflects that behavior.
        self.assertEqual(line_item["relationships"]["supplier_company"], {"id": 9999})
