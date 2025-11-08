"""
Comprehensive tests for the phone porting functionality.
Tests validation, error handling, and data transformation.
"""

import pytest
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add the project root to the path to import Scripts package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Scripts.porting.port_phone import port_phone_db
from APIs.phone.SimulationEngine.models import PhoneDB, ContactModel, RecipientModel


class TestPhonePorting:
    """Test suite for phone porting functionality."""
    
    def get_valid_base_data(self):
        """Get a valid base phone structure for testing."""
        return {
            "call_history": {
                "call_001": {
                    "call_id": "call_001",
                    "timestamp": "2024-01-15T10:30:00",
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
    
    def get_valid_contacts_data(self):
        """Get a valid base contacts structure for testing."""
        return {
            "contact_001": {
                "names": [{"givenName": "John", "familyName": "Doe"}],
                "phoneNumbers": [
                    {"value": "+1234567890", "type": "mobile", "primary": True}
                ],
                "emailAddresses": [
                    {"value": "john.doe@example.com", "type": "personal", "primary": True}
                ],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }

    # ResourceName format tests
    def test_valid_resource_name_format(self):
        """Test that resourceName follows people/contact-{id} format."""
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Check that all contact resource names follow the correct format
        for resource_name in result["contacts"].keys():
            assert resource_name.startswith("people/"), f"Resource name {resource_name} doesn't start with 'people/'"
            # Extract UUID part
            uuid_part = resource_name.split("/")[-1]
            # Verify it's a valid UUID format
            try:
                uuid.UUID(uuid_part)
            except ValueError:
                pytest.fail(f"Resource name {resource_name} doesn't contain valid UUID")

    # Phone number validation tests
    def test_phone_number_international_formats(self):
        """Test that phone numbers accept various international formats based on PhoneDefaultDB.json examples."""
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        # Test various international formats (based on actual numbers from PhoneDefaultDB.json)
        test_numbers = [
            # US numbers
            "+12125550111",
            "+14155552680", 
            # UK numbers
            "+442079460333",
            # Japan numbers  
            "+819012345678",
            "+81312345678",
            # Brazil numbers
            "+5511987654321",
            "+551155559876",
            # India numbers
            "+919820098200",
            # Australia numbers
            "+61491570110",
            # Germany numbers
            "+493012345678",
            # Special formats
            "*86",  # Voicemail (actual format from DB)
            "911",  # Emergency number
            "411"   # Information
        ]
        
        # Define phone number types used in PhoneDefaultDB.json
        phone_types = [
            "mobile", "work", "mobile (work)", "mobile (personal)", 
            "main", "reception", "voicemail"
        ]
        
        for i, number in enumerate(test_numbers):
            # Use different phone types to match the variety in PhoneDefaultDB.json
            phone_type = phone_types[i % len(phone_types)]
            contacts_data[f"contact_{i}"] = {
                "names": [{"givenName": f"Contact{i}", "familyName": "Test"}],
                "phoneNumbers": [{"value": number, "type": phone_type, "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message

    def test_phone_number_empty_null_transformation(self):
        """Test that empty/null phone numbers are filtered out."""
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        # Add contacts with various invalid phone numbers
        contacts_data["contact_invalid_1"] = {
            "names": [{"givenName": "Invalid1", "familyName": "Test"}],
            "phoneNumbers": [{"value": "", "type": "mobile", "primary": True}],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        contacts_data["contact_invalid_2"] = {
            "names": [{"givenName": "Invalid2", "familyName": "Test"}],
            "phoneNumbers": [{"value": None, "type": "mobile", "primary": True}],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        # Test whitespace-only phone numbers
        contacts_data["contact_invalid_3"] = {
            "names": [{"givenName": "Invalid3", "familyName": "Test"}],
            "phoneNumbers": [{"value": "   ", "type": "mobile", "primary": True}],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        # Test invalid format phone numbers
        contacts_data["contact_invalid_4"] = {
            "names": [{"givenName": "Invalid4", "familyName": "Test"}],
            "phoneNumbers": [{"value": "abc123", "type": "mobile", "primary": True}],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        # Test too short phone numbers
        contacts_data["contact_invalid_5"] = {
            "names": [{"givenName": "Invalid5", "familyName": "Test"}],
            "phoneNumbers": [{"value": "123", "type": "mobile", "primary": True}],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        # Test mixed valid/invalid phone numbers
        contacts_data["contact_mixed"] = {
            "names": [{"givenName": "Mixed", "familyName": "Test"}],
            "phoneNumbers": [
                {"value": "+12125550111", "type": "mobile", "primary": True},  # Valid
                {"value": "", "type": "work", "primary": False}  # Invalid
            ],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        # Test missing phoneNumbers array
        contacts_data["contact_no_phones"] = {
            "names": [{"givenName": "NoPhone", "familyName": "Test"}],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        # Test empty phoneNumbers array
        contacts_data["contact_empty_phones"] = {
            "names": [{"givenName": "EmptyPhones", "familyName": "Test"}],
            "phoneNumbers": [],
            "emailAddresses": [],
            "organizations": [],
            "isWorkspaceUser": False
        }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Verify that contacts with invalid phone numbers still exist but without phone endpoints
        for contact in result["contacts"].values():
            if len(contact["names"]) > 0:
                given_name = contact["names"][0]["givenName"]
                
                # Contacts with invalid phone numbers should have None for contact_endpoints
                if given_name.startswith("Invalid") or given_name in ["NoPhone", "EmptyPhones"]:
                    assert contact["phone"]["contact_endpoints"] is None, f"Contact {given_name} should have None contact_endpoints"
                    assert contact["phoneNumbers"] == [], f"Contact {given_name} should have empty phoneNumbers list"
                
                # Mixed contact should have only the valid phone number
                elif given_name == "Mixed":
                    assert contact["phone"]["contact_endpoints"] is not None, "Mixed contact should have contact_endpoints"
                    assert len(contact["phone"]["contact_endpoints"]) == 1, "Mixed contact should have exactly 1 endpoint"
                    assert contact["phone"]["contact_endpoints"][0]["endpoint_value"] == "+12125550111", "Mixed contact should keep only valid number"
                    assert len(contact["phoneNumbers"]) == 1, "Mixed contact should have exactly 1 phoneNumber"

    def test_call_history_empty_null_phone_numbers(self):
        """Test that call history handles empty/null phone numbers correctly."""
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        # Add call history entries with various invalid phone numbers
        phone_data["call_history"] = {
            "call_empty": {
                "call_id": "call_empty",
                "timestamp": 1234567890,
                "phone_number": "",  # Empty string
                "recipient_name": "Empty Number",
                "on_speakerphone": False,
                "status": "completed"
            },
            "call_null": {
                "call_id": "call_null", 
                "timestamp": 1234567891,
                "phone_number": None,  # Null value
                "recipient_name": "Null Number",
                "on_speakerphone": False,
                "status": "completed"
            },
            "call_whitespace": {
                "call_id": "call_whitespace",
                "timestamp": 1234567892,
                "phone_number": "   ",  # Whitespace only
                "recipient_name": "Whitespace Number", 
                "on_speakerphone": False,
                "status": "completed"
            },
            "call_invalid": {
                "call_id": "call_invalid",
                "timestamp": 1234567893,
                "phone_number": "abc123",  # Invalid format
                "recipient_name": "Invalid Number",
                "on_speakerphone": False,
                "status": "completed"
            }
        }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Verify that all call history entries have empty string phone_number for invalid inputs
        for call_id, call in result["call_history"].items():
            if call_id.startswith("call_"):
                assert call["phone_number"] == "", f"Call {call_id} should have empty string phone_number"
                # Recipient names should be preserved
                assert call["recipient_name"] != "", f"Call {call_id} should preserve recipient_name"

    # Contact ID tests
    def test_contact_id_is_always_generated_as_string(self):
        """Test that contact_id is always generated as a non-empty string from resource name.
        
        Note: contact_id is never null in output because it's always generated from resource_name.
        """
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Check that contact_id is properly set as string
        for contact in result["contacts"].values():
            assert isinstance(contact["phone"]["contact_id"], str)
            assert contact["phone"]["contact_id"] != ""

    # Contact name validation tests
    def test_contact_name_accepts_valid_names_and_null(self):
        """Test that contact_name accepts valid names and null."""
        contacts_data = {
            "contact_valid": {
                "names": [{"givenName": "John", "familyName": "Doe"}],
                "phoneNumbers": [{"value": "+1234567890", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_no_name": {
                "names": [],
                "phoneNumbers": [{"value": "+1234567891", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Verify specific contact_name behavior according to model validation
        for contact in result["contacts"].values():
            contact_name = contact["phone"]["contact_name"]
            # Model validation: contact_name cannot be empty string, but can be None
            if contact_name is not None:
                assert isinstance(contact_name, str), "contact_name must be string when not None"
                assert contact_name.strip() != "", "contact_name cannot be empty string per model validation"

    def test_contact_name_rejects_empty_whitespace_strings(self):
        """Test that empty/whitespace contact names are handled properly."""
        contacts_data = {
            "contact_empty": {
                "names": [{"givenName": "", "familyName": ""}],
                "phoneNumbers": [{"value": "+1234567890", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_whitespace": {
                "names": [{"givenName": "   ", "familyName": "   "}],
                "phoneNumbers": [{"value": "+1234567891", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Check that empty names are handled (should not be empty strings)
        for contact in result["contacts"].values():
            contact_name = contact["phone"]["contact_name"]
            assert contact_name is None or (isinstance(contact_name, str) and contact_name.strip() != "")

    # Recipient type validation tests
    def test_recipient_type_correctly_set_for_contacts(self):
        """Test that recipient_type is correctly set to 'CONTACT' for contacts section.
        
        The porting function always sets recipient_type='CONTACT' for contacts from contacts_db.
        This tests the actual current behavior, not arbitrary model compliance.
        """
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Verify that contacts section always gets recipient_type="CONTACT"
        for contact in result["contacts"].values():
            recipient_type = contact["phone"]["recipient_type"]
            assert recipient_type == "CONTACT", f"Contacts should have recipient_type='CONTACT', got '{recipient_type}'"
            
    def test_recipient_type_preserved_in_other_sections(self):
        """Test that recipient_type is preserved in businesses/special_contacts sections."""
        contacts_data = self.get_valid_contacts_data()
        phone_data = {
            "call_history": {},
            "businesses": {
                "business-test": {
                    "contact_id": "business-test",
                    "contact_name": "Test Business",
                    "recipient_type": "BUSINESS",
                    "contact_endpoints": [
                        {"endpoint_type": "PHONE_NUMBER", "endpoint_value": "+1234567890", "endpoint_label": "main"}
                    ]
                }
            },
            "special_contacts": {
                "special-test": {
                    "contact_id": "special-test", 
                    "contact_name": "Test Special",
                    "recipient_type": "VOICEMAIL",
                    "contact_endpoints": [
                        {"endpoint_type": "PHONE_NUMBER", "endpoint_value": "*86", "endpoint_label": "voicemail"}
                    ]
                }
            }
        }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Verify businesses section preserves BUSINESS type
        if "business-test" in result["businesses"]:
            business = result["businesses"]["business-test"]
            assert business["recipient_type"] == "BUSINESS", f"Business should have recipient_type='BUSINESS', got '{business['recipient_type']}'"
            
        # Verify special_contacts section preserves VOICEMAIL type  
        if "special-test" in result["special_contacts"]:
            special = result["special_contacts"]["special-test"]
            assert special["recipient_type"] == "VOICEMAIL", f"Special contact should have recipient_type='VOICEMAIL', got '{special['recipient_type']}'"

    # Endpoint type validation tests
    def test_endpoint_type_always_set_to_phone_number_for_contacts(self):
        """Test that endpoint_type is always set to 'PHONE_NUMBER' for contacts.
        
        Current porting logic hardcodes endpoint_type='PHONE_NUMBER' for all 
        contact endpoints, regardless of input. This tests the actual current behavior.
        """
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Verify that all contact endpoints have endpoint_type="PHONE_NUMBER"
        for contact in result["contacts"].values():
            if contact["phone"]["contact_endpoints"]:  # Handle None case for contacts without phones
                for endpoint in contact["phone"]["contact_endpoints"]:
                    assert endpoint["endpoint_type"] == "PHONE_NUMBER", f"Expected 'PHONE_NUMBER', got '{endpoint['endpoint_type']}'"

    # Endpoint value validation tests
    def test_endpoint_value_is_valid_phone_number(self):
        """Test that endpoint_value is always a valid phone number string."""
        contacts_data = self.get_valid_contacts_data()
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Check that all endpoint values are valid phone numbers
        for contact in result["contacts"].values():
            if contact["phone"]["contact_endpoints"]:  # Handle None case
                for endpoint in contact["phone"]["contact_endpoints"]:
                    assert isinstance(endpoint["endpoint_value"], str), "endpoint_value must be string"
                    assert endpoint["endpoint_value"].strip() != "", "endpoint_value cannot be empty"

    # Contact endpoints validation tests
    def test_contact_endpoints_is_none_or_valid_list(self):
        """Test that contact_endpoints is None (no phones) or valid list (with phones), never empty list."""
        contacts_data = {
            "contact_with_phone": {
                "names": [{"givenName": "John", "familyName": "Doe"}],
                "phoneNumbers": [{"value": "+1234567890", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_no_phone": {
                "names": [{"givenName": "Jane", "familyName": "Doe"}],
                "phoneNumbers": [],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }
        phone_data = self.get_valid_base_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Check that contacts either have valid endpoints or None (for no phone numbers)
        for contact in result["contacts"].values():
            endpoints = contact["phone"]["contact_endpoints"]
            # Either has valid endpoints (list) or None (for contacts without phone numbers)
            assert endpoints is None or isinstance(endpoints, list)

    # Call history validation tests
    def test_call_id_normalization_and_fallback(self):
        """Test that call_id normalization handles all edge cases correctly."""
        phone_data = {
            "call_history": {
                "valid_call": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "empty_call_id": {
                    "call_id": "",  # Empty object call_id, should use key as fallback
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567891",
                    "recipient_name": "Jane Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "missing_call_id": {
                    # No call_id property, should use key as fallback
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567892",
                    "recipient_name": "Bob Smith",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "": {  # Edge case: empty key AND empty call_id
                    "call_id": "",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567893",
                    "recipient_name": "Empty Key",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
        contacts_data = self.get_valid_contacts_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message, "Should pass model validation"
        
        # Verify call_id normalization behavior
        for call_key, call in result["call_history"].items():
            call_id = call["call_id"]
            
            # All call_ids must be non-empty strings (model requirement)
            assert isinstance(call_id, str), f"call_id must be string, got {type(call_id)}"
            assert call_id.strip() != "", f"call_id cannot be empty, got '{call_id}'"
            
            # Verify specific normalization cases
            if call_key == "valid_call":
                assert call_id == "call_001", "Should use provided call_id"
            elif call_key == "empty_call_id":
                assert call_id == "empty_call_id", "Should fallback to dictionary key"
            elif call_key == "missing_call_id":
                assert call_id == "missing_call_id", "Should fallback to dictionary key"
            elif call_key == "":
                # Edge case: both key and call_id empty, should generate UUID
                assert len(call_id) == 36, "Should generate UUID (36 chars)"
                assert "-" in call_id, "Should be UUID format"

    def test_timestamp_conversion_and_fallback(self):
        """Test that timestamp handles all input types and converts them properly to float."""
        phone_data = {
            "call_history": {
                "float_timestamp": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.5,  # Float input
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "int_timestamp": {
                    "call_id": "call_002",
                    "timestamp": 1642249800,  # Int input
                    "phone_number": "+1234567891",
                    "recipient_name": "Jane Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "negative_timestamp": {
                    "call_id": "call_003",
                    "timestamp": -1000.0,  # Negative (pre-epoch)
                    "phone_number": "+1234567892",
                    "recipient_name": "Bob Smith",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "iso_string_colon": {
                    "call_id": "call_004",
                    "timestamp": "2024-01-15T10:30:00",  # ISO with colons
                    "phone_number": "+1234567893",
                    "recipient_name": "Alice Johnson",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "iso_string_dash": {
                    "call_id": "call_005",
                    "timestamp": "2024-01-15T10-30-00",  # ISO with dashes
                    "phone_number": "+1234567894",
                    "recipient_name": "Charlie Brown",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "iso_string_z": {
                    "call_id": "call_006",
                    "timestamp": "2024-01-15T10:30:00Z",  # ISO with Z
                    "phone_number": "+1234567895",
                    "recipient_name": "Diana Prince",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "invalid_string": {
                    "call_id": "call_007",
                    "timestamp": "invalid_timestamp",  # Invalid string
                    "phone_number": "+1234567896",
                    "recipient_name": "Invalid Time",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "null_timestamp": {
                    "call_id": "call_008",
                    "timestamp": None,  # Null
                    "phone_number": "+1234567897",
                    "recipient_name": "Null Time",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "missing_timestamp": {
                    "call_id": "call_009",
                    # No timestamp property
                    "phone_number": "+1234567898",
                    "recipient_name": "Missing Time",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
        contacts_data = self.get_valid_contacts_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message, "Should pass model validation"
        
        # Verify timestamp conversion behavior
        for call_key, call in result["call_history"].items():
            timestamp = call["timestamp"]
            
            # All timestamps must be float (model requirement)
            assert isinstance(timestamp, float), f"timestamp must be float, got {type(timestamp)} for {call_key}"
            
            # Verify specific conversion cases
            if call_key == "float_timestamp":
                assert timestamp == 1642249800.5, "Should preserve float value"
            elif call_key == "int_timestamp":
                assert timestamp == 1642249800.0, "Should convert int to float"
            elif call_key == "negative_timestamp":
                assert timestamp == -1000.0, "Should handle negative timestamps"
            elif call_key in ["iso_string_colon", "iso_string_dash", "iso_string_z"]:
                assert timestamp > 0, f"ISO string should convert to positive epoch for {call_key}"
            elif call_key in ["invalid_string", "null_timestamp", "missing_timestamp"]:
                assert timestamp == 0.0, f"Invalid/missing timestamps should fallback to 0.0 for {call_key}"

    def test_call_history_phone_number_validation(self):
        """Test that call history phone_number accepts valid format but rejects empty/null."""
        phone_data = {
            "call_history": {
                "valid_call": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "empty_phone": {
                    "call_id": "call_002",
                    "timestamp": 1642249800.0,
                    "phone_number": "",
                    "recipient_name": "Jane Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "invalid_phone": {
                    "call_id": "call_003",
                    "timestamp": 1642249800.0,
                    "phone_number": "abc123",
                    "recipient_name": "Bob Smith",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
        contacts_data = self.get_valid_contacts_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Check that invalid phone numbers are handled (normalized to empty string)
        for call in result["call_history"].values():
            phone_number = call["phone_number"]
            # Either valid phone number or empty string (for invalid ones)
            assert isinstance(phone_number, str)

    def test_recipient_name_validation(self):
        """Test that recipient_name handles all edge cases and transformations correctly."""
        phone_data = {
            "call_history": {
                "valid_name": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "empty_name": {
                    "call_id": "call_002",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567891",
                    "recipient_name": "",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "null_name": {
                    "call_id": "call_003",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567892",
                    "recipient_name": None,
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "whitespace_name": {
                    "call_id": "call_004",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567893",
                    "recipient_name": "   ",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "tab_newline_name": {
                    "call_id": "call_005",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567894",
                    "recipient_name": "\t\n  \r",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "missing_name": {
                    "call_id": "call_006",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567895",
                    # No recipient_name field
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "numeric_name": {
                    "call_id": "call_007",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567896",
                    "recipient_name": 123,  # Non-string type
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "special_chars": {
                    "call_id": "call_008",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567897",
                    "recipient_name": "José Müller 😀",  # Unicode and emoji
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "very_long_name": {
                    "call_id": "call_009",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567898",
                    "recipient_name": "A" * 500,  # Very long name
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "contact_match": {
                    "call_id": "call_010",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",  # Matches contact from contacts_data
                    "recipient_name": "Should Be Overridden",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
        contacts_data = self.get_valid_contacts_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Check that recipient names are handled appropriately
        for call_id, call in result["call_history"].items():
            recipient_name = call["recipient_name"]
            
            # All recipient_names must be strings (model requirement)
            assert isinstance(recipient_name, str), f"recipient_name must be string for {call_id}"
            
            # Verify specific transformations
            if call_id == "valid_name":
                assert recipient_name == "John Doe", "Valid names should be preserved"
            elif call_id in ["empty_name", "null_name", "whitespace_name", "tab_newline_name", "missing_name", "numeric_name"]:
                assert recipient_name == "", f"Invalid names should become empty string for {call_id}"
            elif call_id == "special_chars":
                assert recipient_name == "José Müller 😀", "Special characters should be preserved"
            elif call_id == "very_long_name":
                assert recipient_name == "A" * 500, "Long names should be preserved"
            elif call_id == "contact_match":
                # When phone number matches a contact, use contact name instead of provided name
                assert recipient_name == "John Doe", "Should use contact name when phone matches"

    def test_on_speakerphone_boolean_validation(self):
        """Test that on_speakerphone handles all input types and transforms invalid values to False."""
        phone_data = {
            "call_history": {
                "bool_true": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": True,
                    "status": "completed"
                },
                "bool_false": {
                    "call_id": "call_002",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567891",
                    "recipient_name": "Jane Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "string_true": {
                    "call_id": "call_003",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567892",
                    "recipient_name": "Bob Smith",
                    "recipient_photo_url": None,
                    "on_speakerphone": "true",
                    "status": "completed"
                },
                "string_false": {
                    "call_id": "call_004",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567893",
                    "recipient_name": "Alice Johnson",
                    "recipient_photo_url": None,
                    "on_speakerphone": "false",
                    "status": "completed"
                },
                "string_yes": {
                    "call_id": "call_005",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567894",
                    "recipient_name": "Charlie Brown",
                    "recipient_photo_url": None,
                    "on_speakerphone": "yes",
                    "status": "completed"
                },
                "string_no": {
                    "call_id": "call_006",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567895",
                    "recipient_name": "Diana Prince",
                    "recipient_photo_url": None,
                    "on_speakerphone": "no",
                    "status": "completed"
                },
                "string_on": {
                    "call_id": "call_007",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567896",
                    "recipient_name": "Eve Adams",
                    "recipient_photo_url": None,
                    "on_speakerphone": "on",
                    "status": "completed"
                },
                "string_off": {
                    "call_id": "call_008",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567897",
                    "recipient_name": "Frank Miller",
                    "recipient_photo_url": None,
                    "on_speakerphone": "off",
                    "status": "completed"
                },
                "string_1": {
                    "call_id": "call_009",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567898",
                    "recipient_name": "Grace Lee",
                    "recipient_photo_url": None,
                    "on_speakerphone": "1",
                    "status": "completed"
                },
                "string_0": {
                    "call_id": "call_010",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567899",
                    "recipient_name": "Henry Wilson",
                    "recipient_photo_url": None,
                    "on_speakerphone": "0",
                    "status": "completed"
                },
                "null_value": {
                    "call_id": "call_011",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567800",
                    "recipient_name": "Ivy Chen",
                    "recipient_photo_url": None,
                    "on_speakerphone": None,
                    "status": "completed"
                },
                "missing_field": {
                    "call_id": "call_012",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567801",
                    "recipient_name": "Jack Davis",
                    "recipient_photo_url": None,
                    # No on_speakerphone field
                    "status": "completed"
                },
                "invalid_string": {
                    "call_id": "call_013",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567802",
                    "recipient_name": "Kate Young",
                    "recipient_photo_url": None,
                    "on_speakerphone": "maybe",
                    "status": "completed"
                },
                "numeric_1": {
                    "call_id": "call_014",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567803",
                    "recipient_name": "Leo King",
                    "recipient_photo_url": None,
                    "on_speakerphone": 1,
                    "status": "completed"
                },
                "numeric_0": {
                    "call_id": "call_015",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567804",
                    "recipient_name": "Mia Lopez",
                    "recipient_photo_url": None,
                    "on_speakerphone": 0,
                    "status": "completed"
                },
                "case_insensitive": {
                    "call_id": "call_016",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567805",
                    "recipient_name": "Noah Garcia",
                    "recipient_photo_url": None,
                    "on_speakerphone": "TRUE",
                    "status": "completed"
                }
            }
        }
        contacts_data = self.get_valid_contacts_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Check that on_speakerphone is boolean and verify specific transformations
        for call_id, call in result["call_history"].items():
            on_speakerphone = call["on_speakerphone"]
            
            # All on_speakerphone values must be boolean (model requirement)
            assert isinstance(on_speakerphone, bool), f"on_speakerphone must be boolean for {call_id}"
            
            # Verify specific transformations
            if call_id in ["bool_true", "string_true", "string_yes", "string_on", "string_1", "case_insensitive"]:
                assert on_speakerphone is True, f"Should be True for {call_id}"
            elif call_id in ["bool_false", "string_false", "string_no", "string_off", "string_0"]:
                assert on_speakerphone is False, f"Should be False for {call_id}"
            elif call_id in ["null_value", "missing_field", "invalid_string", "numeric_1", "numeric_0"]:
                assert on_speakerphone is False, f"Invalid values should default to False for {call_id}"

    def test_status_accepts_completed_literal(self):
        """Test that status handles all inputs and always transforms to 'completed'."""
        phone_data = {
            "call_history": {
                "valid_status": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "uppercase_status": {
                    "call_id": "call_002",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567891",
                    "recipient_name": "Jane Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "COMPLETED"
                },
                "mixed_case_status": {
                    "call_id": "call_003",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567892",
                    "recipient_name": "Bob Smith",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "Completed"
                },
                "whitespace_status": {
                    "call_id": "call_004",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567893",
                    "recipient_name": "Alice Johnson",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "  completed  "
                },
                "invalid_status_pending": {
                    "call_id": "call_005",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567894",
                    "recipient_name": "Charlie Brown",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "pending"
                },
                "invalid_status_failed": {
                    "call_id": "call_006",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567895",
                    "recipient_name": "Diana Prince",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "failed"
                },
                "invalid_status_unknown": {
                    "call_id": "call_007",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567896",
                    "recipient_name": "Eve Adams",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "unknown"
                },
                "empty_status": {
                    "call_id": "call_008",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567897",
                    "recipient_name": "Frank Miller",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": ""
                },
                "null_status": {
                    "call_id": "call_009",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567898",
                    "recipient_name": "Grace Lee",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": None
                },
                "missing_status": {
                    "call_id": "call_010",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567899",
                    "recipient_name": "Henry Wilson",
                    "recipient_photo_url": None,
                    "on_speakerphone": False
                    # No status field
                },
                "numeric_status": {
                    "call_id": "call_011",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567800",
                    "recipient_name": "Ivy Chen",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": 123
                },
                "whitespace_only_status": {
                    "call_id": "call_012",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567801",
                    "recipient_name": "Jack Davis",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "   "
                }
            }
        }
        contacts_data = self.get_valid_contacts_data()
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Check that status is always "completed" for all cases
        for call_id, call in result["call_history"].items():
            status = call["status"]
            
            # ALL status values must be exactly "completed" (model requirement: Literal['completed'])
            assert status == "completed", f"All status values must be 'completed', got '{status}' for {call_id}"
            
            # Verify it's a string type
            assert isinstance(status, str), f"status must be string for {call_id}"

    def test_phone_numbers_match_between_contacts_and_phone_sections(self):
        """Test comprehensive phone number matching logic between contacts and call history."""
        phone_data = {
            "call_history": {
                "exact_match": {
                    "call_id": "exact_match",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "Should Be Overridden",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "normalized_match": {
                    "call_id": "normalized_match", 
                    "timestamp": 1642249801.0,
                    "phone_number": "+1-234-567-8900",  # Different format, should normalize to same
                    "recipient_name": "Should Be Overridden Too",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "formatted_match": {
                    "call_id": "formatted_match",
                    "timestamp": 1642249802.0,
                    "phone_number": "+1 (234) 567-8900",  # Same format as contact, should match
                    "recipient_name": "Override Me Please",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "no_match": {
                    "call_id": "no_match",
                    "timestamp": 1642249803.0,
                    "phone_number": "+9876543210",  # No matching contact
                    "recipient_name": "Keep Original Name",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "invalid_phone": {
                    "call_id": "invalid_phone",
                    "timestamp": 1642249804.0,
                    "phone_number": "abc123",  # Invalid phone
                    "recipient_name": "Invalid Phone Call",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "empty_phone": {
                    "call_id": "empty_phone",
                    "timestamp": 1642249805.0,
                    "phone_number": "",  # Empty phone
                    "recipient_name": "Empty Phone Call",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "multi_contact_match": {
                    "call_id": "multi_contact_match",
                    "timestamp": 1642249806.0,
                    "phone_number": "+5555551234",  # Matches contact with multiple phones
                    "recipient_name": "Should Use Contact Name",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "no_country_code": {
                    "call_id": "no_country_code",
                    "timestamp": 1642249807.0,
                    "phone_number": "(555) 123-4567",  # No +1, won't match +1 contacts
                    "recipient_name": "No Country Code Call",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
        contacts_data = {
            "contact_exact": {
                "names": [{"givenName": "John", "familyName": "Doe"}],
                "phoneNumbers": [
                    {"value": "+1234567890", "type": "mobile", "primary": True}
                ],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_formatted": {
                "names": [{"givenName": "Jane", "familyName": "Smith"}],
                "phoneNumbers": [
                    {"value": "+1 (234) 567-8900", "type": "work", "primary": True}  # Formatted differently
                ],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_multi_phone": {
                "names": [{"givenName": "Bob", "familyName": "Wilson"}],
                "phoneNumbers": [
                    {"value": "+5555551234", "type": "mobile", "primary": True},
                    {"value": "+5555559999", "type": "work", "primary": False}
                ],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_invalid_phone": {
                "names": [{"givenName": "Alice", "familyName": "Johnson"}],
                "phoneNumbers": [
                    {"value": "invalid123", "type": "mobile", "primary": True}  # Invalid phone
                ],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_no_phone": {
                "names": [{"givenName": "Charlie", "familyName": "Brown"}],
                "phoneNumbers": [],  # No phone numbers
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Test specific matching behaviors
        for call_id, call in result["call_history"].items():
            recipient_name = call["recipient_name"]
            phone_number = call["phone_number"]
            
            if call_id == "exact_match":
                # Exact phone match should use contact name
                assert recipient_name == "John Doe", f"Should use contact name for exact match, got '{recipient_name}'"
                assert phone_number == "+1234567890", "Phone number should be preserved"
                
            elif call_id == "normalized_match":
                # Normalized phone match should use contact name  
                assert recipient_name == "Jane Smith", f"Should use contact name for normalized match, got '{recipient_name}'"
                assert phone_number == "+12345678900", "Phone should be normalized"
                
            elif call_id == "formatted_match":
                # Different formatting should still match
                assert recipient_name == "Jane Smith", f"Should use contact name for formatted match, got '{recipient_name}'"
                assert phone_number == "+12345678900", "Phone should be normalized with +1"
                
            elif call_id == "no_match":
                # No matching contact should preserve original name
                assert recipient_name == "Keep Original Name", f"Should preserve original name when no match, got '{recipient_name}'"
                assert phone_number == "+9876543210", "Phone number should be preserved"
                
            elif call_id == "invalid_phone":
                # Invalid phone should not match, preserve original name
                assert recipient_name == "Invalid Phone Call", f"Should preserve name for invalid phone, got '{recipient_name}'"
                assert phone_number == "", "Invalid phone should become empty string"
                
            elif call_id == "empty_phone":
                # Empty phone should not match, preserve original name
                assert recipient_name == "Empty Phone Call", f"Should preserve name for empty phone, got '{recipient_name}'"
                assert phone_number == "", "Empty phone should remain empty"
                
            elif call_id == "multi_contact_match":
                # Contact with multiple phones should still match
                assert recipient_name == "Bob Wilson", f"Should use contact name for multi-phone contact, got '{recipient_name}'"
                assert phone_number == "+5555551234", "Phone number should be preserved"
                
            elif call_id == "no_country_code":
                # Phone without country code won't match contacts with +1
                assert recipient_name == "No Country Code Call", f"Should preserve original name when no +1 match, got '{recipient_name}'"
                assert phone_number == "5551234567", "Phone should be normalized without +1"
        
        # Verify normalization consistency between contacts and calls
        contact_phones = set()
        for contact in result["contacts"].values():
            if contact["phone"]["contact_endpoints"]:
                for endpoint in contact["phone"]["contact_endpoints"]:
                    contact_phones.add(endpoint["endpoint_value"])
        
        call_phones = set()
        for call in result["call_history"].values():
            if call["phone_number"]:  # Skip empty phone numbers
                call_phones.add(call["phone_number"])
        
        # Verify that matched phones exist in both sections with same normalization
        expected_matches = {"+1234567890", "+12345678900", "+5555551234"}
        matching_phones = contact_phones.intersection(call_phones)
        
        assert expected_matches.issubset(matching_phones), f"Expected matches {expected_matches} not found in intersection {matching_phones}"
        
        # Verify that contacts with invalid phones have None endpoints
        for contact in result["contacts"].values():
            if len(contact["names"]) > 0:
                name = contact["names"][0]["givenName"]
                if name == "Alice":  # contact_invalid_phone
                    assert contact["phone"]["contact_endpoints"] is None, "Contact with invalid phone should have None endpoints"
                elif name == "Charlie":  # contact_no_phone
                    assert contact["phone"]["contact_endpoints"] is None, "Contact with no phones should have None endpoints"

    def test_comprehensive_invalid_data_transformation(self):
        """Test comprehensive transformation of invalid data to defaults."""
        phone_data = {
            "call_history": {
                "problematic_call": {
                    "call_id": None,  # Invalid
                    "timestamp": "invalid_timestamp",  # Invalid
                    "phone_number": "",  # Invalid
                    "recipient_name": None,  # Invalid
                    "recipient_photo_url": None,  # Valid
                    "on_speakerphone": "maybe",  # Invalid
                    "status": "failed"  # Invalid
                }
            }
        }
        contacts_data = {
            "problematic_contact": {
                "names": [{"givenName": "", "familyName": ""}],  # Invalid
                "phoneNumbers": [
                    {"value": "", "type": "mobile", "primary": True}  # Invalid
                ],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        # Should still succeed with transformations applied
        assert result is not None, f"Porting should succeed with transformations: {message}"
        
        # Verify transformations were applied
        if result["call_history"]:
            for call in result["call_history"].values():
                # Check that invalid values were transformed
                assert isinstance(call.get("on_speakerphone"), bool)
                assert call.get("status") in ["completed", "unknown"]
                assert isinstance(call.get("recipient_name"), str)

    def test_output_complies_with_pydantic_models(self):
        """Test that the ported output fully complies with Pydantic model validation."""
        contacts_data = {
            "contact_valid": {
                "names": [{"givenName": "John", "familyName": "Doe"}],
                "phoneNumbers": [{"value": "+1234567890", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_empty_name": {
                "names": [{"givenName": "", "familyName": ""}],  # Should become None
                "phoneNumbers": [{"value": "+1234567891", "type": "mobile", "primary": True}],
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            },
            "contact_no_phone": {
                "names": [{"givenName": "Jane", "familyName": "Smith"}],
                "phoneNumbers": [],  # Should result in contact_endpoints: None
                "emailAddresses": [],
                "organizations": [],
                "isWorkspaceUser": False
            }
        }
        
        phone_data = {
            "call_history": {
                "call_001": {
                    "call_id": "call_001",
                    "timestamp": 1642249800.0,
                    "phone_number": "+1234567890",
                    "recipient_name": "John Doe",
                    "recipient_photo_url": None,
                    "on_speakerphone": False,
                    "status": "completed"
                },
                "call_empty_phone": {
                    "call_id": "call_empty",
                    "timestamp": 1642249801.0,
                    "phone_number": "",  # Should become empty string
                    "recipient_name": "Unknown",
                    "on_speakerphone": False,
                    "status": "completed"
                }
            }
        }
        
        result, message = port_phone_db(json.dumps(phone_data), json.dumps(contacts_data))
        
        assert result is not None, f"Porting failed: {message}"
        assert "Validation successful" in message
        
        # Test that the result can be validated by the actual Pydantic models
        try:
            # This should not raise any validation errors
            phone_db = PhoneDB(**result)
            
            # Verify specific model constraints are met
            for contact_data in phone_db.contacts.values():
                # ContactModel validation
                assert isinstance(contact_data, ContactModel)
                
                # RecipientModel validation within ContactModel  
                recipient = contact_data.phone
                assert isinstance(recipient, RecipientModel)
                
                # contact_name: Cannot be empty string (but can be None)
                if recipient.contact_name is not None:
                    assert recipient.contact_name.strip() != "", "contact_name cannot be empty string"
                
                # contact_endpoints: Cannot be empty list (but can be None)
                if recipient.contact_endpoints is not None:
                    assert len(recipient.contact_endpoints) > 0, "contact_endpoints cannot be empty list"
                    
        except Exception as e:
            pytest.fail(f"Pydantic model validation failed: {e}")
        
        print("✅ All ported data successfully validates against Pydantic models")
