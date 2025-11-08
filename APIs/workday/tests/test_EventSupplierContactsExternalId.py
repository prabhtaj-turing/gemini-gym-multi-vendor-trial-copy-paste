from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine.custom_errors import InvalidInputError, EventNotFound, InvalidEventType
from workday.SimulationEngine import db
import workday as WorkdayStrategicSourcingAPI
from workday.EventSupplierContactsExternalId import delete
import pytest
class TestEventsAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
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
                    1: {"id": 1, "name": "Event 1", "type": "RFP", "external_id": "event_ext_1", "title_contains": "RFP"},
                    2: {"id": 2, "name": "Event 2", "type": "Other"},
                    3: {"id": 3, "name": "Event 3", "external_id": "event_ext_2"},
                },
                "worksheets": {1: {"event_id": 1, "name": "Worksheet 1"}},
                "line_items": {
                    1: {"event_id": "1", "worksheet_id": 1, "name": "Line Item 1"}
                },
                "bids": {1: {"event_id": 1, "supplier_id": 1, "status": "submitted"}},
                "bid_line_items": {
                    1: {
                        "type": "bid_line_items",
                        "id": 1,
                        "bid_id": 1,
                        "event_id": "1",
                        "description": "Bid Line Item 1",
                        "amount": 100,
                        "attributes": {
                            "data": {
                                "column_1": "Quantity: 1",
                                "column_2": "Unit Price: $100"
                            },
                            "updated_at": "2024-01-15T10:30:00Z"
                        },
                        "relationships": {
                            "event": {
                                "type": "events",
                                "id": 1
                            },
                            "bid": {
                                "type": "bids",
                                "id": 1
                            },
                            "line_item": {
                                "type": "line_items",
                                "id": 1
                            },
                            "worksheets": {
                                "type": "worksheets",
                                "id": 1
                            }
                        }
                    }
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

        WorkdayStrategicSourcingAPI.SimulationEngine.db.save_state("test_db.json")

    def tearDown(self):
        WorkdayStrategicSourcingAPI.SimulationEngine.db.load_state("test_db.json")

    def test_empty_event_id(self):
        with self.assertRaises(InvalidInputError):
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
                "", {"type": "supplier_contacts", "supplier_contact_external_ids": []}
            )

    def test_whitespace_only_event_id(self):
        with self.assertRaises(InvalidInputError):
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
                "   ", {"type": "supplier_contacts", "supplier_contact_external_ids": []}
            )

    def test_pydantic_validation_fails(self):
        with self.assertRaises(InvalidInputError):
            # Missing required key
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
                "event_ext_1", {"type": "supplier_contacts"}
            )

    def test_event_not_found(self):
        with self.assertRaises(EventNotFound):
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
                "does_not_exist",
                {"type": "supplier_contacts", "supplier_contact_external_ids": []},
            )

    def test_wrong_event_type(self):
        with self.assertRaises(InvalidEventType):
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
                "event_ext_2",
                {"type": "supplier_contacts", "supplier_contact_external_ids": []},
            )

    def test_idempotency(self):
        # first call
        WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
            "event_ext_1",
            {"type": "supplier_contacts", "supplier_contact_external_ids": ["c1"]},
        )
        # second call – duplicate + new
        res = WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
            "event_ext_1",
            {
                "type": "supplier_contacts",
                "supplier_contact_external_ids": ["c1", "c2", "c1"],
            },
        )
        self.assertEqual(sorted(res["supplier_contacts"]), ["c1", "c2"])

    def test_returns_full_event(self):
        res = WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
            "event_ext_1",
            {"type": "supplier_contacts", "supplier_contact_external_ids": ["c3"]},
        )
        self.assertEqual(res["external_id"], "event_ext_1")
        self.assertEqual(res["type"], "RFP")
        self.assertIn("c3", res["supplier_contacts"])

    def test_event_supplier_contacts_external_id_post(self):
        # The test for post also needs the 'type' field
        result = WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post(
            "event_ext_1",
            {
                "type": "supplier_contacts", # <-- FIXED: Added required 'type' field
                "supplier_contact_external_ids": ["contact_ext_1", "contact_ext_2"]
            },
        )
        self.assertIsNotNone(result)
        self.assertIn("contact_ext_1", result["supplier_contacts"])

    def test_post_success_event_has_no_contacts_list_initially(self):
        """
        Tests successfully adding contacts to an RFP event that does not yet have a 'supplier_contacts' list.
        """
        # Event 3 does not have a "type" or "supplier_contacts" initially
        # Let's set it up as a valid RFP event for this test
        db.DB["events"]["events"][3]["type"] = "RFP"
        
        data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["new_contact_1"]
        }
        
        result = WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post("event_ext_2", data)
        self.assertIn("supplier_contacts", result)
        self.assertEqual(result["supplier_contacts"], ["new_contact_1"])

    def test_post_idempotency_adding_duplicate_and_new_contacts(self):
        """
        Tests that adding a mix of existing and new contacts only adds the new ones.
        """
        # First, add an initial contact
        initial_data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["contact_ext_1"]
        }
        WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post("event_ext_1", initial_data)
        
        # Now, try to add the same contact again plus a new one
        second_data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["contact_ext_1", "contact_ext_2"]
        }
        result = WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post("event_ext_1", second_data)
        
        self.assertListEqual(sorted(result["supplier_contacts"]), ["contact_ext_1", "contact_ext_2"])

    def test_post_failure_event_not_found(self):
        """
        Tests that EventNotFound is raised for a non-existent event external_id.
        """
        data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["contact_ext_1"]
        }
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post,
            EventNotFound,
            "Event with external_id 'non_existent_event' not found in the database.",
            None,
            "non_existent_event",
            data
        )

    def test_post_failure_invalid_event_type(self):
        """
        Tests that InvalidEventType is raised when the event is not an RFP.
        """
        # --- The Fix ---
        # This setup line must be moved outside and before the assertion call.
        # The trailing comma has also been removed.
        WorkdayStrategicSourcingAPI.SimulationEngine.db.DB['events']['events'][3]['type'] = 'AUCTION'

        data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["contact_ext_1"]
        }
        
        # Now, call the assertion with the correct arguments.
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post,
            InvalidEventType,
            "Event 'event_ext_2' is of type 'AUCTION', but must be 'RFP'.",
            None,
            "event_ext_2", # Use the external_id of event 3 for the test
            data
        )


    def test_post_failure_empty_event_id(self):
        """
        Tests that InvalidInputError is raised for an empty event_external_id.
        """
        data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["contact_ext_1"]
        }
        self.assert_error_behavior(
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post,
            InvalidInputError,
            "event_external_id cannot be empty.",
            None,
            "", # Empty event_id
            data
        )

    def test_post_failure_invalid_payload_wrong_type(self):
        """
        Tests that InvalidInputError is raised for a payload with the wrong 'type' field.
        """
        data = {
            "type": "wrong_type", # Invalid value for the literal
            "supplier_contact_external_ids": ["contact_ext_1"]
        }
        
        with self.assertRaises(InvalidInputError) as cm:
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post("event_ext_1", data)

        self.assertIn("Invalid data format", str(cm.exception))


    def test_post_failure_invalid_payload_missing_key(self):
        """
        Tests that InvalidInputError is raised for a payload missing the required contacts key.
        """
        data = {"type": "supplier_contacts"} # Missing supplier_contact_external_ids
        
        with self.assertRaises(InvalidInputError) as cm:
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post("event_ext_1", data)

        self.assertIn("Invalid data format", str(cm.exception))

    def test_post_failure_invalid_payload_bad_list_data(self):
        """
        Tests that InvalidInputError is raised when the contacts list contains invalid data.
        """
        data = {
            "type": "supplier_contacts",
            "supplier_contact_external_ids": ["contact_ext_1", "   "] # Contains whitespace-only string
        }
        
        # Use the standard unittest context manager to allow for flexible message checking
        with self.assertRaises(InvalidInputError) as cm:
            WorkdayStrategicSourcingAPI.EventSupplierContactsExternalId.post("event_ext_1", data)
        
        self.assertIn("Invalid data format", str(cm.exception))

class DeleteSupplierContactsTest(BaseTestCaseWithErrorHandler):
    """Line-by-line coverage for workday.EventSupplierContactsExternalId.delete"""

    # --- helpers ----------------------------------------------------------

    @staticmethod
    def _find_event_by_external_id(ext_id: str):
        """Return the event dict whose external_id == ext_id."""
        return next(
            (ev for ev in db.DB["events"]["events"].values()
             if ev.get("external_id") == ext_id),
            None
        )

    def test_event_not_found_raises(self):
        """ if not event … -> raise EventNotFound"""
        with pytest.raises(ValueError, match="Event not found"):
            delete("does_not_exist", {"supplier_contact_external_ids": []})

    def test_event_wrong_type_raises(self):
        """ event exists but type != RFP -> raise InvalidEventType"""
        # event_ext_2 exists but has no "type" → will be rejected
        with pytest.raises(ValueError, match="not of type RFP"):
            delete("event_ext_2", {"supplier_contact_external_ids": []})

    def test_empty_supplier_contact_list_ok(self):
        """ event.setdefault returns [] -> True"""
        event = self._find_event_by_external_id("event_ext_1")
        assert event is not None
        event["supplier_contacts"] = []  # ensure list exists
        assert delete("event_ext_1", {"supplier_contact_external_ids": []})

    def test_missing_contact_ids_raises(self):
        """ missing list non-empty -> raise ValueError"""
        event = self._find_event_by_external_id("event_ext_1")
        event["supplier_contacts"] = ["c1", "c2"]
        with pytest.raises(ValueError, match="Supplier contact external id"):
            delete("event_ext_1", {"supplier_contact_external_ids": ["c1", "missing"]})

    def test_happy_path_removes_contacts(self):
        """for cid in to_remove … contacts.remove(cid)"""
        event = self._find_event_by_external_id("event_ext_1")
        event["supplier_contacts"] = ["cA", "cB", "cC"]
        assert delete("event_ext_1", {"supplier_contact_external_ids": ["cA", "cC"]})
        assert event["supplier_contacts"] == ["cB"]

    def test_no_supplier_contact_key_defaults_to_empty(self):
        """data.get("supplier_contact_external_ids", [])"""
        event = self._find_event_by_external_id("event_ext_1")
        event["supplier_contacts"] = ["dummy"]
        assert delete("event_ext_1", {})