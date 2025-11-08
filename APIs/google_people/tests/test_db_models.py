"""
Comprehensive tests for Google People Pydantic models.

This module tests all the Pydantic models defined in db_models.py to ensure
they correctly validate data according to the actual Google People API structure
and the service implementation.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from typing import Dict, Any

from APIs.google_people.SimulationEngine.db_models import (
    SourceType, FieldMetadata, Name, EmailAddress, EmailType, PhoneNumber, PhoneType,
    Address, AddressType, Organization, OrganizationType, Birthday, Photo, Url, UrlType,
    UserDefined, Person, ContactGroup, ContactGroupType, OtherContact, DirectoryPerson,
    GooglePeopleDB
)


class TestSourceType:
    """Test SourceType enum."""
    
    def test_source_type_values(self):
        """Test that SourceType has correct values."""
        assert SourceType.SOURCE_TYPE_UNSPECIFIED == "SOURCE_TYPE_UNSPECIFIED"
        assert SourceType.ACCOUNT == "ACCOUNT"
        assert SourceType.PROFILE == "PROFILE"
        assert SourceType.DOMAIN_PROFILE == "DOMAIN_PROFILE"
        assert SourceType.CONTACT == "CONTACT"
        assert SourceType.OTHER_CONTACT == "OTHER_CONTACT"
        assert SourceType.DOMAIN_CONTACT == "DOMAIN_CONTACT"
        assert SourceType.DIRECTORY == "DIRECTORY"


class TestFieldMetadata:
    """Test FieldMetadata model."""
    
    def test_field_metadata_minimal(self):
        """Test FieldMetadata with minimal data."""
        metadata = FieldMetadata()
        assert metadata.primary is None
        assert metadata.source is None
        assert metadata.source_primary is None
        assert metadata.verified is None
    
    def test_field_metadata_complete(self):
        """Test FieldMetadata with complete data."""
        metadata = FieldMetadata(
            primary=True,
            source={"type": "PROFILE", "id": "test_id"},
            source_primary=True,
            verified=True
        )
        assert metadata.primary is True
        assert metadata.source == {"type": "PROFILE", "id": "test_id"}
        assert metadata.source_primary is True
        assert metadata.verified is True
    
    def test_field_metadata_invalid_source(self):
        """Test FieldMetadata with invalid source type."""
        with pytest.raises(ValidationError):
            FieldMetadata(source="invalid_source")


class TestName:
    """Test Name model."""
    
    def test_name_minimal(self):
        """Test Name with minimal data."""
        name = Name()
        assert name.display_name is None
        assert name.family_name is None
        assert name.given_name is None
    
    def test_name_complete(self):
        """Test Name with complete data."""
        name = Name(
            displayName="John Doe",
            familyName="Doe",
            givenName="John",
            middleName="Michael",
            honorificPrefix="Dr.",
            honorificSuffix="Jr."
        )
        assert name.display_name == "John Doe"
        assert name.family_name == "Doe"
        assert name.given_name == "John"
        assert name.middle_name == "Michael"
        assert name.honorific_prefix == "Dr."
        assert name.honorific_suffix == "Jr."
    
    def test_name_whitespace_stripping(self):
        """Test that whitespace is stripped from name fields."""
        name = Name(
            displayName="  John Doe  ",
            familyName="  Doe  ",
            givenName="  John  "
        )
        assert name.display_name == "John Doe"
        assert name.family_name == "Doe"
        assert name.given_name == "John"
    
    def test_name_with_metadata(self):
        """Test Name with metadata."""
        metadata = FieldMetadata(primary=True)
        name = Name(
            metadata=metadata,
            displayName="John Doe"
        )
        assert name.metadata.primary is True
        assert name.display_name == "John Doe"


class TestEmailAddress:
    """Test EmailAddress model."""
    
    def test_email_address_minimal(self):
        """Test EmailAddress with minimal required data."""
        email = EmailAddress(value="test@example.com")
        assert email.value == "test@example.com"
        assert email.type is None
        assert email.display_name is None
        assert email.formatted_type is None
    
    def test_email_address_complete(self):
        """Test EmailAddress with complete data."""
        email = EmailAddress(
            value="john.doe@example.com",
            type=EmailType.WORK,
            displayName="John Doe",
            formattedType="Work"
        )
        assert email.value == "john.doe@example.com"
        assert email.type == EmailType.WORK
        assert email.display_name == "John Doe"
        assert email.formatted_type == "Work"
    
    def test_email_address_invalid_email(self):
        """Test EmailAddress with invalid email format."""
        with pytest.raises(ValidationError):
            EmailAddress(value="invalid-email")
    
    def test_email_address_whitespace_stripping(self):
        """Test that whitespace is stripped from email fields."""
        email = EmailAddress(
            value="  test@example.com  ",
            displayName="  John Doe  ",
            formattedType="  Work  "
        )
        assert email.value == "test@example.com"
        assert email.display_name == "John Doe"
        assert email.formatted_type == "Work"


class TestPhoneNumber:
    """Test PhoneNumber model."""
    
    def test_phone_number_minimal(self):
        """Test PhoneNumber with minimal required data."""
        phone = PhoneNumber(value="+1234567890")
        assert phone.value == "+1234567890"
        assert phone.type is None
        assert phone.formatted_type is None
        assert phone.canonical_form is None
    
    def test_phone_number_complete(self):
        """Test PhoneNumber with complete data."""
        phone = PhoneNumber(
            value="+1234567890",
            type=PhoneType.MOBILE,
            formattedType="Mobile",
            canonicalForm="+1234567890"
        )
        assert phone.value == "+1234567890"
        assert phone.type == PhoneType.MOBILE
        assert phone.formatted_type == "Mobile"
        assert phone.canonical_form == "+1234567890"
    
    def test_phone_number_format_cleaning(self):
        """Test that phone number format is cleaned."""
        phone = PhoneNumber(value="+1 (234) 567-8900")
        assert phone.value == "+12345678900"
    
    def test_phone_number_invalid_format(self):
        """Test PhoneNumber with invalid format."""
        with pytest.raises(ValidationError):
            PhoneNumber(value="invalid-phone")
    
    def test_phone_number_empty_value(self):
        """Test PhoneNumber with empty value."""
        with pytest.raises(ValidationError):
            PhoneNumber(value="")


class TestAddress:
    """Test Address model."""
    
    def test_address_minimal(self):
        """Test Address with minimal data."""
        address = Address()
        assert address.type is None
        assert address.formatted_value is None
        assert address.street_address is None
        assert address.city is None
    
    def test_address_complete(self):
        """Test Address with complete data."""
        address = Address(
            type=AddressType.HOME,
            formattedValue="123 Main St, Anytown, NY 12345",
            streetAddress="123 Main St",
            city="Anytown",
            region="NY",
            postalCode="12345",
            country="United States",
            countryCode="US"
        )
        assert address.type == AddressType.HOME
        assert address.formatted_value == "123 Main St, Anytown, NY 12345"
        assert address.street_address == "123 Main St"
        assert address.city == "Anytown"
        assert address.region == "NY"
        assert address.postal_code == "12345"
        assert address.country == "United States"
        assert address.country_code == "US"
    
    def test_address_invalid_country_code(self):
        """Test Address with invalid country code."""
        with pytest.raises(ValidationError):
            Address(countryCode="INVALID")
    
    def test_address_whitespace_stripping(self):
        """Test that whitespace is stripped from address fields."""
        address = Address(
            formattedValue="  123 Main St  ",
            streetAddress="  123 Main St  ",
            city="  Anytown  "
        )
        assert address.formatted_value == "123 Main St"
        assert address.street_address == "123 Main St"
        assert address.city == "Anytown"


class TestOrganization:
    """Test Organization model."""
    
    def test_organization_minimal(self):
        """Test Organization with minimal data."""
        org = Organization()
        assert org.type is None
        assert org.name is None
        assert org.title is None
        assert org.department is None
    
    def test_organization_complete(self):
        """Test Organization with complete data."""
        org = Organization(
            type=OrganizationType.WORK,
            name="Acme Corp",
            title="Software Engineer",
            department="Engineering",
            location="San Francisco, CA",
            jobDescription="Develop software solutions",
            symbol="ACME",
            domain="acme.com",
            costCenter="ENG001"
        )
        assert org.type == OrganizationType.WORK
        assert org.name == "Acme Corp"
        assert org.title == "Software Engineer"
        assert org.department == "Engineering"
        assert org.location == "San Francisco, CA"
        assert org.job_description == "Develop software solutions"
        assert org.symbol == "ACME"
        assert org.domain == "acme.com"
        assert org.cost_center == "ENG001"
    
    def test_organization_whitespace_stripping(self):
        """Test that whitespace is stripped from organization fields."""
        org = Organization(
            name="  Acme Corp  ",
            title="  Software Engineer  ",
            department="  Engineering  "
        )
        assert org.name == "Acme Corp"
        assert org.title == "Software Engineer"
        assert org.department == "Engineering"


class TestBirthday:
    """Test Birthday model."""
    
    def test_birthday_minimal(self):
        """Test Birthday with minimal data."""
        birthday = Birthday()
        assert birthday.date is None
        assert birthday.text is None
    
    def test_birthday_with_date(self):
        """Test Birthday with date components."""
        birthday = Birthday(
            date={"year": 1990, "month": 5, "day": 15},
            text="May 15, 1990"
        )
        assert birthday.date == {"year": 1990, "month": 5, "day": 15}
        assert birthday.text == "May 15, 1990"
    
    def test_birthday_invalid_date(self):
        """Test Birthday with invalid date structure."""
        with pytest.raises(ValidationError):
            Birthday(date={"year": 1990, "month": 5})  # Missing day
    
    def test_birthday_whitespace_stripping(self):
        """Test that whitespace is stripped from birthday text."""
        birthday = Birthday(text="  May 15, 1990  ")
        assert birthday.text == "May 15, 1990"


class TestPhoto:
    """Test Photo model."""
    
    def test_photo_minimal(self):
        """Test Photo with minimal data."""
        photo = Photo()
        assert photo.url is None
        assert photo.default is None
    
    def test_photo_complete(self):
        """Test Photo with complete data."""
        photo = Photo(
            url="https://example.com/photo.jpg",
            default=True
        )
        assert str(photo.url) == "https://example.com/photo.jpg"
        assert photo.default is True
    
    def test_photo_invalid_url(self):
        """Test Photo with invalid URL."""
        with pytest.raises(ValidationError):
            Photo(url="invalid-url")


class TestUrl:
    """Test Url model."""
    
    def test_url_minimal(self):
        """Test Url with minimal required data."""
        url = Url(value="https://example.com")
        assert str(url.value) == "https://example.com/"
        assert url.type is None
        assert url.formatted_type is None
    
    def test_url_complete(self):
        """Test Url with complete data."""
        url = Url(
            value="https://example.com",
            type=UrlType.HOME,
            formattedType="Home Page"
        )
        assert str(url.value) == "https://example.com/"
        assert url.type == UrlType.HOME
        assert url.formatted_type == "Home Page"
    
    def test_url_invalid_value(self):
        """Test Url with invalid URL."""
        with pytest.raises(ValidationError):
            Url(value="invalid-url")
    
    def test_url_whitespace_stripping(self):
        """Test that whitespace is stripped from URL fields."""
        url = Url(
            value="https://example.com",
            formattedType="  Home Page  "
        )
        assert url.formatted_type == "Home Page"


class TestUserDefined:
    """Test UserDefined model."""
    
    def test_user_defined_minimal(self):
        """Test UserDefined with minimal required data."""
        field = UserDefined(key="custom_field", value="custom_value")
        assert field.key == "custom_field"
        assert field.value == "custom_value"
    
    def test_user_defined_whitespace_stripping(self):
        """Test that whitespace is stripped from user defined fields."""
        field = UserDefined(
            key="  custom_field  ",
            value="  custom_value  "
        )
        assert field.key == "custom_field"
        assert field.value == "custom_value"


class TestPerson:
    """Test Person model."""
    
    def test_person_minimal(self):
        """Test Person with minimal required data."""
        person = Person(
            resourceName="people/123",
            etag="etag_123",
            names=[Name(givenName="John", familyName="Doe")],
            emailAddresses=[EmailAddress(value="john@example.com")],
            phoneNumbers=[PhoneNumber(value="+1234567890")],
            organizations=[Organization(name="Acme Corp")],
            created="2023-01-01T00:00:00Z",
            updated="2023-01-01T00:00:00Z"
        )
        assert person.resource_name == "people/123"
        assert person.etag == "etag_123"
        assert len(person.names) == 1
        assert len(person.email_addresses) == 1
        assert len(person.phone_numbers) == 1
        assert len(person.organizations) == 1
        assert person.created == "2023-01-01T00:00:00Z"
        assert person.updated == "2023-01-01T00:00:00Z"
    
    def test_person_invalid_resource_name(self):
        """Test Person with invalid resource name."""
        with pytest.raises(ValidationError):
            Person(
                resourceName="invalid_resource",
                etag="etag_123",
                names=[Name(givenName="John", familyName="Doe")],
                emailAddresses=[EmailAddress(value="john@example.com")],
                phoneNumbers=[PhoneNumber(value="+1234567890")],
                organizations=[Organization(name="Acme Corp")],
                created="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z"
            )
    
    def test_person_invalid_timestamp(self):
        """Test Person with invalid timestamp."""
        with pytest.raises(ValidationError):
            Person(
                resourceName="people/123",
                etag="etag_123",
                names=[Name(givenName="John", familyName="Doe")],
                emailAddresses=[EmailAddress(value="john@example.com")],
                phoneNumbers=[PhoneNumber(value="+1234567890")],
                organizations=[Organization(name="Acme Corp")],
                created="invalid-timestamp",
                updated="2023-01-01T00:00:00Z"
            )


class TestContactGroup:
    """Test ContactGroup model."""
    
    def test_contact_group_minimal(self):
        """Test ContactGroup with minimal required data."""
        group = ContactGroup(
            resourceName="contactGroups/123",
            etag="etag_123",
            name="Test Group",
            groupType="USER_CONTACT_GROUP",
            memberCount=0,
            memberResourceNames=[],
            created="2023-01-01T00:00:00Z",
            updated="2023-01-01T00:00:00Z"
        )
        assert group.resource_name == "contactGroups/123"
        assert group.etag == "etag_123"
        assert group.name == "Test Group"
        assert group.group_type == "USER_CONTACT_GROUP"
        assert group.member_count == 0
        assert group.member_resource_names == []
        assert group.created == "2023-01-01T00:00:00Z"
        assert group.updated == "2023-01-01T00:00:00Z"
    
    def test_contact_group_invalid_resource_name(self):
        """Test ContactGroup with invalid resource name."""
        with pytest.raises(ValidationError):
            ContactGroup(
                resourceName="invalid_resource",
                etag="etag_123",
                name="Test Group",
                groupType="USER_CONTACT_GROUP",
                memberCount=0,
                memberResourceNames=[],
                created="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z"
            )
    
    def test_contact_group_invalid_member_resource_names(self):
        """Test ContactGroup with invalid member resource names."""
        with pytest.raises(ValidationError):
            ContactGroup(
                resourceName="contactGroups/123",
                etag="etag_123",
                name="Test Group",
                groupType="USER_CONTACT_GROUP",
                memberCount=1,
                memberResourceNames=["invalid_member"],
                created="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z"
            )


class TestOtherContact:
    """Test OtherContact model."""
    
    def test_other_contact_minimal(self):
        """Test OtherContact with minimal required data."""
        contact = OtherContact(
            resourceName="otherContacts/123",
            etag="etag_123",
            names=[Name(givenName="John", familyName="Doe")],
            emailAddresses=[EmailAddress(value="john@example.com")],
            phoneNumbers=[PhoneNumber(value="+1234567890")],
            organizations=[Organization(name="Acme Corp")],
            created="2023-01-01T00:00:00Z",
            updated="2023-01-01T00:00:00Z"
        )
        assert contact.resource_name == "otherContacts/123"
        assert contact.etag == "etag_123"
        assert len(contact.names) == 1
        assert len(contact.email_addresses) == 1
        assert len(contact.phone_numbers) == 1
        assert len(contact.organizations) == 1
        assert contact.created == "2023-01-01T00:00:00Z"
        assert contact.updated == "2023-01-01T00:00:00Z"
    
    def test_other_contact_invalid_resource_name(self):
        """Test OtherContact with invalid resource name."""
        with pytest.raises(ValidationError):
            OtherContact(
                resourceName="invalid_resource",
                etag="etag_123",
                names=[Name(givenName="John", familyName="Doe")],
                emailAddresses=[EmailAddress(value="john@example.com")],
                phoneNumbers=[PhoneNumber(value="+1234567890")],
                organizations=[Organization(name="Acme Corp")],
                created="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z"
            )


class TestDirectoryPerson:
    """Test DirectoryPerson model."""
    
    def test_directory_person_minimal(self):
        """Test DirectoryPerson with minimal required data."""
        person = DirectoryPerson(
            resourceName="directoryPeople/123",
            etag="etag_123",
            names=[Name(givenName="John", familyName="Doe")],
            emailAddresses=[EmailAddress(value="john@example.com")],
            phoneNumbers=[PhoneNumber(value="+1234567890")],
            organizations=[Organization(name="Acme Corp")],
            created="2023-01-01T00:00:00Z",
            updated="2023-01-01T00:00:00Z"
        )
        assert person.resource_name == "directoryPeople/123"
        assert person.etag == "etag_123"
        assert len(person.names) == 1
        assert len(person.email_addresses) == 1
        assert len(person.phone_numbers) == 1
        assert len(person.organizations) == 1
    
    def test_directory_person_invalid_resource_name(self):
        """Test DirectoryPerson with invalid resource name."""
        with pytest.raises(ValidationError):
            DirectoryPerson(
                resourceName="invalid_resource",
                etag="etag_123",
                names=[Name(givenName="John", familyName="Doe")],
                emailAddresses=[EmailAddress(value="john@example.com")],
                phoneNumbers=[PhoneNumber(value="+1234567890")],
                organizations=[Organization(name="Acme Corp")]
            )


class TestGooglePeopleDB:
    """Test GooglePeopleDB model."""
    
    def test_google_people_db_empty(self):
        """Test GooglePeopleDB with empty data."""
        db = GooglePeopleDB()
        assert db.people == {}
        assert db.contact_groups == {}
        assert db.other_contacts == {}
        assert db.directory_people == {}
    
    def test_google_people_db_with_data(self):
        """Test GooglePeopleDB with data."""
        person = Person(
            resourceName="people/123",
            etag="etag_123",
            names=[Name(givenName="John", familyName="Doe")],
            emailAddresses=[EmailAddress(value="john@example.com")],
            phoneNumbers=[PhoneNumber(value="+1234567890")],
            organizations=[Organization(name="Acme Corp")],
            created="2023-01-01T00:00:00Z",
            updated="2023-01-01T00:00:00Z"
        )
        
        db = GooglePeopleDB(people={"people/123": person})
        assert len(db.people) == 1
        assert "people/123" in db.people
        assert db.people["people/123"].resource_name == "people/123" 

class TestIntegrationWithActualData:
    """Test integration with actual database data structure."""
    
    def test_person_from_actual_data(self):
        """Test creating a Person from actual database data structure."""
        # This simulates the actual data structure from GooglePeopleDefaultDB.json
        actual_data = {
            "resourceName": "people/me",
            "etag": "etag_me_123",
            "names": [
                {
                    "metadata": {
                        "primary": True,
                        "source": {
                            "type": "PROFILE",
                            "id": "profile_id_123"
                        }
                    },
                    "displayName": "John Doe",
                    "familyName": "Doe",
                    "givenName": "John"
                }
            ],
            "emailAddresses": [
                {
                    "metadata": {
                        "primary": True,
                        "source": {
                            "type": "PROFILE",
                            "id": "profile_id_123"
                        }
                    },
                    "value": "john.doe@gmail.com",
                    "type": "work"
                }
            ],
            "phoneNumbers": [
                {
                    "metadata": {
                        "primary": True,
                        "source": {
                            "type": "PROFILE",
                            "id": "profile_id_123"
                        }
                    },
                    "value": "+15551234567",
                    "type": "mobile"
                }
            ],
            "organizations": [
                {
                    "metadata": {
                        "primary": True,
                        "source": {
                            "type": "PROFILE",
                            "id": "profile_id_123"
                        }
                    },
                    "name": "Google",
                    "title": "Software Engineer",
                    "type": "work"
                }
            ],
            "created": "2023-01-15T10:30:00Z",
            "updated": "2024-01-15T14:20:00Z"
        }
        
        # This should work without validation errors
        person = Person(**actual_data)
        assert person.resource_name == "people/me"
        assert person.etag == "etag_me_123"
        assert len(person.names) == 1
        assert person.names[0].display_name == "John Doe"
        assert person.names[0].family_name == "Doe"
        assert person.names[0].given_name == "John"
        assert len(person.email_addresses) == 1
        assert person.email_addresses[0].value == "john.doe@gmail.com"
        assert person.email_addresses[0].type == EmailType.WORK
        assert len(person.phone_numbers) == 1
        assert person.phone_numbers[0].value == "+15551234567"
        assert person.phone_numbers[0].type == PhoneType.MOBILE
        assert len(person.organizations) == 1
        assert person.organizations[0].name == "Google"
        assert person.organizations[0].title == "Software Engineer"
        assert person.organizations[0].type == OrganizationType.WORK
        assert person.created == "2023-01-15T10:30:00Z"
        assert person.updated == "2024-01-15T14:20:00Z"
    
    def test_contact_group_from_actual_data(self):
        """Test creating a ContactGroup from actual database data structure."""
        actual_data = {
            "resourceName": "contactGroups/family",
            "etag": "etag_family_group",
            "name": "Family",
            "groupType": "USER_CONTACT_GROUP",
            "memberResourceNames": ["people/contact_001"],
            "memberCount": 1,
            "created": "2023-01-20T08:00:00Z",
            "updated": "2024-01-10T16:30:00Z"
        }
        
        # This should work without validation errors
        group = ContactGroup(**actual_data)
        assert group.resource_name == "contactGroups/family"
        assert group.etag == "etag_family_group"
        assert group.name == "Family"
        assert group.group_type == "USER_CONTACT_GROUP"
        assert group.member_resource_names == ["people/contact_001"]
        assert group.member_count == 1
        assert group.created == "2023-01-20T08:00:00Z"
        assert group.updated == "2024-01-10T16:30:00Z"


if __name__ == "__main__":
    pytest.main([__file__])
