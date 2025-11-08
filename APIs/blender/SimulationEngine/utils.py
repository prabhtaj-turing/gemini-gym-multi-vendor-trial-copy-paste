import uuid
from typing import Any, Dict, List, Optional

from .db import DB  # Import the global DB dictionary

# Import Enums and other necessary specific types from models
from . import models # Changed to import the module

from . import custom_errors # Changed to import the module
import os
from .models import PolyhavenAssetTypeData
import uuid
# --- Category 1: Consistency Maintenance Functions (Update DB Status) ---

def add_object_to_scene(scene_name: str, object_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new object to the specified scene in the global DB (dictionary).
    Modifies the global DB.
    Assumes object_data is a valid dictionary for an object.
    """
    if 'current_scene' not in DB:
        raise custom_errors.SceneNotFoundError("No current scene available in DB.")
    current_scene_dict = DB['current_scene']

    if not current_scene_dict or current_scene_dict.get('name') != scene_name:
        raise custom_errors.SceneNotFoundError(f"Scene '{scene_name}' does not match current scene '{current_scene_dict.get('name')}'.")

    if 'name' not in object_data:
        raise ValueError("Object data must include a 'name'.")
    object_name = object_data['name']

    scene_objects = current_scene_dict.get('objects', {})
    if object_name in scene_objects:
        raise custom_errors.DuplicateNameError(f"Object '{object_name}' already exists in scene '{scene_name}'.")

    # Ensure ID is a string
    if 'id' not in object_data or object_data['id'] is None:
        object_data['id'] = str(uuid.uuid4())
    elif not isinstance(object_data['id'], str): # Convert if it's UUID object or other
        object_data['id'] = str(object_data['id'])
            
    # Ensure default fields if not provided, matching typical JSON structure
    object_data.setdefault('type', models.BlenderObjectType.MESH.value) # Default to MESH if not specified
    object_data.setdefault('location', [0.0, 0.0, 0.0])
    object_data.setdefault('rotation_euler', [0.0, 0.0, 0.0])
    object_data.setdefault('scale', [1.0, 1.0, 1.0])
    object_data.setdefault('dimensions', [2.0, 2.0, 2.0]) # Default cube size
    object_data.setdefault('material_names', [])
    object_data.setdefault('is_visible', True)
    object_data.setdefault('is_renderable', True)

    if 'objects' not in current_scene_dict: # Should exist if current_scene_dict is valid
        current_scene_dict['objects'] = {}
    current_scene_dict['objects'][object_name] = object_data
    
    return object_data.copy()


def remove_object_from_scene(scene_name: str, object_name: str) -> bool:
    """
    Removes an object from the specified scene in the global DB.
    Modifies the global DB.
    """
    if 'current_scene' not in DB:
        raise custom_errors.SceneNotFoundError("No current scene available in DB.")
    current_scene_dict = DB['current_scene']

    if not current_scene_dict or current_scene_dict.get('name') != scene_name:
        raise custom_errors.SceneNotFoundError(f"Scene '{scene_name}' does not match current scene '{current_scene_dict.get('name')}'.")

    scene_objects = current_scene_dict.get('objects', {})
    if object_name not in scene_objects:
        raise custom_errors.ObjectNotFoundError(f"Object '{object_name}' not found in scene '{scene_name}'.")

    removed_object = scene_objects.pop(object_name)

    if current_scene_dict.get('active_camera_name') == removed_object.get('name'):
        current_scene_dict['active_camera_name'] = None
    
    for obj_iter_name, obj_iter_data in scene_objects.items():
        if obj_iter_data.get('parent_name') == removed_object.get('name'):
            obj_iter_data['parent_name'] = None
            
    return True

def update_polyhaven_asset_download_status(
    asset_id: str,
    is_downloaded: bool,
    downloaded_resolution: Optional[str] = None,
    downloaded_file_format: Optional[str] = None,
    local_file_path: Optional[str] = None,
    blender_name: Optional[str] = None,
    imported_as_blender_object_id: Optional[str] = None,
    imported_as_blender_material_id: Optional[str] = None,
    imported_as_world_environment: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Updates download status of a Polyhaven asset in the global DB.
    Modifies the global DB. Asset IDs in DB are strings.
    """
    if 'polyhaven_assets_db' not in DB or asset_id not in DB['polyhaven_assets_db']:
        raise custom_errors.AssetNotFoundError(f"Polyhaven asset '{asset_id}' not found.")
    
    asset_info_dict = DB['polyhaven_assets_db'][asset_id]
    asset_info_dict['is_downloaded'] = is_downloaded

    if is_downloaded:
        asset_info_dict['downloaded_resolution'] = downloaded_resolution
        asset_info_dict['downloaded_file_format'] = downloaded_file_format
        asset_info_dict['local_file_path'] = local_file_path
        asset_info_dict['blender_name'] = blender_name
        asset_info_dict['imported_as_blender_object_id'] = imported_as_blender_object_id # Keep as string
        asset_info_dict['imported_as_blender_material_id'] = imported_as_blender_material_id # Keep as string
        if imported_as_world_environment is not None:
             asset_info_dict['imported_as_world_environment'] = imported_as_world_environment
    else: # Reset fields
        asset_info_dict['downloaded_resolution'] = None
        asset_info_dict['downloaded_file_format'] = None
        asset_info_dict['local_file_path'] = None
        asset_info_dict['blender_name'] = None
        asset_info_dict['imported_as_blender_object_id'] = None
        asset_info_dict['imported_as_blender_material_id'] = None
        asset_info_dict['imported_as_world_environment'] = False
        
    return asset_info_dict.copy()


def apply_texture_to_material(
    material_name: str,
    texture_polyhaven_id: Optional[str] = None,
    base_color_value: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Applies texture or color to a material in the global DB.
    Modifies the global DB.
    """
    if 'materials' not in DB or material_name not in DB['materials']:
        raise custom_errors.MaterialNotFoundError(f"Material '{material_name}' not found.")
    material_dict = DB['materials'][material_name]

    if texture_polyhaven_id:
        if 'polyhaven_assets_db' not in DB or texture_polyhaven_id not in DB['polyhaven_assets_db']:
            raise custom_errors.AssetNotFoundError(f"Polyhaven texture asset '{texture_polyhaven_id}' not found.")
        asset_info_dict = DB['polyhaven_assets_db'][texture_polyhaven_id]
        
        if asset_info_dict.get('type') != models.PolyhavenAssetTypeData.TEXTURE.value:
            raise ValueError(f"Asset '{texture_polyhaven_id}' is not a texture (type: {asset_info_dict.get('type')}).")
        if not asset_info_dict.get('is_downloaded'):
            raise custom_errors.InvalidStateError(f"Texture asset '{texture_polyhaven_id}' must be downloaded before applying.")
        
        material_dict['base_color_texture_polyhaven_id'] = texture_polyhaven_id
        material_dict['base_color_value'] = [0.8, 0.8, 0.8] # Default when texture is applied
    elif base_color_value:
        if not (isinstance(base_color_value, list) and len(base_color_value) == 3 and all(isinstance(v, (float, int)) for v in base_color_value)):
            raise ValueError("Invalid base_color_value format. Expected list of 3 floats/ints.")
        material_dict['base_color_value'] = base_color_value
        material_dict['base_color_texture_polyhaven_id'] = None
    else:
        raise ValueError("Either texture_polyhaven_id or base_color_value must be provided.")

    return material_dict.copy()

def assign_material_to_object(
    scene_name: str,
    object_name: str,
    material_name: str,
    replace_existing: bool = True
) -> bool:
    """
    Assigns an existing material to an object in the global DB.
    Modifies the global DB.
    """
    if 'current_scene' not in DB:
        raise custom_errors.SceneNotFoundError("No current scene available in DB.")
    current_scene_dict = DB['current_scene']

    if not current_scene_dict or current_scene_dict.get('name') != scene_name:
        raise custom_errors.SceneNotFoundError(f"Scene '{scene_name}' does not match current scene '{current_scene_dict.get('name')}'.")

    scene_objects = current_scene_dict.get('objects', {})
    if object_name not in scene_objects:
        raise custom_errors.ObjectNotFoundError(f"Object '{object_name}' not found in scene '{scene_name}'.")
    obj_dict = scene_objects[object_name]

    if 'materials' not in DB or material_name not in DB['materials']:
        raise custom_errors.MaterialNotFoundError(f"Material '{material_name}' not found.")

    if 'material_names' not in obj_dict or not isinstance(obj_dict['material_names'], list):
        obj_dict['material_names'] = []


    if replace_existing:
        obj_dict['material_names'] = [material_name]
    else:
        if material_name not in obj_dict['material_names']:
            obj_dict['material_names'].append(material_name)
            
    return True

def create_material(material_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new material in the global DB.
    Modifies the global DB.
    """
    if 'name' not in material_data:
        raise ValueError("Material data must include a 'name'.")
    material_name = material_data['name']

    materials_dict = DB.get('materials', {})
    if material_name in materials_dict:
        raise custom_errors.DuplicateNameError(f"Material '{material_name}' already exists.")

    if 'id' not in material_data or material_data['id'] is None:
        material_data['id'] = str(uuid.uuid4())
    elif not isinstance(material_data['id'], str):
        material_data['id'] = str(material_data['id'])
            
    # Set defaults if not present
    material_data.setdefault('base_color_value', [0.8, 0.8, 0.8])
    material_data.setdefault('metallic', 0.0)
    material_data.setdefault('roughness', 0.5)
    material_data.setdefault('base_color_texture_polyhaven_id', None)

    if 'materials' not in DB:
        DB['materials'] = {}
    DB['materials'][material_name] = material_data
    
    return material_data.copy()

def create_asset(asset_id, name, type, tags, author, res_opts, fmt_opts):
    dict_to_return = {
        'asset_id': asset_id, 
        'name': name, 
        'type': type, 
        'tags': tags, 
        'author': author, 
        'resolution_options': res_opts, 
        'file_format_options': fmt_opts, 
        'is_downloaded': False, 
        'downloaded_resolution': None, 
        'downloaded_file_format': None, 
        'local_file_path': None, 
        'blender_name': None, 
        'imported_as_blender_object_id': None, 
        'imported_as_blender_material_id': None, 
        'imported_as_world_environment': False
        }
    
    return dict_to_return

# --- Category 2: Essential Utility/Interaction Helper Functions (Getters) ---
# These functions do NOT modify the global DB dictionary.
# They return copies of data from the DB.

def transform_object_to_info_model(obj_data: Dict[str, Any]) -> models.BlenderObjectInfoModel:
    """
    Transforms object data from the database into a BlenderObjectInfoModel.
    This ensures type validation and proper structure for the API response.
    """
    # Extract only the fields that are part of BlenderObjectInfoModel
    info_data = {
        'name': obj_data.get('name'),
        'type': obj_data.get('type'),
        'location': obj_data.get('location', [0.0, 0.0, 0.0]),
        'rotation_euler': obj_data.get('rotation_euler', [0.0, 0.0, 0.0]),
        'scale': obj_data.get('scale', [1.0, 1.0, 1.0]),
        'dimensions': obj_data.get('dimensions', [2.0, 2.0, 2.0]),
        'vertex_count': obj_data.get('vertex_count'),
        'edge_count': obj_data.get('edge_count'),
        'face_count': obj_data.get('face_count'),
        'material_names': obj_data.get('material_names', []),
        'is_visible': obj_data.get('is_visible', True),
        'is_renderable': obj_data.get('is_renderable', True)
    }
    
    # Create and validate the model
    return models.BlenderObjectInfoModel(**info_data).model_dump()

def get_scene_data_dict(scene_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves comprehensive scene data as a dictionary from the global DB.
    If scene_name is None, implies current/default scene.
    """
    if 'current_scene' not in DB or DB['current_scene'] is None: 
        raise custom_errors.SceneNotFoundError("No current scene available in DB.")
    current_scene_dict = DB['current_scene']
    
    if scene_name is not None and current_scene_dict.get('name') != scene_name:
        raise custom_errors.SceneNotFoundError(f"Requested scene '{scene_name}' does not match current scene '{current_scene_dict.get('name')}'.")
    
    objects_dict = current_scene_dict.get('objects', {})
    camera_count = sum(1 for obj in objects_dict.values() if obj.get('type') == models.BlenderObjectType.CAMERA.value)
    light_count = sum(1 for obj in objects_dict.values() if obj.get('type') == models.BlenderObjectType.LIGHT.value)
    object_count = len(objects_dict)

    return {
        "name": current_scene_dict.get('name'),
        "camera_count": camera_count,
        "object_count": object_count,
        "light_count": light_count,
        "active_camera_name": current_scene_dict.get('active_camera_name'),
        "world_settings": current_scene_dict.get('world_settings', {}).copy(),
        "render_settings": current_scene_dict.get('render_settings', {}).copy(),
    }

def get_object_data_dict(object_name: str) -> Dict[str, Any]:
    """
    Retrieves detailed object data as a dictionary from the global DB.
    """
    if 'current_scene' not in DB or not DB['current_scene']:
         raise custom_errors.SceneNotFoundError("No current scene available in DB.")
    current_scene_dict = DB['current_scene']


    scene_objects = current_scene_dict.get('objects', {})
    if object_name not in scene_objects:
        raise custom_errors.ObjectNotFoundError(f"Object '{object_name}' not found in scene.")
    
    return scene_objects[object_name].copy()

def get_material_data_dict(material_name: str) -> Dict[str, Any]:
    """
    Retrieves detailed material data as a dictionary from the global DB.
    """
    if 'materials' not in DB or material_name not in DB['materials']:
        raise custom_errors.MaterialNotFoundError(f"Material '{material_name}' not found.")
    return DB['materials'][material_name].copy()

def get_polyhaven_asset_data_dict(asset_id: str) -> Dict[str, Any]:
    """
    Retrieves Polyhaven asset data as a dictionary from the global DB.
    """
    if 'polyhaven_assets_db' not in DB or asset_id not in DB['polyhaven_assets_db']:
        raise custom_errors.AssetNotFoundError(f"Polyhaven asset '{asset_id}' not found.")
    return DB['polyhaven_assets_db'][asset_id].copy()

def generate_simulated_file_path(base_path: str, asset_category: str, asset_id: str, resolution: str, file_format: str) -> str:
    type_specific_path = os.path.join(base_path, asset_category)
    filename = f"{asset_id}_{resolution}.{file_format}"
    return os.path.join(type_specific_path, filename)

# Helper function to generate a unique-enough Blender name
def generate_blender_name(asset_name: str, asset_id: str, asset_data_type: PolyhavenAssetTypeData) -> str:
    # Sanitize asset_id for use in the name (typically for uniqueness/reference)
    sanitized_asset_id = asset_id.replace('-', '_').replace('.', '_')
    
    # asset_name is used directly for readability, spaces are generally fine in Blender names.
    # Problematic characters in asset_name itself for Blender are rare but could be handled here if needed.
    
    prefix = "PH"
    type_suffix = ""

    if asset_data_type == PolyhavenAssetTypeData.HDRI:
        type_suffix = "WorldHDRI"
    elif asset_data_type == PolyhavenAssetTypeData.TEXTURE:
        type_suffix = "Material"
    elif asset_data_type == PolyhavenAssetTypeData.MODEL:
        type_suffix = "Model"
    else:
        # Fallback, should ideally not be reached if types are well-defined
        type_suffix = asset_data_type.value.capitalize()
    
    return f"{prefix} {asset_name} ({sanitized_asset_id}) {type_suffix}"

def get_hyper3d_job_data_dict(job_id_str: str) -> Dict[str, Any]:
    """
    Retrieves Hyper3D job data as a dictionary from the global DB.
    Job IDs in DB (keys) are strings.
    """
    if 'hyper3d_jobs' not in DB or job_id_str not in DB['hyper3d_jobs']:
        raise custom_errors.JobNotFoundError(f"Hyper3D job with ID '{job_id_str}' not found.")
    
    job_info_dict = DB['hyper3d_jobs'][job_id_str].copy() # Get a copy to add properties

    # Manually add 'is_completed' and 'is_successful' based on 'poll_overall_status'
    # These correspond to the @property logic in the Pydantic model
    poll_status_str = job_info_dict.get('poll_overall_status')
    
    completed_statuses = [
        models.JobOverallStatus.COMPLETED.value,
        models.JobOverallStatus.FAILED.value,
        models.JobOverallStatus.CANCELED.value
    ]
    job_info_dict['is_completed'] = poll_status_str in completed_statuses
    
    if job_info_dict['is_completed']:
        job_info_dict['is_successful'] = poll_status_str == models.JobOverallStatus.COMPLETED.value
    else:
        job_info_dict['is_successful'] = None  # Or False, depending on desired representation for non-completed

    return job_info_dict

def add_job_to_db(internal_job_id: str, mode_at_creation: str, subscription_key: Optional[str] = None,
                  request_id: Optional[str] = None, poll_details_specific: Optional[Any] = None,
                  task_uuid: Optional[str] = None, status: str = 'PENDING'):
    job_entry = {
        'internal_job_id': internal_job_id,
        'mode_at_creation': mode_at_creation,
        'text_prompt': 'Test prompt for job ' + internal_job_id,
        'input_image_paths': None,
        'input_image_urls': None,
        'bbox_condition': None,
        'submission_status': 'success_queued',
        'submission_message': 'Job initiated.',
        'task_uuid': task_uuid if mode_at_creation == 'MAIN_SITE' else None,
        'request_id': request_id,
        'subscription_key': subscription_key,
        'poll_overall_status': status,
        'poll_message': 'Job status not yet polled.',
        'poll_details_specific': poll_details_specific,
        'asset_name_for_import': f'Asset_{internal_job_id[:8]}',
        'import_status': None,
        'import_message': None,
        'imported_blender_object_id': None,
        'imported_blender_object_name': None,
        'imported_blender_object_type': None
    }

    DB['hyper3d_jobs'][internal_job_id] = job_entry


def update_job_import_failure(job_dict_in_db: Optional[Dict[str, Any]], error_message: str):
    """Updates the job record in the DB to reflect an import failure."""
    if job_dict_in_db:
        job_dict_in_db['import_status'] = models.ExecutionStatus.ERROR.value
        job_dict_in_db['import_message'] = error_message
