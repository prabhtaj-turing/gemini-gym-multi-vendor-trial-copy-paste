from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ParameterSchema(BaseModel):
    """Defines the schema for a single function parameter."""
    type: str = Field(..., description="The data type of the parameter (e.g., 'STRING', 'INTEGER', 'OBJECT').")
    description: str = Field(..., description="A description of what the parameter is.")

class ParametersDefinition(BaseModel):
    """Defines the JSON schema for all parameters of a function."""
    type: str = Field(default="OBJECT", description="The type of the schema, typically 'OBJECT'.")
    properties: Dict[str, ParameterSchema] = Field(..., description="A dictionary mapping parameter names to their individual schemas.")
    required: Optional[List[str]] = Field(None, description="An optional list of required parameter names.")

class Tool(BaseModel):
    """Represents a single tool's FCSpec."""
    name: str = Field(..., description="The name of the tool/function.")
    description: str = Field(..., description="A detailed description of what the tool does.")
    parameters: ParametersDefinition = Field(..., description="The schema defining the function's parameters.")

class ToolContainer(BaseModel):
    """Validates the final tool structure returned for the Google Generative AI model."""
    tool: List[Tool] = Field(..., description="A list containing the function declaration.", min_items=1, max_items=1)

class ToolExplorerDB(BaseModel):
    """The structure of the database for tool explorer service."""
    services: Dict[str, Dict[str, Tool]] = Field(..., description="Services mapped to their tools.")