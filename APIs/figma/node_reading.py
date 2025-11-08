from common_utils.tool_spec_decorator import tool_spec
from collections.abc import Mapping
from typing import Dict, Any, List, Optional, Union, Set

from figma.SimulationEngine.db import DB  # Assuming DB is imported
from figma.SimulationEngine import utils  # Assuming utils is imported
from figma.SimulationEngine.custom_errors import NodeNotFoundError, FigmaOperationError, InvalidInputError, ValidationError, PluginError, NodeTypeError
from figma.SimulationEngine.models import ( # Assuming these models are defined in models.py
    FigmaNodeDetails,
    FigmaNodeDetailColor,
    FigmaNodeDetailBoundingBox,
    FigmaNodeDetailPaint,
    FigmaNodeDetailEffect,
    FigmaNodeDetailEffectOffset,
    FigmaNodeDetailFontName
)

from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.utils import _recursive_scan_node_children, _CONTAINER_NODE_TYPES, _KNOWN_FIGMA_TYPES

from figma.SimulationEngine.models import Node, DBDocumentNode, SelectedNodeInfo
from figma.SimulationEngine.custom_errors import FigmaOperationError, NoSelectionError

@tool_spec(
    spec={
        'name': 'get_node_info',
        'description': """ Get detailed information about a specific node in Figma.
        
        Gets detailed information about a specific node in Figma. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'nodeId': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma node to retrieve.'
                }
            },
            'required': [
                'nodeId'
            ]
        }
    }
)
def get_node_info(nodeId: str) -> Dict[str, Any]:
    """Get detailed information about a specific node in Figma.

    Gets detailed information about a specific node in Figma.

    Args:
        nodeId (str): The unique identifier of the Figma node to retrieve.

    Returns:
        Dict[str, Any]: Detailed information for the specified node. It includes the following keys:
          id (str): The unique identifier of the node.
          name (str): The name of the node.
          type (str): The type of the node (e.g., 'DOCUMENT', 'CANVAS', 'FRAME', 'RECTANGLE', 'TEXT', 'COMPONENT', 'INSTANCE', 'VECTOR').
          visible (bool): Whether the node is visible on the canvas.
          locked (bool): Whether the node is locked for editing.
          opacity (float): Opacity of the node, between 0.0 (transparent) and 1.0 (opaque).
          absoluteBoundingBox (Dict[str, float]): The node's bounding box in absolute coordinates on the page. Contains keys:
            x (float): X-coordinate of the top-left corner.
            y (float): Y-coordinate of the top-left corner.
            width (float): Width of the bounding box.
            height (float): Height of the bounding box.
          fills (List[Dict[str, Any]]): A list of paints applied to the node's fill. Each item in the list is a dictionary with keys:
            type (str): Type of paint (e.g., 'SOLID', 'GRADIENT_LINEAR', 'IMAGE').
            visible (bool): Whether this paint is visible.
            opacity (Optional[float]): Opacity of this paint (0.0-1.0).
            color (Optional[Dict[str, float]]): RGBA color for SOLID paints. Contains keys:
              r (float): Red component (0.0-1.0).
              g (float): Green component (0.0-1.0).
              b (float): Blue component (0.0-1.0).
              a (float): Alpha component (0.0-1.0).
          strokes (List[Dict[str, Any]]): A list of paints applied to the node's stroke. Each item in the list is a dictionary with keys:
            type (str): Type of paint (e.g., 'SOLID', 'GRADIENT_LINEAR', 'IMAGE').
            visible (bool): Whether this paint is visible.
            opacity (Optional[float]): Opacity of this paint (0.0-1.0).
            color (Optional[Dict[str, float]]): RGBA color for SOLID paints. Contains keys:
              r (float): Red component (0.0-1.0).
              g (float): Green component (0.0-1.0).
              b (float): Blue component (0.0-1.0).
              a (float): Alpha component (0.0-1.0).
          strokeWeight (float): The thickness of the stroke.
          strokeAlign (str): Position of the stroke ('INSIDE', 'OUTSIDE', 'CENTER').
          effects (List[Dict[str, Any]]): A list of effects applied to the node (e.g., drop shadow, blur). Each item in the list is a dictionary with keys:
            type (str): Type of effect (e.g., 'DROP_SHADOW', 'LAYER_BLUR').
            visible (bool): Whether this effect is visible.
            radius (float): Radius for blur effects or spread for shadow effects.
            color (Optional[Dict[str, float]]): RGBA color for shadow effects. Contains keys:
              r (float): Red component (0.0-1.0).
              g (float): Green component (0.0-1.0).
              b (float): Blue component (0.0-1.0).
              a (float): Alpha component (0.0-1.0).
            offset (Optional[Dict[str, float]]): X/Y offset for shadow effects. Contains keys:
              x (float): X offset.
              y (float): Y offset.
          children (Optional[List[Dict[str, Any]]]): An array of child nodes if this node is a container. Each child node object has the same structure as this 'node_details' object.
          parentId (Optional[str]): The ID of the parent node, if any.
          characters (Optional[str]): For TEXT nodes: The text content.
          fontSize (Optional[float]): For TEXT nodes: The font size in pixels.
          fontName (Optional[Dict[str, str]]): For TEXT nodes: Font family and style. Contains keys:
            family (str): Font family name.
            style (str): Font style (e.g., 'Regular', 'Bold').
          componentId (Optional[str]): For INSTANCE nodes: The ID of the main component.
          layoutMode (Optional[str]): For FRAME nodes: Auto layout mode ('NONE', 'HORIZONTAL', 'VERTICAL').
          itemSpacing (Optional[float]): For auto-layout FRAME nodes: Spacing between items.
          paddingLeft (Optional[float]): For auto-layout FRAME nodes: Left padding.
          paddingRight (Optional[float]): For auto-layout FRAME nodes: Right padding.
          paddingTop (Optional[float]): For auto-layout FRAME nodes: Top padding.
          paddingBottom (Optional[float]): For auto-layout FRAME nodes: Bottom padding.
          primaryAxisAlignItems (Optional[str]): For auto-layout FRAME nodes: Alignment along the primary axis.
          counterAxisAlignItems (Optional[str]): For auto-layout FRAME nodes: Alignment along the counter axis.

    Raises:
        NodeNotFoundError: If the node with the given nodeId does not exist.
        FigmaOperationError: If there is an issue communicating with the Figma plugin environment,
                             or if node data fails Pydantic validation.
        InvalidInputError: If the nodeId is malformed or missing.
    """
    if not nodeId or not isinstance(nodeId, str):
        raise InvalidInputError("Node ID must be a non-empty string.")

    if not isinstance(DB, Mapping) or not isinstance(DB.get('files'), list):
        raise FigmaOperationError(
            "Figma data source (DB) must be a dictionary and contain a 'files' list."
        )

    # 2. Get the current file key and find the corresponding file.
    current_file = utils.get_current_file()

    # 3. Validate the state of the current file.
    # This checks if the key existed, if the file was found, and if it has a valid document.
    if not current_file:
        raise FigmaOperationError(
            f"Validation failed: The 'current_file_key' is invalid or the corresponding file was not found in the 'files' list."
        )

    if not isinstance(current_file.get('document'), dict):
        raise FigmaOperationError(
            f"Validation failed: The current file is missing a valid 'document' object."
        )

    node_data = utils.get_node_from_db(DB, nodeId)

    if node_data is None:
        raise NodeNotFoundError(f"Node with ID '{nodeId}' not found.")

    def _format_node_to_model_recursive(current_node_data: Dict[str, Any], current_node_id: str) -> FigmaNodeDetails:
        # Prepare absoluteBoundingBox
        bbox_data = current_node_data.get('absoluteBoundingBox')
        if not isinstance(bbox_data, dict):
            bbox_data_prepared = bbox_data if isinstance(bbox_data, dict) else {}
        else:
            bbox_data_prepared = bbox_data

        prepared_bbox = FigmaNodeDetailBoundingBox(
            x=bbox_data_prepared.get('x', 0.0), # Defaulting to 0.0 if missing, as field is non-optional
            y=bbox_data_prepared.get('y', 0.0),
            width=bbox_data_prepared.get('width', 0.0),
            height=bbox_data_prepared.get('height', 0.0)
        )


        # Prepare Fills
        prepared_fills: List[FigmaNodeDetailPaint] = []
        fills_data_source = current_node_data.get('fills') or []
        actual_fills_list: List[Any] = []
        if isinstance(fills_data_source, dict) and 'root' in fills_data_source and isinstance(fills_data_source['root'], list): # Compatibility with potential RootModel dump
            actual_fills_list = fills_data_source['root']
        elif isinstance(fills_data_source, list):
            actual_fills_list = fills_data_source

        for fill_item_data in actual_fills_list:
            if isinstance(fill_item_data, dict):
                color_data = fill_item_data.get('color')
                prepared_color = None
                if isinstance(color_data, dict):
                    # FigmaNodeDetailColor fields (r,g,b,a) are non-optional floats
                    prepared_color = FigmaNodeDetailColor(
                        r=color_data.get('r', 0.0), # Defaulting to 0.0 if sub-field missing
                        g=color_data.get('g', 0.0),
                        b=color_data.get('b', 0.0),
                        a=color_data.get('a', 1.0)  # Defaulting alpha to 1.0
                    )
                prepared_fills.append(
                    FigmaNodeDetailPaint(
                        type=fill_item_data.get('type', 'UNKNOWN'), # Default type if missing
                        visible=fill_item_data.get('visible', True),
                        opacity=fill_item_data.get('opacity'), # Optional in model
                        color=prepared_color # Optional in model
                    )
                )

        # Prepare Strokes
        prepared_strokes: List[FigmaNodeDetailPaint] = []
        strokes_data_source = current_node_data.get('strokes') or []
        for stroke_item_data in strokes_data_source:
            if isinstance(stroke_item_data, dict):
                color_data = stroke_item_data.get('color')
                prepared_color = None
                if isinstance(color_data, dict):
                    prepared_color = FigmaNodeDetailColor(
                        r=color_data.get('r', 0.0),
                        g=color_data.get('g', 0.0),
                        b=color_data.get('b', 0.0),
                        a=color_data.get('a', 1.0)
                    )
                prepared_strokes.append(
                    FigmaNodeDetailPaint(
                        type=stroke_item_data.get('type', 'UNKNOWN'),
                        visible=stroke_item_data.get('visible', True),
                        opacity=stroke_item_data.get('opacity'),
                        color=prepared_color
                    )
                )

        # Prepare Effects
        prepared_effects: List[FigmaNodeDetailEffect] = []
        effects_data_source = current_node_data.get('effects') or []
        for effect_item_data in effects_data_source:
            if isinstance(effect_item_data, dict):
                color_data = effect_item_data.get('color')
                prepared_effect_color = None
                if isinstance(color_data, dict):
                    prepared_effect_color = FigmaNodeDetailColor(
                        r=color_data.get('r', 0.0),
                        g=color_data.get('g', 0.0),
                        b=color_data.get('b', 0.0),
                        a=color_data.get('a', 1.0)
                    )

                offset_data = effect_item_data.get('offset')
                prepared_effect_offset = None
                if isinstance(offset_data, dict):
                    prepared_effect_offset = FigmaNodeDetailEffectOffset(
                        x=offset_data.get('x', 0.0), # Defaulting if missing
                        y=offset_data.get('y', 0.0)
                    )
                
                # FigmaNodeDetailEffect.radius is non-optional float
                prepared_effects.append(
                    FigmaNodeDetailEffect(
                        type=effect_item_data.get('type', 'UNKNOWN'),
                        visible=effect_item_data.get('visible', True),
                        radius=effect_item_data.get('radius', 0.0), # Defaulting to 0.0
                        color=prepared_effect_color, # Optional in model
                        offset=prepared_effect_offset # Optional in model
                    )
                )

        # Parent ID
        parent_node_dict = utils.get_parent_of_node_from_db(DB, current_node_id)
        parent_id = parent_node_dict.get('id') if parent_node_dict else None

        # Text Properties
        characters: Optional[str] = None
        font_size: Optional[float] = None
        font_name_model: Optional[FigmaNodeDetailFontName] = None
        if current_node_data.get('type') == 'TEXT':
            characters = current_node_data.get('characters', current_node_data.get('text')) # Prefer 'characters'
            node_style_data = current_node_data.get('style')
            if isinstance(node_style_data, dict):
                font_size = node_style_data.get('fontSize')
                family = node_style_data.get('fontFamily')
                style = node_style_data.get('fontPostScriptName') # Often contains style
                if family or style: # Ensure at least one is present to create FontName
                     font_name_model = FigmaNodeDetailFontName(
                        family=family or "Unknown", # Default if one is missing
                        style=style or "Regular"
                    )


        # Instance Properties
        component_id: Optional[str] = None
        if current_node_data.get('type') == 'INSTANCE':
            component_id = current_node_data.get('componentId')

        # Frame / Auto Layout properties
        layout_mode: Optional[str] = None
        item_spacing: Optional[float] = None
        padding_left: Optional[float] = None
        padding_right: Optional[float] = None
        padding_top: Optional[float] = None
        padding_bottom: Optional[float] = None
        primary_axis_align_items: Optional[str] = None
        counter_axis_align_items: Optional[str] = None

        node_type = current_node_data.get('type')
        if node_type in ['FRAME', 'COMPONENT', 'COMPONENT_SET', 'INSTANCE']:
            layout_mode = current_node_data.get('layoutMode')
            if layout_mode and layout_mode != 'NONE':
                item_spacing = current_node_data.get('itemSpacing')
                padding_left = current_node_data.get('paddingLeft')
                padding_right = current_node_data.get('paddingRight')
                padding_top = current_node_data.get('paddingTop')
                padding_bottom = current_node_data.get('paddingBottom')
                primary_axis_align_items = current_node_data.get('primaryAxisAlignItems')
                counter_axis_align_items = current_node_data.get('counterAxisAlignItems')

        # Children (Recursive call)
        prepared_children: Optional[List[FigmaNodeDetails]] = None
        children_data_list = current_node_data.get('children')
        if isinstance(children_data_list, list):
            prepared_children = []
            for child_node_data in children_data_list:
                if isinstance(child_node_data, dict) and child_node_data.get('id'):
                    prepared_children.append(
                        _format_node_to_model_recursive(child_node_data, child_node_data['id'])
                    )
            if not prepared_children: # Ensure it's None if list ends up empty vs empty list
                prepared_children = None


        # Instantiate the main Pydantic model for the current node
        # FigmaNodeDetails.opacity is non-optional float, defaults to 1.0 if not present or None
        node_opacity = current_node_data.get('opacity')

        return FigmaNodeDetails(
            id=current_node_data.get('id', current_node_id), # Ensure ID is present
            name=current_node_data.get('name', 'Unnamed Node'), # Default name
            type=current_node_data.get('type', 'UNKNOWN'), # Default type
            visible=current_node_data.get('visible', True),
            locked=current_node_data.get('locked', False),
            opacity=node_opacity if node_opacity is not None else 1.0,
            absoluteBoundingBox=prepared_bbox,
            fills=prepared_fills,
            strokes=prepared_strokes,
            strokeWeight=current_node_data.get('strokeWeight', 0.0), # non-optional float
            strokeAlign=current_node_data.get('strokeAlign', 'INSIDE'), # Default if missing
            effects=prepared_effects,
            children=[child.model_dump() for child in prepared_children] if prepared_children else None,
            parentId=parent_id,
            characters=characters,
            fontSize=font_size,
            fontName=font_name_model,
            componentId=component_id,
            layoutMode=layout_mode,
            itemSpacing=item_spacing,
            paddingLeft=padding_left,
            paddingRight=padding_right,
            paddingTop=padding_top,
            paddingBottom=padding_bottom,
            primaryAxisAlignItems=primary_axis_align_items,
            counterAxisAlignItems=counter_axis_align_items,
        )

    try:
        node_details_model = _format_node_to_model_recursive(node_data, nodeId)
        # .model_dump() includes None values by default for Optional fields, which matches typical API behavior.
        # Use model_dump(exclude_none=True) if keys with None values should be omitted.
        return node_details_model.model_dump()
    except PydanticValidationError as e:
        # Catch validation errors from Pydantic and raise as FigmaOperationError
        error_details = e.errors()
        raise FigmaOperationError(
            f"Data validation error for node '{nodeId}': Details: {error_details[0].get('msg')}"
        )
    except Exception as e: # Catch any other unexpected errors during formatting
        raise FigmaOperationError(f"An unexpected error occurred while formatting node data for '{nodeId}': {str(e)}")

@tool_spec(
    spec={
        'name': 'get_selection',
        'description': """ Get information about the current selection in Figma.
        
        Gets information about the current selection in Figma. This function returns
        a list of dictionaries, where each dictionary represents a currently
        selected node. Each dictionary provides a summary of the node, including
        its unique identifier ('id'), name ('name'), type ('type'), and the ID
        of its parent node ('parentId'). """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_selection() -> List[Dict[str, Any]]:
    """Get information about the current selection in Figma.

    Gets information about the current selection in Figma. This function returns
    a list of dictionaries, where each dictionary represents a currently
    selected node. Each dictionary provides a summary of the node, including
    its unique identifier ('id'), name ('name'), type ('type'), and the ID
    of its parent node ('parentId').

    Returns:
        List[Dict[str, Any]]: A list of currently selected nodes. Each dictionary
            in the list provides a summary of a selected node with the
            following keys:
            id (str): The unique identifier of the selected node.
            name (str): The name of the selected node.
            type (str): The type of the node (e.g., 'FRAME', 'RECTANGLE', 'TEXT').
            parentId (str): The ID of the parent node.

    Raises:
        NoSelectionError: If no nodes are currently selected in the Figma document.
        FigmaOperationError: If there is an issue communicating with the Figma plugin environment
                             or if data integrity issues are found (e.g., selected node not found).
    """
    if not isinstance(DB, dict):
        raise FigmaOperationError("Internal DB is not configured correctly or not accessible.")

    selected_node_ids: Optional[List[str]] = DB.get('current_selection_node_ids')

    if not selected_node_ids:
        raise NoSelectionError("No nodes are currently selected.")

    files_list = DB.get('files')
    if not isinstance(files_list, list) or not files_list:
        raise FigmaOperationError("Figma file data is missing, not a list, or empty in DB.")


    if not isinstance(files_list[0], dict):
        raise FigmaOperationError("Figma file data entry is not a dictionary.")
    
    file_data_dict = utils.get_current_file()

    document_dict = file_data_dict.get('document')
    if not isinstance(document_dict, dict):
        raise FigmaOperationError("Document data is missing or not a dictionary in the Figma file.")

    # Parse the document dictionary into Pydantic models to leverage utils
    doc_model = DBDocumentNode.model_validate(document_dict).model_dump()
    if not doc_model.get('id') or not isinstance(doc_model.get('id'), str):
        raise FigmaOperationError("Document root node is missing a valid ID.")


    result_list: List[Dict[str, Any]] = []

    # The list of nodes to search within. These are typically canvases, children of the document.
    search_root_list_for_nodes: List[Node] = doc_model.get('children') or []

    for node_id_to_find in selected_node_ids:
        if not isinstance(node_id_to_find, str):
            # Selected IDs must be strings.
            raise FigmaOperationError(f"Invalid node ID type in selection list: {type(node_id_to_find)}. Must be a string.")

        # Find the selected node model using the utility function.
        selected_node_model: Optional[Node] = utils.find_node_by_id(search_root_list_for_nodes, node_id_to_find)

        if not selected_node_model:
            # If a selected ID doesn't correspond to any node found.
            raise FigmaOperationError(f"Selected node ID '{node_id_to_find}' not found within the document's canvases or their children.")

        # Extract properties from the found node model
        node_id = selected_node_model.get('id')
        node_name = selected_node_model.get('name') if selected_node_model.get('name') is not None else ""
        node_type = selected_node_model.get('type')

        # Validate essential properties that must exist and be strings for the return dictionary.
        if not node_id or not isinstance(node_id, str):
            raise FigmaOperationError(f"Found node for ID '{node_id_to_find}' is missing a valid 'id' string property.")
        if not node_type or not isinstance(node_type, str):
            raise FigmaOperationError(f"Found node '{node_id}' (ID: {node_id}) is missing a valid 'type' string property.")

        # Find the parent model. The search for parent starts from the document model itself.
        parent_model: Optional[Node] = utils.find_direct_parent_of_node([doc_model], node_id_to_find)

        if not parent_model or not parent_model.get('id') or not isinstance(parent_model.get('id'), str):
            # This case implies the node is orphaned, or it's the document root itself (which shouldn't be selected this way).
            if selected_node_model.get('id') == doc_model.get('id'):
                 raise FigmaOperationError(f"The document root node (ID: {doc_model.get('id')}) was unexpectedly in selection; it has no parent in this context.")
            raise FigmaOperationError(f"Could not find a valid parent with a string ID for selected node '{node_id_to_find}'.")

        parent_id = parent_model.get('id')
        result = {
            'id': node_id,
            'name': node_name,
            'type': node_type,
            'parentId': parent_id,
        }

        result_list.append(SelectedNodeInfo(**result).model_dump())

    return result_list


@tool_spec(
    spec={
        'name': 'scan_nodes_by_types',
        'description': """ Scan for child nodes with specific types in the selected Figma node.
        
        This function scans for child nodes with specific types within the Figma node
        identified by `node_id`. It searches through the descendants of the specified
        container node and returns a list of nodes that match the types provided in
        the `types` list. Each found node is represented as a dictionary containing
        its basic information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The ID of the Figma node to be scanned for descendant nodes.'
                },
                'types': {
                    'type': 'array',
                    'description': """ A list of node type strings (e.g., 'RECTANGLE', 'TEXT')
                    to filter the search. Only nodes of these types will be returned. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'node_id',
                'types'
            ]
        }
    }
)
def scan_nodes_by_types(node_id: str, types: List[str]) -> List[Dict[str, Any]]:
    """Scan for child nodes with specific types in the selected Figma node.

    This function scans for child nodes with specific types within the Figma node
    identified by `node_id`. It searches through the descendants of the specified
    container node and returns a list of nodes that match the types provided in
    the `types` list. Each found node is represented as a dictionary containing
    its basic information.

    Args:
        node_id (str): The ID of the Figma node to be scanned for descendant nodes.
        types (List[str]): A list of node type strings (e.g., 'RECTANGLE', 'TEXT')
            to filter the search. Only nodes of these types will be returned.

    Returns:
        List[Dict[str, Any]]: A list of nodes matching the specified types found
            within the given container node (and its descendants). Each dictionary
            in the list represents a found node and provides basic information
            with the following keys:
            'id' (str): The unique identifier of the found node.
            'name' (str): The name of the found node.
            'type' (str): The type of the found node (this will be one of the types
                          specified in the input 'types' list).
            'parentId' (str): The ID of the immediate parent of this node.

    Raises:
        NodeNotFoundError: If the node with the given node_id (the container to scan)
            does not exist.
        NodeTypeError: If the specified node cannot contain child nodes.
        InvalidInputError: If the 'types' list is empty or contains unrecognized
            node type strings.
        PluginError: If there is an issue scanning for nodes by type within Figma.
        ValidationError: If input arguments fail validation.
    """
    # --- Input Validation ---
    if not isinstance(node_id, str):
        raise ValidationError("Argument 'node_id' must be a string.")
    if not node_id: # Check for empty string
        raise ValidationError("Argument 'node_id' cannot be empty.")

    if not isinstance(types, list):
        raise ValidationError("Argument 'types' must be a list.")
    if not types:  # Check for empty list
        raise InvalidInputError("Argument 'types' list cannot be empty.")

    types_set: Set[str] = set()
    for item_type in types:
        if not isinstance(item_type, str):
            raise ValidationError("All elements in 'types' list must be strings.")
        if not item_type: # Check for empty string element
            raise ValidationError("Elements in 'types' list cannot be empty strings.")
        if item_type not in _KNOWN_FIGMA_TYPES:
            # Provide a more helpful error message for unrecognized types.
            example_known_types = ", ".join(list(_KNOWN_FIGMA_TYPES)[:3]) + ", etc."
            raise InvalidInputError(
                f"Unrecognized node type '{item_type}' in 'types' list. "
                f"Known types include: {example_known_types}"
            )
        types_set.add(item_type)


    # 2. --- DB Access and Find Starting Node Object ---
    if not isinstance(DB, dict): 
        raise PluginError("Internal error: DB object is not a dictionary.")

    start_node_obj = utils.get_node_from_db(DB, node_id)

    if start_node_obj is None:
        raise NodeNotFoundError(
            f"Node with ID '{node_id}' not found in any file in the DB."
        )

    # 3. --- Validate Starting Node (remains the same) ---
    # ... (validation code using _CONTAINER_NODE_TYPES) ...
    start_node_type = start_node_obj.get('type')
    if start_node_type is None:
        raise PluginError(f"Starting node '{node_id}' is missing 'type' attribute.")
    
    if start_node_type not in _CONTAINER_NODE_TYPES: 
        example_containers = ", ".join(list(_CONTAINER_NODE_TYPES)[:3]) + ", etc."
        raise NodeTypeError(
            f"Node '{node_id}' (type: '{start_node_type}') cannot contain child nodes. "
            f"Scanning requires a container type like {example_containers}."
        )

    # 4. --- Perform Recursive Scan (uses _scan_descendants_recursively) ---
    found_nodes_list: List[Dict[str, Any]] = []
    try:
        # _scan_descendants_recursively should be defined in this file or imported
        utils._scan_descendants_recursively(
            start_node_obj,
            types_set,
            found_nodes_list
        )
    except PluginError:
        raise
    except ValidationError as ve: # If using Pydantic FoundNodeInfo
        raise PluginError(f"Data validation error for a found node: {ve}")
    except RecursionError:
        raise PluginError("An unexpected error occurred during node scanning: maximum recursion depth exceeded while calling a Python object")
    except Exception as e:
        raise PluginError(f"An unexpected error occurred during node scanning: {str(e)}")
        
    return found_nodes_list