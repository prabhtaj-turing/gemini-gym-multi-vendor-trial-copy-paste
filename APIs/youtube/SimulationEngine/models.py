from typing import Optional, Dict, Any, List

from pydantic import BaseModel, ValidationError, ConfigDict, field_validator, StrictBool, Field


class SnippetInputModel(BaseModel):
    """
    Pydantic model for the 'snippet' input argument.
    This model allows any arbitrary key-value pairs, effectively validating
    that the input is a dictionary-like structure for thread metadata.
    """

    model_config = ConfigDict(extra="allow")


class ThumbnailObjectModel(BaseModel):
    url:str
    height:int
    width:int


class ThumbnailInputModel(BaseModel):
    """
    Pydantic model for Thumbnail input for playlist
    """
    default : ThumbnailObjectModel
    medium : ThumbnailObjectModel
    high : ThumbnailObjectModel

class TopLevelCommentInputModel(BaseModel):
    """
    Pydantic model for the 'top_level_comment' input argument.
    It expects an optional 'id' field of type string and allows other
    arbitrary fields.
    """

    id: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class ResourceIdModel(BaseModel):
    """
    Pydantic model for the 'resourceId' output argument.
    It expects a 'kind' field of type string and a 'channelId' field of type string.
    """
    kind: str
    channelId: str

class SnippetModel(BaseModel):
    """
    Pydantic model for the 'snippet' argument in the Subscriptions API.
    It expects a 'channelId' field of type string and a 'resourceId' field of type ResourceIdModel.
    """
    channelId: str
    resourceId: ResourceIdModel
    model_config = ConfigDict(extra="forbid")

class CommentSnippetModel(BaseModel):
    """
    Pydantic model for comment thread snippet validation.
    """

    channelId: Optional[str] = None
    videoId: Optional[str] = None
    parentId: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class CommentInsertModel(BaseModel):
    """
    Pydantic model for comment insert validation.
    """

    part: str
    snippet: Optional[CommentSnippetModel] = None
    moderation_status: str = "published"
    banned_author: StrictBool = False

    @field_validator("part")
    @classmethod
    def validate_part_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("part parameter cannot be empty or contain only whitespace")
        
        # Validate that all part components are strings
        requested_parts = [p.strip() for p in v.split(",") if p.strip()]
        
        if not requested_parts:
            raise ValueError("part parameter must contain at least one component")
        
        for part_component in requested_parts:
            if not isinstance(part_component, str):
                raise ValueError("All part components must be strings")
        
        return v

    @field_validator("moderation_status")
    @classmethod
    def validate_moderation_status(cls, v):
        valid_statuses = ["heldForReview", "published", "rejected"]
        if v not in valid_statuses:
            raise ValueError(f"moderation_status must be one of: {', '.join(valid_statuses)}")
        return v


class CommentThreadUpdateModel(BaseModel):
    """
    Pydantic model for comment thread update validation.
    """

    thread_id: str
    snippet: Optional[CommentSnippetModel] = None
    comments: Optional[List[str]] = None

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("thread_id cannot be empty")
        return v

    @field_validator("comments")
    @classmethod
    def validate_comments_list(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError("comments must be a list of strings")
        if v is not None:
            for comment_id in v:
                if not isinstance(comment_id, str):
                    raise ValueError("all comment IDs must be strings")


class CommentUpdateModel(BaseModel):
    """
    Pydantic model for comment update validation.
    """

    comment_id: str
    snippet: Optional[CommentSnippetModel] = None
    moderation_status: Optional[str] = None
    banned_author: Optional[StrictBool] = None

    @field_validator("moderation_status")
    @classmethod
    def validate_moderation_status(cls, v):
        if v is not None and v not in ["heldForReview", "published", "rejected"]:
            raise ValueError(
                'moderation_status must be one of: "heldForReview", "published", "rejected"'
            )
        return v

    @field_validator("comment_id")
    @classmethod
    def validate_comment_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("comment_id cannot be empty")
        return v


class MembershipSnippetModel(BaseModel):
    """
    Pydantic model for membership snippet validation.
    """

    memberChannelId: str
    hasAccessToLevel: str
    mode: str
    model_config = ConfigDict(extra="allow")

    @field_validator("memberChannelId")
    @classmethod
    def validate_member_channel_id(cls, v):
        if not v or not v.strip():
            raise ValueError("memberChannelId cannot be empty")
        return v.strip()

    @field_validator("hasAccessToLevel")
    @classmethod
    def validate_has_access_to_level(cls, v):
        if not v or not v.strip():
            raise ValueError("hasAccessToLevel cannot be empty")
        return v.strip()

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if not v or not v.strip():
            raise ValueError("mode cannot be empty")
        return v.strip()

class MembershipInsertModel(BaseModel):
    """
    Pydantic model for membership insert validation.
    """

    part: str
    snippet: MembershipSnippetModel

    @field_validator("part")
    @classmethod
    def validate_part(cls, v):
        if not isinstance(v, str):
            raise ValueError("part must be a string")
        if not v or not v.strip():
            raise ValueError("part cannot be empty")
        
        # Parse comma-separated parts
        part_components = [p.strip() for p in v.split(",")]
        
        # Check for empty components after stripping
        if not part_components:
            raise ValueError("part parameter must contain at least one component")
        
        for component in part_components:
            if not component:
                raise ValueError("part parameter cannot contain empty components")
            if not isinstance(component, str):
                raise ValueError("all part components must be strings")
        
        return v.strip()

class MembershipUpdateSnippetModel(BaseModel):
    """
    Pydantic model for membership snippet validation.
    """

    memberChannelId: Optional[str] = None
    hasAccessToLevel: Optional[str] = None
    mode: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class MembershipUpdateModel(BaseModel):
    """
    Pydantic model for membership update validation.
    """

    part: str
    id: str
    snippet: MembershipUpdateSnippetModel

    @field_validator("part")
    @classmethod
    def validate_part_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("'part' parameter cannot be empty")
        return v

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("'id' parameter cannot be empty")
        return v
class ThumbnailRecordUpdateModel(BaseModel):
    """
    Pydantic model for thumbnail record update validation.
    """
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

class ThumbnailsUpdateModel(BaseModel):
    """
    Pydantic model for thumbnails update validation.
    """
    default: Optional[ThumbnailRecordUpdateModel] = None
    medium: Optional[ThumbnailRecordUpdateModel] = None
    high: Optional[ThumbnailRecordUpdateModel] = None

class SnippetUpdateModel(BaseModel):
    """
    Pydantic model for snippet update validation.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    channelId: Optional[str] = None
    tags: Optional[List[str]] = None
    categoryId: Optional[str] = None
    channelTitle: Optional[str] = None
    thumbnails: Optional[ThumbnailsUpdateModel] = None
    publishedAt: Optional[str] = None
    
class StatusUpdateModel(BaseModel):
    """
    Pydantic model for status update validation.
    """
    uploadStatus: Optional[str] = None
    privacyStatus: Optional[str] = None
    embeddable: Optional[StrictBool] = None
    madeForKids: Optional[StrictBool] = None
    
class StatisticsUpdateModel(BaseModel):
    """
    Pydantic model for statistics update validation.
    """
    viewCount: Optional[int] = None
    likeCount: Optional[int] = None
    dislikeCount: Optional[int] = None
    favoriteCount: Optional[int] = None


class CaptionSnippetModel(BaseModel):
    """Pydantic model for caption snippet validation."""
    
    videoId: str = Field(
        ..., 
        description="The ID that YouTube uses to uniquely identify the video that the caption track is associated with."
    )

    text: str = Field(
        ...,
        description="The text of the caption track."
    )
    
    @field_validator('videoId')
    @classmethod
    def validate_videoId(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("videoId must be a non-empty string.")
        return v.strip()

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("text must be a non-empty string.")
        return v.strip()
    
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

class ThumbnailRecordUploadModel(BaseModel):
    """
    Pydantic model for thumbnail record upload validation.
    """
    url: str
    width: int
    height: int

class ThumbnailsUploadModel(BaseModel):
    """
    Pydantic model for thumbnails upload validation.
    """
    default: ThumbnailRecordUploadModel
    medium: ThumbnailRecordUploadModel
    high: ThumbnailRecordUploadModel

class SnippetUploadModel(BaseModel):
    """
    Pydantic model for snippet upload validation.
    """
    title: str
    description: str
    channelId: str
    tags: List[str]
    categoryId: str
    channelTitle: str
    thumbnails: ThumbnailsUploadModel

class StatusUploadModel(BaseModel):
    """
    Pydantic model for status upload validation.
    """
    uploadStatus: str
    privacyStatus: str
    embeddable: StrictBool
    madeForKids: StrictBool

class VideoUploadModel(BaseModel):
    """
    Pydantic model for video upload validation.
    """
    snippet: SnippetUploadModel
    status: StatusUploadModel

class ChannelUpdateProperties(BaseModel):
    """Pydantic model for validating channel update properties."""
    categoryId: Optional[str] = None
    forUsername: Optional[str] = None
    hl: Optional[str] = None
    managedByMe: Optional[bool] = None
    maxResults: Optional[int] = None
    mine: Optional[bool] = None
    mySubscribers: Optional[bool] = None
    onBehalfOfContentOwner: Optional[str] = None
    
    @field_validator('categoryId')
    @classmethod
    def validate_category_id(cls, v):
        if v is not None and not v.strip():
            raise ValueError("categoryId cannot be an empty string.")
        # Note: Database validation for categoryId is handled in the function itself
        # as it requires access to the DB which is not available in the model context
        return v
    
    @field_validator('forUsername')
    @classmethod
    def validate_for_username(cls, v):
        if v is not None and not v.strip():
            raise ValueError("forUsername cannot be an empty string.")
        return v
    
    @field_validator('hl')
    @classmethod
    def validate_hl(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("hl cannot be an empty string.")
            valid_hl_values = [
                "af", "az", "id", "ms", "bs", "ca", "cs", "da", "de", "et",
                "en-IN", "en-GB", "en", "es", "es-419", "es-US", "eu", "fil",
                "fr", "fr-CA", "gl", "hr", "zu", "is", "it", "sw", "lv", "lt",
                "hu", "nl", "no", "uz", "pl", "pt-PT", "pt", "ro", "sq", "sk",
                "sl", "sr-Latn", "fi", "sv", "vi", "tr", "be", "bg", "ky", "kk",
                "mk", "mn", "ru", "sr", "uk", "el", "hy", "iw", "ur", "ar", "fa",
                "ne", "mr", "hi", "as", "bn", "pa", "gu", "or", "ta", "te", "kn",
                "ml", "si", "th", "lo", "my", "ka", "am", "km"
            ]
            if v not in valid_hl_values:
                raise ValueError("Invalid hl value, must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km")
        return v
    
    @field_validator('maxResults')
    @classmethod
    def validate_max_results(cls, v):
        if v is not None and v < 0:
            raise ValueError("maxResults cannot be negative.")
        return v
    
    @field_validator('onBehalfOfContentOwner')
    @classmethod
    def validate_on_behalf_of_content_owner(cls, v):
        if v is not None and not v.strip():
            raise ValueError("onBehalfOfContentOwner cannot be an empty string.")
        return v
    
    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the model


class UpdateChannelSectionSnippet(BaseModel):
    """Pydantic model for validating channel section snippet."""
    channelId: Optional[str] = None
    type: Optional[str] = None
    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the model

class InsertChannelSectionSnippet(BaseModel):
    """Pydantic model for validating channel section snippet."""
    channelId: str
    type: str
    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the model

class CaptionUpdateSnippetModel(BaseModel):
    """Pydantic model for validating caption snippet."""
    videoId: Optional[str] = None
    text: Optional[str] = None

    @field_validator('videoId')
    @classmethod
    def validate_videoId(cls, v):
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("videoId must be a non-empty string.")
        return v
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("text must be a non-empty string.")
        return v

    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the model