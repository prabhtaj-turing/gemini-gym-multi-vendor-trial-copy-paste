import json
import os
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Union, Annotated, List, Any

# --- Service Discovery ---
def _get_service_names() -> List[str]:
    """Dynamically discovers service names from the APIs directory structure."""
    try:
        # Go up one level from common_utils to APIs/
        api_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'APIs'))
        services = []
        for entry in os.listdir(api_root_dir):
            # Exclude common_utils and any other non-service directories
            if os.path.isdir(os.path.join(api_root_dir, entry)) and entry not in ["common_utils", "__pycache__"]:
                services.append(entry)
        return sorted(services)
    except FileNotFoundError:
        # Fallback for environments where directory structure might not exist
        return []

# --- Enums ---
# Dynamically create an Enum for service names
Service = Enum("Service", {name: name for name in _get_service_names()})

class MutationName(str, Enum):
    """Enum for possible mutation names."""
    M01 = "m01"
    NO_MUTATION = ""

class DocMode(str, Enum):
    """Valid documentation modes."""
    RAW_DOCSTRING = "raw_docstring"
    CONCISE = "concise"
    MEDIUM_DETAIL = "medium_detail"

# --- Base Configuration Classes ---
class MutationOverride(BaseModel):
    """Defines a override for mutation."""
    mutation_name: Optional[MutationName] = None

class AuthenticationOverride(BaseModel):
    """Defines an override for authentication settings."""
    authentication_enabled: Optional[bool] = None

class AuthenticationOverrideService(BaseModel):
    """Defines an override for authentication settings."""
    authentication_enabled: Optional[bool] = None
    excluded_functions: Optional[List[str]] = None
    is_authenticated: Optional[bool] = None

class ErrorTypeConfig(BaseModel):
    """Configuration for a specific error type."""
    probability: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="Probability of this error occurring (0.0 to 1.0)"
    )
    dampen_factor: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="Dampening factor for error probability (0.0 to 1.0)"
    )
    num_errors_simulated: Optional[int] = Field(
        default=None, ge=0,
        description="Number of errors to simulate for this type"
    )

class ServiceDocumentationConfig(BaseModel):
    """Documentation configuration for a specific service."""
    doc_mode: DocMode = Field(
        description="Documentation mode for the service"
    )

class GlobalDocumentationConfig(BaseModel):
    """Global documentation configuration."""
    doc_mode: DocMode = Field(
        description="Global documentation mode"
    )

class DocumentationConfig(BaseModel):
    """Documentation configuration with global and services sections."""
    global_config: Optional[GlobalDocumentationConfig] = Field(None, alias="global")
    services: Optional[Dict[str, ServiceDocumentationConfig]] = None

    @field_validator('services')
    def validate_service_names(cls, v):
        """Validates that all keys in the services dictionary are valid service names."""
        if v is None:
            return v
        
        valid_service_names = {s.value for s in Service}
        for service_name in v.keys():
            if service_name not in valid_service_names:
                raise ValueError(f"'{service_name}' is not a valid service. Valid services are: {', '.join(sorted(valid_service_names))}")
        return v

class ServiceErrorConfig(BaseModel):
    """Error simulation configuration for a specific service."""
    config: Dict[str, Union[ErrorTypeConfig, Annotated[int, Field(ge=0)]]] = Field(
        description="Error simulation configuration for the service"
    )
    max_errors_per_run: Optional[int] = Field(default=None, ge=0)


class GlobalErrorConfig(BaseModel):
    """Global error simulation configuration."""
    config: Optional[Dict[str, Union[ErrorTypeConfig, Annotated[int, Field(ge=0)]]]] = Field(
        default={},
        description="Global error simulation configuration"
    )
    max_errors_per_run: Optional[int] = Field(default=None, ge=0)


class ErrorSimulationConfig(BaseModel):
    """
    Defines the overall error simulation framework configuration, including global
    settings and service-specific overrides.
    """
    global_config: Optional[GlobalErrorConfig] = Field(None, alias="global")
    services: Optional[Dict[str, ServiceErrorConfig]] = None

    @field_validator('services')
    def validate_service_names(cls, v):
        """Validates that all keys in the services dictionary are valid service names."""
        if v is None:
            return v
        
        valid_service_names = {s.value for s in Service}
        for service_name in v.keys():
            if service_name not in valid_service_names:
                raise ValueError(f"'{service_name}' is not a valid service. Valid services are: {', '.join(sorted(valid_service_names))}")
        return v

class ErrorOverride(BaseModel):
    """Defines an override for error handling settings."""
    error_mode: Optional[str] = None
    print_error_reports: Optional[bool] = None

class ErrorOverrideService(BaseModel):
    """Defines an override for error handling settings per service."""
    error_mode: Optional[str] = None
    print_error_reports: Optional[bool] = None

class MutationConfig(BaseModel):
    """
    Defines the overall mutation framework configuration, including global
    settings and service-specific overrides.
    """
    global_config: Optional[MutationOverride] = Field(None, alias="global")
    services: Optional[Dict[str, MutationOverride]] = None

    @field_validator('services')
    def validate_service_names(cls, v):
        """Validates that all keys in the services dictionary are valid service names."""
        if v is None:
            return v
        
        valid_service_names = {s.value for s in Service}
        for service_name in v.keys():
            if service_name not in valid_service_names:
                raise ValueError(f"'{service_name}' is not a valid service. Valid services are: {', '.join(sorted(valid_service_names))}")
        return v

class AuthenticationConfig(BaseModel):
    """
    Defines the overall authentication framework configuration, including global
    settings and service-specific overrides.
    """
    global_config: Optional[AuthenticationOverride] = Field(None, alias="global")
    services: Optional[Dict[str, AuthenticationOverrideService]] = None

    @field_validator('services')
    def validate_service_names(cls, v):
        """Validates that all keys in the services dictionary are valid service names."""
        if v is None:
            return v
        
        valid_service_names = {s.value for s in Service}
        for service_name in v.keys():
            if service_name not in valid_service_names:
                raise ValueError(f"'{service_name}' is not a valid service. Valid services are: {', '.join(sorted(valid_service_names))}")
        return v

class ErrorModeConfig(BaseModel):
    """
    Defines the overall error handling framework configuration, including global
    settings and service-specific overrides.
    """
    global_config: Optional[ErrorOverride] = Field(None, alias="global")
    services: Optional[Dict[str, ErrorOverrideService]] = None

    @field_validator('services')
    def validate_service_names(cls, v):
        """Validates that all keys in the services dictionary are valid service names."""
        if v is None:
            return v
        
        valid_service_names = {s.value for s in Service}
        for service_name in v.keys():
            if service_name not in valid_service_names:
                raise ValueError(f"'{service_name}' is not a valid service. Valid services are: {', '.join(sorted(valid_service_names))}")
        return v

class SearchEngineConfig(BaseModel):
    pass

class FrameworkFeatureConfig(BaseModel):
    """
    The root model for all framework feature configurations.
    """
    mutation: Optional[MutationConfig] = None
    authentication: Optional[AuthenticationConfig] = None
    search_engine: Optional[SearchEngineConfig] = Field(None, alias="search_engine")
    documentation: Optional[DocumentationConfig] = None
    error: Optional[ErrorSimulationConfig] = None
    error_mode: Optional[ErrorModeConfig] = None

def validate_config(file_path):
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        FrameworkFeatureConfig.model_validate(config_data)
        print("Validation successful!")
    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    validate_config('/Users/mujtaba/Gen Agents/google-agents-api-gen/default_framework_config.json')