import datetime as dt
from uuid import UUID, uuid4
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

# ---------------------------
# Enum Types
# ---------------------------

class PresenceStatus(str, Enum):
    """User presence status"""
    ACTIVE = "active"
    AWAY = "away"

# ---------------------------
# Sub-models for nested structures
# ---------------------------

class UserProfile(BaseModel):
    """
    User profile information.
    
    Contains detailed information about a user's profile including contact details,
    display preferences, and avatar settings.
    """
    email: Optional[str] = Field(
        None,
        description="User's email address."
    )
    display_name: Optional[str] = Field(
        None,
        description="User's display name shown in the Slack workspace."
    )
    image: Optional[str] = Field(
        None,
        description="Base64 encoded image or URL to the user's profile picture."
    )
    image_crop_x: Optional[int] = Field(
        None,
        description="X-coordinate for image crop positioning."
    )
    image_crop_y: Optional[int] = Field(
        None,
        description="Y-coordinate for image crop positioning."
    )
    image_crop_w: Optional[int] = Field(
        None,
        description="Width of the image crop."
    )
    title: Optional[str] = Field(
        None,
        description="User's job title or role."
    )

class Reaction(BaseModel):
    """
    Reaction to a message.
    
    Represents an emoji reaction added to a message by one or more users.
    """
    name: str = Field(
        ...,
        description="Name of the emoji reaction (e.g., 'thumbsup', 'rocket')."
    )
    users: List[str] = Field(
        default_factory=list,
        description="List of user IDs who reacted with this emoji."
    )
    count: int = Field(
        ...,
        description="Total count of this reaction. Should match the length of users list."
    )

class Message(BaseModel):
    """
    A message in a Slack channel.
    
    Represents a single message posted in a channel, including timestamp, user, content, and reactions.
    """
    ts: str = Field(
        ...,
        description="Timestamp of the message in Slack format (e.g., '1688682784.334459')."
    )
    user: str = Field(
        ...,
        description="User ID of the message sender."
    )
    text: str = Field(
        ...,
        description="The text content of the message."
    )
    reactions: List[Reaction] = Field(
        default_factory=list,
        description="List of reactions to this message."
    )

class FileComment(BaseModel):
    """
    Comment on a Slack file.
    
    Represents a comment made by a user on a shared file.
    """
    user: str = Field(
        ...,
        description="User ID of the commenter."
    )
    comment: str = Field(
        ...,
        description="The comment text."
    )
    timestamp: int = Field(
        ...,
        description="Unix timestamp when the comment was created."
    )

class UsergroupPrefs(BaseModel):
    """
    Preferences for a usergroup.
    
    Contains configuration settings like which channels the usergroup has access to.
    """
    channels: List[str] = Field(
        default_factory=list,
        description="List of channel IDs associated with this usergroup."
    )
    groups: List[str] = Field(
        default_factory=list,
        description="List of private group IDs associated with this usergroup."
    )

# ---------------------------
# Internal Storage Models
# ---------------------------

class CurrentUserStorage(BaseModel):
    """
    Internal storage model for the current authenticated user.
    
    Represents the currently logged-in user's basic information.
    """
    id: str = Field(
        ...,
        description="Unique identifier for the current user."
    )
    is_admin: bool = Field(
        ...,
        description="Indicates whether the current user has admin privileges."
    )

class UserStorage(BaseModel):
    """
    Internal storage model for Slack users.
    
    Represents a user in the Slack workspace with their profile and status information.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this user."
    )
    team_id: Optional[str] = Field(
        None,
        description="Team/workspace ID this user belongs to."
    )
    name: str = Field(
        ...,
        description="Username (typically lowercase with dots/underscores)."
    )
    real_name: Optional[str] = Field(
        None,
        description="User's full real name."
    )
    profile: Optional[UserProfile] = Field(
        None,
        description="Detailed profile information for the user."
    )
    is_admin: bool = Field(
        False,
        description="Indicates whether the user has admin privileges."
    )
    is_bot: bool = Field(
        False,
        description="Indicates whether this user is a bot account."
    )
    deleted: bool = Field(
        False,
        description="Indicates whether the user account has been deleted."
    )
    presence: Optional[str] = Field(
        None,
        description="Current presence status of the user (active or away)."
    )

class ChannelStorage(BaseModel):
    """
    Internal storage model for Slack channels.
    
    Represents a channel (conversation space) containing messages, files, and metadata.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this channel."
    )
    name: str = Field(
        ...,
        description="Name of the channel."
    )
    is_private: bool = Field(
        False,
        description="Indicates whether the channel is private or public."
    )
    team_id: Optional[str] = Field(
        None,
        description="Team/workspace ID this channel belongs to. Can be null."
    )
    messages: List[Message] = Field(
        default_factory=list,
        description="List of messages in this channel."
    )
    conversations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Nested conversations/threads within the channel."
    )
    files: Dict[str, bool] = Field(
        default_factory=dict,
        description="Dictionary mapping file IDs to boolean indicating if they're in this channel."
    )

class FileStorage(BaseModel):
    """
    Internal storage model for Slack files.
    
    Represents a file that has been uploaded or shared in Slack.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this file."
    )
    created: int = Field(
        ...,
        description="Unix timestamp when the file was created."
    )
    timestamp: int = Field(
        ...,
        description="Unix timestamp for the file (typically same as created)."
    )
    name: str = Field(
        ...,
        description="Filename with extension."
    )
    title: str = Field(
        ...,
        description="Human-readable title for the file."
    )
    mimetype: str = Field(
        ...,
        description="MIME type of the file (e.g., 'application/pdf')."
    )
    filetype: str = Field(
        ...,
        description="File extension/type (e.g., 'pdf', 'docx')."
    )
    user: str = Field(
        ...,
        description="User ID of the file uploader."
    )
    size: int = Field(
        ...,
        description="File size in bytes."
    )
    url_private: str = Field(
        ...,
        description="Private URL to access the file."
    )
    permalink: str = Field(
        ...,
        description="Permanent link to the file."
    )
    comments: List[FileComment] = Field(
        default_factory=list,
        description="List of comments on this file."
    )
    channels: List[str] = Field(
        default_factory=list,
        description="List of channel IDs where this file is shared."
    )

class ReminderStorage(BaseModel):
    """
    Internal storage model for Slack reminders.
    
    Represents a reminder that has been set for a user.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this reminder."
    )
    creator_id: str = Field(
        ...,
        description="User ID of who created the reminder."
    )
    user_id: str = Field(
        ...,
        description="User ID of who will receive the reminder."
    )
    text: str = Field(
        ...,
        description="The reminder message text."
    )
    time: int = Field(
        ...,
        description="Unix timestamp when the reminder should trigger."
    )
    complete_ts: Optional[int] = Field(
        None,
        description="Unix timestamp when the reminder was completed. Null if not completed."
    )
    channel_id: Optional[str] = Field(
        None,
        description="Channel ID associated with this reminder. Can be null."
    )

class UsergroupStorage(BaseModel):
    """
    Internal storage model for Slack usergroups.
    
    Represents a group of users that can be mentioned together or assigned permissions collectively.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this usergroup."
    )
    team_id: str = Field(
        ...,
        description="Team/workspace ID this usergroup belongs to."
    )
    is_usergroup: bool = Field(
        True,
        description="Indicates that this is a usergroup (should always be true)."
    )
    name: str = Field(
        ...,
        description="Display name of the usergroup."
    )
    handle: str = Field(
        ...,
        description="Handle used to mention the usergroup (e.g., '@marketing-team')."
    )
    description: str = Field(
        ...,
        description="Description of the usergroup's purpose."
    )
    date_create: int = Field(
        ...,
        description="Unix timestamp when the usergroup was created."
    )
    date_update: int = Field(
        ...,
        description="Unix timestamp when the usergroup was last updated."
    )
    date_delete: int = Field(
        0,
        description="Unix timestamp when the usergroup was deleted. 0 if not deleted."
    )
    auto_type: Optional[str] = Field(
        None,
        description="Auto-type classification (e.g., 'admin'). Can be null."
    )
    created_by: str = Field(
        ...,
        description="User ID of who created the usergroup."
    )
    updated_by: str = Field(
        ...,
        description="User ID of who last updated the usergroup."
    )
    deleted_by: Optional[str] = Field(
        None,
        description="User ID of who deleted the usergroup. Null if not deleted."
    )
    prefs: UsergroupPrefs = Field(
        ...,
        description="Preferences and settings for the usergroup."
    )
    users: List[str] = Field(
        default_factory=list,
        description="List of user IDs that are members of this usergroup."
    )
    user_count: int = Field(
        0,
        description="Total count of users in this usergroup. Should match length of users list."
    )
    disabled: bool = Field(
        False,
        description="Indicates whether the usergroup is disabled."
    )

# ---------------------------
# Root Database Model
# ---------------------------

class SlackDB(BaseModel):
    """
    Root model that validates the entire Slack database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for users, channels, files, reminders, usergroups, and other Slack entities.
    """
    current_user: CurrentUserStorage = Field(
        ...,
        description="Information about the currently authenticated user."
    )
    users: Dict[str, UserStorage] = Field(
        default_factory=dict,
        description="Dictionary of users indexed by their user ID."
    )
    channels: Dict[str, ChannelStorage] = Field(
        default_factory=dict,
        description="Dictionary of channels indexed by their channel ID."
    )
    files: Dict[str, FileStorage] = Field(
        default_factory=dict,
        description="Dictionary of files indexed by their file ID."
    )
    reminders: Dict[str, ReminderStorage] = Field(
        default_factory=dict,
        description="Dictionary of reminders indexed by their reminder ID."
    )
    usergroups: Dict[str, UsergroupStorage] = Field(
        default_factory=dict,
        description="Dictionary of usergroups indexed by their usergroup ID."
    )
    scheduled_messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of scheduled messages (structure flexible for future extensions)."
    )
    ephemeral_messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of ephemeral messages (structure flexible for future extensions)."
    )

    class Config:
        extra = "forbid"

