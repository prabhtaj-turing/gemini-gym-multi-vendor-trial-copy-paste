from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class FieldMode(str, Enum):
    NULLABLE = "NULLABLE"
    REQUIRED = "REQUIRED"
    REPEATED = "REPEATED"

class BigQueryFieldType(str, Enum):
    STRING = "STRING"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIME = "TIME"
    BYTES = "BYTES"
    NUMERIC = "NUMERIC"
    BIGNUMERIC = "BIGNUMERIC"
    JSON = "JSON"
    ARRAY = "ARRAY"
    STRUCT = "STRUCT"
    GEOGRAPHY = "GEOGRAPHY"

class SchemaField(BaseModel):
    name: str
    type: BigQueryFieldType
    mode: FieldMode = FieldMode.NULLABLE
    description: Optional[str] = None
    defaultValue: Optional[Any] = None
    fields: Optional[List['SchemaField']] = None

class TableMetadata(BaseModel):
    table_id: str
    dataset_id: str
    project_id: str
    type: str = "TABLE"
    creation_time: datetime
    last_modified_time: Optional[datetime] = None
    expiration_time: Optional[datetime] = None
    num_rows: Optional[int] = None
    size_bytes: Optional[int] = None
    fields: List[SchemaField] = Field(default_factory=list)

class Table(BaseModel):
    metadata: TableMetadata
    rows: List[Dict[str, Any]] = []

class Dataset(BaseModel):
    dataset_id: str
    tables: List[Table] = []

class Project(BaseModel):
    project_id: str
    datasets: List[Dataset] = []

class BigQueryDatabase(BaseModel):
    projects: List[Project] = []
