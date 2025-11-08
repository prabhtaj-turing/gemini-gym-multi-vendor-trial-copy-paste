from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# ---------------------------
# Enum Types
# ---------------------------

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class MessageSenderType(str, Enum):
    USER = "user"
    GROUP = "group"

class StatusCode(str, Enum):
    OK = "OK"
    PERMISSION_DENIED = "PERMISSION_DENIED"

class SupportedAction(str, Enum):
    REPLY = "reply"

# ---------------------------
# Core API Models (from schema)
# ---------------------------

class MessageNotification(BaseModel):
    """One single notification in messaging category"""
    sender_id: str = Field(..., description="The ID of the user who sent the message")
    content: str = Field(..., description="The main content of the notification")
    content_type: ContentType = Field(..., description="The type of content in the notification")
    date: str = Field(..., description="Date when the message was sent in format YYYY-MM-DD")
    time_of_day: str = Field(..., description="Time when the message was sent in format hh:mm:ss")
    
    @validator('date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('time_of_day')
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, '%H:%M:%S')
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM:SS format')

class MessageSender(BaseModel):
    """The sender of the message"""
    type: MessageSenderType = Field(..., description="The type of the sender")
    name: str = Field(..., description="The name of the sender")

class BundledMessageNotification(BaseModel):
    """Notification bundle from one sender within a single app"""
    key: str = Field(..., description="Unique identifier for this notification bundle")
    localized_app_name: str = Field(..., description="The localized app name")
    app_package_name: str = Field(..., description="The app package name")
    sender: MessageSender = Field(..., description="The sender of the bundle")
    message_count: int = Field(..., description="The number of messages in this bundle")
    message_notifications: List[MessageNotification] = Field(..., description="All message notifications in this bundle")
    supported_actions: List[SupportedAction] = Field(default_factory=list, description="The supported actions on this notifications bundle")

class Notifications(BaseModel):
    """All notifications retrieved from user's device"""
    action_card_content_passthrough: Optional[str] = Field(None, description="Action card content passthrough")
    card_id: Optional[str] = Field(None, description="Card ID")
    bundled_message_notifications: List[BundledMessageNotification] = Field(default_factory=list, description="Notifications bundled by sender and app")
    is_permission_denied: Optional[bool] = Field(None, description="Indicates permission issue when fetching notifications")
    status_code: StatusCode = Field(StatusCode.OK, description="The status code of the operation")
    skip_reply_disclaimer: Optional[bool] = Field(None, description="Indicates whether the reply disclaimer should be skipped")
    total_message_count: int = Field(0, description="The total number of messages across all bundled notifications")

class ReplyResponse(BaseModel):
    """Response confirming whether or not the reply was successfully sent"""
    action_card_content_passthrough: Optional[str] = Field(None, description="Action card content passthrough")
    card_id: Optional[str] = Field(None, description="Card ID")
    emitted_action_count: int = Field(0, description="Number of replies generated with this tool call")



class ReplyAction(BaseModel):
    """A reply action that was sent to a notification"""
    id: str = Field(..., description="Unique reply identifier")
    bundle_key: str = Field(..., description="The bundle key this reply was sent to")
    recipient_name: str = Field(..., description="The recipient of the reply")
    message_body: str = Field(..., description="The reply message text")
    app_name: str = Field(..., description="The application used to send the reply")
    status: str = Field(..., description="The reply status")
    created_at: str = Field(..., description="Timestamp when the reply was created")
    updated_at: str = Field(..., description="Timestamp when the reply was last updated")


class RepliesResponse(BaseModel):
    """Response containing sent replies for testing and assertion purposes"""
    replies: List[ReplyAction] = Field(default_factory=list, description="List of matching replies")
    total_count: int = Field(0, description="Total number of matching replies")

# ---------------------------
# API Response Models (matching the JSON spec exactly)
# ---------------------------

class MessageNotificationResponse(BaseModel):
    """Message notification as returned by the API (with sender_name instead of sender_id)"""
    sender_name: str = Field(..., description="The name of the user who sent the message")
    content: str = Field(..., description="The main content of the notification")
    content_type: ContentType = Field(..., description="The type of content in the notification")
    date: str = Field(..., description="Date when the message was sent in format YYYY-MM-DD")
    time_of_day: str = Field(..., description="Time when the message was sent in format hh:mm:ss")
    
    @validator('date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('time_of_day')
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, '%H:%M:%S')
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM:SS format')

class BundledMessageNotificationResponse(BaseModel):
    """Notification bundle as returned by the API"""
    key: str = Field(..., description="Unique identifier for this notification bundle")
    localized_app_name: str = Field(..., description="The localized app name")
    app_package_name: str = Field(..., description="The app package name")
    sender: MessageSender = Field(..., description="The sender of the bundle")
    message_count: int = Field(..., description="The number of messages in this bundle")
    message_notifications: List[MessageNotificationResponse] = Field(..., description="All message notifications in this bundle")
    supported_actions: List[SupportedAction] = Field(default_factory=list, description="The supported actions on this notifications bundle")

class NotificationsResponse(BaseModel):
    """All notifications retrieved from user's device as returned by the API"""
    action_card_content_passthrough: Optional[str] = Field(None, description="Action card content passthrough")
    card_id: Optional[str] = Field(None, description="Card ID")
    bundled_message_notifications: List[BundledMessageNotificationResponse] = Field(default_factory=list, description="Notifications bundled by sender and app")
    is_permission_denied: Optional[bool] = Field(None, description="Indicates permission issue when fetching notifications")
    status_code: StatusCode = Field(StatusCode.OK, description="The status code of the operation")
    skip_reply_disclaimer: Optional[bool] = Field(None, description="Indicates whether the reply disclaimer should be skipped")
    total_message_count: int = Field(0, description="The total number of messages across all bundled notifications")

# ---------------------------
# Internal Storage Models
# ---------------------------

class MessageNotificationStorage(BaseModel):
    """Internal storage model for message notifications"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    content: str
    content_type: ContentType
    date: str
    time_of_day: str
    bundle_key: str = Field(..., description="Reference to parent bundle")
    
    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('ID cannot be an empty string')
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError('ID must be a valid UUID4 string')
        return v
    
    @validator('date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('time_of_day')
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, '%H:%M:%S')
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM:SS format')

class MessageSenderStorage(BaseModel):
    """Internal storage model for message senders"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: MessageSenderType

    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('ID cannot be an empty string')
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError('ID must be a valid UUID4 string')
        return v

class BundledNotificationStorage(BaseModel):
    """Internal storage model for bundled notifications"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str = Field(..., description="Unique bundle identifier")
    localized_app_name: str
    app_package_name: str
    sender_id: str = Field(..., description="Reference to message sender")
    message_count: int = Field(default=0, ge=0)
    message_notification_ids: List[str] = Field(default_factory=list, description="List of message notification IDs in this bundle")
    supported_actions: List[SupportedAction] = Field(default_factory=list)
    is_read: bool = Field(default=False, description="Indicates if the notification bundle has been read")

    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('ID cannot be an empty string')
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError('ID must be a valid UUID4 string')
        return v

class ReplyActionStorage(BaseModel):
    """Internal storage model for reply actions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bundle_key: str
    recipient_name: str
    message_body: str
    app_name: str
    status: str
    created_at: str
    updated_at: str

    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('ID cannot be an empty string')
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError('ID must be a valid UUID4 string')
        return v

    @validator('created_at', 'updated_at')
    def validate_timestamp_format(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Timestamp must be in ISO format')

# ---------------------------
# Root Database Model
# ---------------------------

class NotificationsDB(BaseModel):
    """Validates entire database structure"""
    message_notifications: Dict[str, MessageNotificationStorage] = Field(default_factory=dict)
    message_senders: Dict[str, MessageSenderStorage] = Field(default_factory=dict)
    bundled_notifications: Dict[str, BundledNotificationStorage] = Field(default_factory=dict)
    reply_actions: Dict[str, ReplyActionStorage] = Field(default_factory=dict)

    class Config:
        str_strip_whitespace = True