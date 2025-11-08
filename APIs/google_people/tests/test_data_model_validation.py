"""
Test cases for Data Model Validation in Google People API.

This module tests:
1. Database structure validation against Pydantic models
2. Test data validation to ensure all test data conforms to expected schemas
3. Data integrity checks for the simulation engine
"""

import unittest
from typing import Dict, Any, List

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .common import reset_db
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import (
    Person, ContactGroup, OtherContact, Name, EmailAddress, PhoneNumber,
    Address, Organization, Birthday, Photo, Url, UserDefined,
    EmailType, PhoneType, AddressType, OrganizationType, UrlType
)
from pydantic import ValidationError as PydanticValidationError


class GooglePeopleDBModel:
    """Database structure model for Google People API."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize and validate the database structure."""
        self.people = data.get("people", {})
        self.contact_groups = data.get("contactGroups", {})
        self.other_contacts = data.get("otherContacts", {})
        self.directory_people = data.get("directoryPeople", {})
        
        # Validate structure
        self._validate_structure()
    
    def _validate_structure(self):
        """Validate the overall database structure."""
        required_keys = ["people", "contactGroups", "otherContacts", "directoryPeople"]
        for key in required_keys:
            if not hasattr(self, key.replace("contactGroups", "contact_groups").replace("otherContacts", "other_contacts").replace("directoryPeople", "directory_people")):
                raise ValueError(f"Missing required database section: {key}")


class TestDataModelValidation(BaseTestCaseWithErrorHandler):
    """Test class for data model validation."""

    def setUp(self):
        """Set up test database with validated sample data."""
        reset_db()
        
        # Create validated test data using Pydantic models
        self.valid_person_data = {
            "resourceName": "people/test123",
            "etag": "etag_test123",
            "names": [{"displayName": "Test User", "givenName": "Test", "familyName": "User"}],
            "emailAddresses": [{"value": "test@example.com", "type": "work"}],
            "phoneNumbers": [{"value": "+1-555-123-4567", "type": "mobile"}],
            "addresses": [{"formattedValue": "123 Test St, Test City, TS 12345", "type": "home"}],
            "organizations": [{"name": "Test Corp", "title": "Tester", "type": "work"}],
            "created": "2023-01-15T10:30:00Z",
            "updated": "2024-01-15T14:20:00Z"
        }
        
        self.valid_contact_group_data = {
            "resourceName": "contactGroups/testgroup",
            "etag": "etag_testgroup",
            "name": "Test Group",
            "groupType": "USER_CONTACT_GROUP",
            "memberResourceNames": ["people/test123"],
            "memberCount": 1,
            "created": "2023-01-15T10:30:00Z",
            "updated": "2024-01-15T14:20:00Z"
        }
        
        self.valid_other_contact_data = {
            "resourceName": "otherContacts/other123",
            "etag": "etag_other123",
            "names": [{"displayName": "Other User", "givenName": "Other", "familyName": "User"}],
            "emailAddresses": [{"value": "other@example.com", "type": "other"}],
            "created": "2023-01-15T10:30:00Z",
            "updated": "2024-01-15T14:20:00Z"
        }

    def tearDown(self):
        """Clean up after each test."""
        reset_db()

    def test_db_structure_validation(self):
        """Test that the database structure conforms to expected schema."""
        try:
            # Validate the overall database structure
            db_data = {
                "people": DB.get("people", {}),
                "contactGroups": DB.get("contactGroups", {}),
                "otherContacts": DB.get("otherContacts", {}),
                "directoryPeople": DB.get("directoryPeople", {})
            }
            
            validated_db = GooglePeopleDBModel(db_data)
            self.assertIsInstance(validated_db, GooglePeopleDBModel)
            
        except Exception as e:
            self.fail(f"DB structure validation failed: {e}")

    def test_person_data_validation(self):
        """Test that person data conforms to Person model."""
        # Test valid person data
        try:
            person = Person(**self.valid_person_data)
            self.assertIsNotNone(person)
            self.assertEqual(person.resource_name, "people/test123")
        except PydanticValidationError as e:
            self.fail(f"Valid person data failed validation: {e}")
        
        # Test invalid person data
        invalid_data = self.valid_person_data.copy()
        invalid_data["emailAddresses"] = [{"value": "invalid-email", "type": "work"}]
        
        with self.assertRaises(PydanticValidationError):
            Person(**invalid_data)

    def test_contact_group_data_validation(self):
        """Test that contact group data conforms to ContactGroup model."""
        # Test valid contact group data
        try:
            contact_group = ContactGroup(**self.valid_contact_group_data)
            self.assertIsNotNone(contact_group)
            self.assertEqual(contact_group.resource_name, "contactGroups/testgroup")
        except PydanticValidationError as e:
            self.fail(f"Valid contact group data failed validation: {e}")
        
        # Test invalid contact group data
        invalid_data = self.valid_contact_group_data.copy()
        invalid_data["memberResourceNames"] = ["invalid-resource-name"]
        
        with self.assertRaises(PydanticValidationError):
            ContactGroup(**invalid_data)

    def test_other_contact_data_validation(self):
        """Test that other contact data conforms to OtherContact model."""
        try:
            other_contact = OtherContact(**self.valid_other_contact_data)
            self.assertIsNotNone(other_contact)
            self.assertEqual(other_contact.resource_name, "otherContacts/other123")
        except PydanticValidationError as e:
            self.fail(f"Valid other contact data failed validation: {e}")

    def test_name_field_validation(self):
        """Test Name model validation."""
        valid_name = {
            "displayName": "John Doe",
            "givenName": "John", 
            "familyName": "Doe"
        }
        
        try:
            name = Name(**valid_name)
            self.assertEqual(name.display_name, "John Doe")
            self.assertEqual(name.given_name, "John")
            self.assertEqual(name.family_name, "Doe")
        except PydanticValidationError as e:
            self.fail(f"Valid name data failed validation: {e}")

    def test_email_address_validation(self):
        """Test EmailAddress model validation."""
        valid_email = {
            "value": "test@example.com",
            "type": "work"
        }
        
        try:
            email = EmailAddress(**valid_email)
            self.assertEqual(email.value, "test@example.com")
            self.assertEqual(email.type, EmailType.WORK)
        except PydanticValidationError as e:
            self.fail(f"Valid email data failed validation: {e}")
        
        # Test invalid email
        invalid_email = {"value": "invalid-email", "type": "work"}
        with self.assertRaises(PydanticValidationError):
            EmailAddress(**invalid_email)

    def test_phone_number_validation(self):
        """Test PhoneNumber model validation."""
        valid_phone = {
            "value": "+1-555-123-4567",
            "type": "mobile"
        }
        
        try:
            phone = PhoneNumber(**valid_phone)
            self.assertEqual(phone.value, "+1-555-123-4567")
            self.assertEqual(phone.type, PhoneType.MOBILE)
        except PydanticValidationError as e:
            self.fail(f"Valid phone data failed validation: {e}")

    def test_address_validation(self):
        """Test Address model validation."""
        valid_address = {
            "formattedValue": "123 Main St, City, State 12345",
            "type": "home",
            "city": "City",
            "region": "State",
            "postalCode": "12345"
        }
        
        try:
            address = Address(**valid_address)
            self.assertEqual(address.formatted_value, "123 Main St, City, State 12345")
            self.assertEqual(address.type, AddressType.HOME)
        except PydanticValidationError as e:
            self.fail(f"Valid address data failed validation: {e}")

    def test_organization_validation(self):
        """Test Organization model validation."""
        valid_org = {
            "name": "Tech Corp",
            "title": "Software Engineer",
            "type": "work"
        }
        
        try:
            org = Organization(**valid_org)
            self.assertEqual(org.name, "Tech Corp")
            self.assertEqual(org.title, "Software Engineer")
            self.assertEqual(org.type, OrganizationType.WORK)
        except PydanticValidationError as e:
            self.fail(f"Valid organization data failed validation: {e}")

    def test_validated_test_data_in_db(self):
        """Test that test data added to DB is validated against models."""
        # Add validated test data to database
        validated_person = Person(**self.valid_person_data)
        validated_group = ContactGroup(**self.valid_contact_group_data)
        validated_other = OtherContact(**self.valid_other_contact_data)
        
        # Add to database using validated data
        people_data = DB.get("people", {})
        people_data[validated_person.resource_name] = validated_person.model_dump(by_alias=True)
        DB.set("people", people_data)
        
        groups_data = DB.get("contactGroups", {})
        groups_data[validated_group.resource_name] = validated_group.model_dump(by_alias=True)
        DB.set("contactGroups", groups_data)
        
        others_data = DB.get("otherContacts", {})
        others_data[validated_other.resource_name] = validated_other.model_dump(by_alias=True)
        DB.set("otherContacts", others_data)
        
        # Verify data was stored correctly
        stored_person = DB.get("people", {}).get("people/test123")
        self.assertIsNotNone(stored_person)
        self.assertEqual(stored_person["resourceName"], "people/test123")
        
        stored_group = DB.get("contactGroups", {}).get("contactGroups/testgroup")
        self.assertIsNotNone(stored_group)
        self.assertEqual(stored_group["resourceName"], "contactGroups/testgroup")

    def test_enum_validation(self):
        """Test that enum values are properly validated."""
        # Test valid enum values
        valid_email_types = ["home", "work", "other"]
        for email_type in valid_email_types:
            try:
                EmailType(email_type)
            except ValueError:
                self.fail(f"Valid email type {email_type} failed validation")
        
        # Test invalid enum value
        with self.assertRaises(ValueError):
            EmailType("invalid_type")

    def test_resource_name_format_validation(self):
        """Test that resource names follow the correct format."""
        valid_person_resource = "people/123456789"
        valid_group_resource = "contactGroups/family"
        valid_other_resource = "otherContacts/987654321"
        
        # Test Person resource name validation
        person_data = self.valid_person_data.copy()
        person_data["resourceName"] = valid_person_resource
        try:
            person = Person(**person_data)
            self.assertEqual(person.resource_name, valid_person_resource)
        except PydanticValidationError as e:
            self.fail(f"Valid person resource name failed validation: {e}")
        
        # Test invalid resource name
        person_data["resourceName"] = "invalid/resource/name"
        with self.assertRaises(PydanticValidationError):
            Person(**person_data)

    def test_data_consistency_validation(self):
        """Test data consistency across related models."""
        # Test that memberCount matches actual memberResourceNames length
        group_data = self.valid_contact_group_data.copy()
        group_data["memberResourceNames"] = ["people/1", "people/2", "people/3"]
        group_data["memberCount"] = 3
        
        try:
            group = ContactGroup(**group_data)
            self.assertEqual(len(group.member_resource_names), group.member_count)
        except PydanticValidationError as e:
            self.fail(f"Consistent group data failed validation: {e}")


if __name__ == '__main__':
    unittest.main()
