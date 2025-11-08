from pydantic import BaseModel, Field, ValidationError, HttpUrl
from typing import Optional, Dict, Any, List
import json
import os


class User(BaseModel):
    """Pydantic model for Instagram users."""
    name: str = Field(..., description="Display name of the user", min_length=1, max_length=100)
    username: str = Field(..., description="Username of the user", min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9._]+$')


class Media(BaseModel):
    """Pydantic model for Instagram media posts."""
    user_id: str = Field(..., description="ID of the user who owns the media", min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9]+$')
    image_url: HttpUrl = Field(..., description="URL of the media image")
    caption: str = Field(default="", description="Caption or description for the media", max_length=2200)


class Comment(BaseModel):
    """Pydantic model for Instagram comments."""
    media_id: str = Field(..., description="ID of the media post being commented on", min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9]+$')
    user_id: str = Field(..., description="ID of the user making the comment", min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9]+$')
    message: str = Field(..., description="Comment text", min_length=1, max_length=300)


class InstagramDatabase(BaseModel):
    """Pydantic model for the complete Instagram database structure."""
    users: Dict[str, User] = Field(..., description="Users by user ID")
    media: Dict[str, Media] = Field(..., description="Media posts by media ID")
    comments: Dict[str, Comment] = Field(..., description="Comments by comment ID")
    
    class Config:
        str_strip_whitespace = True