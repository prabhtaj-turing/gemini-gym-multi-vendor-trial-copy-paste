from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, HttpUrl, EmailStr
import re
import uuid
from datetime import datetime, timezone
from enum import Enum


class SourceType(str, Enum):
    """Source types for metadata.
    
    Based on the actual source types found in GooglePeopleDefaultDB.json
    and used in the service functions (people.py).
    """
    SOURCE_TYPE_UNSPECIFIED = "SOURCE_TYPE_UNSPECIFIED"
    ACCOUNT = "ACCOUNT"
    PROFILE = "PROFILE"
    DOMAIN_PROFILE = "DOMAIN_PROFILE"
    CONTACT = "CONTACT"
    OTHER_CONTACT = "OTHER_CONTACT"
    DOMAIN_CONTACT = "DOMAIN_CONTACT"
    DIRECTORY = "DIRECTORY"  # Alias for DOMAIN_CONTACT in database


class FieldMetadata(BaseModel):
    """Metadata for a field."""
    primary: Optional[bool] = Field(None, description="Whether this is the primary field")
    source: Optional[Dict[str, Any]] = Field(None, description="Source information")
    source_primary: Optional[bool] = Field(None, description="Whether the source is primary")
    verified: Optional[bool] = Field(None, description="Whether the field is verified")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        """Validate source structure."""
        if v is not None and not isinstance(v, dict):
            raise ValueError('Source must be a dictionary')
        return v


class Name(BaseModel):
    """A person's name."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the name")
    display_name: Optional[str] = Field(None, alias="displayName", max_length=100, description="Display name")
    display_name_last_first: Optional[str] = Field(None, alias="displayNameLastFirst", max_length=100, description="Last first display name")
    family_name: Optional[str] = Field(None, alias="familyName", max_length=100, description="Family name")
    given_name: Optional[str] = Field(None, alias="givenName", max_length=100, description="Given name")
    honorific_prefix: Optional[str] = Field(None, alias="honorificPrefix", max_length=20, description="Honorific prefix")
    honorific_suffix: Optional[str] = Field(None, alias="honorificSuffix", max_length=20, description="Honorific suffix")
    middle_name: Optional[str] = Field(None, alias="middleName", max_length=100, description="Middle name")
    phonetic_family_name: Optional[str] = Field(None, alias="phoneticFamilyName", max_length=100, description="Phonetic family name")
    phonetic_given_name: Optional[str] = Field(None, alias="phoneticGivenName", max_length=100, description="Phonetic given name")
    phonetic_honorific_prefix: Optional[str] = Field(None, alias="phoneticHonorificPrefix", max_length=20, description="Phonetic honorific prefix")
    phonetic_honorific_suffix: Optional[str] = Field(None, alias="phoneticHonorificSuffix", max_length=20, description="Phonetic honorific suffix")
    phonetic_middle_name: Optional[str] = Field(None, alias="phoneticMiddleName", max_length=100, description="Phonetic middle name")
    unstructured_name: Optional[str] = Field(None, alias="unstructuredName", max_length=200, description="Unstructured name")

    @field_validator(
        "display_name", "display_name_last_first", "family_name", "given_name",
        "honorific_prefix", "honorific_suffix", "middle_name",
        "phonetic_family_name", "phonetic_given_name", "phonetic_honorific_prefix",
        "phonetic_honorific_suffix", "phonetic_middle_name", "unstructured_name"
    )
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class EmailType(str, Enum):
    """Email address types."""
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class EmailAddress(BaseModel):
    """A person's email address."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the email")
    value: EmailStr = Field(..., description="The email address")
    type: Optional[EmailType] = Field(None, description="The type of email address")
    display_name: Optional[str] = Field(None, alias="displayName", max_length=100, description="Display name")
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100, description="Formatted type")

    @field_validator("display_name", "formatted_type")
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class PhoneType(str, Enum):
    """Phone number types."""
    HOME = "home"
    WORK = "work"
    MOBILE = "mobile"
    HOME_FAX = "homeFax"
    WORK_FAX = "workFax"
    OTHER_FAX = "otherFax"
    PAGER = "pager"
    WORK_MOBILE = "workMobile"
    WORK_PAGER = "workPager"
    MAIN = "main"
    GOOGLE_VOICE = "googleVoice"
    OTHER = "other"


class PhoneNumber(BaseModel):
    """A person's phone number."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the phone number")
    value: str = Field(..., description="The phone number", max_length=50)
    type: Optional[PhoneType] = Field(None, description="The type of phone number")
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100, description="Formatted type")
    canonical_form: Optional[str] = Field(None, alias="canonicalForm", max_length=50, description="Canonical form")

    @field_validator("value")
    @classmethod
    def validate_phone_value(cls, v):
        """Validate phone number format."""
        if not v or not v.strip():
            raise ValueError('Phone number value cannot be empty')
        # More flexible phone number pattern that accepts various formats
        # Remove common separators and spaces
        cleaned = re.sub(r'[-\s\(\)\.]', '', v.strip())
        # Basic international phone number pattern
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, cleaned):
            raise ValueError('Invalid phone number format (expected E.164 or similar)')
        return cleaned

    @field_validator("formatted_type", "canonical_form")
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class AddressType(str, Enum):
    """Address types."""
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class Address(BaseModel):
    """A person's address."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the address")
    type: Optional[AddressType] = Field(None, description="The type of address")
    formatted_value: Optional[str] = Field(None, alias="formattedValue", max_length=500, description="Formatted value")
    street_address: Optional[str] = Field(None, alias="streetAddress", max_length=200, description="Street address")
    extended_address: Optional[str] = Field(None, alias="extendedAddress", max_length=200, description="Extended address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    region: Optional[str] = Field(None, max_length=100, description="Region")
    postal_code: Optional[str] = Field(None, alias="postalCode", max_length=20, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    country_code: Optional[str] = Field(None, alias="countryCode", max_length=10, description="Country code")
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100, description="Formatted type")

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v):
        if v is not None and not re.fullmatch(r'^[A-Z]{2}$', v):
            raise ValueError('Invalid country code format (expected two uppercase letters)')
        return v

    @field_validator(
        "formatted_value", "street_address", "extended_address", "city",
        "region", "postal_code", "country", "formatted_type"
    )
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class OrganizationType(str, Enum):
    """Organization types."""
    WORK = "work"
    SCHOOL = "school"
    OTHER = "other"


class Organization(BaseModel):
    """A person's organization."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the organization")
    type: Optional[OrganizationType] = Field(None, description="The type of organization")
    name: Optional[str] = Field(None, max_length=200, description="Organization name")
    title: Optional[str] = Field(None, max_length=200, description="Job title")
    department: Optional[str] = Field(None, max_length=200, description="Department")
    location: Optional[str] = Field(None, max_length=200, description="Location")
    job_description: Optional[str] = Field(None, alias="jobDescription", max_length=500, description="Job description")
    symbol: Optional[str] = Field(None, max_length=100, description="Symbol")
    domain: Optional[str] = Field(None, max_length=100, description="Domain")
    cost_center: Optional[str] = Field(None, alias="costCenter", max_length=100, description="Cost center")
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100, description="Formatted type")

    @field_validator(
        "name", "title", "department", "location", "job_description",
        "symbol", "domain", "cost_center", "formatted_type"
    )
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class Birthday(BaseModel):
    """A person's birthday."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the birthday")
    date: Optional[Dict[str, int]] = Field(None, description="Date components (year, month, day)")
    text: Optional[str] = Field(None, max_length=100, description="Text representation of birthday")

    @field_validator("date")
    @classmethod
    def validate_date_components(cls, v):
        if v:
            if not all(k in v for k in ["year", "month", "day"]):
                raise ValueError("Date dictionary must contain 'year', 'month', and 'day' keys")
        return v

    @field_validator("text")
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class Photo(BaseModel):
    """A person's photo."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the photo")
    url: Optional[HttpUrl] = Field(None, description="The URL of the photo")
    default: Optional[bool] = Field(None, description="Whether this is the default photo")


class UrlType(str, Enum):
    """URL types."""
    HOME = "home"
    WORK = "work"
    BLOG = "blog"
    PROFILE = "profile"
    HOME_PAGE = "homePage"
    FTP = "ftp"
    RESERVED = "reserved"
    OTHER = "other"


class Url(BaseModel):
    """A person's URL."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the URL")
    value: HttpUrl = Field(..., description="The URL")
    type: Optional[UrlType] = Field(None, description="The type of URL")
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100, description="Formatted type")

    @field_validator("formatted_type")
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class UserDefined(BaseModel):
    """A user-defined field."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the field")
    key: str = Field(..., max_length=100, description="Key for the user-defined field")
    value: str = Field(..., max_length=500, description="Value for the user-defined field")

    @field_validator("key", "value")
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v


class Person(BaseModel):
    """A person in the Google People API."""
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    names: List[Name] = Field(default_factory=list, description="The person's names")
    email_addresses: List[EmailAddress] = Field(default_factory=list, alias="emailAddresses", description="The person's email addresses")
    phone_numbers: List[PhoneNumber] = Field(default_factory=list, alias="phoneNumbers", description="The person's phone numbers")
    organizations: List[Organization] = Field(default_factory=list, description="The person's organizations")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")
    # Fields with default empty lists (API uses .get(field, []))
    addresses: List[Address] = Field(default_factory=list, description="The person's addresses")
    birthdays: List[Birthday] = Field(default_factory=list, description="The person's birthdays")
    photos: List[Photo] = Field(default_factory=list, description="The person's photos")
    urls: List[Url] = Field(default_factory=list, description="The person's URLs")
    user_defined: List[UserDefined] = Field(default_factory=list, alias="userDefined", description="The person's user-defined fields")

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Resource name cannot be empty')
        if not v.strip().startswith('people/'):
            raise ValueError('Resource name must start with "people/"')
        return v.strip()

    @field_validator('etag')
    @classmethod
    def validate_etag(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('ETag cannot be empty')
        return v.strip()

    @field_validator('created', 'updated')
    @classmethod
    def validate_timestamp(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Timestamp cannot be empty')
        try:
            datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
            return v.strip()
        except ValueError:
            raise ValueError('Invalid ISO 8601 timestamp format')


class ContactGroupType(str, Enum):
    """Contact group types."""
    USER_CONTACT_GROUP = "USER_CONTACT_GROUP"
    SYSTEM_CONTACT_GROUP = "SYSTEM_CONTACT_GROUP"


class ContactGroup(BaseModel):
    """A contact group in the Google People API."""
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    name: Optional[str] = Field(None, max_length=200, description="The name of the contact group")
    group_type: Optional[str] = Field(None, alias="groupType", max_length=50, description="The group type")
    member_count: int = Field(default=0, alias="memberCount", ge=0, description="Number of members")
    member_resource_names: List[str] = Field(default_factory=list, alias="memberResourceNames", description="Resource names of group members")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Resource name cannot be empty')
        if not v.strip().startswith('contactGroups/'):
            raise ValueError('Resource name must start with "contactGroups/"')
        return v.strip()

    @field_validator('etag')
    @classmethod
    def validate_etag(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('ETag cannot be empty')
        return v.strip()

    @field_validator("name", "group_type")
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip()
        return v

    @field_validator('created', 'updated')
    @classmethod
    def validate_timestamp(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Timestamp cannot be empty')
        try:
            datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
            return v.strip()
        except ValueError:
            raise ValueError('Invalid ISO 8601 timestamp format')

    @field_validator('member_resource_names')
    @classmethod
    def validate_member_resource_names(cls, v):
        if v:
            for resource_name in v:
                if not resource_name.startswith('people/'):
                    raise ValueError(f'Member resource name {resource_name} must start with "people/"')
        return v


class OtherContact(BaseModel):
    """An other contact in the Google People API."""
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    names: List[Name] = Field(default_factory=list, description="The other contact's names")
    email_addresses: List[EmailAddress] = Field(default_factory=list, alias="emailAddresses", description="The other contact's email addresses")
    phone_numbers: List[PhoneNumber] = Field(default_factory=list, alias="phoneNumbers", description="The other contact's phone numbers")
    organizations: List[Organization] = Field(default_factory=list, description="The other contact's organizations")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")
    # Fields with default empty lists (API uses .get(field, []))
    addresses: List[Address] = Field(default_factory=list, description="The other contact's addresses")
    birthdays: List[Birthday] = Field(default_factory=list, description="The other contact's birthdays")
    photos: List[Photo] = Field(default_factory=list, description="The other contact's photos")
    urls: List[Url] = Field(default_factory=list, description="The other contact's URLs")
    user_defined: List[UserDefined] = Field(default_factory=list, alias="userDefined", description="The other contact's user-defined fields")

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Resource name cannot be empty')
        if not v.strip().startswith('otherContacts/'):
            raise ValueError('Resource name must start with "otherContacts/"')
        return v.strip()

    @field_validator('etag')
    @classmethod
    def validate_etag(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('ETag cannot be empty')
        return v.strip()

    @field_validator('created', 'updated')
    @classmethod
    def validate_timestamp(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Timestamp cannot be empty')
        try:
            datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
            return v.strip()
        except ValueError:
            raise ValueError('Invalid ISO 8601 timestamp format')


class DirectoryPerson(BaseModel):
    """A directory person in the Google People API."""
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    names: List[Name] = Field(default_factory=list, description="The person's names")
    email_addresses: List[EmailAddress] = Field(default_factory=list, alias="emailAddresses", description="The person's email addresses")
    phone_numbers: List[PhoneNumber] = Field(default_factory=list, alias="phoneNumbers", description="The person's phone numbers")
    organizations: List[Organization] = Field(default_factory=list, description="The person's organizations")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")
    # Fields with default empty lists (API uses .get(field, []))
    addresses: List[Address] = Field(default_factory=list, description="The person's addresses")
    photos: List[Photo] = Field(default_factory=list, description="The person's photos")
    urls: List[Url] = Field(default_factory=list, description="The person's URLs")

    @field_validator('resource_name')
    @classmethod
    def validate_resource_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Resource name cannot be empty')
        if not v.strip().startswith('directoryPeople/'):
            raise ValueError('Resource name must start with "directoryPeople/"')
        return v.strip()

    @field_validator('etag')
    @classmethod
    def validate_etag(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError('ETag cannot be empty')
        return v.strip()


class GooglePeopleDB(BaseModel):
    """Main database model for Google People API simulation."""
    people: Dict[str, Person] = Field(default_factory=dict, description="Dictionary of people by resource name")
    contact_groups: Dict[str, ContactGroup] = Field(default_factory=dict, alias="contactGroups", description="Dictionary of contact groups by resource name")
    other_contacts: Dict[str, OtherContact] = Field(default_factory=dict, alias="otherContacts", description="Dictionary of other contacts by resource name")
    directory_people: Dict[str, DirectoryPerson] = Field(default_factory=dict, alias="directoryPeople", description="Dictionary of directory people by resource name")

    @field_validator('people', mode='before')
    @classmethod
    def validate_people(cls, v):
        """Convert people dictionary to Person instances."""
        if isinstance(v, dict):
            return {k: Person(**person_data) if isinstance(person_data, dict) else person_data 
                   for k, person_data in v.items()}
        return v

    @field_validator('contact_groups', mode='before')
    @classmethod
    def validate_contact_groups(cls, v):
        """Convert contact groups dictionary to ContactGroup instances."""
        if isinstance(v, dict):
            return {k: ContactGroup(**group_data) if isinstance(group_data, dict) else group_data 
                   for k, group_data in v.items()}
        return v

    @field_validator('other_contacts', mode='before')
    @classmethod
    def validate_other_contacts(cls, v):
        """Convert other contacts dictionary to OtherContact instances."""
        if isinstance(v, dict):
            return {k: OtherContact(**contact_data) if isinstance(contact_data, dict) else contact_data 
                   for k, contact_data in v.items()}
        return v

    @field_validator('directory_people', mode='before')
    @classmethod
    def validate_directory_people(cls, v):
        """Convert directory people dictionary to DirectoryPerson instances."""
        if isinstance(v, dict):
            return {k: DirectoryPerson(**person_data) if isinstance(person_data, dict) else person_data 
                   for k, person_data in v.items()}
        return v

