from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict
import re

# =============================================================================
# Database Object Models (LinkedInDefaultDB.json)
# =============================================================================

class Locale(BaseModel):
    """Model for locale information."""
    country: str = Field(..., description="Country code (e.g., 'US')", min_length=2, max_length=2)
    language: str = Field(..., description="Language code (e.g., 'en')", min_length=2, max_length=2)


class LocalizedField(BaseModel):
    """Model for localized field with locale mappings."""
    localized: Dict[str, str] = Field(..., description="Dictionary with locale keys (e.g., 'en_US') mapping to localized text")
    preferredLocale: Locale = Field(..., description="Preferred locale for the field")

    @field_validator('localized')
    @classmethod
    def validate_localized(cls, v):
        """Validate that localized dictionary is not empty and has valid locale keys."""
        if not v:
            raise ValueError("localized dictionary cannot be empty")

        for locale_key, text in v.items():
            if not locale_key or not isinstance(locale_key, str):
                raise ValueError("locale keys must be non-empty strings")
            if not text or not isinstance(text, str):
                raise ValueError("localized text must be non-empty strings")
            if '_' not in locale_key:
                raise ValueError("locale keys must be in format <language>_<COUNTRY> (e.g., 'en_US')")

        return v


class People(BaseModel):
    """
    Model for a LinkedIn person/member.

    Represents a person entity in the LinkedIn system with localized name information.
    """
    id: str = Field(..., description="Unique identifier for the person")
    firstName: LocalizedField = Field(..., description="Localized first name with locale mappings")
    localizedFirstName: str = Field(..., description="First name in the preferred locale", min_length=1)
    lastName: LocalizedField = Field(..., description="Localized last name with locale mappings")
    localizedLastName: str = Field(..., description="Last name in the preferred locale", min_length=1, max_length=255)
    vanityName: str = Field(..., description="URL-friendly version of the member's name", min_length=1, max_length=100)

    @field_validator('vanityName')
    @classmethod
    def validate_vanity_name(cls, v):
        """Validate vanity name format."""
        if not v or not isinstance(v, str):
            raise ValueError("vanityName must be a non-empty string")

        # Check for valid characters (alphanumeric and hyphens)
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("vanityName can only contain lowercase letters, numbers, and hyphens")

        # Check for minimum length
        if len(v) < 3:
            raise ValueError("vanityName must be at least 3 characters long")

        return v


class OrganizationTypeEnum(str, Enum):
    """Valid organization types."""
    COMPANY = "COMPANY"
    SCHOOL = "SCHOOL"


class Organization(BaseModel):
    """
    Model for a LinkedIn organization.

    Represents an organization entity such as a company or school.
    """
    id: int = Field(..., description="Unique identifier for the organization")
    vanityName: str = Field(..., description="Organization's vanity name (e.g., 'global-tech')", min_length=3, max_length=100)
    name: LocalizedField = Field(..., description="Localized organization name")
    primaryOrganizationType: OrganizationTypeEnum = Field(..., description="Type of organization")

    @field_validator('vanityName')
    @classmethod
    def validate_vanity_name(cls, v):
        """Validate vanity name format."""
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-z0-9-_]+$', v):
            raise ValueError("vanityName can only contain lowercase letters, numbers, hyphens, and underscores")
        return v


class OrganizationRoleEnum(str, Enum):
    """Valid organization roles."""
    ADMINISTRATOR = "ADMINISTRATOR"
    DIRECT_SPONSORED_CONTENT_POSTER = "DIRECT_SPONSORED_CONTENT_POSTER"
    RECRUITING_POSTER = "RECRUITING_POSTER"
    LEAD_CAPTURE_ADMINISTRATOR = "LEAD_CAPTURE_ADMINISTRATOR"
    LEAD_GEN_FORMS_MANAGER = "LEAD_GEN_FORMS_MANAGER"
    ANALYST = "ANALYST"
    CURATOR = "CURATOR"
    CONTENT_ADMINISTRATOR = "CONTENT_ADMINISTRATOR"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class AclStateEnum(str, Enum):
    """Valid ACL states."""
    ACTIVE = "ACTIVE"
    REQUESTED = "REQUESTED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class OrganizationAclRecord(BaseModel):
    """
    Model for an organization access control list (ACL) entry.

    Represents permissions and roles assigned to users for organizations.
    """
    aclId: str = Field(..., description="ACL record unique identifier")
    role: OrganizationRoleEnum = Field(..., description="Role assigned to the person")
    organization: str = Field(..., description="URN of the organization (e.g., 'urn:li:organization:1')", min_length=1, max_length=255)
    roleAssignee: str = Field(..., description="URN of the person assigned the role (e.g., 'urn:li:person:1')", min_length=1, max_length=255)
    state: AclStateEnum = Field(..., description="Current state of the ACL")

    @field_validator('organization')
    @classmethod
    def validate_organization_urn(cls, value):
        """Validates the URN format for the organization field."""
        urn_pattern = r'^urn:li:organization:\d+$'
        if not re.match(urn_pattern, value):
            raise ValueError(f"Invalid organization URN format: '{value}'. Expected format like 'urn:li:organization:1'.")
        return value

    @field_validator('roleAssignee')
    @classmethod
    def validate_role_assignee_urn(cls, value):
        """Validates the URN format for the roleAssignee field."""
        urn_pattern = r'^urn:li:person:\d+$'
        if not re.match(urn_pattern, value):
            raise ValueError(f"Invalid roleAssignee URN format: '{value}'. Expected format like 'urn:li:person:1'.")
        return value


class PostVisibilityEnum(str, Enum):
    """Valid post visibility options."""
    PUBLIC = "PUBLIC"
    CONNECTIONS = "CONNECTIONS"
    LOGGED_IN = "LOGGED_IN"
    CONTAINER = "CONTAINER"


class Post(BaseModel):
    """
    Model for a LinkedIn post.

    Represents a post created by a person or organization.
    """
    id: str = Field(..., description="Unique identifier for the post", min_length=1, max_length=255)
    author: str = Field(..., description="URN of the post author (e.g., 'urn:li:person:1' or 'urn:li:organization:1')", min_length=1, max_length=255)
    commentary: str = Field(..., description="Content of the post", min_length=1, max_length=5000)
    visibility: PostVisibilityEnum = Field(..., description="Visibility setting of the post")

    @field_validator('author')
    @classmethod
    def validate_author_urn(cls, value):
        """Validates the URN format for the author field."""
        urn_pattern = r'^urn:li:(person|organization):\d+$'
        if not re.match(urn_pattern, value):
            raise ValueError(
                f"Invalid author URN format: '{value}'. Expected format like 'urn:li:person:1' or 'urn:li:organization:1'."
            )
        return value


class LinkedInDatabase(BaseModel):
    """
    Model for the entire LinkedIn simulation database.

    Contains all entities in the LinkedIn simulation system including people,
    organizations, ACLs, and posts.
    """
    people: Dict[str, People] = Field(default_factory=dict, description="Dictionary of people indexed by ID")
    organizations: Dict[str, Organization] = Field(default_factory=dict, description="Dictionary of organizations indexed by ID")
    organizationAcls: Dict[str, OrganizationAclRecord] = Field(default_factory=dict, description="Dictionary of organization ACLs indexed by ACL ID")
    posts: Dict[str, Post] = Field(default_factory=dict, description="Dictionary of posts indexed by ID")
    next_person_id: int = Field(1, description="Next available person ID", ge=1)
    next_org_id: int = Field(1, description="Next available organization ID", ge=1)
    next_acl_id: int = Field(1, description="Next available ACL ID", ge=1)
    next_post_id: int = Field(1, description="Next available post ID", ge=1)
    current_person_id: str = Field(..., description="ID of the currently authenticated person", min_length=1, max_length=255)

    @model_validator(mode='after')
    def validate_current_person_exists(self):
        """Validate that current_person_id references an existing person."""
        if self.current_person_id not in self.people:
            raise ValueError(f"current_person_id '{self.current_person_id}' does not exist in people dictionary")
        return self