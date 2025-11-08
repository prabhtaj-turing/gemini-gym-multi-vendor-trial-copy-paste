from pydantic import BaseModel, Field, ValidationError, HttpUrl
from typing import Optional, Dict, Any, List
import re

class UserCreateModel(BaseModel):
    """
    Pydantic model for validating user creation input.
    """
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user")
    name: str = Field(..., min_length=1, description="Name of the user")
    username: str = Field(..., min_length=1, description="Username of the user")

class UserGetModel(BaseModel):
    """
    Pydantic model for validating user retrieval input.
    """
    user_id: str = Field(..., min_length=1, description="Unique identifier of the user to retrieve")

class UserUpdateModel(BaseModel):
    """
    Pydantic model for validating user update input.
    """
    user_id: str = Field(..., min_length=1, description="Unique identifier of the user to update")
    name: Optional[str] = Field(None, min_length=1, description="New name for the user")
    username: Optional[str] = Field(None, min_length=1, description="New username for the user")

class UserDeleteModel(BaseModel):
    """
    Pydantic model for validating user deletion input.
    """
    user_id: str = Field(..., min_length=1, description="Unique identifier of the user to delete")

class MediaCreateModel(BaseModel):
    """
    Pydantic model for validating media creation input.
    """
    user_id: str = Field(..., min_length=1, description="ID of the user who owns the media")
    image_url: HttpUrl = Field(..., min_length=1, description="URL of the media image")
    caption: str = Field(default="", description="Caption or description for the media")

class MediaGetModel(BaseModel):
    """
    Pydantic model for validating media retrieval input.
    """
    media_id: str = Field(..., min_length=1, description="Unique identifier of the media to retrieve")

class MediaDeleteModel(BaseModel):
    """
    Pydantic model for validating media deletion input.
    """
    media_id: str = Field(..., min_length=1, description="Unique identifier of the media to delete")

class CommentCreateModel(BaseModel):
    """
    Pydantic model for validating comment creation input.
    """
    media_id: str = Field(..., min_length=1, description="ID of the media post being commented on")
    user_id: str = Field(..., min_length=1, description="ID of the user making the comment")
    message: str = Field(..., min_length=1, max_length=300, description="Comment text (max 300 characters)")

class CommentListModel(BaseModel):
    """
    Pydantic model for validating comment listing input.
    """
    media_id: str = Field(..., min_length=1, description="ID of the media post to retrieve comments for")

class CommentDeleteModel(BaseModel):
    """
    Pydantic model for validating comment deletion input.
    """
    comment_id: str = Field(..., min_length=1, description="Unique identifier of the comment to delete")

class UserSearchModel(BaseModel):
    """
    Pydantic model for validating user search input.
    """
    username: str = Field(..., min_length=1, description="Username to search for") 