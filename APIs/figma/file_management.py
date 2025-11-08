from common_utils.tool_spec_decorator import tool_spec
# figma/file_management.py

import pathlib
import os
import shutil

from typing import Any, Dict, List, Optional, Tuple
from .SimulationEngine.custom_errors import InvalidInputError, NotFoundError, DownloadError
from .SimulationEngine import utils
from figma import DB
from .SimulationEngine.utils import filter_none_values_from_dict

@tool_spec(
    spec={
        'name': 'get_figma_data',
        'description': """ Retrieves data for a Figma file, optionally scoped to a specific node.
        
        This function retrieves data for a Figma file. If a `node_id` is provided,
        data retrieval focuses on that specific node; otherwise, data for all
        top-level nodes (e.g., canvases/pages) in the file is returned. The function
        fetches metadata about the file, detailed information about the relevant nodes
        (including their properties and any child nodes in a recursive structure),
        and global styles defined within the file. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_key': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma file. Must contain only alphanumeric characters, hyphens, and underscores.'
                },
                'node_id': {
                    'type': 'string',
                    'description': """ The unique identifier of a specific node within
                    the file. Defaults to None. If provided, the 'nodes' field in the response
                    will be focused on this node. If omitted, data for all top-level nodes
                    (e.g., canvases/pages) in the file is returned. Must contain only alphanumeric characters, hyphens, underscores and colons. """
                }
            },
            'required': [
                'file_key'
            ]
        }
    }
)
def get_figma_data(file_key: str, node_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves data for a Figma file, optionally scoped to a specific node.

    This function retrieves data for a Figma file. If a `node_id` is provided,
    data retrieval focuses on that specific node; otherwise, data for all
    top-level nodes (e.g., canvases/pages) in the file is returned. The function
    fetches metadata about the file, detailed information about the relevant nodes
    (including their properties and any child nodes in a recursive structure),
    and global styles defined within the file.

    Args:
        file_key (str): The unique identifier of the Figma file. Must contain only alphanumeric characters, hyphens, and underscores.
        node_id (Optional[str]): The unique identifier of a specific node within
            the file. Defaults to None. If provided, the 'nodes' field in the response
            will be focused on this node. If omitted, data for all top-level nodes
            (e.g., canvases/pages) in the file is returned. Must contain only alphanumeric characters, hyphens, underscores and colons.

    Returns:
        Dict[str, Any]: A dictionary containing the Figma file/node data with the
        following keys:
            metadata (Dict[str, str]): Metadata about the Figma file.
                name (str): The name of the Figma file.
                lastModified (str): ISO 8601 timestamp of when the file was last
                    modified (e.g., 'YYYY-MM-DDTHH:MM:SSZ').
                thumbnailUrl (str): URL of the file's thumbnail image.
            nodes (List[Dict[str, Any]]): A list of node objects. Each node
                represents an element in the Figma file (e.g., frame, group,
                rectangle, text). The structure is recursive for nodes with
                children. All properties within a node are optional. Each
                dictionary in the list can contain the following keys:
                id (Optional[str]): Unique identifier for the node.
                name (Optional[str]): Name of the node.
                type (Optional[str]): Type of the node (e.g., 'GROUP',
                    'RECTANGLE', 'TEXT', 'FRAME', 'CANVAS', 'ELLIPSE',
                    'IMAGE-SVG', 'INSTANCE').
                visible (Optional[bool]): Whether the node is visible.
                locked (Optional[bool]): Whether the node is locked.
                opacity (Optional[float]): Opacity of the node (0 to 1).
                rotation (Optional[float]): Rotation of the node in degrees.
                blendMode (Optional[str]): Blend mode of the node.
                isMask (Optional[bool]): Whether the node is a mask.
                isFixed (Optional[bool]): Whether the node has fixed positioning.
                absoluteBoundingBox (Optional[Dict[str, Any]]): Bounding box of
                    the node in absolute coordinates (e.g., {x, y, width, height}).
                absoluteRenderBounds (Optional[Dict[str, Any]]): Render bounding
                    box of the node in absolute coordinates (e.g., {x, y, width,
                    height}).
                constraints (Optional[Dict[str, Any]]): Layout constraints of the
                    node (e.g., {vertical, horizontal}).
                fills (Optional[Union[str, List[Dict[str, Any]]]]): Fills appliedy
                    to the node. Can be a style ID (string) or an array of fill
                    objects.
                strokes (Optional[List[Dict[str, Any]]]): Strokes applied to the
                    node.
                strokeWeight (Optional[float]): Stroke weight (thickness).
                strokeAlign (Optional[str]): Stroke alignment (e.g., 'INSIDE',
                    'OUTSIDE', 'CENTER').
                strokeJoin (Optional[str]): Stroke join type (e.g., 'MITER',
                    'BEVEL', 'ROUND').
                strokeCap (Optional[str]): Stroke cap type (e.g., 'NONE', 'ROUND',
                    'SQUARE', 'LINE_ARROW', 'TRIANGLE_ARROW').
                strokeDashes (Optional[List[float]]): Dash pattern for strokes
                    (e.g., [5, 5]).
                strokeMiterAngle (Optional[float]): Miter angle for strokes.
                strokeGeometry (Optional[List[Dict[str, Any]]]): Vector paths for
                    strokes.
                fillGeometry (Optional[List[Dict[str, Any]]]): Vector paths for
                    fills.
                cornerRadius (Optional[float]): Overall corner radius for shapes
                    that support it.
                cornerSmoothing (Optional[float]): Corner smoothing value (0 to 1).
                rectangleCornerRadii (Optional[List[float]]): Individual corner
                    radii for rectangles (top-left, top-right, bottom-right,
                    bottom-left).
                borderRadius (Optional[str]): Original schema's border radius value
                    (e.g., '0px 0px 0px 0px'). Kept for compatibility.
                effects (Optional[List[Dict[str, Any]]]): Effects applied to the
                    node (e.g., shadows, blurs).
                layoutAlign (Optional[str]): For children of auto-layout frames,
                    how this node is aligned perpendicular to the layout
                    direction (e.g., 'MIN', 'CENTER', 'MAX', 'STRETCH', 'INHERIT').
                layoutGrow (Optional[float]): For children of auto-layout frames,
                    whether this node should stretch to fill space in the layout
                    direction (0 for fixed size, 1 for stretch).
                layoutSizingHorizontal (Optional[str]): Horizontal sizing mode in
                    auto-layout frames (e.g., 'FIXED', 'HUG', 'FILL').
                layoutSizingVertical (Optional[str]): Vertical sizing mode in
                    auto-layout frames (e.g., 'FIXED', 'HUG', 'FILL').
                styles (Optional[Dict[str, str]]): References to shared styles
                    applied to the node (e.g., {'fills': 'styleId123',
                    'text': 'styleId456'}).
                exportSettings (Optional[List[Dict[str, Any]]]): Export settings
                    defined on the node.
                prototypeInteractions (Optional[List[Dict[str, Any]]]): Prototype
                    interactions defined on the node.
                boundVariables (Optional[Dict[str, Any]]): Variables bound to
                    node properties.
                clipsContent (Optional[bool]): Whether content is clipped to the
                    node's bounds (typically for frames and groups).
                background (Optional[List[Dict[str, Any]]]): Background fills for
                    the node (typically for frames). Use 'fills' for general
                    purpose.
                backgroundColor (Optional[Dict[str, Any]]): Background color of
                    the node (e.g., for frames, canvas, {r, g, b, a}).
                layoutMode (Optional[str]): Layout mode for auto-layout frames
                    ('NONE', 'HORIZONTAL', 'VERTICAL').
                primaryAxisSizingMode (Optional[str]): Sizing mode for the
                    primary axis in auto-layout ('FIXED', 'AUTO'/'HUG').
                counterAxisSizingMode (Optional[str]): Sizing mode for the
                    counter axis in auto-layout ('FIXED', 'AUTO'/'HUG').
                primaryAxisAlignItems (Optional[str]): Alignment of items along
                    the primary axis in auto-layout ('MIN', 'CENTER', 'MAX',
                    'SPACE_BETWEEN').
                counterAxisAlignItems (Optional[str]): Alignment of items along
                    the counter axis in auto-layout ('MIN', 'CENTER', 'MAX',
                    'BASELINE').
                paddingLeft (Optional[float]): Left padding for auto-layout frames.
                paddingRight (Optional[float]): Right padding for auto-layout
                    frames.
                paddingTop (Optional[float]): Top padding for auto-layout frames.
                paddingBottom (Optional[float]): Bottom padding for auto-layout
                    frames.
                paddingHorizontal (Optional[float]): Horizontal padding for
                    auto-layout (sum of left and right if individual paddings
                    are equal, otherwise represents collective horizontal padding).
                paddingVertical (Optional[float]): Vertical padding for
                    auto-layout (sum of top and bottom if individual paddings
                    are equal, otherwise represents collective vertical padding).
                itemSpacing (Optional[float]): Spacing between items in an
                    auto-layout frame.
                itemReverseZIndex (Optional[bool]): Whether items are layered in
                    reverse Z-order in auto-layout.
                strokesIncludedInLayout (Optional[bool]): Whether strokes are
                    included in layout calculations for auto-layout frames.
                layoutGrids (Optional[List[Dict[str, Any]]]): Layout grids
                    defined on the node (for frames).
                textStyle (Optional[str]): Reference to a text style in
                    'globalVars.styles' (for TEXT nodes). This can also be
                    found in 'styles.text'.
                style (Optional[Dict[str, Any]]): Inline style properties of the
                    node, particularly detailed for TEXT nodes (e.g., fontFamily,
                    fontWeight, fontSize).
                characters (Optional[str]): The actual text content for TEXT nodes.
                characterStyleOverrides (Optional[List[float]]): Array of style
                    IDs applied to characters within a text node.
                styleOverrideTable (Optional[Dict[str, Any]]): Table of style
                    overrides, often used for text styles within a text node.
                lineTypes (Optional[List[str]]): Line types for text nodes
                    (e.g., for lists: 'ORDERED', 'UNORDERED', 'NONE').
                lineIndentations (Optional[List[float]]): Line indentations for
                    text nodes.
                componentId (Optional[str]): ID of the main component if this
                    node is an instance of a component.
                componentProperties (Optional[Dict[str, Any]]): Component
                    properties for instances, defining overridden values.
                overrides (Optional[List[Dict[str, Any]]]): A list of overrides
                    applied to this instance.
                uniformScaleFactor (Optional[float]): Uniform scale factor, used
                    by SECTION nodes.
                isExposedInstance (Optional[bool]): Indicates if an instance is
                    exposed from a nested component.
                exposedInstances (Optional[List[str]]): List of exposed instance
                    node IDs that are children of this node.
                booleanOperation (Optional[str]): Type of boolean operation for
                    boolean group nodes (e.g., 'UNION', 'INTERSECT').
                componentPropertyDefinitions (Optional[Dict[str, Any]]):
                    Definitions of component properties if this node is a
                    component or component_set.
                arcData (Optional[Dict[str, Any]]): Data for arcs on ELLIPSE
                    nodes (startingAngle, endingAngle, innerRadius).
                sliceMeasurements (Optional[Dict[str, Any]]): Measurements for
                    SLICE nodes (x, y, width, height relative to parent).
                devStatus (Optional[Dict[str, Any]]): Developer status of the
                    node, if set (e.g., {'type': 'READY_FOR_DEV'}).
                children (Optional[List[Dict[str, Any]]]): An array of child node
                    objects. Structure is recursive.
                layout (Optional[str]): Reference to a layout style in
                    'globalVars.styles'. Distinct from auto-layout properties.
            globalVars (Dict[str, Any]): Global variables, primarily containing
                style definitions.
                styles (Dict[str, Any]): A dictionary mapping style IDs to their
                    definitions. Style definitions can be simple (e.g., a list
                    of color hex strings) or complex objects (e.g., for text
                    properties like fontFamily, fontWeight, or layout properties).
                    Image fills will also be defined here, referenced by their
                    fill ID.

    Raises:
        NotFoundError: If the file with the given file_key or node with node_id
            does not exist.
        InvalidInputError: If any provided input (e.g. file_key) is malformed
            or invalid.
    """
    # Type validation
    if not isinstance(file_key, str):
        raise InvalidInputError(f"file_key must be a string, got {type(file_key).__name__}.")
    
    if node_id is not None and not isinstance(node_id, str):
        raise InvalidInputError(f"node_id must be a string or None, got {type(node_id).__name__}.")

    # Content validation
    if not file_key or not file_key.strip():
        raise InvalidInputError("File key cannot be empty.")

    if node_id is not None and (not node_id or not node_id.strip()):
        raise InvalidInputError("node_id cannot be empty or whitespace-only if provided.")

    # Format validation for file_key (basic pattern check)
    if not file_key.replace('-', '').replace('_', '').isalnum():
        raise InvalidInputError("file_key contains invalid characters. Only alphanumeric characters, hyphens, and underscores are allowed.")

    # Format validation for node_id (basic pattern check)
    if node_id is not None and not node_id.replace('-', '').replace('_', '').replace(':', '').isalnum():
        raise InvalidInputError("node_id contains invalid characters. Only alphanumeric characters, hyphens, underscores, and colons are allowed.")

    figma_file: Optional[Dict] = utils.get_file_by_key(DB, file_key)

    if figma_file is None:
        raise NotFoundError(f"File with key '{file_key}' not found.")

    # Prepare metadata
    metadata_dict: Dict[str, Any] = {
        "name": figma_file.get('name'),
        "lastModified": figma_file.get('lastModified'),
        "thumbnailUrl": figma_file.get('thumbnailUrl'),
    }
    # Remove any keys that ended up with None values from the get() calls
    metadata_dict = filter_none_values_from_dict(metadata_dict)

    # Prepare nodes
    nodes_data: List[Dict[str, Any]] = []
    document_data: Optional[Dict[str, Any]] = figma_file.get('document')

    if document_data and isinstance(document_data, dict):
        base_node_list_from_doc: Optional[List[Any]] = document_data.get('children')

        if base_node_list_from_doc and isinstance(base_node_list_from_doc, list):
            # Filter out any non-dictionary items from the children list, just in case.
            actual_node_dicts: List[Dict[str, Any]] = [
                item for item in base_node_list_from_doc if isinstance(item, dict)
            ]

            if node_id:
                # Use the existing utils.find_node_by_id function for recursive search
                target_node_dict: Optional[Dict[str, Any]] = utils.find_node_by_id(actual_node_dicts, node_id)
                
                if target_node_dict is None:
                    raise NotFoundError(f"Node with ID '{node_id}' not found in file '{file_key}'.")
                
                # Apply the None filtering, similar to model_dump(exclude_none=True)
                nodes_data = [filter_none_values_from_dict(target_node_dict)]
            else:
                # Process all nodes if no specific node_id is given
                nodes_data = [
                    filter_none_values_from_dict(node_dict_item) for node_dict_item in actual_node_dicts
                ]

    # Prepare globalVars
    global_vars_input_dict: Optional[Dict[str, Any]] = figma_file.get('globalVars')
    global_vars_data: Dict[str, Any] = filter_none_values_from_dict(global_vars_input_dict)

    return {
        "metadata": metadata_dict,
        "nodes": nodes_data,
        "globalVars": global_vars_data,
    }

@tool_spec(
    spec={
        'name': 'download_figma_images',
        'description': """ Downloads images for specified nodes from a Figma file to a local path.
        
        The 'file_name' parameter in the input 'nodes' specifies the desired name for the output file. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_key': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma file (used for context).'
                },
                'nodes': {
                    'type': 'array',
                    'description': """ A list of nodes to "download" as images.
                    Each item must be a dictionary with: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'node_id': {
                                'type': 'string',
                                'description': """ The unique identifier of the node. The corresponding
                                                source image in './files/' is assumed to be named
                                               based on this ID (e.g., '{node_id}.png'). """
                            },
                            'file_name': {
                                'type': 'string',
                                'description': """ The desired file name for the downloaded image
                                                  to be saved in local_path (e.g., 'image.png'). """
                            }
                        },
                        'required': [
                            'node_id',
                            'file_name'
                        ]
                    }
                },
                'local_path': {
                    'type': 'string',
                    'description': 'The local directory path where the images should be saved.'
                }
            },
            'required': [
                'file_key',
                'nodes',
                'local_path'
            ]
        }
    }
)
def download_figma_images(file_key: str, nodes: List[Dict[str, str]], local_path: str) -> Tuple[str, str]:
    """Downloads images for specified nodes from a Figma file to a local path.

    The 'file_name' parameter in the input 'nodes' specifies the desired name for the output file.

    Args:
        file_key (str): The unique identifier of the Figma file (used for context).
        nodes (List[Dict[str, str]]): A list of nodes to "download" as images.
            Each item must be a dictionary with:
            node_id (str): The unique identifier of the node. The corresponding
                           source image in './files/' is assumed to be named
                           based on this ID (e.g., '{node_id}.png').
            file_name (str): The desired file name for the downloaded image
                             to be saved in local_path (e.g., 'image.png').
        local_path (str): The local directory path where the images should be saved.

    Returns:
        Tuple[str, str]: A tuple containing the download status message and the
            local path where images were saved.

    Raises:
        NotFoundError: If the Figma file with the given file_key is not found, if a
                       node specified in the nodes list does not exist in the file's metadata,
                       or if a source image file in the './files/' directory is not found.
        InvalidInputError: If inputs are malformed or local_path is invalid/inaccessible.
        DownloadError: If an error occurs during the image copy process for one or
                       more nodes, such as file system errors or permission issues.
    """

    # 1. Input validation
    if not file_key or not isinstance(file_key, str):
        raise InvalidInputError("file_key must be a non-empty string.")

    if not isinstance(nodes, list):
        raise InvalidInputError("nodes argument must be a list.")

    for i, node_spec in enumerate(nodes):
        if not isinstance(node_spec, dict):
            raise InvalidInputError(f"Item at index {i} in nodes list is not a dictionary.")

        node_id = node_spec.get("node_id")
        output_file_name = node_spec.get("file_name") # Renamed for clarity

        if not node_id or not isinstance(node_id, str):
            raise InvalidInputError(f"Item at index {i} in nodes list must have a non-empty string 'node_id'.")
        if not output_file_name or not isinstance(output_file_name, str):
            raise InvalidInputError(f"Item at index {i} in nodes list must have a non-empty string 'file_name'.")

        p_output_file_name = pathlib.Path(output_file_name)
        if p_output_file_name.is_absolute():
            raise InvalidInputError(f"file_name '{output_file_name}' (for node '{node_id}') must be a relative path.")
        if ".." in p_output_file_name.parts:
            raise InvalidInputError(f"file_name '{output_file_name}' (for node '{node_id}') cannot contain '..' components.")

    if not local_path or not isinstance(local_path, str):
        raise InvalidInputError("local_path must be a non-empty string.")

    # 2. Prepare local_path directory (destination)
    p_local_path = pathlib.Path(local_path)
    try:
        p_local_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise InvalidInputError(f"Failed to create or access local directory '{local_path}': {e}")

    if not p_local_path.is_dir():
        raise InvalidInputError(f"Local path '{local_path}' is not a directory or could not be created.")
    if not os.access(str(p_local_path), os.W_OK):
        raise InvalidInputError(f"Local path '{local_path}' is not writable.")

    # 3. (Optional) Retrieve Figma file metadata from DB (simulation)
    figma_file_obj = utils.get_file_by_key(DB, file_key)
    if not figma_file_obj:
        raise NotFoundError(f"Figma file with key '{file_key}' not found.")

    # 4. (Optional) Verify all nodes exist in Figma metadata (simulation)
    search_root_nodes = []
    document = figma_file_obj.get("document")
    if document and "children" in document:
        search_root_nodes = document["children"]
    
    for node_spec in nodes:
        node_id = node_spec["node_id"]
        target_node = utils.find_node_by_id(search_root_nodes, node_id)
        if not target_node:
            raise NotFoundError(f"Node with ID '{node_id}' not found in Figma file '{file_key}'.")

    node_details_for_processing = nodes # Use the validated nodes list directly

    # 5. Perform "downloads" by copying from source './files/{node_id}' to destination 'local_path/output_file_name'
    downloaded_file_info = []
    download_errors_list = []
    
    source_files_root_path = pathlib.Path("./files") # Define the source directory

    for item in node_details_for_processing:
        node_id = item["node_id"]
        output_file_name = item["file_name"] # This is the desired name for the output file

        # --- Assumption for source file naming ---
        # It's assumed the source image in './files/' is named based on the node_id,
        assumed_source_filename_in_source_dir = f"{node_id}.png"
        # --- End of assumption ---

        source_image_full_path = source_files_root_path.joinpath(assumed_source_filename_in_source_dir)
        destination_image_full_path = p_local_path.joinpath(output_file_name).resolve()

        try:
            # Security check: ensure the resolved destination path is still within the intended local_path
            if not str(destination_image_full_path).startswith(str(p_local_path.resolve())):
                download_errors_list.append(
                    f"Invalid output_file_name '{output_file_name}' for node '{node_id}': "
                    f"path resolves to '{destination_image_full_path}', which is outside target directory '{p_local_path.resolve()}'."
                )
                continue

            # Ensure parent directory of the destination image file exists
            destination_image_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if the source image file exists
            if not source_image_full_path.is_file():
                # Using NotFoundError as it's a missing source dependency
                download_errors_list.append(
                    f"Source image file '{source_image_full_path}' (for node_id '{node_id}') not found."
                )
                continue
            
            # Perform the copy from source to destination
            shutil.copy2(source_image_full_path, destination_image_full_path)
            downloaded_file_info.append({"path": str(destination_image_full_path), "node_id": node_id})

        except OSError as e:
            download_errors_list.append(f"Failed to copy image for node '{node_id}' (source: '{source_image_full_path}', dest: '{destination_image_full_path}'): {e}")
        except Exception as e: # Catch any other unexpected errors during file operations
            download_errors_list.append(f"Unexpected error copying image for node '{node_id}' (output file: '{output_file_name}'): {e}")

    # 6. Handle results and errors from copy phase
    if download_errors_list:
        # Check if all errors are due to missing source files
        all_missing_source_files = all(
            "Source image file" in error and "not found" in error 
            for error in download_errors_list
        )
        
        if all_missing_source_files and len(download_errors_list) == 1:
            # If only one source file is missing, raise NotFoundError
            raise NotFoundError(download_errors_list[0])
        elif all_missing_source_files:
            # If multiple source files are missing, raise NotFoundError with summary
            error_summary = "; ".join(download_errors_list)
            raise NotFoundError(f"Multiple source image files not found: {error_summary}")
        else:
            # If there are other types of errors, raise DownloadError
            error_summary = "; ".join(download_errors_list)
            raise DownloadError(f"One or more errors occurred during image processing: {error_summary}")

    num_downloaded = len(downloaded_file_info)

    if not nodes: # Case: Input 'nodes' list was empty.
        status_message = "No nodes specified for processing. 0 images processed."
    else: # Case: Input 'nodes' list was not empty.
        paths_str = ", ".join([info["path"] for info in downloaded_file_info])
        status_message = f"Successfully processed {num_downloaded} image(s) and saved to '{local_path}'."
        if num_downloaded > 0: 
            status_message += f" Paths: {paths_str}"
        # If num_downloaded is 0 but nodes was not empty, it implies all failed and DownloadError was raised.

    return status_message, str(p_local_path)


@tool_spec(
    spec={
        'name': 'set_current_file',
        'description': 'Finds a file by its key in the DB and sets it as the current_file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'file_key': {
                    'type': 'string',
                    'description': """ The fileKey of the file to set as the current file.
                    Must be a non-empty string. """
                }
            },
            'required': [
                'file_key'
            ]
        }
    }
)
def set_current_file(file_key: str) -> bool:
    """
    Finds a file by its key in the DB and sets it as the current_file.

    Args:
        file_key (str): The fileKey of the file to set as the current file.
                  Must be a non-empty string.

    Returns:
        bool: True if the file was found and the current_file_key was updated,
    
    Raises:
        InvalidInputError: If the provided file_key is not a non-empty string or if the 
                            provided file_key does not correspond to any file
                            in the database.
    """
    # Input validation for file_key
    if not isinstance(file_key, str):
        raise InvalidInputError(f"Error: Invalid input type for file_key. Expected string, got {type(file_key).__name__}.")
    if not file_key: # Check for empty string
        raise InvalidInputError("Error: Invalid input. file_key cannot be an empty string.")

    # Create a list of all available file keys
    # Ensure robust access to 'files' and 'fileKey' within each file entry
    available_keys = []
    for f in DB.get("files", []):
        if isinstance(f, dict) and isinstance(f.get("fileKey"), str):
            available_keys.append(f.get("fileKey"))


    if file_key in available_keys:
        DB["current_file_key"] = file_key
        # Clear the current selection since the new file doesn't have those nodes
        DB["current_selection_node_ids"] = []
        return True
    else:
        raise InvalidInputError(f"Error: File with key '{file_key}' not found in the database.")