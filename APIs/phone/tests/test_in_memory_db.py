#!/usr/bin/env python3
"""
Test cases for in-memory database functionality.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from phone.SimulationEngine.db import DB
from phone.SimulationEngine.utils import get_call_history, get_prepared_calls, get_recipient_choices
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (make_call, prepare_call, show_call_recipient_choices)

class TestInMemoryDatabase(BaseTestCaseWithErrorHandler):
    """Test cases for in-memory database functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear the database to ensure clean state for each test
        from phone.SimulationEngine.db import DB, load_state, save_state, DEFAULT_DB_PATH
        import tempfile
        import os
        
        # Create a temporary file for this test
        self.temp_db_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        
        # Clear all data from DB
        DB.clear()
        
        # Load the default state using load_state
        load_state(DEFAULT_DB_PATH)
        
        # Clear dynamic data to start with empty collections
        DB["call_history"] = {}
        DB["prepared_calls"] = {}
        DB["recipient_choices"] = {}
        DB["not_found_records"] = {}
        DB["actions"] = []
        # Save the initial state to temporary file
        save_state(self.temp_db_path)
        
        # Store initial state
        self.initial_call_history = len(get_call_history())
        self.initial_prepared_calls = len(get_prepared_calls())
        self.initial_recipient_choices = len(get_recipient_choices())
        
        self.sample_recipients = [{
            "contact_name": "Test Contact",
            "recipient_type": "CONTACT",
            "contact_endpoints": [{
                "endpoint_type": "PHONE_NUMBER",
                "endpoint_value": "+1-415-555-2671",
                "endpoint_label": "mobile"
            }]
        }]

    def tearDown(self):
        """Clean up after each test."""
        from phone.SimulationEngine.db import save_state
        import os
        
        # Save the current state to temporary file
        save_state(self.temp_db_path)
        
        # Clean up temporary file
        if hasattr(self, 'temp_db_path') and os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_database_structure_validation(self):
        """Test that the database has the correct structure and collections."""
        # Verify required collections exist
        required_collections = [
            "contacts", "businesses", "special_contacts", 
            "call_history", "prepared_calls", "recipient_choices", 
            "not_found_records", "actions"
        ]
        
        for collection in required_collections:
            self.assertIn(collection, DB, f"Required collection '{collection}' should exist in database")
            # Some collections are dictionaries, some are lists
            if collection in ["contacts", "businesses", "special_contacts", "call_history", "prepared_calls", "recipient_choices", "not_found_records"]:
                self.assertIsInstance(DB[collection], dict, f"Collection '{collection}' should be a dictionary")
            elif collection == "actions":
                self.assertIsInstance(DB[collection], list, f"Collection '{collection}' should be a list")
        
        # Verify contacts collection structure (from contacts API)
        if DB["contacts"]:
            for contact_id, contact in DB["contacts"].items():
                self.assertIsInstance(contact_id, str, "Contact ID should be a string")
                self.assertIsInstance(contact, dict, "Contact should be a dictionary")
                
                # Verify required contact fields (contacts API structure)
                required_contact_fields = ["resourceName", "etag", "names", "phoneNumbers"]
                for field in required_contact_fields:
                    self.assertIn(field, contact, f"Contact should contain required field '{field}'")
                
                # Verify names structure
                names = contact["names"]
                self.assertIsInstance(names, list, "Names should be a list")
                if names:
                    name = names[0]
                    self.assertIsInstance(name, dict, "Name should be a dictionary")
                    self.assertIn("givenName", name, "Name should contain givenName")
                    self.assertIn("familyName", name, "Name should contain familyName")
                
                # Verify phoneNumbers structure
                phone_numbers = contact["phoneNumbers"]
                self.assertIsInstance(phone_numbers, list, "Phone numbers should be a list")
                for phone in phone_numbers:
                    self.assertIsInstance(phone, dict, "Phone number should be a dictionary")
                    required_phone_fields = ["value", "type"]
                    for field in required_phone_fields:
                        self.assertIn(field, phone, f"Phone number should contain required field '{field}'")
        
        # Verify businesses collection structure (from phone database)
        if DB["businesses"]:
            for business_id, business in DB["businesses"].items():
                self.assertIsInstance(business_id, str, "Business ID should be a string")
                self.assertIsInstance(business, dict, "Business should be a dictionary")
                
                # Verify required business fields
                required_business_fields = ["contact_id", "contact_name", "recipient_type", "contact_endpoints"]
                for field in required_business_fields:
                    self.assertIn(field, business, f"Business should contain required field '{field}'")
                
                # Verify contact_endpoints structure
                endpoints = business["contact_endpoints"]
                self.assertIsInstance(endpoints, list, "Business endpoints should be a list")
                for endpoint in endpoints:
                    self.assertIsInstance(endpoint, dict, "Business endpoint should be a dictionary")
                    required_endpoint_fields = ["endpoint_type", "endpoint_value", "endpoint_label"]
                    for field in required_endpoint_fields:
                        self.assertIn(field, endpoint, f"Business endpoint should contain required field '{field}'")
                    self.assertEqual(endpoint["endpoint_type"], "PHONE_NUMBER", "Business endpoint type should be PHONE_NUMBER")

    def test_database_file_structure_validation(self):
        """Test that the database file has the correct structure and format."""
        from phone.SimulationEngine.db import DEFAULT_DB_PATH
        import json
        
        # Verify database file exists and is readable
        self.assertTrue(os.path.exists(DEFAULT_DB_PATH), "Database file should exist")
        
        # Verify database file is valid JSON
        try:
            with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except json.JSONDecodeError as e:
            self.fail(f"Database file should be valid JSON: {e}")
        
        # Verify database file has required top-level keys
        required_keys = ["contacts", "businesses", "special_contacts"]
        for key in required_keys:
            self.assertIn(key, db_data, f"Database file should contain required key '{key}'")
            self.assertIsInstance(db_data[key], dict, f"Database file key '{key}' should map to a dictionary")
        
        # Verify contacts in database file have correct structure
        if db_data["contacts"]:
            for contact_id, contact in db_data["contacts"].items():
                self.assertIsInstance(contact_id, str, "Contact ID in file should be a string")
                self.assertIsInstance(contact, dict, "Contact in file should be a dictionary")
                
                # Verify required contact fields in file
                required_contact_fields = ["resourceName", "etag", "names", "phoneNumbers", "phone"]
                for field in required_contact_fields:
                    self.assertIn(field, contact, f"Contact in file should contain required field '{field}'")

    def test_test_data_completeness_validation(self):
        """Test that test data covers all required scenarios and edge cases."""
        # Verify test data covers different recipient types from contacts API
        contact_recipient_types = set()
        for contact_id, contact in DB["contacts"].items():
            # Contacts from contacts API are all CONTACT type
            contact_recipient_types.add("CONTACT")
        
        expected_contact_types = {"CONTACT"}
        for expected_type in expected_contact_types:
            self.assertIn(expected_type, contact_recipient_types, f"Test data should include {expected_type} recipients")
        
        # Verify test data covers different recipient types from businesses
        business_recipient_types = set()
        for business_id, business in DB["businesses"].items():
            if "recipient_type" in business:
                business_recipient_types.add(business["recipient_type"])
        
        expected_business_types = {"BUSINESS"}
        for expected_type in expected_business_types:
            self.assertIn(expected_type, business_recipient_types, f"Test data should include {expected_type} recipients")
        
        # Verify test data covers different endpoint scenarios in contacts
        single_endpoint_contacts = 0
        multiple_endpoint_contacts = 0
        
        for contact_id, contact in DB["contacts"].items():
            if "phoneNumbers" in contact:
                phone_numbers = contact["phoneNumbers"]
                if len(phone_numbers) == 1:
                    single_endpoint_contacts += 1
                elif len(phone_numbers) > 1:
                    multiple_endpoint_contacts += 1
        
        # Verify we have both single and multiple endpoint scenarios
        self.assertGreater(single_endpoint_contacts, 0, "Test data should include contacts with single phone numbers")
        self.assertGreater(multiple_endpoint_contacts, 0, "Test data should include contacts with multiple phone numbers")
        
        # Verify test data includes different phone number formats
        phone_formats = set()
        for contact_id, contact in DB["contacts"].items():
            if "phoneNumbers" in contact:
                for phone in contact["phoneNumbers"]:
                    if "value" in phone:
                        phone_formats.add(phone["value"][:3])  # Country code
        
        self.assertGreater(len(phone_formats), 0, "Test data should include different phone number formats")
        
        # Verify businesses have proper endpoint structure
        business_endpoints = 0
        for business_id, business in DB["businesses"].items():
            if "contact_endpoints" in business:
                business_endpoints += 1
        
        self.assertGreater(business_endpoints, 0, "Test data should include businesses with endpoints")

    def test_database_data_consistency_validation(self):
        """Test that database data is consistent across collections and references."""
        # Verify contacts from contacts API have consistent structure
        for contact_id, contact in DB["contacts"].items():
            # Verify contact has required fields
            self.assertIn("resourceName", contact, f"Contact {contact_id} should have resourceName")
            self.assertIn("names", contact, f"Contact {contact_id} should have names")
            self.assertIn("phoneNumbers", contact, f"Contact {contact_id} should have phoneNumbers")
            
            # Verify names structure
            names = contact["names"]
            self.assertIsInstance(names, list, f"Contact {contact_id} names should be a list")
            if names:
                name = names[0]
                self.assertIn("givenName", name, f"Contact {contact_id} name should have givenName")
                self.assertIn("familyName", name, f"Contact {contact_id} name should have familyName")
            
            # Verify phoneNumbers structure
            phone_numbers = contact["phoneNumbers"]
            self.assertIsInstance(phone_numbers, list, f"Contact {contact_id} phoneNumbers should be a list")
            for phone in phone_numbers:
                self.assertIn("value", phone, f"Contact {contact_id} phone should have value")
                self.assertIn("type", phone, f"Contact {contact_id} phone should have type")
        
        # Verify businesses from phone database have consistent structure
        for business_id, business in DB["businesses"].items():
            # Verify business has required fields
            self.assertIn("contact_id", business, f"Business {business_id} should have contact_id")
            self.assertIn("contact_name", business, f"Business {business_id} should have contact_name")
            self.assertIn("recipient_type", business, f"Business {business_id} should have recipient_type")
            self.assertIn("contact_endpoints", business, f"Business {business_id} should have contact_endpoints")
            
            # Verify recipient_type is correct
            self.assertEqual(business["recipient_type"], "BUSINESS", f"Business {business_id} should have recipient_type BUSINESS")
            
            # Verify contact_endpoints structure
            endpoints = business["contact_endpoints"]
            self.assertIsInstance(endpoints, list, f"Business {business_id} endpoints should be a list")
            self.assertGreater(len(endpoints), 0, f"Business {business_id} should have at least one endpoint")
            
            for endpoint in endpoints:
                self.assertIn("endpoint_type", endpoint, f"Business {business_id} endpoint should have endpoint_type")
                self.assertIn("endpoint_value", endpoint, f"Business {business_id} endpoint should have endpoint_value")
                self.assertIn("endpoint_label", endpoint, f"Business {business_id} endpoint should have endpoint_label")
                self.assertEqual(endpoint["endpoint_type"], "PHONE_NUMBER", f"Business {business_id} endpoint type should be PHONE_NUMBER")
        
        # Verify special_contacts have consistent structure
        if DB["special_contacts"]:
            for contact_id, contact in DB["special_contacts"].items():
                self.assertIn("contact_id", contact, f"Special contact {contact_id} should have contact_id")
                self.assertIn("contact_name", contact, f"Special contact {contact_id} should have contact_name")
                self.assertIn("recipient_type", contact, f"Special contact {contact_id} should have recipient_type")
                self.assertIn("contact_endpoints", contact, f"Special contact {contact_id} should have contact_endpoints")
                
                # Verify contact_endpoints structure
                endpoints = contact["contact_endpoints"]
                self.assertIsInstance(endpoints, list, f"Special contact {contact_id} endpoints should be a list")
                self.assertGreater(len(endpoints), 0, f"Special contact {contact_id} should have at least one endpoint")

    def test_database_initialization_validation(self):
        """Test that database initialization creates the correct structure."""
        # Clear and reinitialize database
        DB.clear()
        from phone.SimulationEngine.db import load_state, DEFAULT_DB_PATH
        load_state(DEFAULT_DB_PATH)
        
        # Verify required collections are created (from database file)
        required_collections = [
            "contacts", "businesses", "special_contacts", 
            "call_history", "prepared_calls", "recipient_choices", 
            "not_found_records"
        ]
        
        for collection in required_collections:
            self.assertIn(collection, DB, f"Collection '{collection}' should be created during initialization")
        
        # Verify dynamic collections exist and have data (from database file)
        dynamic_collections = ["call_history", "prepared_calls", "recipient_choices", "not_found_records"]
        for collection in dynamic_collections:
            self.assertIsInstance(DB[collection], dict, f"Dynamic collection '{collection}' should be a dictionary")
            # These collections may contain existing data from the database file
        
        # Verify static collections have data
        static_collections = ["contacts", "businesses", "special_contacts"]
        for collection in static_collections:
            self.assertGreater(len(DB[collection]), 0, f"Static collection '{collection}' should contain data after initialization")
        
        # Verify actions collection is created as empty list (if not exists, create it)
        if "actions" not in DB:
            DB["actions"] = []
        self.assertIsInstance(DB["actions"], list, "Actions collection should be a list")
        self.assertEqual(len(DB["actions"]), 0, "Actions collection should be empty after initialization")

    def test_make_call_updates_in_memory_db(self):
        """Test that make_call updates the in-memory database."""
        # Make a test call
        result = make_call(
            recipient_name="Test User 1",
            recipient_phone_number="+1-415-555-2671"
        )
        
        # Verify the call was successful
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)
        
        # Check that call history was updated in memory
        updated_call_history = len(get_call_history())
        self.assertGreater(updated_call_history, self.initial_call_history)
        
        # Verify the new call record exists
        call_history = get_call_history()
        call_ids = list(call_history.keys())
        self.assertIn(result["call_id"], call_ids)
        
        # Verify call details
        call_record = call_history[result["call_id"]]
        self.assertEqual(call_record["phone_number"], "+1-415-555-2671")
        self.assertEqual(call_record["recipient_name"], "Test User 1")

    def test_prepare_call_updates_in_memory_db(self):
        """Test that prepare_call updates the in-memory database."""
        # Prepare a test call
        result = prepare_call(recipients=self.sample_recipients)
        
        # Verify the call preparation was successful
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)
        
        # Check that prepared calls were updated in memory
        updated_prepared_calls = len(get_prepared_calls())
        self.assertGreater(updated_prepared_calls, self.initial_prepared_calls)
        
        # Verify the new prepared call record exists
        prepared_calls = get_prepared_calls()
        prepared_call_ids = list(prepared_calls.keys())
        self.assertIn(result["call_id"], prepared_call_ids)

    def test_show_choices_updates_in_memory_db(self):
        """Test that show_call_recipient_choices updates the in-memory database."""
        # Show choices
        result = show_call_recipient_choices(recipients=self.sample_recipients)
        
        # Verify the choices were shown successfully
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)
        
        # Check that recipient choices were updated in memory
        updated_recipient_choices = len(get_recipient_choices())
        self.assertGreater(updated_recipient_choices, self.initial_recipient_choices)
        
        # Verify the new choice record exists
        recipient_choices = get_recipient_choices()
        choice_ids = list(recipient_choices.keys())
        self.assertIn(result["call_id"], choice_ids)
        call_ids = list(recipient_choices.keys())
        self.assertIn(result["call_id"], call_ids)
        
        # Verify choice details
        choice_record = recipient_choices[result["call_id"]]
        self.assertEqual(len(choice_record["recipient_options"]), 1)
        self.assertEqual(choice_record["recipient_options"][0]["contact_name"], "Test Contact")

    def test_multiple_operations_accumulate_in_memory(self):
        """Test that multiple operations accumulate in the in-memory database."""
        # Make multiple calls
        call1 = make_call(recipient_name="User 1", recipient_phone_number="+1-415-555-2671")
        call2 = make_call(recipient_name="User 2", recipient_phone_number="+1-415-555-2672")
        
        # Prepare a call
        prepared = prepare_call(recipients=self.sample_recipients)
        
        # Show choices
        choices = show_call_recipient_choices(recipients=self.sample_recipients)
        
        # Verify all operations were successful
        self.assertEqual(call1["status"], "success")
        self.assertEqual(call2["status"], "success")
        self.assertEqual(prepared["status"], "success")
        self.assertEqual(choices["status"], "success")
        
        # Check that all records were added to memory
        final_call_history = len(get_call_history())
        final_prepared_calls = len(get_prepared_calls())
        final_recipient_choices = len(get_recipient_choices())
        
        # Should have added 2 calls, 1 prepared call, and 1 choice record
        self.assertEqual(final_call_history, self.initial_call_history + 2)
        self.assertEqual(final_prepared_calls, self.initial_prepared_calls + 1)
        self.assertEqual(final_recipient_choices, self.initial_recipient_choices + 1)

    def test_database_changes_not_persisted_to_file(self):
        """Test that database changes are not persisted to the file system."""
        # Get the initial file modification time
        db_file_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'DBs', 'PhoneDefaultDB.json'
        )
        
        if os.path.exists(db_file_path):
            initial_mtime = os.path.getmtime(db_file_path)
            
            # Make some operations that would update the database
            make_call(recipient_name="File Test User", recipient_phone_number="+1-415-555-2671")
            prepare_call(recipients=self.sample_recipients)
            show_call_recipient_choices(recipients=self.sample_recipients)
            
            # Check that the file modification time hasn't changed
            current_mtime = os.path.getmtime(db_file_path)
            self.assertEqual(current_mtime, initial_mtime, 
                           "Database file should not have been modified")

    def test_call_history_structure(self):
        """Test that call history records have the correct structure."""
        # Make a call
        result = make_call(
            recipient_name="Structure Test User",
            recipient_phone_number="+1-415-555-2671",
            on_speakerphone=True
        )
        
        # Get the call record from memory
        call_history = get_call_history()
        call_record = call_history[result["call_id"]]
        
        # Verify the structure
        required_fields = ["call_id", "timestamp", "phone_number", "recipient_name", 
                          "recipient_photo_url", "on_speakerphone", "status"]
        
        for field in required_fields:
            self.assertIn(field, call_record, f"Call record should contain {field}")
        
        # Verify specific values
        self.assertEqual(call_record["phone_number"], "+1-415-555-2671")
        self.assertEqual(call_record["recipient_name"], "Structure Test User")
        self.assertTrue(call_record["on_speakerphone"])
        self.assertEqual(call_record["status"], "completed")

    def test_prepared_call_structure(self):
        """Test that prepared call records have the correct structure."""
        # Prepare a call
        result = prepare_call(recipients=self.sample_recipients)
        
        # Get the prepared call record from memory
        prepared_calls = get_prepared_calls()
        prepared_call_record = prepared_calls[result["call_id"]]
        
        # Verify the structure
        required_fields = ["call_id", "timestamp", "recipients"]
        for field in required_fields:
            self.assertIn(field, prepared_call_record, f"Prepared call record should contain {field}")
        
        # Verify recipients structure
        recipients = prepared_call_record["recipients"]
        self.assertIsInstance(recipients, list)
        self.assertEqual(len(recipients), 1)
        
        recipient = recipients[0]
        self.assertIn("recipient_name", recipient)
        self.assertIn("recipient_type", recipient)
        self.assertIn("endpoints", recipient)

    def test_recipient_choice_structure(self):
        """Test that recipient choice records have the correct structure."""
        # Show choices
        result = show_call_recipient_choices(recipients=self.sample_recipients)
        
        # Get the choice record from memory
        recipient_choices = get_recipient_choices()
        choice_record = recipient_choices[result["call_id"]]
        
        # Verify the structure
        required_fields = ["call_id", "timestamp", "recipient_options"]
        for field in required_fields:
            self.assertIn(field, choice_record, f"Choice record should contain {field}")
        
        # Verify recipient_options structure
        recipient_options = choice_record["recipient_options"]
        self.assertIsInstance(recipient_options, list)
        self.assertEqual(len(recipient_options), 1)
        
        choice = recipient_options[0]
        self.assertIn("contact_name", choice)
        self.assertIn("recipient_type", choice)
        # Check for either endpoints (single endpoint choice) or endpoint (multiple endpoint choice)
        self.assertTrue("endpoints" in choice or "endpoint" in choice)


if __name__ == "__main__":
    unittest.main()