from pydantic import BaseModel, Field, field_validator
from typing import List

class PostInfo(BaseModel):
    """Pydantic model for post_info validation."""
    model_config = {"strict": True}  # Prevent type coercion
    
    title: str = Field(..., min_length=1, description="Title of the video")
    description: str = Field(..., description="Description of the video")
    tags: List[str] = Field(..., description="List of tags for the video")
    thumbnail_url: str = Field(..., min_length=1, description="URL of the thumbnail for the video")
    thumbnail_offset: int = Field(..., ge=0, description="Time offset in seconds for video thumbnail")
    is_ai_generated: bool = Field(..., description="Whether the content is AI-generated")
    
    @field_validator('title', 'thumbnail_url')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('String must not be empty or whitespace only')
        return v