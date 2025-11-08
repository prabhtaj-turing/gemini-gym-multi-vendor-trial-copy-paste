from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional, Union, Literal
from bson import ObjectId
from enum import Enum, IntEnum

class MongoDBBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: lambda oid: str(oid)}
        extra = 'forbid'

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        try:
            return ObjectId(str(v))
        except Exception as e:
            raise ValueError(f"Invalid ObjectId: {e}")

# --------------------------
# Tool Input Validation Models
# --------------------------

class SwitchConnectionInput(MongoDBBaseModel):
    connection_string: Optional[str] = Field(
        None,
        alias="connectionString",
        description="MongoDB connection string to switch to (in the mongodb:// or mongodb+srv:// format)"
    )

class ListCollectionsInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)

class ListDatabasesInput(MongoDBBaseModel):
    pass  # No fields required

class CollectionIndexesInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)

class CreateIndexInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    keys: Dict[str, int] = Field(..., description="The index definition. Each key is a field name and each value must be an integer representing the index direction: 1 for ascending, -1 for descending.")
    name: Optional[str] = Field(None, min_length=1, max_length=128)

class CollectionSchemaInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)

class FindInput(BaseModel):
    database: str = Field(..., description="Name of the MongoDB database")
    collection: str = Field(..., description="Name of the MongoDB collection")
    filter: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query filter for documents")
    projection: Optional[Dict[str, Any]] = Field(default=None, description="Fields to include/exclude in the result")
    limit: int = Field(default=10, ge=0, description="Maximum number of documents to return (0 = no limit)")
    sort: Optional[Dict[str, int]] = Field(default=None, description="Sort order (e.g., {'name': 1} for ASC)")

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, sort_dict):
        if sort_dict is not None:
            for key, value in sort_dict.items():
                if value not in ( 1, -1):
                    raise ValueError(f"Invalid sort direction for '{key}': must be 1 or -1")
        return sort_dict

    @model_validator(mode="after")
    def check_non_empty_fields(self):
        if not self.database:
            raise ValueError("Database name must not be empty")
        if not self.collection:
            raise ValueError("Collection name must not be empty")
        if self.database.isspace():
            raise ValueError("Database name must not be empty")
        if self.collection.isspace():
            raise ValueError("Collection name must not be empty")
        return self


class InsertManyInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    documents: List[Dict[str, Any]] = Field(..., min_items=1)

class DeleteManyInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    filter: Dict[str, Any] = Field(default_factory=dict)

class CollectionStorageSizeInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)

class CountInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    query: Dict[str, Any] = Field(default_factory=dict)

class DbStatsInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)

class AggregateInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    pipeline: List[Dict[str, Any]] = Field(..., min_items=1)

class UpdateManyInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    filter: Dict[str, Any] = Field(default_factory=dict)
    update: Dict[str, Any] = Field(...)
    upsert: bool = Field(default=False)

class RenameCollectionInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    new_name: str = Field(..., alias="newName", min_length=1, max_length=255)
    drop_target: bool = Field(default=False, alias="dropTarget")
    class Config:
        populate_by_name = True # Allow population by Python attribute name (new_name, drop_target)

class DropDatabaseInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)

class DropCollectionInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)

class AggregateMethodArguments(MongoDBBaseModel):
    pipeline: List[Dict[str, Any]] = Field(..., min_items=1)

class FindMethodArguments(MongoDBBaseModel):
    filter: Dict[str, Any] = Field(default_factory=dict)
    projection: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, ge=0)
    sort: Optional[Dict[str, Any]] = None

class CountMethodArguments(MongoDBBaseModel):
    query: Dict[str, Any] = Field(default_factory=dict)

class AggregateMethod(MongoDBBaseModel):
    name: Literal["aggregate"]
    arguments: AggregateMethodArguments

class FindMethod(MongoDBBaseModel):
    name: Literal["find"]
    arguments: FindMethodArguments

class CountMethod(MongoDBBaseModel):
    name: Literal["count"]
    arguments: CountMethodArguments

Method = Union[AggregateMethod, FindMethod, CountMethod]

class ExplainInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)
    method: List[Method] = Field(..., min_items=1, max_items=1)

class CreateCollectionInput(MongoDBBaseModel):
    database: str = Field(..., min_length=1, max_length=63)
    collection: str = Field(..., min_length=1, max_length=255)

class MongoDBLogsType(str, Enum):
    GLOBAL = "global"
    STARTUP_WARNINGS = "startupWarnings"

class MongoDBLogsInput(MongoDBBaseModel):
    log_type: MongoDBLogsType = Field(default=MongoDBLogsType.GLOBAL, alias="type")
    limit: int = Field(default=50, ge=1, le=1024)

# --- create_index ---
class IndexCreationResult(MongoDBBaseModel):
    """
    Details the result of an index creation operation.
    """
    name: str = Field(
        ...,
        description="The system-generated or user-provided name of the index."
    )
    status_message: Optional[str] = Field(
        default=None,
        description=(
            "A message indicating the outcome, such as 'index created successfully', "
            "or details if the index already existed (e.g., 'index with this name/specification "
            "already exists, no action taken')."
        )
    )

class IndexTypeEnum(IntEnum):
    """
    Enum for supported MongoDB index types/directions.
    """
    ASCENDING = 1
    DESCENDING = -1

# --- collection_storage_size ---
class CollectionStorageStatsOutput(MongoDBBaseModel):
    """
    Pydantic model for the return type of collection_storage_size,
    representing storage utilization statistics for a collection.
    """
    ns: str = Field(..., description="The namespace of the collection.")
    size: float = Field(..., description="The total uncompressed size of the data in the collection in bytes.")
    count: int = Field(..., description="The number of documents in the collection.")
    storage_size: float = Field(..., description="The total amount of storage space allocated to this collection for document storage, including free space, in bytes.")
    avg_obj_size: float = Field(..., description="The average size of an object in the collection in bytes.")
    num_indexes: int = Field(..., description="The number of indexes on the collection.")
    total_index_size: float = Field(..., description="The total size of all indexes on the collection in bytes.")
    scale_factor: Optional[float] = Field(None, description="The scale factor used to calculate storage sizes, if applicable.")
# --- collection_indexes ---
class CollectionIndexDetail(MongoDBBaseModel):
    """
    Describes a single index for a collection.
    """
    v: int = Field(..., description="The index version number.")
    key: Dict[str, Literal[1, -1]] = Field(
        ...,
        description="A dictionary specifying the indexed fields and their sort order (1 for ascending, -1 for descending)."
    )
    name: str = Field(..., description="The name of the index.")
    ns: str = Field(
        ...,
        description="The namespace of the index, typically in the format 'database_name.collection_name'."
    )

class SwitchConnectionResponse(MongoDBBaseModel):
    """
    Represents the outcome of a MongoDB connection switch attempt.
    This model defines the structure of the dictionary returned by the
    `switch_connection` function.
    """
    status: Literal["success", "failure"] = Field(
        ...,  # Ellipsis denotes that this field is required
        description="'success' if the switch was successful, 'failure' otherwise."
    )
    message: Optional[str] = Field(
        default=None,
        description="A descriptive message about the connection attempt (e.g., error details on failure, or success confirmation)."
    )
    active_connection_info: Optional[str] = Field(
        default=None,
        description="Information about the new active connection if the switch was successful (e.g., a masked connection string, server version, database name, or an alias)."
    )
