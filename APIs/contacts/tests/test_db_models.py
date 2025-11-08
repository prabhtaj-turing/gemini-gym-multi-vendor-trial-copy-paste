import unittest
import json
import tempfile
import os
from pydantic import ValidationError

from contacts.SimulationEngine.db_models import (
    Name, EmailAddress, PhoneNumber, Organization, WhatsAppContact,
    PhoneEndpoint, PhoneContact, Contact, ContactsDB
)


class TestNameModel(unittest.TestCase):
    """Test cases for Name model."""
    
    def test_name_with_both_fields(self):
        """Test Name with both given_name and family_name."""
        name = Name(givenName="John", familyName="Doe")
        self.assertEqual(name.given_name, "John")
        self.assertEqual(name.family_name, "Doe")
    
    def test_name_with_only_given_name(self):
        """Test Name with only given_name."""
        name = Name(givenName="John")
        self.assertEqual(name.given_name, "John")
        self.assertIsNone(name.family_name)
    
    def test_name_with_only_family_name(self):
        """Test Name with only family_name."""
        name = Name(familyName="Doe")
        self.assertIsNone(name.given_name)
        self.assertEqual(name.family_name, "Doe")
    
    def test_name_with_empty_strings(self):
        """Test Name with empty strings."""
        name = Name(givenName="", familyName="")
        self.assertEqual(name.given_name, "")
        self.assertEqual(name.family_name, "")
    
    def test_name_field_validation(self):
        """Test Name field validation."""
        name = Name(givenName="  John  ", familyName="  Doe  ")
        self.assertEqual(name.given_name, "John")
        self.assertEqual(name.family_name, "Doe")


class TestEmailAddressModel(unittest.TestCase):
    """Test cases for EmailAddress model."""
    
    def test_valid_email(self):
        """Test valid email address."""
        email = EmailAddress(value="john.doe@example.com", type="work", primary=True)
        self.assertEqual(email.value, "john.doe@example.com")
        self.assertEqual(email.type, "work")
        self.assertTrue(email.primary)
    
    def test_email_with_minimal_fields(self):
        """Test email with only required value field."""
        email = EmailAddress(value="test@example.com")
        self.assertEqual(email.value, "test@example.com")
        self.assertIsNone(email.type)
        self.assertIsNone(email.primary)
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        with self.assertRaises(ValidationError):
            EmailAddress(value="invalid-email")
    
    def test_empty_email_value(self):
        """Test empty email value."""
        with self.assertRaises(ValidationError):
            EmailAddress(value="")
    
    def test_email_type_validation(self):
        """Test email type validation."""
        with self.assertRaises(ValidationError):
            EmailAddress(value="test@example.com", type="invalid")
        
        # Valid types
        for email_type in ["home", "work", "other"]:
            email = EmailAddress(value="test@example.com", type=email_type)
            self.assertEqual(email.type, email_type)


class TestPhoneNumberModel(unittest.TestCase):
    """Test cases for PhoneNumber model."""
    
    def test_valid_phone_number(self):
        """Test valid phone number."""
        phone = PhoneNumber(value="+14155552671", type="mobile", primary=True)
        self.assertEqual(phone.value, "+14155552671")
        self.assertEqual(phone.type, "mobile")
        self.assertTrue(phone.primary)
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        # Valid phone numbers
        valid_phones = ["+14155552671", "4155552671", "(415) 555-2671"]
        for phone_val in valid_phones:
            phone = PhoneNumber(value=phone_val, type="mobile", primary=True)
            self.assertEqual(phone.value, phone_val)
        
        # Invalid phone numbers (only validate if value is provided)
        invalid_phones = ["123", "abc", "+12345678901234567890"]
        for phone_val in invalid_phones:
            with self.assertRaises(ValidationError):
                PhoneNumber(value=phone_val, type="mobile", primary=True)
        
        # Empty string should be allowed (Optional field)
        phone = PhoneNumber(value="", type="mobile", primary=True)
        self.assertEqual(phone.value, "")
    
    def test_phone_type_validation(self):
        """Test phone type validation."""
        valid_types = ["mobile", "work", "home", "other"]
        for phone_type in valid_types:
            phone = PhoneNumber(value="+14155552671", type=phone_type, primary=True)
            self.assertEqual(phone.type, phone_type)
        
        with self.assertRaises(ValidationError):
            PhoneNumber(value="+14155552671", type="invalid", primary=True)
    
    def test_optional_fields(self):
        """Test that all fields are optional."""
        # All fields can be None
        phone = PhoneNumber()
        self.assertIsNone(phone.value)
        self.assertIsNone(phone.type)
        self.assertIsNone(phone.primary)
        
        # Partial fields are allowed
        phone = PhoneNumber(value="+14155552671")
        self.assertEqual(phone.value, "+14155552671")
        self.assertIsNone(phone.type)
        self.assertIsNone(phone.primary)


class TestOrganizationModel(unittest.TestCase):
    """Test cases for Organization model."""
    
    def test_valid_organization(self):
        """Test valid organization."""
        org = Organization(name="Google", title="Software Engineer", department="Engineering", primary=True)
        self.assertEqual(org.name, "Google")
        self.assertEqual(org.title, "Software Engineer")
        self.assertEqual(org.department, "Engineering")
        self.assertTrue(org.primary)
    
    def test_organization_without_department(self):
        """Test organization without department."""
        org = Organization(name="Google", title="Software Engineer", primary=True)
        self.assertEqual(org.name, "Google")
        self.assertEqual(org.title, "Software Engineer")
        self.assertIsNone(org.department)
        self.assertTrue(org.primary)
    
    def test_optional_fields_validation(self):
        """Test that all fields are optional."""
        # All fields can be None
        org = Organization()
        self.assertIsNone(org.name)
        self.assertIsNone(org.title)
        self.assertIsNone(org.department)
        self.assertIsNone(org.primary)
        
        # Partial fields are allowed
        org = Organization(name="Google")
        self.assertEqual(org.name, "Google")
        self.assertIsNone(org.title)
        self.assertIsNone(org.department)
        self.assertIsNone(org.primary)


class TestWhatsAppContactModel(unittest.TestCase):
    """Test cases for WhatsAppContact model."""
    
    def test_valid_whatsapp_contact(self):
        """Test valid WhatsApp contact."""
        whatsapp = WhatsAppContact(
            jid="19876543210@s.whatsapp.net",
            name_in_address_book="Jane Doe",
            profile_name="Jane D.",
            phone_number="+19876543210",
            is_whatsapp_user=True
        )
        self.assertEqual(whatsapp.jid, "19876543210@s.whatsapp.net")
        self.assertEqual(whatsapp.name_in_address_book, "Jane Doe")
        self.assertEqual(whatsapp.profile_name, "Jane D.")
        self.assertEqual(whatsapp.phone_number, "+19876543210")
        self.assertTrue(whatsapp.is_whatsapp_user)
    
    def test_whatsapp_contact_without_phone(self):
        """Test WhatsApp contact without phone number."""
        whatsapp = WhatsAppContact(
            jid="contact_12345678@example.com",
            name_in_address_book="John Doe",
            profile_name="John D.",
            is_whatsapp_user=False
        )
        self.assertIsNone(whatsapp.phone_number)
        self.assertFalse(whatsapp.is_whatsapp_user)
    
    def test_invalid_jid_format(self):
        """Test invalid JID format."""
        with self.assertRaises(ValidationError):
            WhatsAppContact(
                jid="invalid-jid",
                name_in_address_book="John Doe",
                profile_name="John D.",
                is_whatsapp_user=True
            )
    
    def test_empty_name_fields(self):
        """Test empty name fields."""
        with self.assertRaises(ValidationError):
            WhatsAppContact(
                jid="19876543210@s.whatsapp.net",
                name_in_address_book="",
                profile_name="Jane D.",
                is_whatsapp_user=True
            )


class TestPhoneEndpointModel(unittest.TestCase):
    """Test cases for PhoneEndpoint model."""
    
    def test_valid_phone_endpoint(self):
        """Test valid phone endpoint."""
        endpoint = PhoneEndpoint(
            endpoint_type="PHONE_NUMBER",
            endpoint_value="+14155552671",
            endpoint_label="mobile"
        )
        self.assertEqual(endpoint.endpoint_type, "PHONE_NUMBER")
        self.assertEqual(endpoint.endpoint_value, "+14155552671")
        self.assertEqual(endpoint.endpoint_label, "mobile")
    
    def test_invalid_endpoint_type(self):
        """Test invalid endpoint type."""
        with self.assertRaises(ValidationError):
            PhoneEndpoint(
                endpoint_type="EMAIL",
                endpoint_value="+14155552671",
                endpoint_label="mobile"
            )
    
    def test_empty_endpoint_fields(self):
        """Test empty endpoint fields."""
        with self.assertRaises(ValidationError):
            PhoneEndpoint(
                endpoint_type="PHONE_NUMBER",
                endpoint_value="",
                endpoint_label="mobile"
            )


class TestPhoneContactModel(unittest.TestCase):
    """Test cases for PhoneContact model."""
    
    def test_valid_phone_contact(self):
        """Test valid phone contact."""
        endpoints = [
            PhoneEndpoint(
                endpoint_type="PHONE_NUMBER",
                endpoint_value="+14155552671",
                endpoint_label="mobile"
            )
        ]
        phone_contact = PhoneContact(
            contact_id="contact_123",
            contact_name="John Doe",
            recipient_type="CONTACT",
            contact_photo_url="https://example.com/photo.jpg",
            contact_endpoints=endpoints
        )
        self.assertEqual(phone_contact.contact_id, "contact_123")
        self.assertEqual(phone_contact.contact_name, "John Doe")
        self.assertEqual(phone_contact.recipient_type, "CONTACT")
        self.assertEqual(phone_contact.contact_photo_url, "https://example.com/photo.jpg")
        self.assertEqual(len(phone_contact.contact_endpoints), 1)
    
    def test_phone_contact_without_photo(self):
        """Test phone contact without photo URL."""
        phone_contact = PhoneContact(
            contact_id="contact_123",
            contact_name="John Doe",
            recipient_type="CONTACT",
            contact_endpoints=[]
        )
        self.assertIsNone(phone_contact.contact_photo_url)
        self.assertEqual(len(phone_contact.contact_endpoints), 0)
    
    def test_invalid_recipient_type(self):
        """Test invalid recipient type."""
        with self.assertRaises(ValidationError):
            PhoneContact(
                contact_id="contact_123",
                contact_name="John Doe",
                recipient_type="GROUP",
                contact_endpoints=[]
            )
    
    def test_invalid_photo_url(self):
        """Test invalid photo URL."""
        with self.assertRaises(ValidationError):
            PhoneContact(
                contact_id="contact_123",
                contact_name="John Doe",
                recipient_type="CONTACT",
                contact_photo_url="invalid-url",
                contact_endpoints=[]
            )


class TestContactModel(unittest.TestCase):
    """Test cases for Contact model."""
    
    def test_valid_contact(self):
        """Test valid contact."""
        names = [Name(givenName="John", familyName="Doe")]
        email_addresses = [EmailAddress(value="john.doe@example.com", type="work", primary=True)]
        phone_numbers = [PhoneNumber(value="+14155552671", type="mobile", primary=True)]
        organizations = [Organization(name="Google", title="Software Engineer", primary=True)]
        
        contact = Contact(
            resourceName="people/c123",
            etag="etag123",
            names=names,
            emailAddresses=email_addresses,
            phoneNumbers=phone_numbers,
            organizations=organizations,
            isWorkspaceUser=False
        )
        
        self.assertEqual(contact.resource_name, "people/c123")
        self.assertEqual(contact.etag, "etag123")
        self.assertEqual(len(contact.names), 1)
        self.assertEqual(len(contact.email_addresses), 1)
        self.assertEqual(len(contact.phone_numbers), 1)
        self.assertEqual(len(contact.organizations), 1)
        self.assertFalse(contact.is_workspace_user)
    
    def test_contact_with_minimal_fields(self):
        """Test contact with minimal required fields."""
        contact = Contact(
            resourceName="people/c123",
            etag="etag123"
        )
        
        self.assertEqual(contact.resource_name, "people/c123")
        self.assertEqual(contact.etag, "etag123")
        self.assertIsNone(contact.names)
        self.assertIsNone(contact.email_addresses)
        self.assertIsNone(contact.phone_numbers)
        self.assertIsNone(contact.organizations)
        self.assertIsNone(contact.is_workspace_user)
    
    def test_contact_validation(self):
        """Test contact field validation."""
        # Invalid resource name
        with self.assertRaises(ValidationError):
            Contact(
                resourceName="invalid",
                etag="etag123",
                names=[Name(givenName="John")],
                isWorkspaceUser=False
            )
        
        # Empty etag
        with self.assertRaises(ValidationError):
            Contact(
                resourceName="people/c123",
                etag="",
                names=[Name(givenName="John")],
                isWorkspaceUser=False
            )
        
        # Missing required fields
        with self.assertRaises(ValidationError):
            Contact(
                etag="etag123"
            )


class TestContactsDBModel(unittest.TestCase):
    """Test cases for ContactsDB model."""
    
    def test_empty_database(self):
        """Test empty database."""
        db = ContactsDB()
        self.assertEqual(len(db.myContacts), 0)
        self.assertEqual(len(db.otherContacts), 0)
        self.assertEqual(len(db.directory), 0)
    
    def test_database_with_contacts(self):
        """Test database with contacts."""
        contact1 = Contact(
            resourceName="people/c1",
            etag="etag1",
            names=[Name(givenName="John")],
            isWorkspaceUser=False
        )
        contact2 = Contact(
            resourceName="people/c2",
            etag="etag2",
            names=[Name(givenName="Jane")],
            isWorkspaceUser=True
        )
        
        db = ContactsDB(
            myContacts={"people/c1": contact1},
            otherContacts={},
            directory={"people/c2": contact2}
        )
        
        self.assertEqual(len(db.myContacts), 1)
        self.assertEqual(len(db.otherContacts), 0)
        self.assertEqual(len(db.directory), 1)
    
    
    
    
    
    


if __name__ == "__main__":
    unittest.main()
