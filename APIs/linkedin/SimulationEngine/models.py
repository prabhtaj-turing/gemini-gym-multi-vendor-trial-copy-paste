from typing import Any, Union

from enum import Enum
from pydantic import BaseModel, Field, field_validator, constr, validator, Field, conint, HttpUrl, model_validator, StrictStr, StrictInt
from typing import Dict, Any, Literal, Optional, List
import re # For regex validation

from .db import DB

class PostDataModel(BaseModel):
    """Pydantic model for validating the structure of post_data."""
    author: str = Field(..., description="URN of the post author")
    commentary: str = Field(..., description="Content of the post")
    visibility: Literal['PUBLIC', 'CONNECTIONS', 'LOGGED_IN', 'CONTAINER'] = Field(
        ..., description="Visibility setting of the post"
    )

    @field_validator('author')
    @classmethod
    def check_author_urn_format(cls, value):
        """Validates the URN format for the author field."""
        # Simple regex based on examples: urn:li:(person|organization):<digits>
        urn_pattern = r'^urn:li:(person|organization):\d+$'
        if not re.match(urn_pattern, value):
            raise ValueError(f"Invalid author URN format: '{value}'. Expected format like 'urn:li:person:1' or 'urn:li:organization:1'.")
        return value

class OrganizationType(str, Enum):
    """Valid organization types."""
    COMPANY = "COMPANY"
    SCHOOL = "SCHOOL"

class PreferredLocale(BaseModel):
    """Model for preferred locale information."""
    country: str = Field(..., description="Country code (e.g., 'US')")
    language: str = Field(..., description="Language code (e.g., 'en')")

class OrganizationName(BaseModel):
    """Model for organization name with localization."""
    localized: Dict[str, str] = Field(..., description="Dictionary with locale keys mapping to localized names")
    preferredLocale: PreferredLocale = Field(..., description="Preferred locale information")

    @validator('localized')
    def validate_localized(cls, v):
        """Validate that localized dictionary is not empty and has valid locale keys."""
        if not v:
            raise ValueError("localized dictionary cannot be empty")
        
        for locale_key, name in v.items():
            if not locale_key or not isinstance(locale_key, str):
                raise ValueError("locale keys must be non-empty strings")
            if not name or not isinstance(name, str):
                raise ValueError("localized names must be non-empty strings")
            if '_' not in locale_key:
                raise ValueError("locale keys must be in format <language>_<COUNTRY> (e.g., 'en_US')")
        
        return v

class OrganizationData(BaseModel):
    """Model for organization data with comprehensive validation."""
    vanityName: str = Field(..., description="Organization's vanity name (e.g., 'global-tech')")
    name: OrganizationName = Field(..., description="Localized organization name")
    primaryOrganizationType: OrganizationType = Field(..., description="Type of organization")

    @validator('vanityName')
    def validate_vanity_name(cls, v):
        """Validate vanity name format and uniqueness."""
        if not v or not isinstance(v, str):
            raise ValueError("vanityName must be a non-empty string")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("vanityName can only contain alphanumeric characters, hyphens, and underscores")
        
        # Check for minimum and maximum length
        if len(v) < 3:
            raise ValueError("vanityName must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("vanityName cannot exceed 50 characters")
        
        # Check for uniqueness (case-insensitive)
        for org in DB["organizations"].values():
            if org.get("vanityName", "").lower() == v.lower():
                raise ValueError(f"Organization with vanity name '{v}' already exists")
        
        return v

    @validator('name')
    def validate_name(cls, v):
        """Validate that name contains at least one localized entry."""
        if not v.localized:
            raise ValueError("name.localized must contain at least one entry")
        return v

class DistributionModel(BaseModel):
    """
    Represents LinkedIn's distribution configuration for a UGC post.

    Args:
        feedDistribution (str): 
            Defines where the post will be distributed. 
            One of: "MAIN_FEED", "NONE". Required field.

        targetEntities (Optional[List[Dict[str, Union[str, List[str]]]]]): 
            A list of dictionaries specifying targeting facets for the distribution.
            Each dictionary can include keys such as:
                - geoLocations (List[str]): Geographic location codes.
                - industries (List[str]): Industry codes.
                - functions (List[str]): Organizational functions.
                - seniorities (List[str]): Seniority levels.
            Defaults to None.

        thirdPartyDistributionChannels (Optional[List[Dict[str, Union[str, int, bool]]]]): 
            External distribution channels outside of LinkedIn. 
            Each dictionary may contain platform-specific metadata. Defaults to None.

    Returns:
        DistributionModel: An instance representing distribution configuration.

    Raises:
        ValueError: If `feedDistribution` is not a valid value or 
            if `targetEntities`/`thirdPartyDistributionChannels` contain invalid structures.
    """

    feedDistribution: Literal["MAIN_FEED", "NONE"] = Field(..., description="Where to distribute. One of: 'MAIN_FEED', 'NONE'")
    targetEntities: Optional[List[Dict[str, Union[str, List[str]]]]] = Field(default=None, description="Targeting facets like geoLocations, industries, etc.")
    thirdPartyDistributionChannels: Optional[List[Dict[str, Union[str, int, bool]]]] = Field(default=None, description="External platforms.")


class ReshareContextModel(BaseModel):
    """
    Represents the reshare context for a LinkedIn UGC (User Generated Content) post.

    Args:
        parent (Optional[str]): URN of the direct parent post. Defaults to None.
        root (Optional[str]): URN of the top-level ancestor post (read-only). Defaults to None.

    Returns:
        ReshareContextModel: An instance representing reshare context.

    Raises:
        ValueError: If `parent` or `root` are not valid URNs.
    """

    parent: Optional[str] = Field(default=None, description="URN of the direct parent post.")
    root: Optional[str] = Field(default=None, description="URN of the top-level ancestor post (read-only).")


class AdContextModel(BaseModel):
    """Model for advertising metadata for ads or viral tracking."""
    dscAdAccount: Optional[str] = Field(default=None, description="Sponsored Account URN. The Ad Account that created the Direct Sponsored Content (DSC). Required when `isDsc` is true; optional otherwise.")
    dscAdType: Optional[Literal["VIDEO", "STANDARD", "CAROUSEL", "JOB_POSTING", "NATIVE_DOCUMENT", "EVENT"]] = Field(default=None, description="Type of the DSC. Required when `isDsc` is true; optional otherwise.")
    dscName: Optional[str] = Field(default=None, description="Plain text name of the DSC post.")
    dscStatus: Optional[Literal["ACTIVE", "ARCHIVED"]] = Field(default=None, description="The status of the advertising company content. Required when `isDsc` is true; optional otherwise.")
    isDsc: Optional[bool] = Field(default=None, description="Whether or not this post is DSC. A posted DSC is created for the sole purpose of sponsorship.")
    objective: Optional[str] = Field(default=None, description="Campaign objective (e.g., 'WEBSITE_VISIT').")

    @model_validator(mode="after")
    def validate_dsc_requirements(self):
        """Validate that DSC-related fields are provided when isDsc is true."""
        if self.isDsc:
            if not self.dscAdAccount:
                raise ValueError("dscAdAccount is required when isDsc is true.")
            if not self.dscAdType:
                raise ValueError("dscAdType is required when isDsc is true.")
            if not self.dscStatus:
                raise ValueError("dscStatus is required when isDsc is true.")
        return self


class LifecycleStateInfoModel(BaseModel):
    """Model for additional lifecycle context."""
    contentStatus: Optional[str] = Field(default=None, description="The status of the content.")
    isEditedByAuthor: Optional[bool] = Field(default=None, description="Whether the content was edited by the author.")
    reviewStatus: Optional[str] = Field(default=None, description="Review status of the post.")


class MediaModel(BaseModel):
    """Model for embedded media."""
    id: str = Field(..., description="URN of the media asset.")
    title: str = Field(..., description="Title of the media.")
    altText: Optional[str] = Field(default=None, description="Accessible text for the media.")


class PollSettingsModel(BaseModel):
    """Model for poll settings."""
    voteSelectionType: Dict[str, Any] = Field(..., description="Type of vote selection.")
    duration: Literal["ONE_DAY", "THREE_DAYS", "SEVEN_DAYS", "FOURTEEN_DAYS"] = Field(..., description="Duration of the poll.")
    isVoterVisibleToAuthor: Dict[str, Any] = Field(..., description="Whether the voter is visible to the author.")


class PollOptionModel(BaseModel):
    """Model for poll options."""
    text: str = Field(..., description="Text of the option.")


class PollModel(BaseModel):
    """Model for poll content."""
    question: Optional[str] = Field(default=None, description="Question of the poll.")
    settings: Optional[PollSettingsModel] = Field(default=None, description="Settings of the poll.")
    options: List[PollOptionModel] = Field(..., description="Options of the poll.")


class MultiImageImageModel(BaseModel):
    """Model for individual images in multi-image post."""
    id: str = Field(..., description="URN of the image asset.")
    title: str = Field(..., description="Title of the image.")
    altText: Optional[str] = Field(default=None, description="Accessible text for the image.")


class MultiImageModel(BaseModel):
    """Model for multi-image post."""
    images: List[MultiImageImageModel] = Field(..., description="Images of the multi-image post.")
    altText: Optional[str] = Field(default=None, description="Accessible text for the multi-image post.")


class ArticleModel(BaseModel):
    """Model for article content."""
    description: Optional[str] = Field(default=None, description="Description of the article.")
    source: str = Field(..., description="External article URL.")
    thumbnail: Optional[str] = Field(default=None, description="URN of the thumbnail image.")
    thumbnailAltText: Optional[str] = Field(default=None, description="Alt text for the custom thumbnail. If empty, there's none. The length must be less than 4,086 characters.")
    title: str = Field(..., description="Custom or saved title of the article.")

    @field_validator("thumbnailAltText")
    @classmethod
    def validate_thumbnail_alt_text_length(cls, value):
        """Validate thumbnail alt text length."""
        if value and len(value) >= 4086:
            raise ValueError("thumbnailAltText must be less than 4,086 characters.")
        return value


class CarouselCardModel(BaseModel):
    """Model for carousel card."""
    landingPage: str = Field(..., description="The URL to the landing page.")
    media: MediaModel = Field(..., description="The media of the card.")


class CarouselModel(BaseModel):
    """Model for carousel content."""
    cards: List[CarouselCardModel] = Field(..., description="The array of cards in the carousel.")


class CelebrationModel(BaseModel):
    """Model for celebration content."""
    recipient: Optional[List[str]] = Field(default=None, description="The URN of the recipient.")
    taggedEntities: Optional[List[str]] = Field(default=None, description="The URN of the tagged entities.")
    type: Literal[
        "CELEBRATE_WELCOME", "CELEBRATE_AWARD", "CELEBRATE_ANNIVERSARY", "CELEBRATE_EVENT",
        "CELEBRATE_GRADUATION", "CELEBRATE_JOB_CHANGE", "CELEBRATE_KUDOS", "CELEBRATE_LAUNCH",
        "CELEBRATE_CAREER_BREAK", "CELEBRATE_CERTIFICATE", "CELEBRATE_EDUCATION", "CELEBRATE_MILESTONE"
    ] = Field(..., description="The type of the celebration.")
    text: Optional[str] = Field(default=None, description="The text of the celebration.")
    media: MediaModel = Field(..., description="The media of the celebration.")


class ReferenceModel(BaseModel):
    """Model for reference content type (e.g., event, appreciation)."""
    id: str = Field(..., description="The URN of the reference that represents a reference such as an event (e.g. urn:li:reference:123).")


class ContentModel(BaseModel):
    """Model for media content details."""
    media: Optional[MediaModel] = Field(default=None, description="Embedded media.")
    poll: Optional[PollModel] = Field(default=None, description="Poll content (refer to Poll API).")
    multiImage: Optional[MultiImageModel] = Field(default=None, description="Multi-image post (refer to MultiImage API).")
    article: Optional[ArticleModel] = Field(default=None, description="Article content.")
    carousel: Optional[CarouselModel] = Field(default=None, description="Carousel content.")
    celebration: Optional[CelebrationModel] = Field(default=None, description="Celebration content.")
    reference: Optional[ReferenceModel] = Field(default=None, description="Reference content type (e.g., event, appreciation).")

class UpdateAdContextModel(BaseModel):
    """Represents the advertising context for a LinkedIn UGC post update."""

    model_config = {"extra": "forbid"}  # Prevent additional fields from being added

    dscName: Optional[str] = None  # Plain text name of the Direct Sponsored Content post
    dscStatus: Optional[str] = None  # Status of the advertising content
class UpdatePostPayload(BaseModel):
    """Pydantic model for LinkedIn UGC Post update payload."""

    model_config = {"extra": "forbid"}  # Prevent additional fields from being added

    # Optional fields (all fields are optional for updates)
    commentary: Optional[constr(strip_whitespace=True, min_length=1)] = None
    lifecycleState: Optional[Literal["PUBLISHED"]] = None
    contentLandingPage: Optional[HttpUrl] = None  # Required if WEBSITE_VISIT objective
    adContext: Optional[UpdateAdContextModel] = None  # Advertising metadata with nested fields
    contentCallToActionLabel: Optional[
        Literal[
            "APPLY",
            "DOWNLOAD",
            "VIEW_QUOTE",
            "LEARN_MORE",
            "SIGN_UP",
            "SUBSCRIBE",
            "REGISTER",
            "JOIN",
            "ATTEND",
            "REQUEST_DEMO",
            "SEE_MORE",
            "BUY_NOW",
            "SHOP_NOW",
        ]
    ] = None

class UpdatePostRequest(BaseModel):
    post_id: constr(strip_whitespace=True, min_length=1)
    post_data: UpdatePostPayload

class CreatePostPayload(BaseModel):
    """Pydantic model for LinkedIn UGC Post creation payload."""

    # Required fields
    author: constr(strip_whitespace=True, min_length=1) = Field(..., description="URN of the post's author. Must be a Person or Organization URN.")
    commentary: constr(strip_whitespace=True, min_length=1) = Field(..., description="User-generated commentary text for the post.")
    distribution: DistributionModel = Field(..., description="Distribution settings, required.")
    lifecycleState: Literal["DRAFT", "PUBLISHED", "PUBLISH_REQUESTED", "PUBLISH_FAILED"] = Field(..., description="Content lifecycle state. Must be PUBLISHED for creation.")
    visibility: Literal["CONNECTIONS", "PUBLIC", "LOGGED_IN", "CONTAINER"] = Field(..., description="Member network visibility.")

    # Conditionally required
    contentLandingPage: Optional[HttpUrl] = Field(default=None, description="URL opened when the member clicks on the content. Required if the campaign creative has the `WEBSITE_VISIT` objective.")

    # Optional
    adContext: Optional[AdContextModel] = Field(default=None, description="Advertising metadata for ads or viral tracking.")
    container: Optional[str] = Field(default=None, description="URN of the container entity holding the post.")
    content: Optional[ContentModel] = Field(default=None, description="Media content details.")
    contentCallToActionLabel: Optional[
        Literal[
            "APPLY",
            "DOWNLOAD",
            "VIEW_QUOTE",
            "LEARN_MORE",
            "SIGN_UP",
            "SUBSCRIBE",
            "REGISTER",
            "JOIN",
            "ATTEND",
            "REQUEST_DEMO",
            "SEE_MORE",
            "BUY_NOW",
            "SHOP_NOW",
        ]
    ] = Field(default=None, description="Call-to-action label displayed on the creative.")
    isReshareDisabledByAuthor: Optional[bool] = Field(default=False, description="If True, disables resharing of the post. Default is False.")
    lifecycleStateInfo: Optional[LifecycleStateInfoModel] = Field(default=None, description="Additional lifecycle context.")
    publishedAt: Optional[int] = Field(default=None, description="Epoch timestamp when the content was published.")
    reshareContext: Optional[ReshareContextModel] = Field(default=None, description="Context information for re-shares.")

    @model_validator(mode="after")
    def validate_content_landing_page(self) -> "CreatePostPayload":
        """
        Validate that `contentLandingPage` is present if campaign objective is WEBSITE_VISIT.
        This assumes such an objective is passed inside `adContext`.
        """
        if self.adContext and self.adContext.objective == "WEBSITE_VISIT" and not self.contentLandingPage:
            raise ValueError(
                "contentLandingPage is required when objective is WEBSITE_VISIT."
            )
        return self

    @field_validator("author")
    @classmethod
    def check_author_urn_format(cls, value):
        """Validates the URN format for the author field."""
        # Simple regex based on examples: urn:li:(person|organization):<digits>
        urn_pattern = r"^urn:li:(person|organization):\d+$"
        if not re.match(urn_pattern, value):
            raise ValueError(
                f"Invalid author URN format: '{value}'. Expected format like 'urn:li:person:1' or 'urn:li:organization:1'."
            )
        return value


class CreatePostResponse(BaseModel):
    """
    Represents the LinkedIn UGC Post object returned from the API.
    """

    id: str = Field(..., description="UGC Post URN or share URN")
    author: str = Field(..., description="URN of the author (person or organization)")
    commentary: Optional[str] = Field(default=None, description="Post commentary text")
    distribution: Optional[DistributionModel] = Field(default=None, description="Distribution configuration")

    adContext: Optional[AdContextModel] = Field(default=None, description="Advertising metadata")
    container: Optional[str] = Field(default=None, description="URN of the container entity")
    content: Optional[ContentModel] = Field(default=None, description="Media content information")
    contentLandingPage: Optional[HttpUrl] = Field(default=None, description="Content landing page URL")
    contentCallToActionLabel: Optional[
        Literal[
            "APPLY",
            "DOWNLOAD",
            "VIEW_QUOTE",
            "LEARN_MORE",
            "SIGN_UP",
            "SUBSCRIBE",
            "REGISTER",
            "JOIN",
            "ATTEND",
            "REQUEST_DEMO",
            "SEE_MORE",
            "BUY_NOW",
            "SHOP_NOW",
        ]
    ] = Field(default=None, description="Call-to-action label")

    createdAt: Optional[int] = Field(default=None, description="Epoch timestamp of resource creation")
    lastModifiedAt: Optional[int] = Field(default=None, description="Epoch timestamp of the last modification")
    publishedAt: Optional[int] = Field(default=None, description="Epoch timestamp when published")

    isReshareDisabledByAuthor: Optional[bool] = Field(default=None, description="Whether resharing is disabled")
    lifecycleState: Optional[
        Literal["DRAFT", "PUBLISHED", "PUBLISH_REQUESTED", "PUBLISH_FAILED"]
    ] = Field(default=None, description="Current lifecycle state")
    lifecycleStateInfo: Optional[LifecycleStateInfoModel] = Field(default=None, description="Additional lifecycle context")

    reshareContext: Optional[ReshareContextModel] = Field(default=None, description="Reshare context information")
    visibility: Optional[Literal["CONNECTIONS", "PUBLIC", "LOGGED_IN", "CONTAINER"]] = Field(default=None, description="Visibility setting of the post")

    class Config:
        from_attributes = True


class LocaleInfo(BaseModel):
    country: str = Field(..., description="Country code (e.g., 'US')")
    language: str = Field(..., description="Language code (e.g., 'en')")


class LocalizedName(BaseModel):
    localized: Dict[str, str] = Field(
        ..., description="Dictionary with locale keys mapping to the localized name"
    )
    preferredLocale: LocaleInfo = Field(
        ..., description="Dictionary with country and language codes"
    )


class PersonDataModel(BaseModel):
    """Pydantic model for validating the structure of person_data."""

    localizedFirstName: str = Field(..., description="Member's first name", min_length=1)
    localizedLastName: str = Field(..., description="Member's last name", min_length=1)
    vanityName: str = Field(..., description="URL-friendly version of the member's name", min_length=1)
    firstName: Dict[str, Dict[str, str]] = Field(
        ..., description="Localized first name with locale mappings and preferred locale"
    )
    lastName: Dict[str, Dict[str, str]] = Field(
        ..., description="Localized last name with locale mappings and preferred locale"
    )


class OrganizationAclDataModel(BaseModel):
    """Pydantic model for validating organization ACL data structure."""
    roleAssignee: str = Field(..., description="URN of the person assigned the role")
    role: Literal[
        'ADMINISTRATOR', 
        'DIRECT_SPONSORED_CONTENT_POSTER', 
        'RECRUITING_POSTER', 
        'LEAD_CAPTURE_ADMINISTRATOR', 
        'LEAD_GEN_FORMS_MANAGER', 
        'ANALYST', 
        'CURATOR', 
        'CONTENT_ADMINISTRATOR'
    ] = Field(..., description="Role assigned to the person")
    organization: str = Field(..., description="URN of the organization")
    state: Literal['ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED'] = Field(
        ..., description="Current state of the ACL"
    )

    @field_validator('roleAssignee')
    @classmethod
    def validate_role_assignee_urn(cls, value):
        """Validates the URN format for the roleAssignee field."""
        urn_pattern = r'^urn:li:person:\d+$'
        if not re.match(urn_pattern, value):
            raise ValueError(f"Invalid roleAssignee URN format: '{value}'. Expected format like 'urn:li:person:1'.")
        return value

    @field_validator('organization')
    @classmethod
    def validate_organization_urn(cls, value):
        """Validates the URN format for the organization field."""
        urn_pattern = r'^urn:li:organization:\d+$'
        if not re.match(urn_pattern, value):
            raise ValueError(f"Invalid organization URN format: '{value}'. Expected format like 'urn:li:organization:1'.")
        return value


class AclIdModel(BaseModel):
    """Pydantic model for validating ACL ID."""
    acl_id: str = Field(..., description="ACL record unique identifier", min_length=1)

    @field_validator('acl_id')
    @classmethod
    def validate_acl_id(cls, value):
        """Validates that ACL ID is a non-empty string."""
        if not value or not value.strip():
            raise ValueError("ACL ID cannot be empty or whitespace only.")
        return value.strip()
    
class GetOrganizationAclsParams(BaseModel):
    query_field: constr(pattern="^roleAssignee$")
    role_assignee: constr(pattern=r"^urn:li:person:\w+$")
    projection: Optional[str] = None
    start: conint(ge=0) = 0
    count: conint(ge=1, le=100) = 10

class OrganizationLocaleModel(BaseModel):
    country: str = Field(..., min_length=2, max_length=2)
    language: str = Field(..., min_length=2, max_length=2)

class OrganizationNameModel(BaseModel):
    localized: Dict[str, str]
    preferredLocale: OrganizationLocaleModel

class OrganizationNameUpdateModel(BaseModel):
    localized: Optional[Dict[str, str]] = None
    preferredLocale: Optional[OrganizationLocaleModel] = None

class PrimaryOrganizationTypeEnum(str, Enum):
    COMPANY = 'COMPANY'
    SCHOOL = 'SCHOOL'

class OrganizationModel(BaseModel):
    vanityName: str = Field(..., min_length=1)
    name: OrganizationNameModel
    primaryOrganizationType: PrimaryOrganizationTypeEnum

class OrganizationUpdateModel(BaseModel):
    vanityName: Optional[str] = Field(None, min_length=1)
    name: Optional[OrganizationNameUpdateModel] = None
    primaryOrganizationType: Optional[PrimaryOrganizationTypeEnum] = None


class OrganizationAcl(BaseModel):
    aclId: str
    roleAssignee: str
    role: Literal[
        "ADMINISTRATOR",
        "DIRECT_SPONSORED_CONTENT_POSTER",
        "RECRUITING_POSTER",
        "LEAD_CAPTURE_ADMINISTRATOR",
        "LEAD_GEN_FORMS_MANAGER",
        "ANALYST",
        "CURATOR",
        "CONTENT_ADMINISTRATOR",
    ]
    organization: str
    state: Literal["ACTIVE", "REQUESTED", "REJECTED", "REVOKED"]
class ProjectionModel(BaseModel):
    projection: Optional[str] = None

    @field_validator("projection")
    @classmethod
    def validate_projection(cls, v):
        if v is None or v == '':
            return v
        v = v.strip()
        if v.startswith("(") and v.endswith(")"):
            v = v[1:-1]
        if re.search(r'[^a-zA-Z0-9_,]', v):
            raise ValueError("Projection string contains invalid characters.")
        if any(not field.strip() for field in v.split(',')):
            raise ValueError("Projection string contains empty field names.")
        return v

class OrganizationACLData(BaseModel):
    roleAssignee: str = Field(..., description="URN of the person to assign the role to")
    role: str = Field(..., description="Role to assign to the person")
    organization: str = Field(..., description="URN of the organization")
    state: str = Field(..., description="Initial state of the ACL")
    
    @field_validator('roleAssignee')
    @classmethod
    def validate_role_assignee(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("roleAssignee must be a non-empty string")
        if not re.match(r'^urn:li:person:\d+$', v):
            raise ValueError("roleAssignee must be a valid LinkedIn person URN (e.g., 'urn:li:person:1')")
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("role must be a non-empty string")
        valid_roles = {
            'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER',
            'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST',
            'CURATOR', 'CONTENT_ADMINISTRATOR', 'VIEWER'
        }
        if v not in valid_roles:
            raise ValueError(f"role must be one of: {', '.join(valid_roles)}")
        return v
    
    @field_validator('organization')
    @classmethod
    def validate_organization(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("organization must be a non-empty string")
        if not re.match(r'^urn:li:organization:\d+$', v):
            raise ValueError("organization must be a valid LinkedIn organization URN (e.g., 'urn:li:organization:1')")
        return v
    
    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("state must be a non-empty string")
        valid_states = {'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED'}
        if v not in valid_states:
            raise ValueError(f"state must be one of: {', '.join(valid_states)}")
        return v

class GetByVanityInputModel(BaseModel):
    query_field: StrictStr
    vanity_name: StrictStr
    projection: Optional[Any] = None
    start: StrictInt = 0
    count: StrictInt = 10
    projected_fields: Optional[List[str]] = None

    @field_validator('query_field')
    @classmethod
    def validate_query_field(cls, v):
        if v != "vanityName":
            raise ValueError("Invalid query parameter. Expected 'vanityName'.")
        return v

    @field_validator('vanity_name')
    @classmethod
    def validate_vanity_name(cls, v):
        if not v.strip():
            raise ValueError("vanity_name cannot be empty")
        return v

    @field_validator('start')
    @classmethod
    def validate_start(cls, v):
        if v < 0:
            raise ValueError("start must be non-negative")
        return v

    @field_validator('count')
    @classmethod
    def validate_count(cls, v):
        if v <= 0:
            raise ValueError("count must be positive")
        if v > 100:
            raise ValueError("count cannot exceed 100")
        return v

    @field_validator('projection')
    @classmethod
    def validate_projection(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("Projection must be a string")
        normalized = v.strip()
        if normalized.startswith('(') and normalized.endswith(')'):
            normalized = normalized[1:-1]

        # Build fields and validate
        fields = [field.strip() for field in normalized.split(',') if field.strip()]
        if not fields:
            raise ValueError("Projection must contain at least one field")

        valid_fields = {'id', 'vanityName', 'name', 'primaryOrganizationType'}
        invalid_fields = [field for field in fields if field not in valid_fields]
        if invalid_fields:
            raise ValueError(
                f"Invalid field(s) in projection: {', '.join(invalid_fields)}"
            )

        return normalized

    @model_validator(mode="after")
    def compute_projected_fields(self):
        if self.projection is None:
            self.projected_fields = None
            return self
        self.projected_fields = [
            field.strip() for field in self.projection.split(',') if field.strip()
        ]
        return self