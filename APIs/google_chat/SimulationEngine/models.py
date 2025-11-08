from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum

from google_chat.SimulationEngine.custom_errors import MissingDisplayNameError
from pydantic import field_validator
from .custom_errors import InvalidParentFormatError


class ThreadDetailInput(BaseModel):
    name: Optional[str] = None
    # threadKey is not directly used by the input processing of create,
    # but could be part of the thread object if provided.

class MessageBodyInput(BaseModel):
    text: Optional[str] = None
    attachment: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    thread: Optional[ThreadDetailInput] = None
    # clientAssignedMessageId is handled by the top-level messageId parameter,
    # not typically part of the message_body input structure for this function.
    # cards, cardsV2, etc. are not directly processed by the core logic shown,
    # so they are omitted here for simplicity unless they were used.
    # If they are passed through, they can be added here or handled by extra='allow'.
    
    class Config:
        extra = 'allow' # Allow other fields not explicitly defined, as original code might pass them through

class MessageUpdateBodyInput(BaseModel):
    text: Optional[str] = None
    attachment: Optional[List[Dict[str, Any]]] = None
    cards: Optional[List[Dict[str, Any]]] = None
    cardsV2: Optional[List[Dict[str, Any]]] = Field(default=None, alias='cards_v2')
    accessoryWidgets: Optional[List[Dict[str, Any]]] = Field(default=None, alias='accessory_widgets')
    
    model_config: ConfigDict = ConfigDict(
        extra = 'allow',
        populate_by_name=True
    )

class MessageUpdateInput(BaseModel):
    """Model for validating message update body parameters."""
    text: Optional[str] = None
    attachment: Optional[List[Dict[str, Any]]] = None
    cards: Optional[List[Dict[str, Any]]] = None
    cardsV2: Optional[List[Dict[str, Any]]] = Field(None, alias='cards_v2')
    accessoryWidgets: Optional[List[Dict[str, Any]]] = Field(None, alias='accessory_widgets')
    
    class Config:
        extra = 'allow'
        populate_by_name = True

class SpaceEventTypeEnum(str, Enum):
    """Enum for all valid Google Chat space event types."""
    MESSAGE_CREATED = "google.workspace.chat.message.v1.created"
    MESSAGE_UPDATED = "google.workspace.chat.message.v1.updated"
    MESSAGE_DELETED = "google.workspace.chat.message.v1.deleted"
    MESSAGE_BATCH_CREATED = "google.workspace.chat.message.v1.batchCreated"
    MESSAGE_BATCH_UPDATED = "google.workspace.chat.message.v1.batchUpdated"
    MESSAGE_BATCH_DELETED = "google.workspace.chat.message.v1.batchDeleted"
    SPACE_UPDATED = "google.workspace.chat.space.v1.updated"
    SPACE_BATCH_UPDATED = "google.workspace.chat.space.v1.batchUpdated"
    MEMBERSHIP_CREATED = "google.workspace.chat.membership.v1.created"
    MEMBERSHIP_UPDATED = "google.workspace.chat.membership.v1.updated"
    MEMBERSHIP_DELETED = "google.workspace.chat.membership.v1.deleted"
    MEMBERSHIP_BATCH_CREATED = "google.workspace.chat.membership.v1.batchCreated"
    MEMBERSHIP_BATCH_UPDATED = "google.workspace.chat.membership.v1.batchUpdated"
    MEMBERSHIP_BATCH_DELETED = "google.workspace.chat.membership.v1.batchDeleted"
    REACTION_CREATED = "google.workspace.chat.reaction.v1.created"
    REACTION_DELETED = "google.workspace.chat.reaction.v1.deleted"
    REACTION_BATCH_CREATED = "google.workspace.chat.reaction.v1.batchCreated"
    REACTION_BATCH_DELETED = "google.workspace.chat.reaction.v1.batchDeleted"


class SpaceTypeEnum(str, Enum):
    SPACE = "SPACE"
    GROUP_CHAT = "GROUP_CHAT"
    DIRECT_MESSAGE = "DIRECT_MESSAGE"

class PredefinedPermissionSettingsEnum(str, Enum):
    UNSPECIFIED = "PREDEFINED_PERMISSION_SETTINGS_UNSPECIFIED"
    COLLABORATION = "COLLABORATION_SPACE"
    ANNOUNCEMENT = "ANNOUNCEMENT_SPACE"

class SpaceThreadingStateEnum(str, Enum):
    SPACE_THREADING_STATE_UNSPECIFIED = "SPACE_THREADING_STATE_UNSPECIFIED"
    THREADED_MESSAGES = "THREADED_MESSAGES"
    GROUPED_MESSAGES = "GROUPED_MESSAGES"
    UNTHREADED_MESSAGES = "UNTHREADED_MESSAGES"

class SpaceHistoryStateEnum(str, Enum):
    HISTORY_STATE_UNSPECIFIED = "HISTORY_STATE_UNSPECIFIED"
    HISTORY_OFF = "HISTORY_OFF"
    HISTORY_ON = "HISTORY_ON"

class AccessStateEnum(str, Enum):
    ACCESS_STATE_UNSPECIFIED = "ACCESS_STATE_UNSPECIFIED"
    PRIVATE = "PRIVATE"
    DISCOVERABLE = "DISCOVERABLE"

class MembershipCountModel(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)
    joinedDirectHumanUserCount: Optional[int] = None
    joinedGroupCount: Optional[int] = None

class SpaceDetailsModel(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)
    description: Optional[str] = None
    guidelines: Optional[str] = None

class AccessSettingsModel(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)
    audience: Optional[str] = None
    accessState: Optional[str] = None

class MembershipCountModel(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)
    joinedDirectHumanUserCount: Optional[int] = None
    joinedGroupCount: Optional[int] = None

class PermissionSettingsModel(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)
    manageMembersAndGroups: Optional[Dict[str, Any]] = None
    modifySpaceDetails: Optional[Dict[str, Any]] = None
    toggleHistory: Optional[Dict[str, Any]] = None
    useAtMentionAll: Optional[Dict[str, Any]] = None
    manageApps: Optional[Dict[str, Any]] = None
    manageWebhooks: Optional[Dict[str, Any]] = None
    postMessages: Optional[Dict[str, Any]] = None
    replyMessages: Optional[Dict[str, Any]] = None

class SpaceThreadingStateEnum(str, Enum):
    SPACE_THREADING_STATE_UNSPECIFIED = "SPACE_THREADING_STATE_UNSPECIFIED"
    THREADED_MESSAGES = "THREADED_MESSAGES"
    GROUPED_MESSAGES = "GROUPED_MESSAGES"
    UNTHREADED_MESSAGES = "UNTHREADED_MESSAGES"

class SpaceHistoryStateEnum(str, Enum):
    HISTORY_STATE_UNSPECIFIED = "HISTORY_STATE_UNSPECIFIED"
    HISTORY_OFF = "HISTORY_OFF"
    HISTORY_ON = "HISTORY_ON"

class SpaceInputModel(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)

    spaceType: SpaceTypeEnum = Field(..., description="Type of the space.")
    displayName: Optional[str] = Field(None, description="Display name for the space, required if spaceType is 'SPACE'.")
    externalUserAllowed: Optional[bool] = Field(None, description="Whether external users are allowed.")
    importMode: Optional[bool] = Field(None, description="Whether the space is in import mode.")
    singleUserBotDm: Optional[bool] = Field(None, description="Whether this is a DM with a single bot.")
    spaceDetails: Optional[SpaceDetailsModel] = Field(None, description="Details about the space.")
    predefinedPermissionSettings: Optional[PredefinedPermissionSettingsEnum] = Field(None, description="Predefined permission settings.")
    accessSettings: Optional[AccessSettingsModel] = Field(None, description="Access settings for the space.")
    
    # Additional fields to align with database schema
    type: Optional[str] = Field(None, description="Type field from database schema.")
    threaded: Optional[bool] = Field(None, description="Whether the space is threaded.")
    spaceThreadingState: Optional[SpaceThreadingStateEnum] = Field(None, description="Threading state of the space.")
    spaceHistoryState: Optional[SpaceHistoryStateEnum] = Field(None, description="History state of the space.")
    createTime: Optional[str] = Field(None, description="Creation time of the space.")
    lastActiveTime: Optional[str] = Field(None, description="Last active time of the space.")
    adminInstalled: Optional[bool] = Field(None, description="Whether the space was admin installed.")
    membershipCount: Optional[MembershipCountModel] = Field(None, description="Membership count details.")
    spaceUri: Optional[str] = Field(None, description="URI of the space.")
    permissionSettings: Optional[PermissionSettingsModel] = Field(None, description="Permission settings for the space.")
    importModeExpireTime: Optional[str] = Field(None, description="Import mode expiration time.")

    @model_validator(mode='after')
    def check_displayName_for_space_type(cls, values):
        # In Pydantic V2, 'values' is the model instance itself.
        # Access fields via attribute access on 'values'.
        space_type = values.spaceType
        display_name = values.displayName

        if space_type == SpaceTypeEnum.SPACE.value:
            if not display_name or not display_name.strip():
                raise MissingDisplayNameError(
                    "displayName is required and cannot be empty when spaceType is 'SPACE'."
                )
        return values        
    

class MemberTypeEnum(str, Enum):
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    HUMAN = 'HUMAN'
    BOT = 'BOT'

class MemberRoleEnum(str, Enum):
    MEMBERSHIP_ROLE_UNSPECIFIED = 'MEMBERSHIP_ROLE_UNSPECIFIED'
    ROLE_MEMBER = 'ROLE_MEMBER'
    ROLE_MANAGER = 'ROLE_MANAGER'

class MemberStateEnum(str, Enum):
    MEMBERSHIP_STATE_UNSPECIFIED = 'MEMBERSHIP_STATE_UNSPECIFIED'
    JOINED = 'JOINED'
    INVITED = 'INVITED'
    NOT_A_MEMBER = 'NOT_A_MEMBER'

class MemberModel(BaseModel):
    name: str = Field(..., pattern=r"^(users/(app|[^/]+))$")
    displayName: Optional[str] = None
    domainId: Optional[str] = None
    type: MemberTypeEnum = MemberTypeEnum.TYPE_UNSPECIFIED.value
    isAnonymous: Optional[bool] = None

class GroupMemberModel(BaseModel):
    name: str = Field(..., pattern=r"^groups/[^/]+$")

class MembershipInputModel(BaseModel):
    role: MemberRoleEnum = MemberRoleEnum.ROLE_MEMBER  # Default from original logic
    state: MemberStateEnum = MemberStateEnum.INVITED    # Default from original logic
    deleteTime: Optional[str] = None
    member: Optional[MemberModel] = None
    groupMember: Optional[GroupMemberModel] = None
    
    @model_validator(mode='after')
    def validate_member_or_group_member(cls, values):
        """Ensure either member or groupMember is provided, but not both."""
        has_member = values.member is not None
        has_group_member = values.groupMember is not None
        
        if not has_member and not has_group_member:
            raise ValueError("Either member or groupMember must be provided")
        
        if has_member and has_group_member:
            raise ValueError("Cannot provide both member and groupMember")
        
        return values

# New models for patch operations
class MembershipPatchModel(BaseModel):
    """Model for membership patch operations. Only certain fields can be updated."""
    role: Optional[MemberRoleEnum] = None
    
    @model_validator(mode='before')
    def check_at_least_one_field(cls, values):
        """Ensure at least one field is provided for a patch operation."""
        if not values:
            raise ValueError("At least one field must be provided for a patch operation")
        return values

    @model_validator(mode='after')
    def validate_has_updatable_fields(cls, values):
        """Ensure that at least one updatable field is present."""
        # For now, only 'role' is supported to be updated
        if not values.role:
            raise ValueError("The patch operation must include at least one updatable field (role)")
        return values

class MembershipUpdateMaskModel(BaseModel):
    """Model to validate the updateMask field in patch operations."""
    updateMask: str
    
    @model_validator(mode='after')
    def validate_update_mask(cls, values):
        """Ensure the updateMask contains valid fields."""
        update_mask = values.updateMask
        if not update_mask:
            raise ValueError("updateMask is required")
            
        # Split the updateMask by commas and check if each field is valid
        valid_fields = {'role'}
        fields = {field.strip() for field in update_mask.split(',')}
        
        # Check if any valid field is in the updateMask
        if not fields.intersection(valid_fields):
            raise ValueError(f"updateMask must contain at least one valid field: {', '.join(valid_fields)}")
            
        return values    

class AttachmentRequestModel(BaseModel):
    """
    Pydantic model for validating attachment request data.
    """
    contentName: Optional[str] = Field(default="unknown", description="Filename of the uploaded attachment")
    contentType: Optional[str] = Field(default="application/octet-stream", description="MIME type of the file")
    
    @field_validator('contentName')
    def validate_content_name(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError("contentName must be a string")
        return v
    
    @field_validator('contentType')
    def validate_content_type(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError("contentType must be a string")
        if '/' not in v:
            raise ValueError("contentType must be a valid MIME type (e.g., 'text/plain', 'image/png')")
        return v 


# Models for space setup validation
class SetupMembershipModel(BaseModel):
    """Model for validating membership entries in space setup requests."""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    member: MemberModel = Field(..., description="Member information")
    groupMember: Optional[GroupMemberModel] = Field(
        None,
        description="Group member information (for group memberships)"
    )
    role: Optional[MemberRoleEnum] = Field(
        MemberRoleEnum.ROLE_MEMBER, 
        description="Member role (defaults to ROLE_MEMBER)"
    )
    state: Optional[MemberStateEnum] = Field(
        MemberStateEnum.INVITED,
        description="Member state (defaults to INVITED)"
    )
    createTime: Optional[str] = Field(
        None,
        description="Creation timestamp (defaults to current UTC time if not provided)"
    )
    deleteTime: Optional[str] = Field(
        None,
        description="Deletion timestamp (optional)"
    )
    
    @model_validator(mode='after')
    def validate_member_format(cls, values):
        """Additional validation for member format."""
        member = values.member
        if not member.name.startswith(('users/', 'users/app')):
            raise ValueError(f"Member name must start with 'users/' or 'users/app', got: {member.name}")
        return values


class SpaceSetupBodyModel(BaseModel):
    """Model for validating the complete setup_body parameter."""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    space: SpaceInputModel = Field(..., description="Space configuration (required)")
    memberships: Optional[List[SetupMembershipModel]] = Field(
        default_factory=list,
        description="List of memberships to create (optional)"
    )
    
    @model_validator(mode='after')
    def validate_setup_constraints(cls, values):
        """Additional validation for setup-specific constraints."""
        space = values.space
        memberships = values.memberships or []
        
        # Validate that member names in memberships are unique
        member_names = []
        for membership in memberships:
            member_name = membership.member.name
            if member_name in member_names:
                raise ValueError(f"Duplicate member name in memberships: {member_name}")
            member_names.append(member_name)
        
        return values    

# New models for Spaces patch operations
class SpaceUpdateMaskModel(BaseModel):
    """Model to validate the updateMask field in space patch operations."""
    updateMask: str
    
    @model_validator(mode='after')
    def validate_update_mask(cls, values):
        """Ensure the updateMask contains valid fields."""
        from google_chat.SimulationEngine.custom_errors import InvalidUpdateMaskFieldError
        
        update_mask = values.updateMask
        if not update_mask:
            raise ValueError("updateMask is required")
            
        # Valid fields for space updates
        valid_fields = {
            'space_details',
            'display_name', 
            'space_type',
            'space_history_state',
            'access_settings.audience',
            'permission_settings'
        }
        
        if update_mask.strip() == "*":
            return values  # Wildcard is valid
            
        fields = [field.strip() for field in update_mask.split(',')]
        invalid_fields = [field for field in fields if field not in valid_fields]
        
        if invalid_fields:
            raise InvalidUpdateMaskFieldError(
                f"Invalid update mask field(s): {', '.join(invalid_fields)}. "
                f"Valid fields are: {', '.join(sorted(valid_fields))}"
            )
            
        return values

class SpaceUpdatesModel(BaseModel):
    """Model for validating space update data in patch operations."""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    displayName: Optional[str] = Field(None, min_length=1, max_length=200)
    spaceType: Optional[SpaceTypeEnum] = None
    spaceDetails: Optional[SpaceDetailsModel] = None
    spaceHistoryState: Optional[SpaceHistoryStateEnum] = None
    accessSettings: Optional[AccessSettingsModel] = None
    permissionSettings: Optional[PermissionSettingsModel] = None
    
    # Additional fields that can be updated via patch operations
    spaceThreadingState: Optional[SpaceThreadingStateEnum] = None
    externalUserAllowed: Optional[bool] = None
    threaded: Optional[bool] = None
    
    @model_validator(mode='after')
    def validate_space_details_description_length(cls, values):
        """Validate that space details description doesn't exceed 150 characters."""
        from google_chat.SimulationEngine.custom_errors import InvalidDescriptionLengthError
        
        if values.spaceDetails and values.spaceDetails.description:
            if len(values.spaceDetails.description) > 150:
                raise InvalidDescriptionLengthError(
                    f"Space description cannot exceed 150 characters. "
                    f"Current length: {len(values.spaceDetails.description)}"
                )
        return values
    
    @model_validator(mode='after')
    def validate_space_type_transition_requirements(cls, values):
        """Validate requirements for space type transitions."""
        from google_chat.SimulationEngine.custom_errors import DisplayNameRequiredError
        
        # If spaceType is being updated to SPACE, displayName must be provided and non-empty
        if values.spaceType == SpaceTypeEnum.SPACE:
            if not values.displayName or not values.displayName.strip():
                raise DisplayNameRequiredError(
                    "displayName is required and cannot be empty when changing spaceType to 'SPACE'"
                )
        return values


class EmojiPayload(BaseModel):
    fileContent: str
    filename: str

class CustomEmoji(BaseModel):
    name: str
    emojiName: Optional[str] = None
    payload: EmojiPayload

class Emoji(BaseModel):
    unicode: Optional[str] = None
    customEmoji: Optional[CustomEmoji] = None

    @model_validator(mode='after')
    def check_unicode_or_custom_emoji(self) -> 'Emoji':
        if not self.unicode and not self.customEmoji:
            raise ValueError("Either 'unicode' or 'customEmoji' must be provided in 'emoji'")
        return self

class User(BaseModel):
    name: str

class ReactionInput(BaseModel):
    name: str
    emoji: Emoji
    user: User


class GetThreadReadStateInput(BaseModel):
    """Input model for the getThreadReadState function."""
    model_config = ConfigDict(extra='forbid')
    name: str = Field(
        ...,
        pattern=r"^users/[^/]+/spaces/[^/]+/threads/[^/]+/threadReadState$",
        description="Resource name of the thread read state to retrieve."
    )
    
class SpaceNotificationSettingPatchModel(BaseModel):
    name: str = Field(..., pattern=r"^users/[^/]+/spaces/[^/]+/spaceNotificationSetting$")
    updateMask: str
    requestBody: Dict[str, Any]

    class Config:
        extra = 'allow'

    @model_validator(mode='after')
    def validate_request_body(cls, values):
        request_body = values.requestBody
        update_mask = values.updateMask
        valid_notification_settings = {
            'NOTIFICATION_SETTING_UNSPECIFIED', 'ALL', 'MAIN_CONVERSATIONS', 'FOR_YOU', 'OFF'
        }
        valid_mute_settings = {
            'MUTE_SETTING_UNSPECIFIED', 'UNMUTED', 'MUTED'
        }

        masks = [m.strip() for m in update_mask.split(',')]

        if 'notification_setting' in masks or '*' in masks:
            notification_setting = request_body.get('notification_setting')
            if notification_setting not in valid_notification_settings:
                raise ValueError(f"Invalid notification_setting: {notification_setting}")

        if 'mute_setting' in masks or '*' in masks:
            mute_setting = request_body.get('mute_setting')
            if mute_setting not in valid_mute_settings:
                raise ValueError(f"Invalid mute_setting: {mute_setting}")

        return values

class GetSpaceReadStateInput(BaseModel):
    """Input model for the getSpaceReadState function."""
    model_config = ConfigDict(extra='forbid')
    name: str = Field(
        ...,
        pattern=r"^users/[^/]+/spaces/[^/]+/spaceReadState$",
        description="Resource name of the space read state to retrieve."
    )

class UpdateSpaceReadStateInput(BaseModel):
    """Input model for the updateSpaceReadState function."""
    model_config = ConfigDict(extra='forbid')
    name: str = Field(
        ...,
        pattern=r"^users/[^/]+/spaces/[^/]+/spaceReadState$",
        description="Resource name of the space read state to update."
    )
    updateMask: str = Field(
        ...,
        description='Comma-separated list of fields to update. Currently only "lastReadTime" is supported.'
    )
    requestBody: dict

    @model_validator(mode='after')
    def check_update_mask(self):
        masks = {m.strip() for m in self.updateMask.split(',')}
        supported_masks = {"lastReadTime"}
        if not masks.intersection(supported_masks) and "*" not in masks:
            raise ValueError(f"updateMask must contain 'lastReadTime' or '*'")
        if "lastReadTime" in masks or "*" in masks:
            if "lastReadTime" not in self.requestBody:
                raise ValueError("lastReadTime is required in requestBody when updateMask contains 'lastReadTime' or '*'")
        return self

class ListMessagesInputModel(BaseModel):
    """Input model for the listMessages function."""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    parent: str = Field(
        ...,
        description="Resource name of the space to list messages from. Format: spaces/{space}"
    )
    pageSize: Optional[int] = Field(
        None,
        description="Maximum number of messages to return. Must be between 1 and 1000."
    )
    pageToken: Optional[str] = Field(
        None,
        description="Token for fetching the next page of results. Must be a valid integer string."
    )
    filter: Optional[str] = Field(
        None,
        description="Query string for filtering messages by createTime and/or thread.name"
    )
    orderBy: Optional[str] = Field(
        None,
        description="Order of returned messages. Must be 'createTime asc' or 'createTime desc'"
    )
    showDeleted: Optional[bool] = Field(
        None,
        description="Whether to include deleted messages"
    )
    
    @model_validator(mode='before')
    def validate_parent(cls, values):
        """Validate parent parameter with exact same error messages."""
        parent = values.get('parent')
        
        if not isinstance(parent, str):
            raise TypeError("parent must be a string.")
        if not parent:
            raise ValueError("parent cannot be an empty string.")
        
        # Validate parent format: should be "spaces/{space}"
        if not parent.startswith("spaces/"):
            raise ValueError("parent must start with 'spaces/' and follow the format 'spaces/{space}'.")
        if len(parent.split("/")) != 2 or not parent.split("/")[1]:
            raise ValueError("parent must follow the format 'spaces/{space}' where {space} is not empty.")
        
        return values
    
    @model_validator(mode='before')
    def validate_page_size(cls, values):
        """Validate pageSize parameter with exact same error messages."""
        pageSize = values.get('pageSize')
        
        if pageSize is not None:
            if not isinstance(pageSize, int):
                raise TypeError("pageSize must be an integer.")
            if pageSize < 0:
                raise ValueError("pageSize cannot be negative.")
            if pageSize > 1000:
                raise ValueError("pageSize cannot exceed 1000. Maximum is 1000.")
        
        return values
    
    @model_validator(mode='before')
    def validate_page_token(cls, values):
        """Validate pageToken parameter with exact same error messages."""
        pageToken = values.get('pageToken')
        
        if pageToken is not None:
            if not isinstance(pageToken, str):
                raise TypeError("pageToken must be a string.")
            try:
                int(pageToken)  # Ensure it can be converted to an integer
            except ValueError:
                raise ValueError("pageToken must be a valid integer.")
        
        return values
    
    @model_validator(mode='before')
    def validate_filter(cls, values):
        """Validate filter parameter with exact same error messages."""
        filter_value = values.get('filter')
        
        if filter_value is not None:
            if not isinstance(filter_value, str):
                raise TypeError("filter must be a string.")
            # Basic filter syntax validation
            if filter_value.strip():
                segments = filter_value.split("AND")
                for segment in segments:
                    segment = segment.strip()
                    if not segment:
                        continue
                    # Check for valid filter patterns
                    if "thread.name" in segment.lower():
                        # Allow both equality and inequality operators for thread.name
                        valid_ops = ["=", "!=", "!"]  # Allow =, !=, and ! (not equal)
                        has_valid_op = any(op in segment for op in valid_ops)
                        if not has_valid_op:
                            raise ValueError("Invalid filter segment: thread.name filter must use '=', '!=', or '!' operator.")
                    elif "createtime" in segment.lower():
                        # Check for valid comparison operators
                        valid_ops = [">=", "<=", ">", "<"]
                        has_valid_op = any(op in segment for op in valid_ops)
                        if not has_valid_op:
                            raise ValueError("Invalid filter segment: createTime filter must use comparison operators (>, <, >=, <=).")
        
        return values
    
    @model_validator(mode='before')
    def validate_order_by(cls, values):
        """Validate orderBy parameter with exact same error messages."""
        orderBy = values.get('orderBy')
        
        if orderBy is not None:
            if not isinstance(orderBy, str):
                raise TypeError("orderBy must be a string.")
            normalized_orderBy = orderBy.lower()
            parts = normalized_orderBy.split()
            if not (len(parts) == 2 and parts[0] == "createtime" and parts[1] in ["asc", "desc"]):
                raise ValueError('orderBy, if provided, must be "createTime asc" or "createTime desc".')
        
        return values
    
    @model_validator(mode='before')
    def validate_show_deleted(cls, values):
        """Validate showDeleted parameter with exact same error messages."""
        showDeleted = values.get('showDeleted')
        
        if showDeleted is not None:
            if not isinstance(showDeleted, bool):
                raise TypeError("showDeleted must be a boolean.")
        
        return values
    
    @model_validator(mode='after')
    def set_default_page_size(cls, values):
        """Set default pageSize if not provided."""
        if values.pageSize is None:
            values.pageSize = 25
        return values
    
class GetSpaceMessagesInput(BaseModel):
    """Input model for the getSpaceMessages function."""
    name: str

    @model_validator(mode='after')
    def validate_name(self):
        parts = self.name.split("/")
        if len(parts) != 4 or parts[0] != 'spaces' or parts[2] != 'messages' or not parts[1] or not parts[3]:
            raise ValueError(f"Invalid message name format: '{self.name}'. Expected 'spaces/{{space}}/messages/{{message}}'")
        return self

class CreateMessageInput(BaseModel):
    parent: str = Field(..., min_length=1, pattern=r"^spaces/[^/]+$")
    message_body: dict
    requestId: Optional[str] = None
    messageReplyOption: str
    messageId: Optional[str] = None # Pattern moved to validator

    
    @field_validator('messageReplyOption')
    def validate_message_reply_option(cls, v):

        # Valid options for messageReplyOption
        VALID_MESSAGE_REPLY_OPTIONS = [
            "MESSAGE_REPLY_OPTION_UNSPECIFIED",
            "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",
            "REPLY_MESSAGE_OR_FAIL",
            "NEW_THREAD",
        ]

        if v not in VALID_MESSAGE_REPLY_OPTIONS:
            raise ValueError(
                f"Invalid messageReplyOption: '{v}'. "
                f"Valid options are: {', '.join(VALID_MESSAGE_REPLY_OPTIONS)}"
            )
        return v

    @field_validator('messageId')
    def validate_message_id(cls, v):
        if v is not None and not v.startswith("client-"):
            raise ValueError(
                "If 'messageId' is provided, it must start with 'client-'."
            )
        return v

    @field_validator('requestId')
    def validate_request_id(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Argument 'requestId' cannot be empty or contain only whitespace if provided.")
        if v is not None and len(v) < 1:
            raise ValueError("String should have at least 1 character")
        return v


class UploadArguments(BaseModel):
    parent: str
    attachment_request: dict

    @field_validator('parent')
    def validate_parent_format(cls, v):
        if not v:
            raise ValueError("parent cannot be empty")
        if not v.startswith("spaces/"):
            raise InvalidParentFormatError("parent must start with 'spaces/'")
        space_parts = v.split("/")
        if len(space_parts) != 2 or not space_parts[1]:
            raise InvalidParentFormatError("parent must be in format 'spaces/{space}' where {space} is not empty")
        return v
    
    @field_validator('attachment_request')
    def validate_attachment_request_type(cls, v):
        if not isinstance(v, dict):
            raise TypeError("attachment_request must be a dictionary")
        return v

class GetSpaceInputModel(BaseModel):
    """Input model for validating get space function parameters."""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    name: str = Field(
        ..., 
        pattern=r"^spaces/[^/]+$",
        description="Resource name of the space. Format: 'spaces/{space}'"
    )
    useAdminAccess: Optional[bool] = Field(
        None,
        description="When True, the caller can view any space as an admin"
    )


class SpaceModel(BaseModel):
    name: str
    spaceType: SpaceTypeEnum
    model_config = ConfigDict(extra='allow', validate_assignment=True, use_enum_values=True)
    displayName: Optional[str] = None
    externalUserAllowed: Optional[bool] = None
    spaceThreadingState: Optional[SpaceThreadingStateEnum] = None
    spaceHistoryState: Optional[SpaceHistoryStateEnum] = None
    createTime: Optional[str] = None
    lastActiveTime: Optional[str] = None
    importMode: Optional[bool] = None
    adminInstalled: Optional[bool] = None
    spaceUri: Optional[str] = None
    predefinedPermissionSettings: Optional[PredefinedPermissionSettingsEnum] = None
    spaceDetails: Optional[SpaceDetailsModel] = None
    membershipCount: Optional[MembershipCountModel] = None
    accessSettings: Optional[AccessSettingsModel] = None
    singleUserBotDm: Optional[bool] = None
    requestId: Optional[str] = None    

