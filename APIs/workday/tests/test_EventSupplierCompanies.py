from ..SimulationEngine.custom_errors import EventNotFoundError, InvalidEventTypeError, SupplierNotFoundError, InvalidPayloadError
from common_utils.base_case import BaseTestCaseWithErrorHandler
import workday as WorkdayStrategicSourcingAPI
from ..SimulationEngine import db

class TestEventsAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up a fresh, populated in-memory database for each test."""
        # Define a clean state for the database
        self.test_db = {
            "events": {
                "events": {
                    "1": {"id": "1", "name": "RFP Event", "type": "RFP", "suppliers": [3]}, # Event with existing supplier
                    "2": {"id": "2", "name": "Auction Event", "type": "AUCTION"},
                    "3": {"id": "3", "name": "Draft RFP", "type": "RFP"}, # Event with no suppliers yet
                }
            },
            "suppliers": {
                "supplier_companies": {
                    1: {"id": 1, "name": "Supplier A"},
                    2: {"id": 2, "name": "Supplier B"},
                    3: {"id": 3, "name": "Supplier C"},
                },
                "contact_types": {},
                "supplier_company_segmentations": {},
                "supplier_contacts": {},
            },
            # Add other necessary empty keys if your code requires them
            "attachments": {}, "awards": {}, "contracts": {}, "fields": {}, "payments": {},
            "projects": {}, "reports": {}, "scim": {}, "spend_categories": {},
        }
        # Deep copy the clean state into the actual DB used by the simulation
        db.DB = self.test_db.copy()


    def test_event_supplier_companies_post_success(self):
        """Test successfully adding new suppliers to an RFP event."""
        payload = {"supplier_ids": [1, 2], "type": "supplier_companies"}
        
        # Call the function to add suppliers to event 3
        result = WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(3, payload)
        
        self.assertIsNotNone(result, "Function should return the updated event dictionary.")
        self.assertIn("suppliers", result, "Event should have a 'suppliers' key.")
        
        # Check that both new suppliers were added
        self.assertIn(1, result["suppliers"])
        self.assertIn(2, result["suppliers"])
        self.assertEqual(len(result["suppliers"]), 2)


    def test_event_supplier_companies_delete(self):
        """Test deleting a supplier after adding them."""
        # First, successfully add suppliers
        add_payload = {"supplier_ids": [1, 2], "type": "supplier_companies"}
        WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(3, add_payload)
        
        # Now, delete one of them
        delete_payload = {"supplier_ids": [1], "type": "supplier_companies"}
        result = WorkdayStrategicSourcingAPI.EventSupplierCompanies.delete(3, delete_payload)
        
        # Verify delete returns True
        self.assertTrue(result, "Delete should return True on success")
        
        # Verify the deletion worked by checking the event data directly
        event = db.DB["events"]["events"]["3"]
        self.assertNotIn(1, event["suppliers"], "Supplier 1 should have been deleted.")
        self.assertIn(2, event["suppliers"], "Supplier 2 should remain.")
    
    def test_post_supplier_is_idempotent(self):
        """Ensure adding the same suppliers twice does not create duplicates."""
        payload = {"supplier_ids": [1, 2], "type": "supplier_companies"}
        
        # Call post twice with the same data
        WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(3, payload)
        result = WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(3, payload)
        
        self.assertEqual(len(result["suppliers"]), 2, "Suppliers list should not contain duplicates.")
        self.assertListEqual(sorted(result["suppliers"]), [1, 2])


    def test_post_supplier_to_event_with_existing_suppliers(self):
        """Test adding new suppliers to an event that already has some."""
        payload = {"supplier_ids": [1, 2], "type": "supplier_companies"}
        
        # Event 1 starts with supplier [3]
        result = WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(1, payload)
        
        self.assertEqual(len(result["suppliers"]), 3, "Should have a total of 3 suppliers.")
        self.assertListEqual(sorted(result["suppliers"]), [1, 2, 3])


    def test_post_supplier_fails_for_non_existent_event(self):
        """Test error when the event_id does not exist."""
        payload = {"supplier_ids": [1], "type": "supplier_companies"}
        # Corrected: Pass arguments 999 and payload directly.
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.post,
            EventNotFoundError,
            "Event with ID 999 not found.",
            event_id=999,
            data=payload
        )

    def test_post_supplier_fails_for_non_rfp_event(self):
        """Test error when the event is not of type 'RFP'."""
        payload = {"supplier_ids": [1], "type": "supplier_companies"}
        # Corrected: Pass arguments 2 and payload directly.
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.post,
            InvalidEventTypeError,
            "Suppliers can only be added to events of type 'RFP'.",
            event_id=2, # Event 2 is type 'AUCTION'
            data=payload
        )

    def test_post_supplier_fails_for_non_existent_supplier(self):
        """Test error when a supplier_id does not exist."""
        payload = {"supplier_ids": [1, 99], "type": "supplier_companies"}
        # Corrected: Pass arguments 1 and payload directly.
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.post,
            SupplierNotFoundError,
            "The following supplier IDs were not found: [99]",
            event_id=1,
            data=payload
        )

    def test_post_supplier_fails_for_invalid_payload_missing_type(self):
        """Test Pydantic validation error for a payload missing the 'type' key."""
        invalid_payload = {"supplier_ids": [1, 2]}
        
        # Use assertRaises directly for more flexible message checking
        with self.assertRaises(InvalidPayloadError) as context:
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(1, invalid_payload)
        
        # Check that the error message contains the key information
        error_message = str(context.exception)
        self.assertIn("type", error_message, "Error message should mention the 'type' field.")
        self.assertIn("Field required", error_message, "Error message should indicate the field is required.")


    def test_post_supplier_fails_for_invalid_payload_wrong_ids_type(self):
        """Test Pydantic validation error for supplier_ids not being a list."""
        invalid_payload = {"supplier_ids": "not-a-list", "type": "supplier_companies"}

        # Use assertRaises directly for more flexible message checking
        with self.assertRaises(InvalidPayloadError) as context:
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.post(1, invalid_payload)
            
        # Check that the error message contains the key information
        error_message = str(context.exception)
        self.assertIn("supplier_ids", error_message, "Error message should mention the 'supplier_ids' field.")
        self.assertIn("Input should be a valid list", error_message, "Error message should indicate a list is required.")

    def test_event_supplier_companies_delete_invalid_payload(self):
        """Test that delete raises InvalidPayloadError for invalid payload (missing type)."""
        invalid_payload = {"supplier_ids": [1]}
        with self.assertRaises(InvalidPayloadError) as context:
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.delete(3, invalid_payload)
        self.assertIn("type", str(context.exception))

    def test_event_supplier_companies_delete_non_existent_event(self):
        """Test that delete raises EventNotFoundError for non-existent event."""
        payload = {"supplier_ids": [1], "type": "supplier_companies"}
        with self.assertRaises(EventNotFoundError):
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.delete(999, payload)

    def test_event_supplier_companies_delete_non_rfp_event(self):
        """Test that delete raises InvalidEventTypeError for non-RFP event."""
        payload = {"supplier_ids": [1], "type": "supplier_companies"}
        with self.assertRaises(InvalidEventTypeError):
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.delete(2, payload)

    def test_event_supplier_companies_delete_non_existent_supplier(self):
        """Test that delete raises SupplierNotFoundError for non-existent supplier."""
        payload = {"supplier_ids": [99], "type": "supplier_companies"}
        with self.assertRaises(SupplierNotFoundError):
            WorkdayStrategicSourcingAPI.EventSupplierCompanies.delete(3, payload)

    def test_event_supplier_companies_delete_success(self):
        """Test that delete returns True on successful removal."""
        payload = {"supplier_ids": [1], "type": "supplier_companies"}
        result = WorkdayStrategicSourcingAPI.EventSupplierCompanies.delete(3, payload)
        self.assertTrue(result, "Delete should return True on successful removal")