"""
Scene-related functionalities for the Blender API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Union
from blender.SimulationEngine import utils
from blender.SimulationEngine.models import SceneModel
from blender.SimulationEngine import custom_errors
from pydantic import ValidationError as PydanticValidationError


@tool_spec(
    spec={
        'name': 'get_scene_info',
        'description': """ Get detailed information about the current Blender scene.
        
        This function retrieves comprehensive information about the current Blender scene.
        The details encompass the scene's name, counts of cameras, objects, and
        lights, the name of the active camera if one exists, settings for the world
        environment including ambient and horizon colors, and various rendering
        configurations like the engine, resolution, and output filepath. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_scene_info() -> Dict[str, Union[str, int, None, Dict[str, Union[str, int, List[float], float, None]]]]:
    """Get detailed information about the current Blender scene.

    This function retrieves comprehensive information about the current Blender scene.
    The details encompass the scene's name, counts of cameras, objects, and
    lights, the name of the active camera if one exists, settings for the world
    environment including ambient and horizon colors, and various rendering
    configurations like the engine, resolution, and output filepath.

    Returns:
        Dict[str, Union[str, int, None, Dict[str, Union[str, int, List[float], float, None]]]]: A dictionary containing comprehensive information about the
            current Blender scene. Keys:
            - 'name' (str): The name of the scene.
            - 'camera_count' (int): Number of cameras in the scene.
            - 'object_count' (int): Number of objects in the scene.
            - 'light_count' (int): Number of lights in the scene.
            - 'active_camera_name' (Optional[str]): Name of the active camera, if any.
            - 'world_settings' (Dict[str, Union[List[float], str, float, None]]): Settings related to the world
                environment. This dictionary may include:
                - 'ambient_color' (List[float]): RGB values for ambient light (range 0-1).
                - 'horizon_color' (List[float]): RGB values for horizon color (range 0-1).
                - 'environment_texture_polyhaven_id' (Optional[str]): Polyhaven asset ID for HDRI environment texture.
                - 'environment_texture_strength' (float): Strength/intensity of the environment texture (range 0-10).
            - 'render_settings' (Dict[str, Union[str, int]]): Settings related to rendering.
                This dictionary may include:
                - 'engine' Optional[str]: The render engine used (e.g., 'CYCLES', 'EEVEE').
                - 'resolution_x' Optional[int]: Render output width in pixels.
                - 'resolution_y' Optional[int]: Render output height in pixels.
                - 'resolution_percentage' Optional[int]: Percentage scaling for resolution.
                - 'filepath' Optional[str]: Default output path and file name pattern for renders.

    Raises:
        SceneNotFoundError: If the current scene is not found in the DB.
    """
    try:
        return utils.get_scene_data_dict()
    except Exception as e:
        raise custom_errors.SceneNotFoundError("No current scene available in DB.")
