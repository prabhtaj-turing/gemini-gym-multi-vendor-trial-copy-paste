"""
Polyhaven integration functionalities for the Blender API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
import uuid
from typing import Dict, Optional, List, Set, Union

from pydantic import ValidationError as PydanticValidationError

from blender.SimulationEngine import utils
from blender.SimulationEngine.custom_errors import InvalidAssetTypeError
from blender.SimulationEngine.custom_errors import (
    ValidationError,
    AssetNotFoundError,
    DownloadError,
    BlenderImportError,
    DuplicateNameError,
    InvalidInputError,
)
from blender.SimulationEngine.db import DB
from blender.SimulationEngine.models import (
    DownloadPolyhavenAssetArguments,
    PolyhavenAssetTypeAPI,
    PolyhavenAssetInternalInfo,
    PolyhavenAssetTypeData,
    BlenderObjectType,
    _COMPATIBLE_FORMATS_BY_ASSET_TYPE_API,
    SearchPolyhavenAssetsArguments,
    _ASSET_TYPE_SEARCH_TO_DATA_MAP,
    PolyhavenAssetTypeSearchable,
)

@tool_spec(
    spec={
        'name': 'get_polyhaven_categories',
        'description': 'Get a list of categories for a specific asset type on Polyhaven.',
        'parameters': {
            'type': 'object',
            'properties': {
                'asset_type': {
                    'type': 'string',
                    'description': """ The type of asset to get categories for (hdris, textures, models, all). 
                    Defaults to "hdris". """
                }
            },
            'required': []
        }
    }
)
def get_polyhaven_categories(asset_type: str = "hdris") -> List[str]:
    """
    Get a list of categories for a specific asset type on Polyhaven.
    
    Args:
        asset_type (str): The type of asset to get categories for (hdris, textures, models, all). 
                          Defaults to "hdris".
                                    
    Returns:
        List[str]: A list of category names available for the specified asset type on Polyhaven.
        
    Raises:
        InvalidAssetTypeError: If the provided asset_type is not one of the supported values 
                               ('hdris', 'textures', 'models', 'all') or is otherwise unrecognized by Polyhaven.
    """
    # Function body would read from DB.polyhaven_categories_cache.
    if not isinstance(asset_type, str):
        raise InvalidAssetTypeError("Input should be a valid string")

    try:
        # Convert the validated string asset_type to its corresponding enum member.
        # This step ensures that the string is one of the recognized enum values.
        asset_type_enum_member = PolyhavenAssetTypeSearchable(asset_type)
    except ValueError:
        # This occurs if current_asset_type_str is a string (passed Pydantic validation for type str),
        # but not a valid value in the PolyhavenAssetTypeSearchable enum (e.g., "unknown_type").
        valid_types = [e.value for e in PolyhavenAssetTypeSearchable]
        raise InvalidAssetTypeError(
            f"Invalid asset_type '{asset_type}'. Must be one of {valid_types}."
        )

    # Access the categories cache from the DB.
    categories_cache = DB.get('polyhaven_categories_cache', {})

    if asset_type_enum_member == PolyhavenAssetTypeSearchable.ALL:
        all_categories_set = set()
        for specific_type_key_enum in [
            PolyhavenAssetTypeSearchable.HDRIS,
            PolyhavenAssetTypeSearchable.TEXTURES,
            PolyhavenAssetTypeSearchable.MODELS,
        ]:
            categories_for_type = categories_cache.get(specific_type_key_enum.value, [])  # Use .value for string key
            all_categories_set.update(categories_for_type)
        return sorted(list(all_categories_set))
    else:
        # For a specific asset type (HDRIs, Textures, or Models).
        # Using .value to ensure string key lookup if categories_cache keys are strings.
        categories = categories_cache.get(asset_type_enum_member.value, [])
        return sorted(list(set(categories)))




@tool_spec(
    spec={
        'name': 'search_polyhaven_assets',
        'description': """ Search for assets on Polyhaven with optional filtering.
        
        This function searches for assets on Polyhaven. It allows specifying the
        `asset_type` (such as 'hdris', 'textures', 'models', or 'all') and an
        optional comma-separated list of `categories` for filtering. The function
        returns a list of matching assets, where each asset includes basic
        information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'asset_type': {
                    'type': 'string',
                    'description': 'Asset Type. Defaults to "all". Type validation is handled internally.'
                },
                'categories': {
                    'type': 'string',
                    'description': 'Categories. Defaults to None. Type validation is handled internally.'
                }
            },
            'required': []
        }
    }
)
def search_polyhaven_assets(asset_type: str = "all", categories: Optional[str] = None) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Search for assets on Polyhaven with optional filtering.

    This function searches for assets on Polyhaven. It allows specifying the
    `asset_type` (such as 'hdris', 'textures', 'models', or 'all') and an
    optional comma-separated list of `categories` for filtering. The function
    returns a list of matching assets, where each asset includes basic
    information.

    Args:
        asset_type (str): Asset Type. Defaults to "all". Type validation is handled internally.
        categories (Optional[str]): Categories. Defaults to None. Type validation is handled internally.

    Returns:
        List[Dict[str, Union[str, List[str]]]]: A list of matching Polyhaven assets. Each dictionary
            in the list represents an asset and contains the following keys:
            - asset_id (str): The unique identifier for the asset on Polyhaven.
            - name (str): The display name of the asset.
            - type (str): The type of the asset (e.g., 'hdri', 'texture', 'model').
            - tags (List[str]): A list of tags associated with the asset.
            - author (Optional[str]): The author or creator of the asset.
            - resolution_options (List[str]): Available resolutions for download
                (e.g., "1k", "2k", "4k").
            - file_format_options (List[str]): Available file formats for download
                (e.g., "hdr", "exr" for HDRIs; "jpg", "png" for textures;
                "gltf", "fbx" for models).

    Raises:
        InvalidInputError: If the search parameters (e.g., asset_type, categories)
            are invalid or malformed.
    """
    try:
        # Validate inputs using the Pydantic model.
        # This aligns with the inputSchema provided in the function's documentation.
        args = SearchPolyhavenAssetsArguments(asset_type=asset_type, categories=categories)
        
        validated_asset_type = args.asset_type
        validated_categories = args.categories

    except PydanticValidationError as e:
        # Translate Pydantic's ValidationError to InvalidInputError
        # with specific messages expected by tests.
        first_error = e.errors()[0]
        error_loc = first_error.get('loc', ())
        error_type = first_error.get('type', '') # Pydantic's internal error type string

        if 'asset_type' in error_loc:
            # Handles cases like asset_type=123 (input not a string)
            if error_type.startswith('string_') or error_type == 'str_type': # Pydantic v1 'string_type', Pydantic v2 'str_type'
                raise InvalidInputError("Asset type must be a string.")
            # Handles invalid string values, e.g., asset_type='badtype'
            elif error_type == 'value_error': # From `raise ValueError` in a Pydantic validator
                if 'ctx' in first_error and 'error' in first_error['ctx']:
                    original_error_msg = str(first_error['ctx']['error'])
                    raise InvalidInputError(original_error_msg)
                else: # Fallback if context structure is different
                    raise InvalidInputError(first_error.get('msg', 'Invalid asset_type.'))
            else: # Fallback for other asset_type errors
                 raise InvalidInputError(f"Invalid asset_type: {first_error.get('input', asset_type)}. Details: {first_error.get('msg', 'Unknown error')}")

        elif 'categories' in error_loc:
            # Handles cases like categories=123 (input not a string, not None)
            if error_type.startswith('string_') or error_type == 'str_type':
                raise InvalidInputError("Categories parameter must be a string if provided.")
            elif error_type == 'value_error':
                if 'ctx' in first_error and 'error' in first_error['ctx']:
                    original_error_msg = str(first_error['ctx']['error'])
                    raise InvalidInputError(original_error_msg)
                else:
                    raise InvalidInputError(first_error.get('msg', 'Invalid categories parameter.'))
            else: # Fallback for other categories errors
                raise InvalidInputError(f"Invalid categories parameter: {first_error.get('input', categories)}. Details: {first_error.get('msg', 'Unknown error')}")
        
        # General fallback if error location is unexpected or not handled above
        raise InvalidInputError(f"Input validation error: {e.errors()}")

    # ----- Main function logic, using validated_asset_type and validated_categories -----
    
    # Parse the comma-separated categories string.
    filter_categories_set: Set[str] = set()
    if validated_categories:
        parsed_cats = [cat.strip() for cat in validated_categories.split(',') if cat.strip()]
        if parsed_cats:
            filter_categories_set = set(parsed_cats)
    
    polyhaven_assets_db = DB.get('polyhaven_assets_db', {})
    if not polyhaven_assets_db:
        return []

    matching_assets = []

    for asset_id_from_db_key, asset_info_dict in polyhaven_assets_db.items():
        if not isinstance(asset_info_dict, dict):
            continue

        # 1. Asset Type Filtering
        if validated_asset_type != PolyhavenAssetTypeSearchable.ALL.value:
            expected_data_type = _ASSET_TYPE_SEARCH_TO_DATA_MAP.get(validated_asset_type)
            if expected_data_type is None:
                continue
            if asset_info_dict.get('type') != expected_data_type:
                continue

        # 2. Category Filtering
        if filter_categories_set:
            asset_tags = asset_info_dict.get('tags', [])
            if not isinstance(asset_tags, list):
                asset_tags = []
            asset_tags_set = {tag for tag in asset_tags if isinstance(tag, str)}
            if not filter_categories_set.intersection(asset_tags_set):
                continue

        asset_id_value = asset_info_dict.get('asset_id', asset_id_from_db_key)
        result_item = {
            "asset_id": asset_id_value,
            "name": asset_info_dict.get('name'),
            "type": asset_info_dict.get('type'),
            "tags": asset_info_dict.get('tags', []) if isinstance(asset_info_dict.get('tags'), list) else [],
            "author": asset_info_dict.get('author'),
            "resolution_options": asset_info_dict.get('resolution_options', []) if isinstance(asset_info_dict.get('resolution_options'), list) else [],
            "file_format_options": asset_info_dict.get('file_format_options', []) if isinstance(asset_info_dict.get('file_format_options'), list) else []
        }
        matching_assets.append(result_item)

    return matching_assets


@tool_spec(
    spec={
        'name': 'download_polyhaven_asset',
        'description': 'This function downloads a Polyhaven asset, identified by its `asset_id` and `asset_type`, and imports it into Blender.',
        'parameters': {
            'type': 'object',
            'properties': {
                'asset_id': {
                    'type': 'string',
                    'description': 'The ID of the asset to download.'
                },
                'asset_type': {
                    'type': 'string',
                    'description': 'The type of asset (hdris, textures, models).'
                },
                'resolution': {
                    'type': 'string',
                    'description': 'The resolution to download (e.g., 1k, 2k, 4k). Defaults to "1k".'
                },
                'file_format': {
                    'type': 'string',
                    'description': 'Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models). Defaults to None.'
                }
            },
            'required': [
                'asset_id',
                'asset_type'
            ]
        }
    }
)
def download_polyhaven_asset(
        asset_id: str, 
        asset_type: str, 
        resolution: str = "1k",
        file_format: Optional[str] = None
    ) -> Dict[str, str]:
    """
    This function downloads a Polyhaven asset, identified by its `asset_id` and `asset_type`, and imports it into Blender.
    
    Args:
        asset_id (str): The ID of the asset to download.
        asset_type (str): The type of asset (hdris, textures, models).
        resolution (str): The resolution to download (e.g., 1k, 2k, 4k). Defaults to "1k".
        file_format (Optional[str]): Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models). Defaults to None.

    Returns:
        Dict[str, str]: A dictionary detailing the outcome of the asset download and import operation. It contains the following keys:
            - status (str): Indicates if the operation was a 'success' or 'failure'.
            - message (str): A human-readable message providing more details about the outcome.
            - asset_name_in_blender (str): If successful, the name assigned to the imported asset, material, or world object within Blender. Present only on success and if applicable.
            - file_path (str): If successful, the local file system path where the asset was downloaded. Present only on success.

    Raises:
        AssetNotFoundError: If the specified asset_id does not exist on Polyhaven.
        DownloadError: If there's an issue downloading the asset file (invalid resolution/format requested).
        BlenderImportError: If there's an issue importing the downloaded asset into Blender.
        InvalidInputError: If parameters like resolution or file_format are invalid for the given asset or asset_type.
        ValidationError: If input arguments fail validation.
    """
    _DEFAULT_RESOLUTION_VALUE = "1k"  # Matches schema default

    # --- 1. Pydantic Input Validation ---
    try:
        args = DownloadPolyhavenAssetArguments(
            asset_id=asset_id,
            asset_type=asset_type,
            resolution=resolution,
            file_format=file_format
        )
    except PydanticValidationError as e:
        error_msg = "Input validation failed."
        if e.errors():
            error_msg = e.errors()[0]['msg']
        raise ValidationError(error_msg)

    if args.file_format == "" or args.file_format == "null":
        args.file_format = None

    # --- 2. Check Polyhaven Service Status ---
    polyhaven_status_dict = DB.get('polyhaven_service_status', {})
    if not polyhaven_status_dict.get('is_enabled', True):
        service_message = polyhaven_status_dict.get('message',
                                                    'No specific reason provided.')  # Polyhaven service is not enabled.
        raise DownloadError(
            f"Polyhaven download failed: {service_message}"
        )

    # --- 3. Validate `asset_type` parameter value ---
    try:
        api_asset_type_enum = PolyhavenAssetTypeAPI(args.asset_type)
    except ValueError:
        valid_api_types = [e.value for e in PolyhavenAssetTypeAPI]
        raise InvalidInputError(
            f"Invalid asset_type provided: '{args.asset_type}'. Must be one of {valid_api_types}."
        )

    # --- 4. Retrieve Asset from DB ---
    if 'polyhaven_assets_db' not in DB or args.asset_id not in DB['polyhaven_assets_db']:
        raise AssetNotFoundError(f"Polyhaven asset '{args.asset_id}' not found.")

    asset_data_from_db = DB['polyhaven_assets_db'][args.asset_id]
    try:
        asset_info = PolyhavenAssetInternalInfo(**asset_data_from_db)
    except PydanticValidationError as e:
        raise DownloadError(
            f"Internal error: Could not parse database data for asset '{args.asset_id}'. Details: {e}"
        )

    # --- 5. Verify Asset Type Consistency ---
    expected_data_type: PolyhavenAssetTypeData
    if api_asset_type_enum == PolyhavenAssetTypeAPI.HDRIS:
        expected_data_type = PolyhavenAssetTypeData.HDRI
    elif api_asset_type_enum == PolyhavenAssetTypeAPI.TEXTURES:
        expected_data_type = PolyhavenAssetTypeData.TEXTURE
    elif api_asset_type_enum == PolyhavenAssetTypeAPI.MODELS:
        expected_data_type = PolyhavenAssetTypeData.MODEL

    if asset_info.type != expected_data_type:
        raise InvalidInputError(
            f"Asset '{args.asset_id}' is of type '{asset_info.type.value}', not '{args.asset_type}'."
        )

    # --- 6. Validate Requested File Format (if provided) for compatibility with Asset Type ---
    if args.file_format:
        compatible_formats = _COMPATIBLE_FORMATS_BY_ASSET_TYPE_API.get(api_asset_type_enum, [])
        if args.file_format not in compatible_formats:
            raise InvalidInputError(
                f"File format '{args.file_format}' is not compatible with asset type '{api_asset_type_enum.value}'.")

    # --- 7. Validate Requested Resolution ---
    if not asset_info.resolution_options:
        raise InvalidInputError(
            f"Resolution '{args.resolution}' not available for asset '{args.asset_id}'. No resolutions listed."
        )
    if args.resolution not in asset_info.resolution_options:
        message_intro = f"Resolution '{args.resolution}'"
        if args.resolution == _DEFAULT_RESOLUTION_VALUE:
            message_intro = f"Default resolution '{_DEFAULT_RESOLUTION_VALUE}'"
        raise InvalidInputError(
            f"{message_intro} not available for asset '{args.asset_id}'. "
            f"Available: {asset_info.resolution_options}."
        )

    # --- 8. Determine and Validate Actual File Format ---
    actual_file_format: str
    if args.file_format:
        if not asset_info.file_format_options:  # This should never happen.
            raise InvalidInputError(
                f"File format '{args.file_format}' not available for asset '{args.asset_id}' "
                f"(type '{asset_info.type.value}'). No file formats listed.")
        if args.file_format not in asset_info.file_format_options:
            raise InvalidInputError(
                f"File format '{args.file_format}' not available for asset '{args.asset_id}' "
                f"(type '{asset_info.type.value}'). Available: {asset_info.file_format_options}.")
        actual_file_format = args.file_format
    else:
        if not asset_info.file_format_options:
            raise InvalidInputError(
                f"Cannot determine default file format for asset '{args.asset_id}' "
                f"(type '{asset_info.type.value}') as no formats are listed.")

        preferred_defaults = []
        if asset_info.type == PolyhavenAssetTypeData.HDRI:
            preferred_defaults = ['hdr', 'exr']
        elif asset_info.type == PolyhavenAssetTypeData.TEXTURE:
            preferred_defaults = ['jpg', 'png']
        elif asset_info.type == PolyhavenAssetTypeData.MODEL:
            preferred_defaults = ['gltf', 'fbx']

        chosen_default_format = None
        for pref_fmt in preferred_defaults:
            if pref_fmt in asset_info.file_format_options:
                chosen_default_format = pref_fmt
                break

        if chosen_default_format:
            actual_file_format = chosen_default_format
        else:
            actual_file_format = asset_info.file_format_options[0]

    # --- 9. Simulate Download & Update DB for Download Success ---
    simulated_download_base_path = "/mnt/polyhaven_assets"
    local_file_path = utils.generate_simulated_file_path(
        simulated_download_base_path,
        api_asset_type_enum.value,  # Use API enum value for path category
        args.asset_id,
        args.resolution,
        actual_file_format
    )

    # Update DB to reflect download success; import-related fields are initially None/False.
    download_update_params = {
        "asset_id": args.asset_id,
        "is_downloaded": True,
        "downloaded_resolution": args.resolution,
        "downloaded_file_format": actual_file_format,
        "local_file_path": local_file_path,
        "blender_name": None,  # Will be set upon successful import
        "imported_as_blender_object_id": None,
        "imported_as_blender_material_id": None,
        "imported_as_world_environment": False,
    }
    utils.update_polyhaven_asset_download_status(**download_update_params)

    # --- 10. Simulate Blender Import and Update DB State on Import Success ---
    blender_name = utils.generate_blender_name(asset_info.name, args.asset_id, asset_info.type)

    # Parameters for updating DB upon successful import
    import_success_update_params = {
        "asset_id": args.asset_id,
        "is_downloaded": True,  # Already true, but part of util signature
        "downloaded_resolution": args.resolution,
        "downloaded_file_format": actual_file_format,
        "local_file_path": local_file_path,
        "blender_name": blender_name,  # This is the key field set on import success
        "imported_as_blender_object_id": None,
        "imported_as_blender_material_id": None,
        "imported_as_world_environment": False,  # Default, overridden for HDRIs
    }

    current_scene_data = DB.get('current_scene', {})
    current_scene_name = current_scene_data.get('name')
    if not current_scene_name:
        raise BlenderImportError("Cannot import asset: Current scene is not defined or has no name.")

    try:
        if asset_info.type == PolyhavenAssetTypeData.HDRI:
            if 'world_settings' not in current_scene_data:
                current_scene_data['world_settings'] = {}  # Should be handled by SceneModel default
            current_scene_data['world_settings']['environment_texture_polyhaven_id'] = args.asset_id
            current_scene_data['world_settings']['environment_texture_strength'] = 1.0
            import_success_update_params["imported_as_world_environment"] = True

        elif asset_info.type == PolyhavenAssetTypeData.TEXTURE:
            material_id = str(uuid.uuid4())
            material_data_for_creation = {
                "id": material_id, "name": blender_name,
                "base_color_texture_polyhaven_id": args.asset_id,
            }
            created_material_dict = utils.create_material(material_data_for_creation)
            import_success_update_params["imported_as_blender_material_id"] = created_material_dict['id']

        elif asset_info.type == PolyhavenAssetTypeData.MODEL:
            object_id = str(uuid.uuid4())
            object_data_for_creation = {
                "id": object_id, "name": blender_name,
                "type": BlenderObjectType.MESH.value,
            }
            created_object_dict = utils.add_object_to_scene(current_scene_name, object_data_for_creation)
            import_success_update_params["imported_as_blender_object_id"] = created_object_dict['id']

        # If import was successful, update DB with blender_name and specific IDs/flags
        utils.update_polyhaven_asset_download_status(**import_success_update_params)

    except DuplicateNameError:
        # Determine entity type for clearer error message
        entity_type_str = "Entity"
        if asset_info.type == PolyhavenAssetTypeData.TEXTURE:
            entity_type_str = "Material"
        elif asset_info.type == PolyhavenAssetTypeData.MODEL:
            entity_type_str = "Object"

        # blender_name is the name that caused the collision
        colliding_entity_description = f"{entity_type_str} '{blender_name}'"

        raise BlenderImportError(
            f"Failed to import asset into Blender: {colliding_entity_description} could not be created or updated due to a name conflict or other import issue."
        )
    except Exception as e:
        raise BlenderImportError(
            f"An unexpected error occurred during the simulated import of asset '{args.asset_id}'. Details: {e}"
        )

    # --- 11. Construct Success Response ---
    return {
        "status": "success",
        "message": f"Asset '{args.asset_id}' ({asset_info.name}) successfully downloaded "
                   f"({args.resolution}, {actual_file_format}) and imported into Blender as '{blender_name}'.",
        "asset_name_in_blender": blender_name,
        "file_path": local_file_path,
    }


@tool_spec(
    spec={
        'name': 'get_polyhaven_status',
        'description': """ Checks if PolyHaven integration is enabled in Blender and returns a message indicating whether
        
        PolyHaven features are available. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_polyhaven_status() -> Dict[str, Union[bool, str]]:
    """
    Checks if PolyHaven integration is enabled in Blender and returns a message indicating whether
    PolyHaven features are available.

    Returns:
        Dict[str, Union[bool, str]]: A dictionary containing information about the Polyhaven integration status, with the following keys:
            - is_enabled (bool): True if Polyhaven integration (e.g., the addon) is enabled and functional, False otherwise.
            - message (str): A descriptive message about the integration status.

    Raises:
        ValidationError: If Polyhaven service status is not configured in DB or is missing the 'is_enabled' or 'message' keys.
    """
    if "polyhaven_service_status" not in DB:
        raise ValidationError("Polyhaven service status not configured in DB.")

    polyhaven_status_data = DB['polyhaven_service_status']

    if 'is_enabled' not in polyhaven_status_data:
        raise ValidationError("Polyhaven service status is missing 'is_enabled' key.")
    
    if 'message' not in polyhaven_status_data:
        raise ValidationError("Polyhaven service status is missing 'message' key.")

    # Construct the return dictionary directly from the DB data.
    return {
        "is_enabled": polyhaven_status_data['is_enabled'],
        "message": polyhaven_status_data['message'],
    }
