"""
Pydantic Models for the Generic Service

This module defines the data structures for the service using Pydantic, ensuring
data validation and consistency across the API, the simulation engine, and the
database.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# ---------------------------
# Enum Types
# ---------------------------

class EntityStatus(str, Enum):
    """An example enum for the status of an entity."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

# ---------------------------
# Input Validation Models
# ---------------------------

class ComplexInput(BaseModel):
    """
    Defines the structure for a complex dictionary input parameter.
    This model is used to validate the structure and types of the data within
    the dictionary passed to a tool.
    """
    config_name: str = Field(
        ...,
        description="The name of the configuration. This is a mandatory, non-empty string.",
        min_length=1
    )
    value: int = Field(
        ...,
        description="A numerical value for the configuration. This is a mandatory, positive integer.",
        gt=0
    )
    enabled: bool = Field(
        True,
        description="A flag to enable or disable this configuration. This is optional and defaults to True if not provided."
    )

# ---------------------------
# Tool Interface Models
# ---------------------------

class ToolInput(BaseModel):
    """Input model for the generic tool, providing validation and documentation."""
    entity_name: str = Field(
        ...,
        description="The name of the anismol to create or modify. This must be a non-empty string with a maximum length of 100 characters.",
        min_length=1,
        max_length=100
    )
    complex_param: ComplexInput = Field(
        ...,
        description="A dictionary containing the configuration for the entity."
    )
    is_dry_run: bool = Field(
        False,
        description="If True, the function will only validate the inputs and return a success message without performing any actual entity creation or modification. Defaults to False."
    )

class ParamsReceived(BaseModel):
    """A dictionary reflecting the exact parameters that were received and validated by the tool."""
    entity_name: str = Field(..., description="The original 'entity_name' input.")
    complex_param: ComplexInput = Field(..., description="The original 'complex_param' input, validated and with defaults applied.")
    is_dry_run: bool = Field(..., description="The original 'is_dry_run' input.")

class ToolOutputData(BaseModel):
    """A dictionary containing the detailed payload of the response."""
    entity_id: str = Field(..., description="The unique identifier of the entity that was affected by the operation. In a dry run, this will be 'dry-run-not-created'.")
    params_received: ParamsReceived = Field(..., description="A dictionary reflecting the exact parameters that were received and validated by the tool.")

class ToolOutput(BaseModel):
    """Defines the exact structure of the JSON returned by the tool."""
    success: bool = Field(..., description="Indicates whether the operation was successful.")
    message: str = Field(..., description="A human-readable message describing the outcome.")
    data: ToolOutputData = Field(..., description="A dictionary containing the detailed payload of the response.")



# ---------------------------
# Internal Storage Models
# ---------------------------

class EntityStorage(BaseModel):
    """Internal storage model for an entity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: EntityStatus = Field(default=EntityStatus.ACTIVE)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        """Ensures the ID is a valid UUID4 string."""
        if not v.strip():
            raise ValueError('ID cannot be an empty string')
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError('ID must be a valid UUID4 string')
        return v

# ---------------------------
# Root Database Model
# ---------------------------

class GenericServiceDB(BaseModel):
    """
    The root model for the entire database. It validates the structure of all
    tables and their contents.
    """
    entities: Dict[str, EntityStorage] = Field(default_factory=dict)
    # The 'actions' table has been removed for a more generic template.
    # If you need to audit tool calls, you can add:
    # actions: List[Action] = Field(default_factory=list)
    # ...and define the Action model accordingly.

    class Config:
        str_strip_whitespace = True