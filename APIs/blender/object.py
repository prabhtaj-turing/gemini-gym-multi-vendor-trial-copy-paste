"""
Object-related functionalities for the Blender API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List, Optional, Union

from pydantic import ValidationError as PydanticValidationError

from blender.SimulationEngine import custom_errors
from blender.SimulationEngine import models
from blender.SimulationEngine import utils
from blender.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_object_info',
        'description': """ Get detailed information about a specific object in the Blender scene.
        
        This function gets detailed information about a specific object in the Blender scene. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'object_name': {
                    'type': 'string',
                    'description': 'The name of the object to get information about.'
                }
            },
            'required': [
                'object_name'
            ]
        }
    }
)
def get_object_info(object_name: str) -> Dict[str, Union[str, bool, int, List[Union[str, float]]]]:
    """Get detailed information about a specific object in the Blender scene.

    This function gets detailed information about a specific object in the Blender scene.

    Args:
        object_name (str): The name of the object to get information about. 

    Returns:
        Dict[str, Union[str, bool, int, List[Union[str, float]]]]: A dictionary containing detailed information about the specified Blender object. It includes the following keys:
            - name (str): The name of the object.
            - type (str): The type of the object (e.g., 'MESH', 'CAMERA', 'LIGHT').
            - location (List[float]): X, Y, Z coordinates of the object's origin.
            - rotation_euler (List[float]): X, Y, Z Euler rotation in radians.
            - scale (List[float]): X, Y, Z scale factors.
            - dimensions (List[float]): X, Y, Z dimensions of the object's bounding box.
            - vertex_count (Optional[int]): Number of vertices (if the object is a mesh).
            - edge_count (Optional[int]): Number of edges (if the object is a mesh).
            - face_count (Optional[int]): Number of faces (if the object is a mesh).
            - material_names (List[str]): List of material names assigned to the object.
            - is_visible (bool): Whether the object is visible in the viewport.
            - is_renderable (bool): Whether the object is set to be renderable.

    Raises:
        ObjectNotFoundError: If the object with the specified name is not found in the scene
                            or if there are no objects in the current scene.
        InvalidInputError: If input arguments fail validation.
        ValidationError: If output object fails the model validation.
        SceneNotFoundError: If the current scene is not found in the database.
    """
    if not isinstance(object_name, str):
        raise custom_errors.InvalidInputError("object_name must be a string")

    if 'current_scene' not in DB or DB['current_scene'] is None:
        raise custom_errors.SceneNotFoundError("No objects found in scene.")

    if 'objects' not in DB['current_scene']:
        raise custom_errors.ObjectNotFoundError("No objects found in scene.")

    if object_name not in DB['current_scene']['objects']:
        raise custom_errors.ObjectNotFoundError(f"Object '{object_name}' not found in scene.")

    # Get the raw object data from the database
    obj_data = utils.get_object_data_dict(object_name)

    # Transform to BlenderObjectInfoModel and return its model_dump
    try:
        object_info_model = utils.transform_object_to_info_model(obj_data)
    except PydanticValidationError as e:
        raise custom_errors.ValidationError(f"Error transforming object data to BlenderObjectInfoModel: {e}")

    return object_info_model


@tool_spec(
    spec={
        'name': 'set_object_texture',
        'description': 'Apply a previously downloaded Polyhaven texture to an object.',
        'parameters': {
            'type': 'object',
            'properties': {
                'object_name': {
                    'type': 'string',
                    'description': 'Name of the object to apply the texture to.'
                },
                'texture_id': {
                    'type': 'string',
                    'description': 'ID of the Polyhaven texture to apply (must be downloaded first and must be a valid texture asset type).'
                }
            },
            'required': [
                'object_name',
                'texture_id'
            ]
        }
    }
)
def set_texture(object_name: str, texture_id: str) -> Dict[str, str]:
    """
    Apply a previously downloaded Polyhaven texture to an object.

    Args:
        object_name (str): Name of the object to apply the texture to.
        texture_id (str): ID of the Polyhaven texture to apply (must be downloaded first and must be a valid texture asset type).

    Returns:
        Dict[str, str]: A dictionary detailing the outcome of the texture application. Contains the following keys:
            'status' (str): Indicates if the operation was 'success' or 'failure'.
            'message' (str): A human-readable message describing the outcome.
            'object_name' (str): The name of the object targeted for texture application.
            'texture_id' (str): The ID of the texture that was applied or attempted to be applied.

    Raises:
        ObjectNotFoundError: If the object with the specified object_name is not found in the Blender scene.
        InvalidInputError: If object_name or texture_id is not a string,
                            or if texture asset not found in Polyhaven assets database, 
                            or the texture_id does not correspond to a valid texture asset type.
        InvalidStateError: If the texture asset is not downloaded.
    """
    # --- Basic input validation ---
    if not isinstance(object_name, str):
        raise custom_errors.InvalidInputError("object_name must be a string")
    if not isinstance(texture_id, str):
        raise custom_errors.InvalidInputError("texture_id must be a string")

    # --- Ensure the target object exists ---
    try:
        obj_dict = utils.get_object_data_dict(object_name)
    except custom_errors.ObjectNotFoundError as e:
        raise  # Re-raise as is for caller

    # --- Validate the Polyhaven texture asset ---
    if 'polyhaven_assets_db' not in DB or texture_id not in DB['polyhaven_assets_db']:
        # Treat missing asset as not downloaded / invalid
        raise custom_errors.InvalidInputError(f"Texture asset '{texture_id}' not found in Polyhaven assets database.")

    texture_asset_info = DB['polyhaven_assets_db'][texture_id]

    # Ensure asset type is TEXTURE
    if texture_asset_info.get('type') != models.PolyhavenAssetTypeData.TEXTURE.value:
        raise custom_errors.InvalidInputError(
            f"Asset '{texture_id}' is not a texture (type is '{texture_asset_info.get('type')}').")

    # Ensure asset is downloaded
    if not texture_asset_info.get('is_downloaded'):
        # No dedicated error type; use InvalidStateError to communicate requirement
        raise custom_errors.InvalidStateError(
            f"Texture asset '{texture_id}' must be downloaded before applying.")

    # --- Determine or create a material for the object ---

    existing_material_names = obj_dict.get('material_names', []) if isinstance(obj_dict.get('material_names'),
                                                                               list) else []

    if existing_material_names:
        # Use the first existing material
        material_name_to_use = existing_material_names[0]
    else:
        # Create a new material
        material_name_to_use = f"{object_name}_Mat"
        # Ensure uniqueness of material name
        counter = 1
        while 'materials' in DB and material_name_to_use in DB['materials']:
            material_name_to_use = f"{object_name}_Mat_{counter}"
            counter += 1

        utils.create_material({
            'name': material_name_to_use,
            'base_color_value': [0.8, 0.8, 0.8]
        })

        # Assign the newly created material to the object
        utils.assign_material_to_object(DB['current_scene']['name'], object_name, material_name_to_use,
                                        replace_existing=False)

    # --- Apply the texture to the material ---
    utils.apply_texture_to_material(material_name_to_use, texture_polyhaven_id=texture_id)

    return {
        'status': 'success',
        'message': f"Texture '{texture_id}' applied to object '{object_name}' using material '{material_name_to_use}'.",
        'object_name': object_name,
        'texture_id': texture_id
    }
