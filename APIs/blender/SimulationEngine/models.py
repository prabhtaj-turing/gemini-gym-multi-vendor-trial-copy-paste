from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Literal

from pydantic import BaseModel, Field, conlist, field_validator

# --- Enums ---

class BlenderObjectType(str, Enum):
    MESH = "MESH"
    CAMERA = "CAMERA"
    LIGHT = "LIGHT"
    EMPTY = "EMPTY"
    # Add other common Blender object types as needed

class RenderEngineType(str, Enum):
    CYCLES = "CYCLES"
    EEVEE = "EEVEE"
    WORKBENCH = "WORKBENCH"

class PolyhavenAssetTypeAPI(str, Enum):
    """Asset types used in API parameters like download_polyhaven_asset."""
    HDRIS = "hdris"
    TEXTURES = "textures"
    MODELS = "models"

class PolyhavenAssetTypeData(str, Enum):
    """Concrete asset types as returned by Polyhaven for an individual asset."""
    HDRI = "hdri"
    TEXTURE = "texture"
    MODEL = "model"

class PolyhavenAssetTypeSearchable(str, Enum):
    """Asset types used for searching or getting categories, including 'all'."""
    HDRIS = "hdris"
    TEXTURES = "textures"
    MODELS = "models"
    ALL = "all"

class Hyper3DMode(str, Enum):
    MAIN_SITE = "MAIN_SITE"
    FAL_AI = "FAL_AI"

class JobOverallStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    SUCCESS_QUEUED = "success_queued" # For initial submission

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"

_ASSET_TYPE_SEARCH_TO_DATA_MAP = {
    PolyhavenAssetTypeSearchable.HDRIS.value: PolyhavenAssetTypeData.HDRI.value,
    PolyhavenAssetTypeSearchable.TEXTURES.value: PolyhavenAssetTypeData.TEXTURE.value,
    PolyhavenAssetTypeSearchable.MODELS.value: PolyhavenAssetTypeData.MODEL.value,
}

_VALID_ASSET_TYPES_ENUM_VALUES = [item.value for item in PolyhavenAssetTypeSearchable]
_EXPECTED_ASSET_TYPES_FOR_ERROR_MSG = ['all', 'hdris', 'textures', 'models']

# General compatibility of file formats with API asset types
_COMPATIBLE_FORMATS_BY_ASSET_TYPE_API = {
    PolyhavenAssetTypeAPI.HDRIS: ['hdr', 'exr'],
    PolyhavenAssetTypeAPI.TEXTURES: ['jpg', 'png'],
    PolyhavenAssetTypeAPI.MODELS: ['gltf', 'fbx', 'blend'],
}
# --- Basic Data Structures ---

ColorRGB = conlist(float, min_length=3, max_length=3) # R, G, B (0-1)
Vector3D = conlist(float, min_length=3, max_length=3) # X, Y, Z

# --- Blender-Specific Models ---

class WorldSettingsModel(BaseModel):
    ambient_color: ColorRGB = Field(default_factory=lambda: [0.05, 0.05, 0.05])
    horizon_color: ColorRGB = Field(default_factory=lambda: [0.5, 0.5, 0.5])
    # Add other world settings like environment texture (HDRI) linking here later
    environment_texture_polyhaven_id: Optional[str] = None
    environment_texture_strength: float = 1.0

    class Config:
        validate_assignment = True
        extra = "forbid"  # Forbid extra fields

class RenderSettingsModel(BaseModel):
    engine: RenderEngineType = RenderEngineType.CYCLES
    resolution_x: int = 1920
    resolution_y: int = 1080
    resolution_percentage: int = 100
    filepath: str = "/tmp/render_####.png" # Blender's default pattern
    # Add other render settings as needed

    class Config:
        validate_assignment = True
        extra = "forbid"  # Forbid extra fields

class MaterialModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str # Should be unique
    base_color_value: ColorRGB = Field(default_factory=lambda: [0.8, 0.8, 0.8])
    base_color_texture_polyhaven_id: Optional[str] = None # Polyhaven asset_id
    metallic: float = 0.0
    roughness: float = 0.5
    # Store other PBR properties or simplified node graph if needed

    class Config:
        validate_assignment = True
        extra = "forbid"  # Forbid extra fields

class BlenderObjectModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str # Should be unique within a scene
    type: BlenderObjectType
    location: Vector3D = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation_euler: Vector3D = Field(default_factory=lambda: [0.0, 0.0, 0.0]) # Radians
    scale: Vector3D = Field(default_factory=lambda: [1.0, 1.0, 1.0])
    dimensions: Vector3D = Field(default_factory=lambda: [2.0, 2.0, 2.0]) # Initial default cube size
    vertex_count: Optional[int] = None
    edge_count: Optional[int] = None
    face_count: Optional[int] = None
    material_names: List[str] = Field(default_factory=list) # Names of MaterialModel instances
    is_visible: bool = True
    is_renderable: bool = True
    parent_name: Optional[str] = None # Name of parent BlenderObjectModel
    # Custom properties for specific types
    camera_focal_length: Optional[float] = None # For CAMERA type
    light_energy: Optional[float] = None # For LIGHT type
    light_color: Optional[ColorRGB] = None # For LIGHT type

    class Config:
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"  # Forbid extra fields

class BlenderObjectInfoModel(BaseModel):
    """
    Represents the detailed information about a specific Blender object,
    as returned by the get_object_info function.
    """
    name: str
    type: BlenderObjectType  # e.g., 'MESH', 'CAMERA', 'LIGHT'
    location: Vector3D  # X, Y, Z coordinates
    rotation_euler: Vector3D  # X, Y, Z Euler rotation in radians
    scale: Vector3D  # X, Y, Z scale factors
    dimensions: Vector3D  # X, Y, Z dimensions of the object's bounding box
    vertex_count: Optional[int] = None
    edge_count: Optional[int] = None
    face_count: Optional[int] = None
    material_names: List[str] = Field(default_factory=list)
    is_visible: bool
    is_renderable: bool

    class Config:
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"  # Forbid extra fields

class SceneModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = "Scene"
    objects: Dict[str, BlenderObjectModel] = Field(default_factory=dict) # name:Object
    active_camera_name: Optional[str] = None # Name of a BlenderObjectModel of type CAMERA
    world_settings: WorldSettingsModel = Field(default_factory=WorldSettingsModel)
    render_settings: RenderSettingsModel = Field(default_factory=RenderSettingsModel)

    @property
    def camera_count(self) -> int:
        return sum(1 for obj in self.objects.values() if obj.type == BlenderObjectType.CAMERA)

    @property
    def light_count(self) -> int:
        return sum(1 for obj in self.objects.values() if obj.type == BlenderObjectType.LIGHT)

    @property
    def object_count(self) -> int:
        return len(self.objects)

    class Config:
        validate_assignment = True
        extra = "forbid"  # Forbid extra fields

# --- Polyhaven Related Models ---

class PolyhavenAssetInternalInfo(BaseModel):
    asset_id: str # Polyhaven's ID, unique key
    name: str
    type: PolyhavenAssetTypeData # e.g., 'hdri', 'texture', 'model'
    tags: List[str] = Field(default_factory=list)
    author: Optional[str] = None
    resolution_options: List[str] = Field(default_factory=list)
    file_format_options: List[str] = Field(default_factory=list)
    # Simulation-specific state
    is_downloaded: bool = False
    downloaded_resolution: Optional[str] = None
    downloaded_file_format: Optional[str] = None
    local_file_path: Optional[str] = None
    blender_name: Optional[str] = None # Name of imported object/material/world in Blender
    # Link to created Blender entities
    imported_as_blender_object_id: Optional[uuid.UUID] = None
    imported_as_blender_material_id: Optional[uuid.UUID] = None
    imported_as_world_environment: bool = False

class PolyhavenServiceStatusModel(BaseModel):
    is_enabled: bool = True # Default to enabled for simulation
    message: str = "Polyhaven integration is enabled."

# Input validation for search_polyhaven_assets function
class SearchPolyhavenAssetsArguments(BaseModel):
    asset_type: str = Field(
        default=PolyhavenAssetTypeSearchable.ALL.value,
        description="Type of assets to search for (hdris, textures, models, all)"
    )
    categories: Optional[str] = Field(
        default=None,
        description="Optional comma-separated list of categories to filter by"
    )

    @field_validator('asset_type')
    def asset_type_must_be_valid_enum_value(cls, v: str):
        if v not in _VALID_ASSET_TYPES_ENUM_VALUES:
            raise ValueError(f"Invalid asset_type: '{v}'. Must be one of {_EXPECTED_ASSET_TYPES_FOR_ERROR_MSG}.")
        return v

    class Config:
        validate_assignment = True

class DownloadPolyhavenAssetArguments(BaseModel):
    asset_id: str = Field(title="Asset Id")
    asset_type: str = Field(title="Asset Type")
    resolution: str = Field(default="1k", title="Resolution")
    file_format: Optional[str] = Field(default=None, title="File Format")

    class Config:
        title = "download_polyhaven_assetArguments" # To match schema title if needed for generation
        extra = 'forbid'
# --- Hyper3D Related Models ---

class Hyper3DServiceStatusModel(BaseModel):
    is_enabled: bool = True # Default to enabled
    mode: Optional[Hyper3DMode] = Hyper3DMode.MAIN_SITE # Default mode
    message: str = "Hyper3D Rodin integration is enabled."

class Hyper3DJobModel(BaseModel):
    internal_job_id: uuid.UUID = Field(default_factory=uuid.uuid4) # Unique ID for DB tracking
    mode_at_creation: Hyper3DMode
    
    # Input parameters stored for reference
    text_prompt: Optional[str] = None
    input_image_paths: Optional[List[str]] = None
    input_image_urls: Optional[List[str]] = None
    bbox_condition: Optional[List[float]] = None # Should be List of 3 floats

    # Submission response details
    submission_status: JobOverallStatus = JobOverallStatus.PENDING
    submission_message: str = "Job initiated."
    task_uuid: Optional[str] = None # For MAIN_SITE
    request_id: Optional[str] = None # For FAL_AI
    subscription_key: Optional[str] = None # For MAIN_SITE (from generation response)

    # Polling status details
    poll_overall_status: JobOverallStatus = JobOverallStatus.PENDING
    poll_message: str = "Job status not yet polled."
    poll_details_specific: Optional[Union[List[str], str]] = None # List[str] for MAIN_SITE, str for FAL_AI
    
    # Import details
    asset_name_for_import: Optional[str] = None # User-provided name for the asset in Blender
    import_status: Optional[ExecutionStatus] = None
    import_message: Optional[str] = None
    imported_blender_object_id: Optional[uuid.UUID] = None # Link to BlenderObjectModel
    imported_blender_object_name: Optional[str] = None
    imported_blender_object_type: Optional[BlenderObjectType] = None

    @property
    def is_completed(self) -> bool:
        return self.poll_overall_status in [JobOverallStatus.COMPLETED, JobOverallStatus.FAILED, JobOverallStatus.CANCELED]

    @property
    def is_successful(self) -> Optional[bool]:
        if not self.is_completed:
            return None
        return self.poll_overall_status == JobOverallStatus.COMPLETED

# --- Code Execution Model ---

class BlenderCodeExecutionOutcomeModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: str # Store as ISO format string
    code_executed: str
    status: ExecutionStatus
    output: Optional[str] = None
    error_message: Optional[str] = None
    return_value_str: Optional[str] = None # Store string representation of return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp format using centralized validation."""
        from common_utils.datetime_utils import validate_blender_datetime, InvalidDateTimeFormatError
        try:
            return validate_blender_datetime(v)
        except InvalidDateTimeFormatError as e:
            from blender.SimulationEngine.custom_errors import InvalidDateTimeFormatError as BlenderInvalidDateTimeFormatError
            raise BlenderInvalidDateTimeFormatError(f"Invalid timestamp format: {e}")

# --- Main Database Model ---

class BlenderDB(BaseModel):
    # Single current scene as per API structure
    current_scene: SceneModel = Field(default_factory=SceneModel)
    
    # Global materials, accessible by name
    materials: Dict[str, MaterialModel] = Field(default_factory=dict) # name:Material

    # Polyhaven simulation data
    polyhaven_service_status: PolyhavenServiceStatusModel = Field(default_factory=PolyhavenServiceStatusModel)
    polyhaven_categories_cache: Dict[PolyhavenAssetTypeSearchable, List[str]] = Field(default_factory=dict)
    polyhaven_assets_db: Dict[str, PolyhavenAssetInternalInfo] = Field(default_factory=dict) # asset_id:AssetInfo
        
    # Hyper3D simulation data
    hyper3d_service_status: Hyper3DServiceStatusModel = Field(default_factory=Hyper3DServiceStatusModel)
    hyper3d_jobs: Dict[uuid.UUID, Hyper3DJobModel] = Field(default_factory=dict) # internal_job_id:JobDetails

    # Logs for executed Python code
    execution_logs: List[BlenderCodeExecutionOutcomeModel] = Field(default_factory=list)

    # Configuration for the simulation itself, if any
    # e.g., base_file_path_for_downloads: str = "/tmp/blender_sim_downloads/"

    class Config:
        validate_assignment = True # Ensures type checking on attribute assignment

# To handle forward references if models were in different files or for complex nesting:
# BlenderObjectModel.update_forward_refs()
# SceneModel.update_forward_refs()
# etc. (Not strictly necessary here as they are all defined before use or use string names for refs)


class GenerateHyper3DModelViaTextResponse(BaseModel):
    """
    Defines the structure of the dictionary returned by generate_hyper3d_model_via_text.
    """
    status: Literal['success_queued', 'failure']
    message: str
    task_uuid: Optional[str] = None
    request_id: Optional[str] = None
    subscription_key: Optional[str] = None


class ImportGeneratedAssetArguments(BaseModel):
    name: str
    task_uuid: str = Field(default="null")
    request_id: str = Field(default="null")


class ImportGeneratedAssetResponse(BaseModel):
    """
    Defines the structure of the dictionary returned by import_generated_asset.
    """
    status: Literal['success', 'failure']
    message: str
    asset_name_in_blender: Optional[str] = None
    blender_object_type: Optional['BlenderObjectType'] = None # Forward reference
