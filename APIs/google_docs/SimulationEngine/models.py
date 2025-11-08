from typing import Dict, Any, Union, Optional
from pydantic import BaseModel, ConfigDict

class LocationModel(BaseModel):
    """Model for the 'location' part of an insertText request."""
    model_config = ConfigDict(extra='forbid')
    index: int

class InsertTextPayloadModel(BaseModel):
    """Model for the payload of an 'insertText' request."""
    model_config = ConfigDict(extra='forbid')
    text: str
    location: LocationModel

class InsertTextRequestModel(BaseModel):
    """Model for a complete 'insertText' request object."""
    model_config = ConfigDict(extra='forbid')
    insertText: InsertTextPayloadModel

class UpdateDocumentStylePayloadModel(BaseModel):
    """Model for the payload of an 'updateDocumentStyle' request."""
    model_config = ConfigDict(extra='forbid')
    documentStyle: Dict[str, Any]  # The internal structure of documentStyle is not specified.

class UpdateDocumentStyleRequestModel(BaseModel):
    """Model for a complete 'updateDocumentStyle' request object."""
    model_config = ConfigDict(extra='forbid')
    updateDocumentStyle: UpdateDocumentStylePayloadModel

class RangeModel(BaseModel):
    """Model for the 'range' part of a deleteContentRange request."""
    model_config = ConfigDict(extra='forbid')
    startIndex: int
    endIndex: int

class DeleteContentRangePayloadModel(BaseModel):
    """Model for the payload of a 'deleteContentRange' request."""
    model_config = ConfigDict(extra='forbid')
    range: RangeModel

class DeleteContentRangeRequestModel(BaseModel):
    """Model for a complete 'deleteContentRange' request object."""
    model_config = ConfigDict(extra='forbid')
    deleteContentRange: DeleteContentRangePayloadModel

class ContainsTextModel(BaseModel):
    """Model for the 'containsText' part of a replaceAllText request."""
    model_config = ConfigDict(extra='forbid')
    text: str
    matchCase: Optional[bool] = False

class ReplaceAllTextPayloadModel(BaseModel):
    """Model for the payload of a 'replaceAllText' request."""
    model_config = ConfigDict(extra='forbid')
    containsText: ContainsTextModel
    replaceText: str

class ReplaceAllTextRequestModel(BaseModel):
    """Model for a complete 'replaceAllText' request object."""
    model_config = ConfigDict(extra='forbid')
    replaceAllText: ReplaceAllTextPayloadModel

class InsertTableLocationModel(BaseModel):
    """Model for the 'location' part of an insertTable request."""
    model_config = ConfigDict(extra='forbid')
    index: int

class InsertTableEndOfSegmentLocationModel(BaseModel):
    """Model for the 'endOfSegmentLocation' part of an insertTable request."""
    model_config = ConfigDict(extra='forbid')
    segmentId: str  # Empty string ("") indicates document body

class InsertTablePayloadModel(BaseModel):
    """Model for the payload of an 'insertTable' request."""
    model_config = ConfigDict(extra='forbid')
    rows: int
    columns: int
    location: Optional[InsertTableLocationModel] = None
    endOfSegmentLocation: Optional[InsertTableEndOfSegmentLocationModel] = None

class InsertTableRequestModel(BaseModel):
    """Model for a complete 'insertTable' request object."""
    model_config = ConfigDict(extra='forbid')
    insertTable: InsertTablePayloadModel

# Union model for items in the 'requests' list.
# An item must be one of the explicitly defined request types.
RequestItemModel = Union[InsertTextRequestModel, UpdateDocumentStyleRequestModel, DeleteContentRangeRequestModel, ReplaceAllTextRequestModel, InsertTableRequestModel]