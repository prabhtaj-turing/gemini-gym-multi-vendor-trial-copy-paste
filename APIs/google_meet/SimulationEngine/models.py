from typing import Optional, Dict
from pydantic import BaseModel, Field, validator

class SpaceContentModel(BaseModel):
    """
    Pydantic model for validating the structure of space_content.
    """
    meetingCode: str
    meetingUri: str
    accessType: str
    entryPointAccess: str = Field("ALL", description="Who can access the entry points (e.g., 'ALL', 'CREATOR_APP_ONLY')")

class SpaceUpdateMaskModel(BaseModel):
    """
    Pydantic model for validating the 'update_mask' dictionary.
    It includes known fields of a space object, all optional for patching.
    It also allows for additional, unspecified fields to be present in the mask.
    """
    id: Optional[str] = None
    meetingCode: Optional[str] = None
    meetingUri: Optional[str] = None
    accessType: Optional[str] = None  # E.g., "TRUSTED", "RESTRICTED", "OPEN"
    entryPointAccess: Optional[str] = None  # E.g., "ALL", "CREATOR_APP_ONLY"

    # Pydantic V2 configuration:
    # Allow any other fields to be part of the update_mask,
    # reflecting "Additional fields that were updated" and the original Dict[str, Any] type hint.
    model_config = {
        "extra": "allow"
    }

# Common parameter validation models that can be reused across the API
class ListParamsBase(BaseModel):
    """
    Base model for common list operation parameters.
    """
    pageSize: int = Field(100, ge=1, description="The maximum number of items to return per page")
    pageToken: Optional[str] = Field(None, description="The token for continued list pagination")

class ParentResourceParams(BaseModel):
    """
    Model for validating parent resource parameters.
    """
    parent: str = Field(..., min_length=1, description="The parent resource name")
    
    @validator('parent')
    def validate_parent(cls, v):
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("parent cannot be empty or whitespace only")
        return v

class ResourceNameParams(BaseModel):
    """
    Model for validating resource name parameters.
    """
    name: str = Field(..., min_length=1, description="The resource name")

class ParticipantSessionsListParams(ParentResourceParams, ListParamsBase):
    """
    Pydantic model for validating ParticipantSessions list function parameters.
    """
    filter: Optional[str] = Field(None, description="An optional filter string to apply to the sessions")

class ParticipantsListParams(ParentResourceParams, ListParamsBase):
    """
    Pydantic model for validating Participants list function parameters.
    """
    pass

class ParticipantsGetParams(ResourceNameParams):
    """
    Pydantic model for validating Participants get function parameters.
    """
    pass

class TranscriptsListParams(ParentResourceParams, ListParamsBase):
    """
    Pydantic model for validating Transcripts list function parameters.
    """
    pass

class TranscriptEntriesListParams(ParentResourceParams, ListParamsBase):
    """
    Pydantic model for validating TranscriptEntries list function parameters.
    """
    pass

class TranscriptEntriesGetParams(ResourceNameParams):
    """
    Pydantic model for validating TranscriptEntries get function parameters.
    """
    pass


# ---------------------------
# Root Database Model
# ---------------------------

class GoogleMeetDB(BaseModel):
    """Validates entire database structure"""
    spaces: Dict[str, SpaceContentModel]
    update_mask: Dict[str, SpaceUpdateMaskModel] = Field(default_factory=dict)
    list_params: Dict[str, ListParamsBase] = Field(default_factory=dict)
    parent_resource_params: Dict[str, ParentResourceParams] = Field(default_factory=dict)
    resource_name_params: Dict[str, ResourceNameParams] = Field(default_factory=dict)
    participant_sessions_list_params: Dict[str, ParticipantSessionsListParams] = Field(default_factory=dict)
    participants_list_params: Dict[str, ParticipantsListParams] = Field(default_factory=dict)
    participants_get_params: Dict[str, ParticipantsGetParams] = Field(default_factory=dict)
    transcripts_list_params: Dict[str, TranscriptsListParams] = Field(default_factory=dict)
    transcript_entries_list_params: Dict[str, TranscriptEntriesListParams] = Field(default_factory=dict)
    transcript_entries_get_params: Dict[str, TranscriptEntriesGetParams] = Field(default_factory=dict)

    class Config:
        str_strip_whitespace = True
