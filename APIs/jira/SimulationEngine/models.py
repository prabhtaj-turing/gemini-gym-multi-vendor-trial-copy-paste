from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any, Union
import re


class JiraAssignee(BaseModel):
    """Represents a Jira issue assignee."""
    name: str

    class Config:
        strict = True


class JiraAttachment(BaseModel):
    """Represents a Jira issue attachment metadata."""
    id: int
    filename: str
    fileSize: int
    mimeType: str
    created: str
    checksum: str
    parentId: str
    content: Optional[str] = None
    encoding: Optional[str] = None

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate that the filename only contains allowed characters."""
        allowed_chars_pattern = r"^[a-zA-Z0-9_.-]+$"
        if not re.match(allowed_chars_pattern, filename):
            raise ValueError(
                "Filename can only contain alphanumeric characters, "
                "underscores, hyphens, and periods."
            )
        return filename

    @field_validator("created")
    @classmethod
    def validate_created_date(cls, v: str) -> str:
        """Validate created date format using centralized validation."""
        from common_utils.datetime_utils import validate_jira_datetime, InvalidDateTimeFormatError
        try:
            return validate_jira_datetime(v)
        except InvalidDateTimeFormatError as e:
            from jira.SimulationEngine.custom_errors import InvalidDateTimeFormatError as JiraInvalidDateTimeFormatError
            raise JiraInvalidDateTimeFormatError(f"Invalid created date format: {e}")

    class Config:
        strict = True

      
class JiraIssueFields(BaseModel):
    """Represents the fields of a Jira issue. Only project, summary, and issuetype are required."""
    project: str
    summary: str
    issuetype: str
    description: Optional[str] = ""
    priority: Optional[str] = "Low"
    status: Optional[str] = "Open"
    assignee: Optional[JiraAssignee] = None
    attachments: Optional[List[JiraAttachment]] = []
    due_date: Optional[str] = None
    comments: Optional[List[str]] = []
    created: Optional[str] = None
    updated: Optional[str] = None
    components: Optional[List[str]] = []

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due date format using centralized validation."""
        if v is not None:
            from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
            try:
                return validate_date_only(v)
            except InvalidDateTimeFormatError as e:
                from jira.SimulationEngine.custom_errors import InvalidDateTimeFormatError as JiraInvalidDateTimeFormatError
                raise JiraInvalidDateTimeFormatError(f"Invalid due date format: {e}")
        return v

    class Config:
        strict = True


class JiraIssueResponse(BaseModel):
    """Represents the response from creating a Jira issue."""
    id: str
    fields: JiraIssueFields

    class Config:
        strict = True


class JiraIssueCreationFields(BaseModel):
    """Represents the fields for creating a Jira issue. Only project and summary are required, others have defaults."""
    project: str
    summary: str
    issuetype: Optional[str] = "Task"
    description: Optional[str] = ""
    priority: Optional[str] = "Low"
    assignee: Optional[JiraAssignee] = JiraAssignee(name="Unassigned")
    status: Optional[str] = "Open"
    created: Optional[str] = None
    updated: Optional[str] = None
    due_date: Optional[str] = None
    comments: Optional[List[str]] = []
    components: Optional[List[str]] = []

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due date format using centralized validation."""
        if v is not None:
            from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
            try:
                return validate_date_only(v)
            except InvalidDateTimeFormatError as e:
                from jira.SimulationEngine.custom_errors import InvalidDateTimeFormatError as JiraInvalidDateTimeFormatError
                raise JiraInvalidDateTimeFormatError(f"Invalid due date format: {e}")
        return v

    class Config:
        strict = True

      
class ProfilePayload(BaseModel):
    bio: Optional[str] = None
    joined: Optional[str] = None

class SettingsPayload(BaseModel):
    theme: Optional[str] = "light"
    notifications: Optional[bool] = True

class HistoryPayload(BaseModel):
    action: Optional[str] = None
    timestamp: Optional[str] = None

class UserCreationPayload(BaseModel):
    """
    Pydantic model for validating the input payload for user creation.
    """
    name: str
    emailAddress: EmailStr
    displayName: Optional[str] = None
    profile: Optional[ProfilePayload] = None
    groups: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    settings: Optional[SettingsPayload] = None
    history: Optional[List[HistoryPayload]] = None
    watch: Optional[List[str]] = None

    class Config:
        strict = True


class IssueFieldsUpdateModel(BaseModel):
    """
    Pydantic model for validating the 'fields' argument of update_issue.
    All fields are optional for an update operation.
    """
    summary: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[JiraAssignee] = None
    issuetype: Optional[str] = None
    project: Optional[str] = None
    due_date: Optional[str] = None
    comments: Optional[List[str]] = None
    updated: Optional[str] = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due date format using centralized validation."""
        if v is not None:
            from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
            try:
                return validate_date_only(v)
            except InvalidDateTimeFormatError as e:
                from jira.SimulationEngine.custom_errors import InvalidDateTimeFormatError as JiraInvalidDateTimeFormatError
                raise JiraInvalidDateTimeFormatError(f"Invalid due date format: {e}")
        return v

    class Config:
        extra = 'forbid' # Forbid any extra fields not defined in the model
        strict = True

class IssueReference(BaseModel):
    """Represents a reference to an issue in a link."""
    key: str = Field(..., min_length=1, description="The key of the issue")

    class Config:
        strict = True


class IssueLinkCreationInput(BaseModel):
    """
    Pydantic model for validating input to create_issue_link function.
    """
    type: str = Field(..., min_length=1, description="The type of issue link to create")
    inwardIssue: IssueReference = Field(..., description="The inward issue reference")
    outwardIssue: IssueReference = Field(..., description="The outward issue reference")

    class Config:
        strict = True

class BulkIssueUpdateModel(BaseModel):
    """
    Pydantic model for validating individual issue updates in bulk operations.
    """
    issueId: str = Field(..., description="The ID of the issue to update")
    fields: Optional[IssueFieldsUpdateModel] = Field(None, description="The fields to update")
    assignee: Optional[JiraAssignee] = Field(None, description="The assignee to set")
    status: Optional[str] = Field(None, description="The status to set")
    priority: Optional[str] = Field(None, description="The priority to set")
    summary: Optional[str] = Field(None, description="The summary to set")
    description: Optional[str] = Field(None, description="The description to set")
    delete: Optional[bool] = Field(False, description="Whether to delete this issue")
    deleteSubtasks: Optional[bool] = Field(False, description="Whether to delete subtasks when deleting the issue")

    class Config:
        extra = 'forbid'
        strict = True


class BulkIssueOperationRequestModel(BaseModel):
    """
    Pydantic model for validating the bulk issue operation request.
    """
    issueUpdates: List[BulkIssueUpdateModel] = Field(..., description="List of issue updates to perform")

    class Config:
        extra = 'forbid'
        strict = True

class UserPreferencesUpdate(BaseModel):
    """
    Pydantic model for validating user preferences update input.
    """
    theme: Optional[str] = Field(None, description="The theme preference for the user")
    notifications: Optional[str] = Field(None, description="The notification preference for the user")

    class Config:
        extra = 'forbid'  # Forbid any extra fields not defined in the model
        strict = True


class WebhookInput(BaseModel):
    """
    Pydantic model for validating webhook input data.
    """
    url: str = Field(..., min_length=1, description="The webhook URL endpoint")
    events: List[str] = Field(..., min_length=1, description="List of event types the webhook subscribes to")

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validate URL format and ensure it's not empty or whitespace-only."""
        if not url or not url.strip():
            raise ValueError("url cannot be empty or whitespace-only")
        # Basic URL validation - should start with http:// or https://
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        return url.strip()

    @field_validator("events")
    @classmethod  
    def validate_events(cls, events: List[str]) -> List[str]:
        """Validate events list contains valid event names."""
        if not events:
            raise ValueError("events list cannot be empty")
        
        valid_events = {
            "issue_created", "issue_updated", "issue_deleted", "issue_assigned",
            "project_created", "project_updated", "project_deleted",
            "user_created", "user_updated", "user_deleted"
        }
        
        for event in events:
            if not isinstance(event, str):
                raise ValueError("all events must be strings")
            if not event or not event.strip():
                raise ValueError("event names cannot be empty or whitespace-only")
            if event.strip() not in valid_events:
                raise ValueError(f"invalid event '{event}'. Valid events: {', '.join(sorted(valid_events))}")
        
        return [event.strip() for event in events]

    class Config:
        extra = 'forbid'
        strict = True


class WebhookCreateRequest(BaseModel):
    """
    Pydantic model for validating webhook creation request.
    """
    webhooks: List[WebhookInput] = Field(..., min_length=1, description="List of webhooks to create")

    class Config:
        extra = 'forbid'
        strict = True


# Database Models for Complete DB Validation

class JiraStatus(BaseModel):
    """Represents a Jira status."""
    id: str
    name: str
    description: str
    statusCategory: Optional[str] = None

    class Config:
        strict = True


class JiraReindexInfo(BaseModel):
    """Represents reindex information."""
    running: bool
    type: Optional[str]
    currentProgress: int
    currentSubTask: str
    finishTime: str
    progressUrl: str
    startTime: str
    submittedTime: str
    indexChangeHistory: bool
    indexWorklogs: bool
    indexComments: bool

    class Config:
        strict = True


class JiraApplicationRole(BaseModel):
    """Represents an application role."""
    key: str
    name: str

    class Config:
        strict = True


class JiraStatusCategory(BaseModel):
    """Represents a status category."""
    id: str
    name: str
    description: str

    class Config:
        strict = True


class JiraAvatar(BaseModel):
    """Represents an avatar."""
    id: str
    type: str
    filename: str

    class Config:
        strict = True


class JiraComponent(BaseModel):
    """Represents a component."""
    id: str
    project: str
    name: str
    description: Optional[str]

    class Config:
        strict = True


class JiraDashboard(BaseModel):
    """Represents a dashboard."""
    id: str
    name: str
    owner: str

    class Config:
        strict = True


class JiraFilter(BaseModel):
    """Represents a filter."""
    id: str
    name: str
    jql: str

    class Config:
        strict = True


class JiraGroup(BaseModel):
    """Represents a group."""
    groupId: str
    name: str
    users: List[str]

    class Config:
        strict = True


class JiraIssueLink(BaseModel):
    """Represents an issue link."""
    id: str
    type: str
    inwardIssue: Dict[str, str]  # Dictionary with 'key' field
    outwardIssue: Dict[str, str]  # Dictionary with 'key' field

    class Config:
        strict = True


class JiraIssueLinkType(BaseModel):
    """Represents an issue link type."""
    id: str
    name: str

    class Config:
        strict = True


class JiraIssueType(BaseModel):
    """Represents an issue type."""
    id: str
    name: str

    class Config:
        strict = True


class JiraJQLAutocompleteData(BaseModel):
    """Represents JQL autocomplete data."""
    fields: List[str]
    operators: List[str]

    class Config:
        strict = True


class JiraLicense(BaseModel):
    """Represents a license."""
    id: str
    key: str
    expiry: str

    class Config:
        strict = True


class JiraPermissionScheme(BaseModel):
    """Represents a permission scheme."""
    id: str
    name: str
    permissions: List[str]

    class Config:
        strict = True


class JiraPriority(BaseModel):
    """Represents a priority."""
    id: str
    name: str

    class Config:
        strict = True


class JiraProject(BaseModel):
    """Represents a project."""
    key: str
    name: str
    lead: str

    class Config:
        strict = True


class JiraProjectCategory(BaseModel):
    """Represents a project category."""
    id: str
    name: str

    class Config:
        strict = True


class JiraResolution(BaseModel):
    """Represents a resolution."""
    id: str
    name: str

    class Config:
        strict = True


class JiraRole(BaseModel):
    """Represents a role."""
    id: str
    name: str

    class Config:
        strict = True


class JiraWebhook(BaseModel):
    """Represents a webhook."""
    id: str
    url: str
    events: List[str]

    class Config:
        strict = True


class JiraWorkflow(BaseModel):
    """Represents a workflow."""
    id: str
    name: str
    steps: List[str]

    class Config:
        strict = True


class JiraSecurityLevel(BaseModel):
    """Represents a security level."""
    id: str
    name: str
    description: str

    class Config:
        strict = True


class JiraAttachmentStorage(BaseModel):
    """Represents an attachment."""
    id: int
    filename: str
    fileSize: int
    mimeType: str
    content: str
    encoding: str
    created: str
    checksum: str
    parentId: str

    class Config:
        strict = True


class JiraUserProfile(BaseModel):
    """Represents a user profile."""
    bio: Optional[str] = None
    joined: Optional[str] = None

    class Config:
        strict = True


class JiraUserSettings(BaseModel):
    """Represents user settings."""
    theme: Optional[str] = None
    notifications: Optional[bool] = None

    class Config:
        strict = True


class JiraUserHistory(BaseModel):
    """Represents user history entry."""
    action: str
    timestamp: str

    class Config:
        strict = True


class JiraUser(BaseModel):
    """Represents a user."""
    name: str
    key: str
    active: bool = True
    emailAddress: str
    displayName: str
    profile: Optional[JiraUserProfile] = None
    labels: Optional[List[str]] = None
    settings: Optional[JiraUserSettings] = None
    history: Optional[List[JiraUserHistory]] = None
    watch: Optional[List[str]] = None

    class Config:
        strict = True


class JiraServerInfo(BaseModel):
    """Represents server information."""
    version: str
    deploymentTitle: str
    buildNumber: int
    buildDate: str
    baseUrl: str
    versions: List[str]
    deploymentType: str

    class Config:
        strict = True


class JiraVersion(BaseModel):
    """Represents a version."""
    id: str
    name: str
    description: str
    archived: bool
    released: bool
    releaseDate: str
    userReleaseDate: str
    project: str
    projectId: int
    expand: str
    moveUnfixedIssuesTo: str
    overdue: bool
    releaseDateSet: bool
    self: str
    startDate: str
    startDateSet: bool
    userStartDate: str

    class Config:
        strict = True


class JiraCounters(BaseModel):
    """Represents counters."""
    attachment: int
    issue: int
    user: int

    class Config:
        strict = True


class JiraDB(BaseModel):
    """Validates entire JIRA database structure"""
    statuses: Dict[str, JiraStatus] = Field(default_factory=dict)
    reindex_info: Optional[JiraReindexInfo] = None
    application_properties: Dict[str, str] = Field(default_factory=dict)
    application_roles: Dict[str, JiraApplicationRole] = Field(default_factory=dict)
    status_categories: Dict[str, JiraStatusCategory] = Field(default_factory=dict)
    avatars: List[JiraAvatar] = Field(default_factory=list)
    components: Dict[str, JiraComponent] = Field(default_factory=dict)
    dashboards: Dict[str, JiraDashboard] = Field(default_factory=dict)
    filters: Dict[str, JiraFilter] = Field(default_factory=dict)
    groups: Dict[str, JiraGroup] = Field(default_factory=dict)
    issues: Dict[str, JiraIssueResponse] = Field(default_factory=dict)
    issue_links: List[JiraIssueLink] = Field(default_factory=list)
    issue_link_types: Dict[str, JiraIssueLinkType] = Field(default_factory=dict)
    issue_types: Dict[str, JiraIssueType] = Field(default_factory=dict)
    jql_autocomplete_data: Optional[JiraJQLAutocompleteData] = None
    licenses: Dict[str, JiraLicense] = Field(default_factory=dict)
    my_permissions: Dict[str, bool] = Field(default_factory=dict)
    my_preferences: Dict[str, str] = Field(default_factory=dict)
    permissions: Dict[str, bool] = Field(default_factory=dict)
    permission_schemes: Dict[str, JiraPermissionScheme] = Field(default_factory=dict)
    priorities: Dict[str, JiraPriority] = Field(default_factory=dict)
    projects: Dict[str, JiraProject] = Field(default_factory=dict)
    project_categories: Dict[str, JiraProjectCategory] = Field(default_factory=dict)
    resolutions: Dict[str, JiraResolution] = Field(default_factory=dict)
    roles: Dict[str, JiraRole] = Field(default_factory=dict)
    webhooks: Dict[str, JiraWebhook] = Field(default_factory=dict)
    workflows: Dict[str, JiraWorkflow] = Field(default_factory=dict)
    security_levels: Dict[str, JiraSecurityLevel] = Field(default_factory=dict)
    attachments: Dict[str, JiraAttachmentStorage] = Field(default_factory=dict)
    users: Dict[str, JiraUser] = Field(default_factory=dict)
    server_info: Optional[JiraServerInfo] = None
    versions: Dict[str, JiraVersion] = Field(default_factory=dict)
    counters: Optional[JiraCounters] = None

    class Config:
        str_strip_whitespace = True
        strict = True