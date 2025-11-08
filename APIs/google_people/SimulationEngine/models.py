"""
Google People API - Pydantic Models

This module contains Pydantic models for input validation and data structure
definitions based on the official Google People API specification.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl, ConfigDict


class SourceType(str, Enum):
    """Source types for metadata.
    
    Based on the official Google People API ReadSourceType enum.
    Reference: https://developers.google.com/people/api/rest/v1/ReadSourceType
    """
    READ_SOURCE_TYPE_UNSPECIFIED = "READ_SOURCE_TYPE_UNSPECIFIED"
    READ_SOURCE_TYPE_PROFILE = "READ_SOURCE_TYPE_PROFILE"
    READ_SOURCE_TYPE_CONTACT = "READ_SOURCE_TYPE_CONTACT"
    READ_SOURCE_TYPE_DOMAIN_CONTACT = "READ_SOURCE_TYPE_DOMAIN_CONTACT"
    READ_SOURCE_TYPE_OTHER_CONTACT = "READ_SOURCE_TYPE_OTHER_CONTACT"


class FieldMetadata(BaseModel):
    """Metadata for a field."""
    primary: Optional[bool] = Field(None, description="Whether this is the primary field")
    source: Optional[Dict[str, Any]] = Field(None, description="Source information")
    source_primary: Optional[bool] = Field(None, description="Whether the source is primary")
    verified: Optional[bool] = Field(None, description="Whether the field is verified")


class Name(BaseModel):
    """A person's name."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the name")
    display_name: Optional[str] = Field(None, alias="displayName", max_length=100)
    display_name_last_first: Optional[str] = Field(None, alias="displayNameLastFirst", max_length=100)
    family_name: Optional[str] = Field(None, alias="familyName", max_length=100)
    given_name: Optional[str] = Field(None, alias="givenName", max_length=100)
    honorific_prefix: Optional[str] = Field(None, alias="honorificPrefix", max_length=20)
    honorific_suffix: Optional[str] = Field(None, alias="honorificSuffix", max_length=20)
    middle_name: Optional[str] = Field(None, alias="middleName", max_length=100)
    phonetic_family_name: Optional[str] = Field(None, alias="phoneticFamilyName", max_length=100)
    phonetic_given_name: Optional[str] = Field(None, alias="phoneticGivenName", max_length=100)
    phonetic_honorific_prefix: Optional[str] = Field(None, alias="phoneticHonorificPrefix", max_length=20)
    phonetic_honorific_suffix: Optional[str] = Field(None, alias="phoneticHonorificSuffix", max_length=20)
    phonetic_middle_name: Optional[str] = Field(None, alias="phoneticMiddleName", max_length=100)
    unstructured_name: Optional[str] = Field(None, alias="unstructuredName", max_length=200)


class EmailType(str, Enum):
    """Email address types."""
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class EmailAddress(BaseModel):
    """A person's email address."""
    model_config = ConfigDict(use_enum_values=True)
    
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the email")
    value: EmailStr = Field(..., description="The email address")
    type: Optional[EmailType] = Field(None, description="The type of email address")
    display_name: Optional[str] = Field(None, alias="displayName", max_length=100)
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100)


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
    model_config = ConfigDict(use_enum_values=True)
    
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the phone number")
    value: str = Field(..., description="The phone number", max_length=50)
    type: Optional[PhoneType] = Field(None, description="The type of phone number")
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100)
    canonical_form: Optional[str] = Field(None, alias="canonicalForm", max_length=50)


class AddressType(str, Enum):
    """Address types."""
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class Address(BaseModel):
    """A person's address."""
    model_config = ConfigDict(use_enum_values=True)
    
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the address")
    type: Optional[AddressType] = Field(None, description="The type of address")
    formatted_value: Optional[str] = Field(None, alias="formattedValue", max_length=500)
    street_address: Optional[str] = Field(None, alias="streetAddress", max_length=200)
    extended_address: Optional[str] = Field(None, alias="extendedAddress", max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, alias="postalCode", max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, alias="countryCode", max_length=10)
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100)


class OrganizationType(str, Enum):
    """Organization types."""
    WORK = "work"
    SCHOOL = "school"
    OTHER = "other"


class Organization(BaseModel):
    """A person's organization."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the organization")
    type: Optional[OrganizationType] = Field(None, description="The type of organization")
    name: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    job_description: Optional[str] = Field(None, alias="jobDescription", max_length=500)
    symbol: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=100)
    cost_center: Optional[str] = Field(None, alias="costCenter", max_length=100)
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100)


class Birthday(BaseModel):
    """A person's birthday."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the birthday")
    date: Optional[Dict[str, int]] = Field(None, description="Date components")
    text: Optional[str] = Field(None, max_length=100)


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
    formatted_type: Optional[str] = Field(None, alias="formattedType", max_length=100)


class UserDefined(BaseModel):
    """A user-defined field."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the field")
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=500)


class Nickname(BaseModel):
    """A person's nickname."""
    metadata: Optional[FieldMetadata] = Field(None, description="Metadata for the nickname")
    value: str = Field(..., max_length=100)
    type: Optional[str] = Field(None, description="Nickname type as defined by People API NicknameType")


class Person(BaseModel):
    """A person in the Google People API."""
    model_config = ConfigDict(use_enum_values=True)
    
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    names: Optional[List[Name]] = Field(None, description="The person's names")
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias="emailAddresses", description="The person's email addresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers", description="The person's phone numbers")
    nicknames: Optional[List[Nickname]] = Field(None, alias="nicknames", description="The person's nicknames")
    addresses: Optional[List[Address]] = Field(None, description="The person's addresses")
    organizations: Optional[List[Organization]] = Field(None, description="The person's organizations")
    birthdays: Optional[List[Birthday]] = Field(None, description="The person's birthdays")
    photos: Optional[List[Photo]] = Field(None, description="The person's photos")
    urls: Optional[List[Url]] = Field(None, description="The person's URLs")
    user_defined: Optional[List[UserDefined]] = Field(None, alias="userDefined", description="The person's user-defined fields")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if v and not v.startswith('people/'):
            raise ValueError('Resource name must start with "people/"')
        return v

    @validator('etag')
    def validate_etag(cls, v):
        if v and not v.startswith('etag_'):
            raise ValueError('ETag must start with "etag_"')
        return v


class GetContactRequest(BaseModel):
    """Request model for getting a contact."""
    resource_name: str = Field(..., description="The resource name of the person to retrieve")
    person_fields: Optional[str] = Field(None, description="Comma-separated list of person fields to include")
    sources: Optional[List[str]] = Field(None, description="List of sources to retrieve data from")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('people/'):
            raise ValueError('Resource name must start with "people/"')
        return v

    @validator('person_fields')
    def validate_person_fields(cls, v):
        if v:
            valid_fields = {
                'names', 'emailAddresses', 'phoneNumbers', 'addresses', 'organizations',
                'birthdays', 'photos', 'urls', 'userDefined', 'nicknames', 'resourceName', 'etag',
                'created', 'updated'
            }
            fields = {field.strip() for field in v.split(',')}
            invalid_fields = fields - valid_fields
            if invalid_fields:
                raise ValueError(f'Invalid person fields: {invalid_fields}')
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is None:
            return v
        
        valid_sources = {source.value for source in SourceType}
        invalid_sources = []
        
        for source in v:
            if source is None or source not in valid_sources:
                invalid_sources.append(source)
        
        if invalid_sources:
            raise ValueError(f"Invalid source values: {invalid_sources}. Valid sources are: {list(valid_sources)}")
        
        return v


class CreateContactRequest(BaseModel):
    """Request model for creating a contact."""
    person_data: Person = Field(..., description="The person data to create")

    @validator('person_data')
    def validate_person_data(cls, v):
        if not v.names:
            raise ValueError('At least one name is required')
        if not v.email_addresses:
            raise ValueError('At least one email address is required')
        return v


class UpdateContactRequest(BaseModel):
    """Request model for updating a contact."""
    resource_name: str = Field(..., description="The resource name of the person to update")
    person_data: Person = Field(..., description="The updated person data")
    update_person_fields: Optional[str] = Field(None, description="Comma-separated list of person fields to update")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('people/'):
            raise ValueError('Resource name must start with "people/"')
        return v


class DeleteContactRequest(BaseModel):
    """Request model for deleting a contact."""
    resource_name: str = Field(..., description="The resource name of the person to delete")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('people/'):
            raise ValueError('Resource name must start with "people/"')
        return v


class ListConnectionsRequest(BaseModel):
    """Request model for listing connections."""
    resource_name: str = Field("people/me", description="The resource name to return connections for")
    person_fields: Optional[str] = Field(None, description="Comma-separated list of person fields to include")
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="The number of connections to include in the response")
    page_token: Optional[str] = Field(None, description="A page token, received from a previous response")
    sort_order: Optional[str] = Field(None, description="The order in which the connections should be sorted")
    sync_token: Optional[str] = Field(None, description="A sync token, returned by a previous call")
    request_sync_token: Optional[bool] = Field(None, description="Whether the response should include a sync token")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('people/'):
            raise ValueError('Resource name must start with "people/"')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v and v not in ['LAST_MODIFIED_ASCENDING', 'LAST_MODIFIED_DESCENDING', 'FIRST_NAME_ASCENDING', 'LAST_NAME_ASCENDING']:
            raise ValueError('Invalid sort order')
        return v


class SearchPeopleRequest(BaseModel):
    """Request model for searching people."""
    query: str = Field(..., min_length=1, max_length=1000, description="The plain-text query for the request")
    read_mask: str = Field(..., description="A field mask to restrict which fields on each person are returned")
    sources: Optional[List[str]] = Field(None, description="List of sources to retrieve data from")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @validator('read_mask')
    def validate_read_mask(cls, v):
        if not v.strip():
            raise ValueError('read_mask cannot be empty')
        
        # Validate that read_mask contains valid field names
        valid_fields = {
            'names', 'emailAddresses', 'phoneNumbers', 'addresses', 'organizations',
            'birthdays', 'photos', 'urls', 'userDefined', 'nicknames', 'resourceName',
            'etag', 'created', 'updated'
        }
        
        # Split by comma and check each field
        fields = [field.strip() for field in v.split(',')]
        
        # Check for invalid field names (only check non-empty fields)
        invalid_fields = [field for field in fields if field and field not in valid_fields]
        if invalid_fields:
            raise ValueError(f"Invalid field(s) in read_mask: {invalid_fields}. Valid fields are: {sorted(valid_fields)}")
        
        return v.strip()
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is None:
            return v
        
        valid_sources = {source.value for source in SourceType}
        invalid_sources = []
        
        for source in v:
            if source is None or source not in valid_sources:
                invalid_sources.append(source)
        
        if invalid_sources:
            raise ValueError(f"Invalid source values: {invalid_sources}. Valid sources are: {list(valid_sources)}")
        
        return v


class BatchGetRequest(BaseModel):
    """Request model for batch getting people."""
    resource_names: List[str] = Field(..., min_items=1, max_items=50, description="List of resource names of the people to retrieve")
    person_fields: Optional[str] = Field(None, description="Comma-separated list of person fields to include")
    sources: Optional[List[str]] = Field(None, description="List of sources to retrieve data from")

    @validator('resource_names')
    def validate_resource_names(cls, v):
        for resource_name in v:
            if not resource_name.startswith('people/'):
                raise ValueError(f'Resource name {resource_name} must start with "people/"')
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is None:
            return v
        
        valid_sources = {source.value for source in SourceType}
        invalid_sources = []
        
        for source in v:
            if source is None or source not in valid_sources:
                invalid_sources.append(source)
        
        if invalid_sources:
            raise ValueError(f"Invalid source values: {invalid_sources}. Valid sources are: {list(valid_sources)}")
        
        return v


class GetDirectoryPersonRequest(BaseModel):
    """Request model for getting a directory person."""
    resource_name: str = Field(..., description="The resource name of the directory person to retrieve")
    read_mask: Optional[str] = Field(None, description="A field mask to restrict which fields on each person are returned")
    sources: Optional[List[str]] = Field(None, description="List of sources to retrieve data from")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('directoryPeople/'):
            raise ValueError('Resource name must start with "directoryPeople/"')
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is None:
            return v
        
        valid_sources = {source.value for source in SourceType}
        invalid_sources = []
        
        for source in v:
            if source is None or source not in valid_sources:
                invalid_sources.append(source)
        
        if invalid_sources:
            raise ValueError(f"Invalid source values: {invalid_sources}. Valid sources are: {list(valid_sources)}")
        
        return v


class ListDirectoryPeopleRequest(BaseModel):
    """Request model for listing directory people."""
    read_mask: Optional[str] = Field(None, description="A field mask to restrict which fields on each person are returned")
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="The number of directory people to include in the response")
    page_token: Optional[str] = Field(None, description="A page token, received from a previous response")
    sync_token: Optional[str] = Field(None, description="A sync token, received from a previous response")
    request_sync_token: Optional[bool] = Field(None, description="Whether the response should include a sync token")


class SearchDirectoryPeopleRequest(BaseModel):
    """Request model for searching directory people."""
    query: str = Field(..., min_length=1, max_length=1000, description="The plain-text query for the request")
    read_mask: Optional[str] = Field(None, description="A field mask to restrict which fields on each person are returned")
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="The number of directory people to include in the response")
    page_token: Optional[str] = Field(None, description="A page token, received from a previous response")
    sources: Optional[List[str]] = Field(None, description="List of sources to retrieve data from")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is None:
            return v
        
        valid_sources = {source.value for source in SourceType}
        invalid_sources = []
        
        for source in v:
            if source is None or source not in valid_sources:
                invalid_sources.append(source)
        
        if invalid_sources:
            raise ValueError(f"Invalid source values: {invalid_sources}. Valid sources are: {list(valid_sources)}")
        
        return v


# Contact Groups Models
class ContactGroupType(str, Enum):
    """Contact group types."""
    USER_CONTACT_GROUP = "USER_CONTACT_GROUP"
    SYSTEM_CONTACT_GROUP = "SYSTEM_CONTACT_GROUP"


class ContactGroup(BaseModel):
    """A contact group in the Google People API."""
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    name: Optional[str] = Field(None, max_length=200, description="The name of the contact group")
    group_type: Optional[ContactGroupType] = Field(None, alias="groupType", description="The type of contact group")
    member_resource_names: Optional[List[str]] = Field(None, alias="memberResourceNames", description="List of member resource names")
    member_count: Optional[int] = Field(None, alias="memberCount", description="The number of members in the group")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if v and not v.startswith('contactGroups/'):
            raise ValueError('Resource name must start with "contactGroups/"')
        return v

    @validator('etag')
    def validate_etag(cls, v):
        if v and not v.startswith('etag_'):
            raise ValueError('ETag must start with "etag_"')
        return v

    @validator('member_resource_names')
    def validate_member_resource_names(cls, v):
        if v:
            for resource_name in v:
                if not resource_name.startswith('people/'):
                    raise ValueError(f'Member resource name {resource_name} must start with "people/"')
        return v


class GetContactGroupRequest(BaseModel):
    """Request model for getting a contact group."""
    resource_name: str = Field(..., description="The resource name of the contact group to retrieve")
    max_members: Optional[int] = Field(None, ge=1, le=1000, description="The maximum number of members to return per group")
    group_fields: Optional[str] = Field(None, description="Comma-separated list of group fields to include")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('contactGroups/'):
            raise ValueError('Resource name must start with "contactGroups/"')
        return v

    @validator('group_fields')
    def validate_group_fields(cls, v):
        if v:
            valid_fields = {
                'name', 'groupType', 'memberResourceNames', 'memberCount', 'resourceName', 'etag',
                'created', 'updated'
            }
            fields = {field.strip() for field in v.split(',')}
            invalid_fields = fields - valid_fields
            if invalid_fields:
                raise ValueError(f'Invalid group fields: {invalid_fields}')
        return v


class CreateContactGroupRequest(BaseModel):
    """Request model for creating a contact group."""
    contact_group_data: ContactGroup = Field(..., description="The contact group data to create")

    @validator('contact_group_data')
    def validate_contact_group_data(cls, v):
        if not v.name:
            raise ValueError('Contact group name is required')
        return v


class UpdateContactGroupRequest(BaseModel):
    """Request model for updating a contact group."""
    resource_name: str = Field(..., description="The resource name of the contact group to update")
    contact_group_data: ContactGroup = Field(..., description="The updated contact group data")
    update_group_fields: Optional[str] = Field(None, description="Comma-separated list of group fields to update")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('contactGroups/'):
            raise ValueError('Resource name must start with "contactGroups/"')
        return v


class DeleteContactGroupRequest(BaseModel):
    """Request model for deleting a contact group."""
    resource_name: str = Field(..., description="The resource name of the contact group to delete")
    delete_contacts: Optional[bool] = Field(None, description="Whether to delete the contacts in the group")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('contactGroups/'):
            raise ValueError('Resource name must start with "contactGroups/"')
        return v


class ListContactGroupsRequest(BaseModel):
    """Request model for listing contact groups."""
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="The number of resources to return per page")
    page_token: Optional[str] = Field(None, description="A page token, received from a previous response")
    sync_token: Optional[str] = Field(None, description="A sync token, received from a previous response")
    group_fields: Optional[str] = Field(None, description="Comma-separated list of group fields to include")

    @validator('group_fields')
    def validate_group_fields(cls, v):
        if v:
            valid_fields = {
                'name', 'groupType', 'memberResourceNames', 'memberCount', 'resourceName', 'etag',
                'created', 'updated'
            }
            fields = {field.strip() for field in v.split(',')}
            invalid_fields = fields - valid_fields
            if invalid_fields:
                raise ValueError(f'Invalid group fields: {invalid_fields}')
        return v


class ModifyMembersRequest(BaseModel):
    """Request model for modifying contact group members."""
    resource_name: str = Field(..., description="The resource name of the contact group to modify")
    request_data: Dict[str, Any] = Field(..., description="The modification request data")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('contactGroups/'):
            raise ValueError('Resource name must start with "contactGroups/"')
        return v


# Contact Group Response Models
class GetContactGroupResponse(BaseModel):
    """Response model for getting a contact group."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    name: str
    group_type: Optional[str] = Field(None, alias="groupType")
    member_resource_names: Optional[List[str]] = Field(None, alias="memberResourceNames")
    member_count: Optional[int] = Field(None, alias="memberCount")
    created: Optional[str]
    updated: Optional[str]


class CreateContactGroupResponse(BaseModel):
    """Response model for creating a contact group."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    name: str
    group_type: str = Field(..., alias="groupType")
    member_resource_names: List[str] = Field(..., alias="memberResourceNames")
    member_count: int = Field(..., alias="memberCount")
    created: str
    updated: str


class UpdateContactGroupResponse(BaseModel):
    """Response model for updating a contact group."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    name: Optional[str]
    group_type: Optional[str] = Field(None, alias="groupType")
    member_resource_names: Optional[List[str]] = Field(None, alias="memberResourceNames")
    member_count: Optional[int] = Field(None, alias="memberCount")
    created: Optional[str]
    updated: str


class DeleteContactGroupResponse(BaseModel):
    """Response model for deleting a contact group."""
    success: bool
    deleted_resource_name: str = Field(..., alias="deletedResourceName")
    message: str
    deleted_contacts: bool = Field(..., alias="deletedContacts")


class ListContactGroupsResponse(BaseModel):
    """Response model for listing contact groups."""
    contact_groups: List[Dict[str, Any]] = Field(..., alias="contactGroups")
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")
    next_sync_token: str = Field(..., alias="nextSyncToken")
    total_items: int = Field(..., alias="totalItems")


class ModifyMembersResponse(BaseModel):
    """Response model for modifying contact group members."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    member_count: int = Field(..., alias="memberCount")
    not_found_resource_names: List[str] = Field(..., alias="notFoundResourceNames")


# Other Contacts Models
class OtherContact(BaseModel):
    """An other contact in the Google People API."""
    resource_name: Optional[str] = Field(None, alias="resourceName", description="The resource name")
    etag: Optional[str] = Field(None, description="The ETag of the resource")
    names: Optional[List[Name]] = Field(None, description="The other contact's names")
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias="emailAddresses", description="The other contact's email addresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers", description="The other contact's phone numbers")
    addresses: Optional[List[Address]] = Field(None, description="The other contact's addresses")
    organizations: Optional[List[Organization]] = Field(None, description="The other contact's organizations")
    birthdays: Optional[List[Birthday]] = Field(None, description="The other contact's birthdays")
    photos: Optional[List[Photo]] = Field(None, description="The other contact's photos")
    urls: Optional[List[Url]] = Field(None, description="The other contact's URLs")
    user_defined: Optional[List[UserDefined]] = Field(None, alias="userDefined", description="The other contact's user-defined fields")
    created: Optional[str] = Field(None, description="The creation timestamp")
    updated: Optional[str] = Field(None, description="The last update timestamp")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if v and not v.startswith('otherContacts/'):
            raise ValueError('Resource name must start with "otherContacts/"')
        return v

    @validator('etag')
    def validate_etag(cls, v):
        if v and not v.startswith('etag_'):
            raise ValueError('ETag must start with "etag_"')
        return v


class GetOtherContactRequest(BaseModel):
    """Request model for getting an other contact."""
    resource_name: str = Field(..., description="The resource name of the other contact to retrieve")
    read_mask: Optional[str] = Field(None, description="A field mask to restrict which fields on each person are returned")
    sources: Optional[List[str]] = Field(None, description="List of sources to retrieve data from")

    @validator('resource_name')
    def validate_resource_name(cls, v):
        if not v.startswith('otherContacts/'):
            raise ValueError('Resource name must start with "otherContacts/"')
        return v

    @validator('read_mask')
    def validate_read_mask(cls, v):
        if v:
            valid_fields = {
                'names', 'emailAddresses', 'phoneNumbers', 'addresses', 'organizations',
                'birthdays', 'photos', 'urls', 'userDefined', 'nicknames', 'resourceName', 'etag',
                'created', 'updated'
            }
            fields = {field.strip() for field in v.split(',')}
            invalid_fields = fields - valid_fields
            if invalid_fields:
                raise ValueError(f'Invalid read mask fields: {invalid_fields}')
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is None:
            return v
        
        valid_sources = {source.value for source in SourceType}
        invalid_sources = []
        
        for source in v:
            if source is None or source not in valid_sources:
                invalid_sources.append(source)
        
        if invalid_sources:
            raise ValueError(f"Invalid source values: {invalid_sources}. Valid sources are: {list(valid_sources)}")
        
        return v


class ListOtherContactsRequest(BaseModel):
    """Request model for listing other contacts."""
    read_mask: Optional[str] = Field(None, description="A field mask to restrict which fields on each person are returned")
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="The number of other contacts to include in the response")
    page_token: Optional[str] = Field(None, description="A page token, received from a previous response")
    sync_token: Optional[str] = Field(None, description="A sync token, received from a previous response")
    request_sync_token: Optional[bool] = Field(None, description="Whether the response should include a sync token")

    @validator('read_mask')
    def validate_read_mask(cls, v):
        if v:
            valid_fields = {
                'names', 'emailAddresses', 'phoneNumbers', 'addresses', 'organizations',
                'birthdays', 'photos', 'urls', 'userDefined', 'resourceName', 'etag',
                'created', 'updated'
            }
            fields = {field.strip() for field in v.split(',')}
            invalid_fields = fields - valid_fields
            if invalid_fields:
                raise ValueError(f'Invalid read mask fields: {invalid_fields}')
        return v


class SearchOtherContactsRequest(BaseModel):
    """Request model for searching other contacts."""
    query: str = Field(..., min_length=1, max_length=1000, description="The plain-text query for the request")
    read_mask: Optional[str] = Field(None, description="A field mask to restrict which fields on each person are returned")
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="The number of other contacts to include in the response")
    page_token: Optional[str] = Field(None, description="A page token, received from a previous response")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

    @validator('read_mask')
    def validate_read_mask(cls, v):
        if v:
            valid_fields = {
                'names', 'emailAddresses', 'phoneNumbers', 'addresses', 'organizations',
                'birthdays', 'photos', 'urls', 'userDefined', 'nicknames', 'resourceName', 'etag',
                'created', 'updated'
            }
            fields = {field.strip() for field in v.split(',')}
            invalid_fields = fields - valid_fields
            if invalid_fields:
                raise ValueError(f'Invalid read mask fields: {invalid_fields}')
        return v


# Other Contacts Response Models
class GetOtherContactResponse(BaseModel):
    """Response model for getting an other contact."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    names: Optional[List[Name]]
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias="emailAddresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers")
    addresses: Optional[List[Address]]
    organizations: Optional[List[Organization]]
    birthdays: Optional[List[Birthday]]
    photos: Optional[List[Photo]]
    urls: Optional[List[Url]]
    user_defined: Optional[List[UserDefined]] = Field(None, alias="userDefined")
    created: Optional[str]
    updated: Optional[str]


class ListOtherContactsResponse(BaseModel):
    """Response model for listing other contacts."""
    other_contacts: List[Dict[str, Any]] = Field(..., alias="otherContacts")
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")
    total_items: int = Field(..., alias="totalItems")
    next_sync_token: Optional[str] = Field(None, alias="nextSyncToken")


class SearchOtherContactsResponse(BaseModel):
    """Response model for searching other contacts."""
    results: List[Dict[str, Any]]
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")
    total_items: int = Field(..., alias="totalItems")


# Response models
class GetContactResponse(BaseModel):
    """Response model for getting a contact."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    names: Optional[List[Name]]
    nicknames: Optional[List[Nickname]] = Field(None, alias="nicknames")
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias="emailAddresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers")
    addresses: Optional[List[Address]]
    organizations: Optional[List[Organization]]
    birthdays: Optional[List[Birthday]] = None
    photos: Optional[List[Photo]] = None
    urls: Optional[List[Url]] = None
    user_defined: Optional[List[UserDefined]] = Field(None, alias="userDefined")
    created: Optional[str]
    updated: Optional[str]


class CreateContactResponse(BaseModel):
    """Response model for creating a contact."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    names: List[Name]
    nicknames: Optional[List[Nickname]] = Field(None, alias="nicknames")
    email_addresses: List[EmailAddress] = Field(..., alias="emailAddresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers")
    addresses: Optional[List[Address]]
    organizations: Optional[List[Organization]]
    birthdays: Optional[List[Birthday]]
    photos: Optional[List[Photo]]
    urls: Optional[List[Url]]
    user_defined: Optional[List[UserDefined]] = Field(None, alias="userDefined")
    created: str
    updated: str


class UpdateContactResponse(BaseModel):
    """Response model for updating a contact."""
    resource_name: str = Field(..., alias="resourceName")
    etag: str
    names: Optional[List[Name]]
    nicknames: Optional[List[Nickname]] = Field(None, alias="nicknames")
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias="emailAddresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers")
    addresses: Optional[List[Address]]
    organizations: Optional[List[Organization]]
    birthdays: Optional[List[Birthday]]
    photos: Optional[List[Photo]]
    urls: Optional[List[Url]]
    user_defined: Optional[List[UserDefined]] = Field(None, alias="userDefined")
    created: Optional[str]
    updated: str


class DeleteContactResponse(BaseModel):
    """Response model for deleting a contact."""
    success: bool
    deleted_resource_name: str = Field(..., alias="deletedResourceName")
    message: str


class ListConnectionsResponse(BaseModel):
    """Response model for listing connections."""
    connections: List[Dict[str, Any]]
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")
    total_items: int = Field(..., alias="totalItems")
    next_sync_token: Optional[str] = Field(None, alias="nextSyncToken")


class SearchPeopleResponse(BaseModel):
    """Response model for searching people."""
    results: List[Dict[str, Any]]
    total_items: int = Field(..., alias="totalItems")


class BatchGetResponse(BaseModel):
    """Response model for batch getting people."""
    responses: List[Dict[str, Any]]
    not_found: List[str] = Field(..., alias="notFound")
    total_items: int = Field(..., alias="totalItems")


class ListDirectoryPeopleResponse(BaseModel):
    """Response model for listing directory people."""
    people: List[Dict[str, Any]]
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")
    total_items: int = Field(..., alias="totalItems")
    next_sync_token: Optional[str] = Field(None, alias="nextSyncToken")


class SearchDirectoryPeopleResponse(BaseModel):
    """Response model for searching directory people."""
    results: List[Dict[str, Any]]
    next_page_token: Optional[str] = Field(None, alias="nextPageToken")
    total_items: int = Field(..., alias="totalItems") 