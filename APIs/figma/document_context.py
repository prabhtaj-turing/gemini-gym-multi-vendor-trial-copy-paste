from common_utils.tool_spec_decorator import tool_spec
# figma/document_context.py

from typing import List, Dict, Any, Optional

# Import necessary components from the simulation engine
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import NoDocumentOpenError, FigmaOperationError
from .SimulationEngine import utils
from .SimulationEngine.models import FigmaStyle
from .SimulationEngine import custom_errors
from .SimulationEngine.utils import _build_node_map_recursive, _collect_components_recursive
from .SimulationEngine import models


@tool_spec(
    spec={
        'name': 'get_styles',
        'description': """ Get all styles from the current Figma document.
        
        This function retrieves all styles defined in the current Figma document.
        Each style is represented as a dictionary containing its properties. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_styles() -> List[Dict[str, Any]]:
    """
    Get all styles from the current Figma document.

    This function retrieves all styles defined in the current Figma document.
    Each style is represented as a dictionary containing its properties.

    Returns:
        List[Dict[str, Any]]: A list of all styles defined in the current document. Each dictionary
            in the list represents a style and has the following structure:
            id (str): The unique identifier of the style.
            key (str): A unique key for the style, often used in API requests for
                applying the style.
            name (str): The user-defined name of the style.
            styleType (str): The type of style (e.g., 'FILL', 'TEXT', 'EFFECT', 'GRID').
            description (Optional[str]): An optional description for the style.
            remote (bool): Whether the style is from a remote library.
            paints (Optional[List[Dict[str, Any]]]): Present if 'styleType' is 'FILL'.
                A list of paint objects applied to the style. Each paint object is a
                dictionary that typically includes:
                type (str): The type of paint (e.g., 'SOLID', 'GRADIENT_LINEAR').
                visible (Optional[bool]): Whether the paint is visible (defaults to true).
                opacity (Optional[float]): Opacity of the paint (0 to 1, defaults to 1).
                color (Optional[Dict[str, float]]): For 'SOLID' paint type, a
                    dictionary defining the color (e.g., keys 'r', 'g', 'b', 'a' with float values).
                gradientStops (Optional[List[Dict[str, Any]]]): For gradient paint
                    types, a list of dictionaries, where each dictionary defines a gradient stop.
                Other properties may exist in the paint object dictionary
                depending on the paint 'type'.
            fontSize (Optional[float]): Present if 'styleType' is 'TEXT'. The font size.
            fontName (Optional[Dict[str, str]]): Present if 'styleType' is 'TEXT'.
                A dictionary describing the font family and style. This dictionary contains:
                family (str): Font family.
                style (str): Font style.
            Depending on 'styleType', other properties specific to that style type might also be present in the style dictionary.

    Raises:
        NoDocumentOpenError: If no Figma document is currently open or accessible.
        FigmaOperationError: If there is an issue retrieving styles from the Figma document.
    """
    current_file_key = DB.get('current_file_key')
    if not current_file_key:
        raise NoDocumentOpenError("No Figma document is currently open.")

    files_list_data = DB.get('files')

    # Handle if 'files' key is missing or explicitly None in DB
    if files_list_data is None:
        files_list = [] # Treat as empty list, will lead to "file not found"
    elif not isinstance(files_list_data, list): # Check if the retrieved 'files' entry is a list
        raise FigmaOperationError("Current Figma file data is malformed (expected list).")
    else:
        files_list = files_list_data

    # Iterate through files_list, ensuring each item 'f' is a dict before calling .get()
    current_file = next((f for f in files_list if isinstance(f, dict) and f.get('fileKey') == current_file_key), None)
    
    if not current_file:
        # This error triggers if the list was empty, or no dict element matched the key
        raise FigmaOperationError(f"Current file with key '{current_file_key}' not found.")

    if not isinstance(current_file, dict):
        raise FigmaOperationError("Current Figma document data is malformed (expected dict).")


    global_vars = current_file.get('globalVars', {})
    if not isinstance(global_vars, dict):
         raise FigmaOperationError("Global variables data ('globalVars') in the document is malformed (expected dict).")

    styles_container = global_vars.get('styles')
    if not styles_container:
        return []

    if not isinstance(styles_container, dict):
         raise FigmaOperationError("Style definitions data under 'globalVars' is malformed (expected dict).")

    all_styles_list: List[Dict[str, Any]] = []

    for style_id, style_data in styles_container.items():
        if not isinstance(style_data, dict):
            continue

        style_type = style_data.get('styleType')
        style_name = style_data.get('name')
        style_key = style_data.get('key')

        if not all(isinstance(val, str) for val in [style_type, style_name, style_key]):
            continue
            
        figma_style_instance = FigmaStyle(
            id=style_id,
            key=style_key,
            name=style_name,
            styleType=style_type,
            description=style_data.get('description'),
            remote=bool(style_data.get('remote', False))
        )

        output_style_entry = figma_style_instance.model_dump(exclude_none=True)
        
        style_content = style_data.get('root')
        if isinstance(style_content, dict):
            if style_type == 'FILL':
                output_style_entry['paints'] = [style_content]
            else:
                output_style_entry.update(style_content)
                if style_type == 'TEXT':
                    font_family = style_content.get('fontFamily')
                    font_style_name = style_content.get('fontPostScriptName')
                    if isinstance(font_family, str) and isinstance(font_style_name, str):
                        output_style_entry['fontName'] = {'family': font_family, 'style': font_style_name}

        all_styles_list.append(output_style_entry)

    return all_styles_list


@tool_spec(
    spec={
        'name': 'get_local_components',
        'description': """ Get all local components from the Figma document for current file.
        
        This function retrieves all local components that are defined within the Figma document for current file.
        It returns a list where each item is a dictionary representing a local component.
        Each dictionary contains details for the component, including its unique identifier ('id'),
        a unique 'key' for API usage or instance creation, its user-defined 'name', an
        optional 'description', an optional 'componentSetId' if the component is part of
        a component set (variants), and the 'parentId' indicating the page or frame
        that contains the main component definition. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_local_components() -> List[Dict[str, Any]]:
    """Get all local components from the Figma document for current file.

    This function retrieves all local components that are defined within the Figma document for current file.
    It returns a list where each item is a dictionary representing a local component.
    Each dictionary contains details for the component, including its unique identifier ('id'),
    a unique 'key' for API usage or instance creation, its user-defined 'name', an
    optional 'description', an optional 'componentSetId' if the component is part of
    a component set (variants), and the 'parentId' indicating the page or frame
    that contains the main component definition.

    Returns:
        List[Dict[str, Any]]: A list of all local components defined in the current document.
            Each dictionary in the list represents a component and includes the following keys:
            id (str): The unique identifier of the component node.
            key (str): A unique key for the component, used for creating instances or referencing in APIs.
            name (str): The user-defined name of the component.
            description (Optional[str]): An optional description for the component. Default is None.
            componentSetId (Optional[str]): If the component is part of a component set (variants), this is the ID of that set. Default is None.
            parentId (str): The ID of the page or frame containing this main component definition.

    Raises:
        NoDocumentOpenError: If no Figma document is currently open or accessible.
        FigmaOperationError: If there is an issue retrieving local components from the Figma document.
    """
    current_file_key = DB.get('current_file_key')
    if not current_file_key:
        raise custom_errors.FigmaOperationError("Current file key not found in DB.")

    current_file = next((f for f in DB.get('files', []) if f.get('fileKey') == current_file_key), None)
    if not current_file:
        raise custom_errors.FigmaOperationError(f"Current file with key '{current_file_key}' not found.")

    figma_document_root = current_file.get('document')
    if not figma_document_root:
        raise custom_errors.FigmaOperationError("Current file is missing a 'document' object.")

    # Validate the structure of the document root
    if not isinstance(figma_document_root, dict):
        raise custom_errors.FigmaOperationError(
            "Figma document data is not in the expected format (root must be a dictionary)."
        )

    all_nodes_map: Dict[str, Dict[str, Any]] = {}
    try:
        # Build a map of all nodes for efficient parent lookup during component processing.
        # This step involves traversing the entire document structure once.
        _build_node_map_recursive(figma_document_root, all_nodes_map)
    except Exception as e:
        # Catch unexpected errors during node map creation (e.g., recursion depth, memory issues with huge documents).
        raise custom_errors.FigmaOperationError(
            f"Failed to process document structure while building node map: {e}"
        ) from e


    local_components: List[Dict[str, Any]] = []
    try:
        # Traverse the document structure (again, conceptually) to find and collect components.
        _collect_components_recursive(figma_document_root, local_components, all_nodes_map)
    except KeyError as e:
        raise custom_errors.FigmaOperationError(str(e))
    except Exception as e:
        # Catch any other unexpected errors during the component collection phase.
        raise custom_errors.FigmaOperationError(
            f"An unexpected error occurred while retrieving local components: {e}"
        ) from e

    validated_local_components = [models.LocalComponent(**component).model_dump() for component in local_components]
    return validated_local_components
