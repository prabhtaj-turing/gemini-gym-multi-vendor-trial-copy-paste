from common_utils.tool_spec_decorator import tool_spec
# figma/node_creation.py

import uuid
from typing import Optional, Dict, Any, Tuple, List, Union
import copy
from .SimulationEngine.db import DB
from .SimulationEngine import utils 
from .SimulationEngine import models
from .SimulationEngine import custom_errors
from .SimulationEngine.custom_errors import NodeNotFoundError, CloneError, FigmaOperationError
from pydantic import ValidationError
from .SimulationEngine.models import CreateTextArgs

@tool_spec(
    spec={
        'name': 'create_rectangle',
        'description': """ Create a new rectangle in Figma.
        
        Creates a new rectangle in Figma. The position is defined by the x and y
        coordinates of its top-left corner on the canvas. The dimensions are
        specified by its width and height, which must be positive values.
        An optional name can be assigned to the new rectangle layer. The rectangle
        can be parented to an existing node using `parent_id`; if not provided or empty,
        it is added to the current page. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'x': {
                    'type': 'number',
                    'description': 'The x-coordinate of the top-left corner of the rectangle on the canvas.'
                },
                'y': {
                    'type': 'number',
                    'description': 'The y-coordinate of the top-left corner of the rectangle on the canvas.'
                },
                'width': {
                    'type': 'number',
                    'description': 'The width of the rectangle. Must be a positive value.'
                },
                'height': {
                    'type': 'number',
                    'description': 'The height of the rectangle. Must be a positive value.'
                },
                'name': {
                    'type': 'string',
                    'description': """ An optional name for the new rectangle layer. If not
                    provided, it defaults to "Rectangle". """
                },
                'parent_id': {
                    'type': 'string',
                    'description': """ The optional ID of an existing node to parent the
                    new rectangle to. Defaults to None. If not provided or empty, the rectangle is added to the current page. """
                }
            },
            'required': [
                'x',
                'y',
                'width',
                'height'
            ]
        }
    }
)
def create_rectangle(x: float, y: float, width: float, height: float,
                     name: Optional[str] = None,
                     parent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new rectangle in Figma.

    Creates a new rectangle in Figma. The position is defined by the x and y
    coordinates of its top-left corner on the canvas. The dimensions are
    specified by its width and height, which must be positive values.
    An optional name can be assigned to the new rectangle layer. The rectangle
    can be parented to an existing node using `parent_id`; if not provided or empty,
    it is added to the current page.

    Args:
        x (float): The x-coordinate of the top-left corner of the rectangle on the canvas.
        y (float): The y-coordinate of the top-left corner of the rectangle on the canvas.
        width (float): The width of the rectangle. Must be a positive value.
        height (float): The height of the rectangle. Must be a positive value.
        name (Optional[str]): An optional name for the new rectangle layer. If not
            provided, it defaults to "Rectangle".
        parent_id (Optional[str]): The optional ID of an existing node to parent the
            new rectangle to. Defaults to None. If not provided or empty, the rectangle is added to the current page.

    Returns:
        Dict[str, Any]: Information about the newly created rectangle node. Contains the following keys:
            id (str): The unique identifier of the new rectangle node.
            name (str): The name assigned to the rectangle.
            type (str): The type of the node, which will be 'RECTANGLE'.
            parentId (Optional[str]): The ID of the parent node. This will be the `parent_id`
                input if provided, otherwise it's the ID of the current page where the
                rectangle was created.
            x (float): The x-coordinate of the rectangle's top-left corner on the canvas.
            y (float): The y-coordinate of the rectangle's top-left corner on the canvas.
            width (float): The width of the rectangle.
            height (float): The height of the rectangle.

    Raises:
        ParentNotFoundError: If the specified `parent_id` does not correspond to a valid,
            existing container node in Figma, or if its type is not allowed as a parent.
        InvalidInputError: If required parameters such as `width` or `height` are
            missing, or if they are invalid (e.g., negative or zero values, non-numeric types).
        FigmaOperationError: If an internal error occurs within Figma or the plugin
            while attempting to create the rectangle.
    """

    # 1. Input Validation
    if not all(isinstance(arg, (int, float)) for arg in [x, y, width, height]):
        raise custom_errors.InvalidInputError("Input coordinates (x, y) and dimensions (width, height) must be valid numbers.")
    
    if not (width > 0 and height > 0):
        raise custom_errors.InvalidInputError("Rectangle width and height must be positive values.")

    if name is not None and not isinstance(name, str):
        raise custom_errors.InvalidInputError("Name must be a string if provided.")

    if parent_id is not None and not isinstance(parent_id, str):
        raise custom_errors.InvalidInputError("Parent ID must be a string if provided.")

    # 2. Determine Parent Node
    parent_node_for_modification: Optional[Dict[str, Any]] = None
    actual_parent_id_for_response: Optional[str] = None
    
    if parent_id is not None and parent_id.strip(): 
        # The following block has been removed as per user request:
        # if not isinstance(parent_id, str): 
        #     raise custom_errors.InvalidInputError("Parent ID must be a string.")
        
        stripped_parent_id = parent_id.strip() # Assuming parent_id is a string due to type hint

        parent_node_for_modification = utils.find_node_dict_in_DB(DB, stripped_parent_id)
        
        if not parent_node_for_modification:
            raise custom_errors.ParentNotFoundError(f"Parent node with ID '{stripped_parent_id}' not found.")

        parent_type_str = parent_node_for_modification.get('type')
        try:
            models.ValidParentNodeType(parent_type_str) 
        except ValueError:
            valid_types_list_str = [e.value for e in models.ValidParentNodeType]
            raise custom_errors.ParentNotFoundError(
                f"Node with ID '{stripped_parent_id}' and type '{parent_type_str}' cannot be a parent. Valid parent types are: {valid_types_list_str}."
            )
        actual_parent_id_for_response = stripped_parent_id
    else:
        try:
            current_file = utils.get_current_file()
            if not isinstance(current_file, dict):
                raise ValueError("First file entry in DB is not a dictionary.")
            document_node = current_file.get('document')
            if not isinstance(document_node, dict):
                raise ValueError("Document node in first file is not a dictionary or is missing.")
            canvases_list = document_node.get('children')
            if not isinstance(canvases_list, list) or not canvases_list:
                raise ValueError("Document node has no children (canvases).")
            default_parent_canvas = utils.find_node_by_id(canvases_list, document_node.get('currentPageId'))
            if not isinstance(default_parent_canvas, dict):
                raise ValueError("First canvas in document is not a dictionary.")
            parent_node_for_modification = default_parent_canvas
            actual_parent_id_for_response = default_parent_canvas.get('id')
            if not actual_parent_id_for_response: 
                raise ValueError("Default parent canvas is missing an 'id' attribute.")
            default_parent_type_str = default_parent_canvas.get('type')
            try:
                models.ValidParentNodeType(default_parent_type_str)
            except ValueError:
                valid_types_list_str = [e.value for e in models.ValidParentNodeType]
                raise ValueError(f"Default parent (canvas) is of an unexpected type '{default_parent_type_str}'. Expected one of {valid_types_list_str}.")
        except Exception as e: 
            raise custom_errors.FigmaOperationError(
                f"Cannot create rectangle: Default parent (first canvas of first file) not found or is invalid. Details: {str(e)}"
            )
    
    # 3. Generate New Node ID
    new_node_id = uuid.uuid4().hex 

    # 4. Create Rectangle Node Data using Pydantic Model
    rect_name = name if name is not None else "Rectangle"
    
    default_fill_item = models.FillItem(
        type="SOLID",
        visible=True,
        opacity=1.0,
        blendMode="NORMAL",
        color=models.Color(r=0.75, g=0.75, b=0.75, a=1.0)
    )
    fills_data = [default_fill_item] 
    rectangle_fills = models.Fill(root=fills_data)

    rectangle_node = models.Node(
        id=new_node_id,
        name=rect_name,
        type="RECTANGLE", 
        visible=True,
        locked=False,
        opacity=1.0,
        blendMode="PASS_THROUGH", 
        isMask=False,
        rotation=0.0,
        absoluteBoundingBox=models.AbsoluteBoundingBox(x=x, y=y, width=width, height=height),
        fills=rectangle_fills, 
        strokes=[], 
        strokeWeight=1.0, 
        strokeAlign="INSIDE", 
        cornerRadius=0.0, 
        rectangleCornerRadii=[0.0, 0.0, 0.0, 0.0],
        children=[] 
    )
    new_rectangle_node_dict = rectangle_node.model_dump(exclude_none=True, by_alias=True)

    # 5. Add Node to DB's parent_node_for_modification
    if 'children' not in parent_node_for_modification or not isinstance(parent_node_for_modification.get('children'), list):
        parent_node_for_modification['children'] = []
    parent_node_for_modification['children'].append(new_rectangle_node_dict)

    # 6. Construct Return Value using CreateRectangleResponse Pydantic Model
    response_model = models.CreateRectangleResponse(
        id=new_node_id,
        name=rect_name,
        type="RECTANGLE", 
        parentId=actual_parent_id_for_response,
        x=x, 
        y=y, 
        width=width,
        height=height
    )
    return response_model.model_dump(exclude_none=True)

# Constants for string enum validation, prefixed with underscore to indicate "private" to this module/file
_VALID_LAYOUT_MODES = {"NONE", "HORIZONTAL", "VERTICAL"}
_VALID_LAYOUT_WRAPS = {"NO_WRAP", "WRAP"}
_VALID_PRIMARY_AXIS_ALIGN_ITEMS = {"MIN", "MAX", "CENTER", "SPACE_BETWEEN"}
_VALID_COUNTER_AXIS_ALIGN_ITEMS = {"MIN", "MAX", "CENTER", "BASELINE"}
_VALID_LAYOUT_SIZING = {"FIXED", "HUG", "FILL"}

@tool_spec(
    spec={
        'name': 'clone_node',
        'description': """ Clone an existing node (represented as a dict) in Figma.
        
        This function clones an existing node. It takes the `node_id`
        of the node to be cloned and optionally new `x` and `y` coordinates
        for the clone's position. It returns basic information about the newly
        created cloned node. All node and document structures are assumed to be dictionaries. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The identifier of the node to be cloned. Must be a non-empty string.'
                },
                'x': {
                    'type': 'number',
                    'description': """ The optional x-coordinate for the cloned node's position.
                    If not provided, the clone inherits the x-coordinate of the original node.
                    If provided, must be a valid number within reasonable bounds (-10000 to 10000). """
                },
                'y': {
                    'type': 'number',
                    'description': """ The optional y-coordinate for the cloned node's position.
                    If not provided, the clone inherits the y-coordinate of the original node.
                    If provided, must be a valid number within reasonable bounds (-10000 to 10000). """
                }
            },
            'required': [
                'node_id'
            ]
        }
    }
)
def clone_node(node_id: str, x: Optional[float] = None, y: Optional[float] = None) -> Dict[str, Any]:
    """Clone an existing node (represented as a dict) in Figma.

    This function clones an existing node. It takes the `node_id`
    of the node to be cloned and optionally new `x` and `y` coordinates
    for the clone's position. It returns basic information about the newly
    created cloned node. All node and document structures are assumed to be dictionaries.

    Args:
        node_id (str): The identifier of the node to be cloned. Must be a non-empty string.
        x (Optional[float]): The optional x-coordinate for the cloned node's position.
            If not provided, the clone inherits the x-coordinate of the original node.
            If provided, must be a valid number within reasonable bounds (-10000 to 10000).
        y (Optional[float]): The optional y-coordinate for the cloned node's position.
            If not provided, the clone inherits the y-coordinate of the original node.
            If provided, must be a valid number within reasonable bounds (-10000 to 10000).

    Returns:
        Dict[str, Any]: Basic information about the newly cloned node. This dictionary
            includes the following keys:
            id (str): The unique identifier of the cloned node.
            name (str): The name of the cloned node.
            type (str): The type of the cloned node.
            parentId (str): The ID of the parent node where the clone is placed.
            x (float): The x-coordinate of the cloned node's top-left corner.
            y (float): The y-coordinate of the cloned node's top-left corner.

    Raises:
        InvalidInputError: If `node_id` is not a valid string, or if `x` or `y` are
            provided with non-numeric types or values outside reasonable bounds.
        NodeNotFoundError: If the node with the given nodeId does not exist.
        CloneError: If the node cannot be cloned (e.g., it's a special type
            like the document root, or is locked in a way that prevents
            cloning).
        FigmaOperationError: If there is an issue executing the clone command in Figma.
    """

    # 1. Input Validation
    if not isinstance(node_id, str) or not node_id.strip():
        raise custom_errors.InvalidInputError("node_id must be a non-empty string.")
    
    if x is not None:
        if not isinstance(x, (int, float)):
            raise custom_errors.InvalidInputError("x coordinate must be a number if provided.")
        if not (-10000 <= x <= 10000):
            raise custom_errors.InvalidInputError("x coordinate must be within reasonable bounds (-10000 to 10000).")

    if y is not None:
        if not isinstance(y, (int, float)):
            raise custom_errors.InvalidInputError("y coordinate must be a number if provided.")
        if not (-10000 <= y <= 10000):
            raise custom_errors.InvalidInputError("y coordinate must be within reasonable bounds (-10000 to 10000).")

    # 2. Find Node and Parent
    found_node_details: Optional[Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]] = None

    if not DB.get('files'):
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found (no files in DB).")

    for figma_file_obj in DB.get('files', []):
        figma_document = figma_file_obj.get('document')
        if not figma_document or not figma_document.get('children'):
            continue

        node_to_clone_candidate = utils.find_node_by_id(figma_document.get('children', []), node_id)

        if node_to_clone_candidate:
            parent_obj_candidate = utils.find_direct_parent_of_node(figma_document.get('children', []), node_id)
            
            actual_parent_obj: Dict[str, Any]

            if parent_obj_candidate:
                actual_parent_obj = parent_obj_candidate
            else:
                is_valid_canvas = False
                if node_to_clone_candidate.get('type') == "CANVAS":
                    for canvas_in_doc in figma_document.get('children', []):
                        if canvas_in_doc.get('id') == node_to_clone_candidate.get('id'):
                            is_valid_canvas = True
                            break
                
                if is_valid_canvas:
                    actual_parent_obj = figma_document 
                else:
                    raise FigmaOperationError(
                        f"Node {node_id} found, but its parent structure is ambiguous or invalid "
                        f"in file {figma_file_obj.get('fileKey')}."
                    )
            
            found_node_details = (node_to_clone_candidate, actual_parent_obj, figma_file_obj)
            break 

    if not found_node_details:
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found.")

    original_node, parent_node_obj, _ = found_node_details

    if original_node.get('type') in ["DOCUMENT", "CANVAS"]:
        raise CloneError(f"Nodes of type '{original_node.get('type')}' cannot be cloned.")

    if not parent_node_obj.get('id'):
        raise FigmaOperationError(f"Parent of node '{node_id}' (ID: {parent_node_obj.get('id', 'N/A')}) does not have a valid ID.")

    try:
        cloned_node = copy.deepcopy(original_node)
    except Exception as e: 
        raise FigmaOperationError(f"Failed to deep copy node '{node_id}': {str(e)}")

    cloned_node['id'] = uuid.uuid4().hex
    original_name = original_node.get('name', "Unnamed") 
    cloned_node['name'] = f"{original_name} copy"

    current_x, current_y = 0.0, 0.0 
    
    original_bbox = original_node.get('absoluteBoundingBox')
    if original_bbox:
        if original_bbox.get('x') is not None:
            current_x = original_bbox['x']
        if original_bbox.get('y') is not None:
            current_y = original_bbox['y']

    final_x = x if x is not None else current_x
    final_y = y if y is not None else current_y

    cloned_bbox = cloned_node.get('absoluteBoundingBox')
    if cloned_bbox is None:
        cloned_node['absoluteBoundingBox'] = {'x': final_x, 'y': final_y}
    else:
        cloned_bbox['x'] = final_x
        cloned_bbox['y'] = final_y
    
    children_list = parent_node_obj.get('children')
    
    if children_list is None:
        children_list = []
        parent_node_obj['children'] = children_list 
    
    if not isinstance(children_list, list):
        raise FigmaOperationError(
            f"Parent node '{parent_node_obj.get('id', 'N/A')}' has a 'children' field that is not a list, but type {type(children_list)}."
        )
    
    children_list.append(cloned_node)

    return {
        "id": cloned_node['id'],
        "name": cloned_node['name'],
        "type": cloned_node.get('type'), 
        "parentId": parent_node_obj.get('id'), 
        "x": final_x, 
        "y": final_y, 
    }

@tool_spec(
    spec={
        'name': 'create_frame',
        'description': """ Create a new frame in Figma.
        
        This function creates a new frame in Figma. It allows specifying the frame's
        position (x, y), dimensions (width, height), name, parent node, fill color,
        stroke properties, and various auto-layout configurations. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'x': {
                    'type': 'number',
                    'description': "The x-coordinate of the frame's top-left corner on the canvas."
                },
                'y': {
                    'type': 'number',
                    'description': "The y-coordinate of the frame's top-left corner on the canvas."
                },
                'width': {
                    'type': 'number',
                    'description': 'The width of the frame. Width should be greater than 0.'
                },
                'height': {
                    'type': 'number',
                    'description': 'The height of the frame. Height should be greater than 0.'
                },
                'name': {
                    'type': 'string',
                    'description': 'Optional name for the new frame. Defaults to None.'
                },
                'parent_id': {
                    'type': 'string',
                    'description': """ Optional ID of the parent node (e.g., another
                    frame, page, component) to create the frame within. If not provided,
                    the frame is created on the current page. Defaults to None. """
                },
                'fill_color': {
                    'type': 'object',
                    'description': """ Optional properties for a single fill. Defaults to None.
                    This should be a dictionary conforming to Figma's Paint object structure.
                    For a solid color, an example structure is,
                    {"type": "SOLID", "color": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0}}.
                    Known keys for a solid color fill: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': "The type of paint, e.g., 'SOLID'."
                        },
                        'color': {
                            'type': 'object',
                            'description': 'A dictionary defining the RGBA color.',
                            'properties': {
                                'r': {
                                    'type': 'number',
                                    'description': 'Red component (0.0 to 1.0).'
                                },
                                'g': {
                                    'type': 'number',
                                    'description': 'Green component (0.0 to 1.0).'
                                },
                                'b': {
                                    'type': 'number',
                                    'description': 'Blue component (0.0 to 1.0).'
                                },
                                'a': {
                                    'type': 'number',
                                    'description': 'Alpha component (0.0 to 1.0).'
                                }
                            },
                            'required': [
                                'r',
                                'g',
                                'b',
                                'a'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'color'
                    ]
                },
                'stroke_color': {
                    'type': 'object',
                    'description': """ Optional properties for a single stroke. Defaults to None.
                    This should be a dictionary conforming to Figma's Paint object structure
                    for the stroke color and type. For a solid color, an example structure is,
                    `{'type': 'SOLID', 'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}}`.
                    Known keys for a solid color stroke: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': "The type of paint, e.g., 'SOLID'."
                        },
                        'color': {
                            'type': 'object',
                            'description': 'A dictionary defining the RGBA color.',
                            'properties': {
                                'r': {
                                    'type': 'number',
                                    'description': 'Red component (0.0 to 1.0).'
                                },
                                'g': {
                                    'type': 'number',
                                    'description': 'Green component (0.0 to 1.0).'
                                },
                                'b': {
                                    'type': 'number',
                                    'description': 'Blue component (0.0 to 1.0).'
                                },
                                'a': {
                                    'type': 'number',
                                    'description': 'Alpha component (0.0 to 1.0).'
                                }
                            },
                            'required': [
                                'r',
                                'g',
                                'b',
                                'a'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'color'
                    ]
                },
                'stroke_weight': {
                    'type': 'number',
                    'description': """ Optional stroke weight (thickness) for the
                    frame. Applied if `stroke_color` is also provided. Defaults to None. """
                },
                'layout_mode': {
                    'type': 'string',
                    'description': """ Enables auto-layout and sets its direction. Defaults to None.
                    Valid values: "NONE", "HORIZONTAL", "VERTICAL". If not provided, NONE is used. """
                },
                'layout_wrap': {
                    'type': 'string',
                    'description': """ Specifies wrap behavior for auto-layout when
                    `layout_mode` is HORIZONTAL or VERTICAL. Valid values: "NO_WRAP", "WRAP".
                    Requires `layout_mode` to be set. Defaults to None. """
                },
                'padding_top': {
                    'type': 'number',
                    'description': """ Top padding for an auto-layout frame.
                    Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None. """
                },
                'padding_right': {
                    'type': 'number',
                    'description': """ Right padding for an auto-layout frame.
                    Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None. """
                },
                'padding_bottom': {
                    'type': 'number',
                    'description': """ Bottom padding for an auto-layout frame.
                    Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None. """
                },
                'padding_left': {
                    'type': 'number',
                    'description': """ Left padding for an auto-layout frame.
                    Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None. """
                },
                'primary_axis_align_items': {
                    'type': 'string',
                    'description': """ Alignment of items along the
                    primary axis (horizontal for `layout_mode` HORIZONTAL, vertical for
                    VERTICAL). Valid values: "MIN", "MAX", "CENTER", "SPACE_BETWEEN".
                    Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None. """
                },
                'counter_axis_align_items': {
                    'type': 'string',
                    'description': """ Alignment of items along the
                    counter axis (vertical for `layout_mode` HORIZONTAL, horizontal for
                    VERTICAL). Valid values: "MIN", "MAX", "CENTER", "BASELINE" (for text).
                    Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None. """
                },
                'layout_sizing_horizontal': {
                    'type': 'string',
                    'description': """ Optional horizontal resizing
                    behavior for the frame when it is a child of an auto-layout parent.
                    Valid values: "FIXED" (default), "HUG", "FILL". """
                },
                'layout_sizing_vertical': {
                    'type': 'string',
                    'description': """ Optional vertical resizing
                    behavior for the frame when it is a child of an auto-layout parent.
                    Valid values: "FIXED" (default), "HUG", "FILL". Defaults to None. """
                },
                'item_spacing': {
                    'type': 'number',
                    'description': """ Optional spacing between items in an
                    auto-layout frame. Requires `layout_mode` to be HORIZONTAL or VERTICAL. Defaults to None. """
                }
            },
            'required': [
                'x',
                'y',
                'width',
                'height'
            ]
        }
    }
)
def create_frame(
    x: float,
    y: float,
    width: float,
    height: float,
    name: Optional[str] = None,
    parent_id: Optional[str] = None,
    fill_color: Optional[Dict[str, Union[str, Dict[str, float]]]] = None,
    stroke_color: Optional[Dict[str, Union[str, Dict[str, float]]]] = None,
    stroke_weight: Optional[float] = None,
    layout_mode: Optional[str] = None,
    layout_wrap: Optional[str] = None,
    padding_top: Optional[float] = None,
    padding_right: Optional[float] = None,
    padding_bottom: Optional[float] = None,
    padding_left: Optional[float] = None,
    primary_axis_align_items: Optional[str] = None,
    counter_axis_align_items: Optional[str] = None,
    layout_sizing_horizontal: Optional[str] = None,
    layout_sizing_vertical: Optional[str] = None,
    item_spacing: Optional[float] = None
) -> Dict[str, Any]:
    """Create a new frame in Figma.

    This function creates a new frame in Figma. It allows specifying the frame's
    position (x, y), dimensions (width, height), name, parent node, fill color,
    stroke properties, and various auto-layout configurations.

    Args:
        x (float): The x-coordinate of the frame's top-left corner on the canvas.
        y (float): The y-coordinate of the frame's top-left corner on the canvas.
        width (float): The width of the frame. Width should be greater than 0.
        height (float): The height of the frame. Height should be greater than 0.
        name (Optional[str]): Optional name for the new frame. Defaults to None.
        parent_id (Optional[str]): Optional ID of the parent node (e.g., another
            frame, page, component) to create the frame within. If not provided,
            the frame is created on the current page. Defaults to None.
        fill_color (Optional[Dict[str, Union[str, Dict[str, float]]]]): Optional properties for a single fill. Defaults to None.
            This should be a dictionary conforming to Figma's Paint object structure.
            For a solid color, an example structure is,
            {"type": "SOLID", "color": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0}}.
            Known keys for a solid color fill:
                - type (str): The type of paint, e.g., 'SOLID'.
                - color (Dict[str, float]): A dictionary defining the RGBA color.
                    - r (float): Red component (0.0 to 1.0).
                    - g (float): Green component (0.0 to 1.0).
                    - b (float): Blue component (0.0 to 1.0).
                    - a (float): Alpha component (0.0 to 1.0).
        stroke_color (Optional[Dict[str, Union[str, Dict[str, float]]]]): Optional properties for a single stroke. Defaults to None.
            This should be a dictionary conforming to Figma's Paint object structure
            for the stroke color and type. For a solid color, an example structure is,
            `{'type': 'SOLID', 'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}}`.
            Known keys for a solid color stroke:
                - type (str): The type of paint, e.g., 'SOLID'.
                - color (Dict[str, float]): A dictionary defining the RGBA color.
                    - r (float): Red component (0.0 to 1.0).
                    - g (float): Green component (0.0 to 1.0).
                    - b (float): Blue component (0.0 to 1.0).
                    - a (float): Alpha component (0.0 to 1.0).
        stroke_weight (Optional[float]): Optional stroke weight (thickness) for the
            frame. Applied if `stroke_color` is also provided. Defaults to None.
        layout_mode (Optional[str]): Enables auto-layout and sets its direction. Defaults to None.
            Valid values: "NONE", "HORIZONTAL", "VERTICAL". If not provided, NONE is used.
        layout_wrap (Optional[str]): Specifies wrap behavior for auto-layout when
            `layout_mode` is HORIZONTAL or VERTICAL. Valid values: "NO_WRAP", "WRAP".
            Requires `layout_mode` to be set. Defaults to None.
        padding_top (Optional[float]): Top padding for an auto-layout frame.
            Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None.
        padding_right (Optional[float]): Right padding for an auto-layout frame.
            Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None.
        padding_bottom (Optional[float]): Bottom padding for an auto-layout frame.
            Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None.
        padding_left (Optional[float]): Left padding for an auto-layout frame.
            Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None.
        primary_axis_align_items (Optional[str]): Alignment of items along the
            primary axis (horizontal for `layout_mode` HORIZONTAL, vertical for
            VERTICAL). Valid values: "MIN", "MAX", "CENTER", "SPACE_BETWEEN".
            Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None.
        counter_axis_align_items (Optional[str]): Alignment of items along the
            counter axis (vertical for `layout_mode` HORIZONTAL, horizontal for
            VERTICAL). Valid values: "MIN", "MAX", "CENTER", "BASELINE" (for text).
            Requires `layout_mode` to be set to HORIZONTAL or VERTICAL. Defaults to None.
        layout_sizing_horizontal (Optional[str]): Optional horizontal resizing
            behavior for the frame when it is a child of an auto-layout parent.
            Valid values: "FIXED" (default), "HUG", "FILL".
        layout_sizing_vertical (Optional[str]): Optional vertical resizing
            behavior for the frame when it is a child of an auto-layout parent.
            Valid values: "FIXED" (default), "HUG", "FILL". Defaults to None.
        item_spacing (Optional[float]): Optional spacing between items in an
            auto-layout frame. Requires `layout_mode` to be HORIZONTAL or VERTICAL. Defaults to None.

    Returns:
        Dict[str, Any]: Details of the newly created frame node. Common properties include:
            - id (str): Unique identifier of the frame node.
            - name (str): Name of the frame.
            - type (str): Node type, always "FRAME".
            - parent_id (Optional[str]): ID of the parent node. If not specified
                during creation, this will be the ID of the current page.
            - x (float): X-coordinate of the frame on the canvas.
            - y (float): Y-coordinate of the frame on the canvas.
            - width (float): Width of the frame.
            - height (float): Height of the frame.
            - fills (List[Dict[str, Any]]): List of paints applied to the frame's fill.
                Each dictionary in the list represents a paint layer. For a SOLID
                fill, a dictionary typically includes:
                - type (str): Paint type (e.g., 'SOLID').
                - color (Dict[str, float]): RGBA color (e.g.,
                    {'r':0.0-1.0, 'g':0.0-1.0, 'b':0.0-1.0, 'a':0.0-1.0}).
                    - r (float): Red component (0.0-1.0).
                    - g (float): Green component (0.0-1.0).
                    - b (float): Blue component (0.0-1.0).
                    - a (float): Alpha component (0.0-1.0).
                - opacity (Optional[float]): Opacity of the fill (0.0-1.0).
                - visible (Optional[bool]): Visibility of the fill.
            - strokes (List[Dict[str, Any]]): List of paints applied to the frame's
                stroke. Each dictionary in the list represents a paint layer.
                For a SOLID stroke, a dictionary typically includes:
                - type (str): Paint type (e.g., 'SOLID').
                - color (Dict[str, float]): RGBA color (e.g.,
                    {'r':0.0-1.0, 'g':0.0-1.0, 'b':0.0-1.0, 'a':0.0-1.0}).
                    - r (float): Red component (0.0-1.0).
                    - g (float): Green component (0.0-1.0).
                    - b (float): Blue component (0.0-1.0).
                    - a (float): Alpha component (0.0-1.0).
                - opacity (Optional[float]): Opacity of the stroke (0.0-1.0).
                - visible (Optional[bool]): Visibility of the stroke.
            - stroke_weight (Optional[float]): Thickness of the stroke.
            - stroke_align (Optional[str]): Alignment of the stroke (e.g., 'INSIDE',
                'OUTSIDE', 'CENTER').
            - layout_mode (Optional[str]): Auto layout mode ('NONE', 'HORIZONTAL',
                'VERTICAL').
            - padding_left (Optional[float]): Left padding if auto-layout is enabled.
            - padding_right (Optional[float]): Right padding if auto-layout is enabled.
            - padding_top (Optional[float]): Top padding if auto-layout is enabled.
            - padding_bottom (Optional[float]): Bottom padding if auto-layout is enabled.
            - item_spacing (Optional[float]): Spacing between items if auto-layout is
                enabled and `layout_mode` is HORIZONTAL or VERTICAL.
            - primary_axis_align_items (Optional[str]): Primary axis alignment if
                auto-layout is enabled (e.g., 'MIN', 'MAX', 'CENTER', 'SPACE_BETWEEN').
            - counter_axis_align_items (Optional[str]): Counter axis alignment if
                auto-layout is enabled (e.g., 'MIN', 'MAX', 'CENTER').
            - layout_sizing_horizontal (Optional[str]): Horizontal resizing behavior
                of the frame when it is a child of an auto-layout parent
                (e.g., 'FIXED', 'HUG', 'FILL').
            - layout_sizing_vertical (Optional[str]): Vertical resizing behavior
                of the frame when it is a child of an auto-layout parent
                (e.g., 'FIXED', 'HUG', 'FILL').

    Raises:
        ParentNotFoundError: If the specified `parent_id` does not correspond to a
            valid container node.
        InvalidInputError: If required parameters are invalid or conflicting layout
            properties are provided.
        FigmaOperationError: If there is an issue executing the creation command
            in Figma.
        ValidationError: If input arguments fail validation.
    """

    try:
        validated_args = models.CreateFrameArgs(
            x=x, y=y, width=width, height=height, name=name, parent_id=parent_id,
            fill_color=fill_color, stroke_color=stroke_color, stroke_weight=stroke_weight,
            layout_mode=layout_mode, layout_wrap=layout_wrap,
            padding_top=padding_top, padding_right=padding_right, padding_bottom=padding_bottom, padding_left=padding_left,
            primary_axis_align_items=primary_axis_align_items, counter_axis_align_items=counter_axis_align_items,
            layout_sizing_horizontal=layout_sizing_horizontal, layout_sizing_vertical=layout_sizing_vertical,
            item_spacing=item_spacing
        )
    except ValidationError as e:
        # Convert Pydantic's validation error to the function's expected error types.
        first_error = e.errors()[0]
        error_msg = first_error['msg']
        
        # Check if the error is from our custom cross-field validation.
        if first_error.get('type') == 'value_error':
            # This indicates a logical conflict, like using padding without auto-layout.
            raise custom_errors.InvalidInputError(error_msg) from e
        
        # Otherwise, it's a standard data validation error (e.g., wrong type, value out of range).
        raise custom_errors.ValidationError(f"Input validation failed: {error_msg}") from e

    # Process fills
    processed_fills: List[Dict[str, Any]] = []
    if validated_args.fill_color:
        try:
            processed_paint = utils._validate_and_process_paint_dict(validated_args.fill_color, "fill_color")
            processed_fills.append(processed_paint)
        except custom_errors.InvalidInputError as e:
            raise custom_errors.ValidationError(str(e))
        except Exception:
            raise custom_errors.ValidationError("Input validation failed for fill_color")

    # Process strokes and stroke_weight
    processed_strokes: List[Dict[str, Any]] = []
    actual_stroke_weight: float = 0.0
    if validated_args.stroke_color:
        try:
            processed_paint = utils._validate_and_process_paint_dict(validated_args.stroke_color, "stroke_color")
            processed_strokes.append(processed_paint)
        except custom_errors.InvalidInputError as e:
            raise custom_errors.ValidationError(str(e))
        except Exception as e:
            raise custom_errors.ValidationError("Input validation failed")

        actual_stroke_weight = stroke_weight if stroke_weight is not None else 1.0 # Default stroke weight is 1.0
        if not isinstance(actual_stroke_weight, (int, float)) or actual_stroke_weight < 0:
            raise custom_errors.ValidationError("stroke_weight must be non-negative")
    # If stroke_color is not provided, stroke_weight is ignored and remains 0.0

    # Determine effective layout_mode and validate
    effective_layout_mode = layout_mode if layout_mode is not None else "NONE"
    if effective_layout_mode not in _VALID_LAYOUT_MODES:
        raise custom_errors.ValidationError("Invalid value for layout_mode")

    # Validate auto-layout properties based on effective_layout_mode
    auto_layout_related_args = {
        "layout_wrap": (layout_wrap, _VALID_LAYOUT_WRAPS, "NO_WRAP"),
        "primary_axis_align_items": (primary_axis_align_items, _VALID_PRIMARY_AXIS_ALIGN_ITEMS, "MIN"),
        "counter_axis_align_items": (counter_axis_align_items, _VALID_COUNTER_AXIS_ALIGN_ITEMS, "MIN"),
    }
    padding_args = {
        "padding_top": padding_top, "padding_right": padding_right,
        "padding_bottom": padding_bottom, "padding_left": padding_left,
    }

    if effective_layout_mode == "NONE":
        for arg_name, (val, _, _) in auto_layout_related_args.items():
            if val is not None:
                if arg_name in ["primary_axis_align_items", "counter_axis_align_items"]:
                    raise custom_errors.InvalidInputError("Axis alignment properties require layout_mode to be HORIZONTAL or VERTICAL.")
                else:
                    raise custom_errors.InvalidInputError(f"{arg_name} requires layout_mode to be HORIZONTAL or VERTICAL.")
        for arg_name, val in padding_args.items():
            if val is not None:
                raise custom_errors.InvalidInputError("Padding properties require layout_mode to be HORIZONTAL or VERTICAL.")
            if item_spacing is not None:
                raise custom_errors.InvalidInputError("item_spacing requires layout_mode to be HORIZONTAL or VERTICAL.")
    else: # HORIZONTAL or VERTICAL layout mode
        for arg_name, (val, valid_values, _) in auto_layout_related_args.items():
            if val is not None and val not in valid_values:
                raise custom_errors.ValidationError(f"Invalid value for {arg_name}")
        for arg_name, val in padding_args.items():
            if val is not None:
                if not isinstance(val, (int, float)):
                    raise custom_errors.ValidationError(f"{arg_name} must be non-negative")
                if val < 0:
                    raise custom_errors.ValidationError(f"{arg_name} must be non-negative")
        if item_spacing is not None:
            if not isinstance(item_spacing, (int, float)):
                raise custom_errors.ValidationError("item_spacing must be non-negative")
            if item_spacing < 0:
                raise custom_errors.ValidationError("item_spacing must be non-negative")
    
    # Validate layout sizing properties
    if layout_sizing_horizontal is not None and layout_sizing_horizontal not in _VALID_LAYOUT_SIZING:
        raise custom_errors.ValidationError("Invalid value for layout_sizing_horizontal")
    if layout_sizing_vertical is not None and layout_sizing_vertical not in _VALID_LAYOUT_SIZING:
        raise custom_errors.ValidationError("Invalid value for layout_sizing_vertical")

    current_file = utils.get_current_file()
    if not current_file:
        raise custom_errors.FigmaOperationError("Current file not found.")

    document_info = current_file.get('document')
    if not document_info:
        raise custom_errors.FigmaOperationError("Current file is missing a 'document' object.")

    # Determine the target parent ID
    target_parent_id: str
    if validated_args.parent_id:
        target_parent_id = validated_args.parent_id
    else:
        current_page_id = document_info.get('currentPageId')
        if not current_page_id:
            raise custom_errors.FigmaOperationError("Current page ID not found; cannot determine default parent.")
        target_parent_id = current_page_id

    # Find the parent node object ONCE using a helper.
    def find_node_in_tree(nodes_list: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
        for node in nodes_list:
            if node.get('id') == node_id:
                return node
            if 'children' in node:
                found = find_node_in_tree(node.get('children', []), node_id)
                if found:
                    return found
        return None

    parent_node = find_node_in_tree(document_info.get('children', []), target_parent_id)

    if not parent_node or parent_node.get('type') not in ['FRAME', 'COMPONENT', 'CANVAS', 'GROUP', 'SECTION']:
        raise custom_errors.ParentNotFoundError(f"Parent node with ID '{target_parent_id}' not found or is not a valid container.")

    # --- UNIFIED NAMING LOGIC ---
    final_name: str
    if validated_args.name is None:
        sibling_frames = [child for child in parent_node.get('children', []) if child.get('type') == 'FRAME']
        final_name = f"Frame {len(sibling_frames) + 1}"
    else:
        final_name = validated_args.name

    # --- NODE CONSTRUCTION & STATE MUTATION ---
    new_frame_id = uuid.uuid4().hex
    frame_node: Dict[str, Any] = {
        "id": new_frame_id,
        "type": "FRAME",
        "name": final_name,
        "parent_id": target_parent_id,
        "x": validated_args.x,
        "y": validated_args.y,
        "width": validated_args.width,
        "height": validated_args.height,
        "fills": processed_fills,
        "strokes": processed_strokes,
        "stroke_weight": actual_stroke_weight,
        "stroke_align": "INSIDE",
        "layout_mode": effective_layout_mode,
        "layout_sizing_horizontal": validated_args.layout_sizing_horizontal.value if validated_args.layout_sizing_horizontal else "FIXED",
        "layout_sizing_vertical": validated_args.layout_sizing_vertical.value if validated_args.layout_sizing_vertical else "FIXED",
    }

    if effective_layout_mode != "NONE":
        frame_node.update({
            "layout_wrap": validated_args.layout_wrap.value if validated_args.layout_wrap else "NO_WRAP",
            "padding_top": validated_args.padding_top if validated_args.padding_top is not None else 0.0,
            "padding_right": validated_args.padding_right if validated_args.padding_right is not None else 0.0,
            "padding_bottom": validated_args.padding_bottom if validated_args.padding_bottom is not None else 0.0,
            "padding_left": validated_args.padding_left if validated_args.padding_left is not None else 0.0,
            "primary_axis_align_items": validated_args.primary_axis_align_items.value if validated_args.primary_axis_align_items else "MIN",
            "counter_axis_align_items": validated_args.counter_axis_align_items.value if validated_args.counter_axis_align_items else "MIN",
            "item_spacing": validated_args.item_spacing if validated_args.item_spacing is not None else 0.0,
        })
    else:
        frame_node.update({
            "layout_wrap": "NO_WRAP",
            "padding_top": 0.0, "padding_right": 0.0, "padding_bottom": 0.0, "padding_left": 0.0,
            "primary_axis_align_items": "MIN", "counter_axis_align_items": "MIN",
            "item_spacing": 0.0,
        })

    if 'children' not in parent_node:
        parent_node['children'] = []
    parent_node['children'].append(frame_node)

    # Automatically select the newly created frame
    DB["current_selection_node_ids"] = [frame_node['id']]

    return frame_node

import uuid
from typing import Dict, Any, Optional, List

# Imports for DB, utils, custom_errors as per instructions
from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine import custom_errors
# from .SimulationEngine import models # Not used in this implementation

# Helper function _is_valid_figma_solid_paint_color has been removed.
# Its logic is now integrated into the main create_text function for more specific error messages.

@tool_spec(
    spec={
        'name': 'create_text',
        'description': """ Create a new text element in Figma.
        
        This function creates a new text element on the Figma canvas. It positions
        the text element using the provided `x` and `y` coordinates and sets its
        content using the `text` string. Optional styling attributes such as
        `font_size`, `font_weight`, and `font_color` (as a Figma Paint object)
        can be applied. The created text layer can be assigned an optional `name`
        and can be parented under an existing container node specified by `parent_id`.
        If `parent_id` is not provided, the text node is added to the current page.
        The function returns a dictionary containing information about the newly
        created text node. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'x': {
                    'type': 'number',
                    'description': "The x-coordinate for the text node's position on the canvas."
                },
                'y': {
                    'type': 'number',
                    'description': "The y-coordinate for the text node's position on the canvas."
                },
                'text': {
                    'type': 'string',
                    'description': 'The text content to display. Cannot be empty.'
                },
                'font_size': {
                    'type': 'number',
                    'description': """ The font size of the text in pixels. Must be a
                    positive value if provided. Defaults to None. If not provided, Figma's 
                    standard size is used. Must be a positive value if provided. """
                },
                'font_weight': {
                    'type': 'number',
                    'description': """ The font weight of the text (e.g., 400.0 for
                    regular, 700.0 for bold). Defaults to None. If not provided, Figma's standard
                    weight is used. Must be a positive value if provided. """
                },
                'font_color': {
                    'type': 'object',
                    'description': """ The color of the text, specified as a
                    Figma Paint object. Example: `{'type': 'SOLID', 'color': {'r': 0, 'g': 0, 'b': 0, 'a': 1}}`.
                    Defaults to None. If not provided, Figma's standard color is used.
                    Expected keys: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': "The type of paint. Currently, only 'SOLID' is supported."
                        },
                        'color': {
                            'type': 'object',
                            'description': "A dictionary defining the color's RGBA components.",
                            'properties': {
                                'r': {
                                    'type': 'number',
                                    'description': 'The red color component (0.0-1.0 range).'
                                },
                                'g': {
                                    'type': 'number',
                                    'description': 'The green color component (0.0-1.0 range).'
                                },
                                'b': {
                                    'type': 'number',
                                    'description': 'The blue color component (0.0-1.0 range).'
                                },
                                'a': {
                                    'type': 'number',
                                    'description': 'The alpha (opacity) component (0.0-1.0 range).'
                                }
                            },
                            'required': [
                                'r',
                                'g',
                                'b',
                                'a'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'color'
                    ]
                },
                'name': {
                    'type': 'string',
                    'description': """ An optional name for the created text layer in Figma.
                    Defaults to None. If not provided, the `text` content will be used as the name. """
                },
                'parent_id': {
                    'type': 'string',
                    'description': """ The ID of an existing container node (valid container type accepts:
                    FRAME, GROUP, COMPONENT, INSTANCE, CANVAS) to parent the new text node under. Defaults to None. 
                    If not provided, the text node will be added to the current page. """
                }
            },
            'required': [
                'x',
                'y',
                'text'
            ]
        }
    }
)
def create_text(x: float, 
                y: float, 
                text: str, 
                font_size: Optional[float] = None, 
                font_weight: Optional[float] = None, 
                font_color: Optional[Dict[str, Union[str, Dict[str, float]]]] = None, 
                name: Optional[str] = None, 
                parent_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new text element in Figma.

    This function creates a new text element on the Figma canvas. It positions
    the text element using the provided `x` and `y` coordinates and sets its
    content using the `text` string. Optional styling attributes such as
    `font_size`, `font_weight`, and `font_color` (as a Figma Paint object)
    can be applied. The created text layer can be assigned an optional `name`
    and can be parented under an existing container node specified by `parent_id`.
    If `parent_id` is not provided, the text node is added to the current page.
    The function returns a dictionary containing information about the newly
    created text node.

    Args:
        x (float): The x-coordinate for the text node's position on the canvas.
        y (float): The y-coordinate for the text node's position on the canvas.
        text (str): The text content to display. Cannot be empty.
        font_size (Optional[float]): The font size of the text in pixels. Must be a
            positive value if provided. Defaults to None. If not provided, Figma's 
            standard size is used. Must be a positive value if provided.
        font_weight (Optional[float]): The font weight of the text (e.g., 400.0 for
            regular, 700.0 for bold). Defaults to None. If not provided, Figma's standard
            weight is used. Must be a positive value if provided.
        font_color (Optional[Dict[str, Union[str, Dict[str, float]]]]): The color of the text, specified as a
            Figma Paint object. Example: `{'type': 'SOLID', 'color': {'r': 0, 'g': 0, 'b': 0, 'a': 1}}`.
            Defaults to None. If not provided, Figma's standard color is used.
            Expected keys:
                type (str): The type of paint. Currently, only 'SOLID' is supported.
                color (Dict[str, float]): A dictionary defining the color's RGBA components.
                    r (float): The red color component (0.0-1.0 range).
                    g (float): The green color component (0.0-1.0 range).
                    b (float): The blue color component (0.0-1.0 range).
                    a (float): The alpha (opacity) component (0.0-1.0 range).
        name (Optional[str]): An optional name for the created text layer in Figma.
            Defaults to None. If not provided, the `text` content will be used as the name.
        parent_id (Optional[str]): The ID of an existing container node (valid container type accepts:
          FRAME, GROUP, COMPONENT, INSTANCE, CANVAS) to parent the new text node under. Defaults to None. 
          If not provided, the text node will be added to the current page.

    Returns:
        Dict[str, Any]: Information about the newly created text node. Contains the
            following keys:
            id (str): The unique identifier of the new text node.
            name (str): The name assigned to the text node.
            type (str): The type of the node, which will be 'TEXT'.
            parent_id (Optional[str]): The ID of the parent node if specified,
                otherwise the ID of the current page.
            x (float): The x-coordinate of the text node on the canvas.
            y (float): The y-coordinate of the text node on the canvas.
            characters (str): The text content of the node.
            font_size (float): The font size applied to the text, in pixels.
            fills (List[Dict[str, Any]]): A list of paint objects applied to the
                text, determining its color. Each paint object typically contains:
                type (str): The type of paint. Will be 'SOLID' for text color.
                color (Optional[Dict[str, float]]): For SOLID fills, an object with
                    'r', 'g', 'b' (0-1 range) and 'a' (alpha, 0-1 range)
                    components.
                    r (float): Red component (0.0-1.0 range).
                    g (float): Green component (0.0-1.0 range).
                    b (float): Blue component (0.0-1.0 range).
                    a (float): Alpha component (0.0-1.0 range).

    Raises:
        ParentNotFoundError: If the specified `parent_id` does not correspond to a
            valid container node in Figma.
        ValidationError: If required parameters are invalid (e.g., empty `text`,
            non-positive `font_size`, non-positive `font_weight`, or malformed `font_color` object),
            or if input validation fails.
        FigmaOperationError: If there is an internal issue executing the creation
            command in Figma (e.g., Figma API limits reached, Figma service
            temporarily unavailable).
    """
    try:
        validated_args = CreateTextArgs(
            x=x,
            y=y,
            text=text,
            font_size=font_size,
            font_weight=font_weight,
            font_color=font_color,
            name=name,
            parent_id=parent_id,
        )
        if validated_args.font_color:
            font_color = validated_args.font_color.model_dump(exclude_none=True)
    except ValidationError as e:
        raise e
    
    # --- Determine Parent Node ---
    parent_node_data = None
    resolved_parent_id = None
    valid_container_types = {"FRAME", "GROUP", "COMPONENT", "COMPONENT_SET", "INSTANCE", "CANVAS", "SECTION"}

    if parent_id:
        parent_node_data = utils.get_node_from_db(DB, parent_id)
        
        if not parent_node_data:
            raise custom_errors.ParentNotFoundError(f"Parent node with ID '{parent_id}' not found.")
        
        parent_type = parent_node_data.get('type')
        if parent_type not in valid_container_types:
            raise custom_errors.ParentNotFoundError(
                f"Node with ID '{parent_id}' is not a valid container type (e.g., FRAME, GROUP, COMPONENT, INSTANCE, CANVAS)."
            )
        
        if not isinstance(parent_node_data.get('children'), list):
            parent_node_data['children'] = [] 
        
        resolved_parent_id = parent_id
    else:
        try:
            if not (DB.get('files') and isinstance(DB['files'], list) and DB['files'] and
                    isinstance(DB['files'][0], dict) and isinstance(DB['files'][0].get('document'), dict) and
                    isinstance(DB['files'][0]['document'].get('children'), list) and DB['files'][0]['document']['children'] and
                    isinstance(DB['files'][0]['document']['children'][0], dict)):
                # This specific error message might be too generic if the issue is deeper in the structure
                raise IndexError("DB structure for default page is invalid or incomplete.")

            parent_node_data = DB['files'][0]['document']['children'][0] 
            resolved_parent_id = parent_node_data.get('id')

            if not resolved_parent_id:
                 raise custom_errors.FigmaOperationError("Default page (first canvas) is missing an ID.")

            if parent_node_data.get('type') not in valid_container_types:
                 raise custom_errors.FigmaOperationError(f"Default page is not a valid container type: {parent_node_data.get('type')}.")

            if not isinstance(parent_node_data.get('children'), list):
                 parent_node_data['children'] = []

        except (IndexError, KeyError, TypeError) as e:
            raise custom_errors.FigmaOperationError(
                f"Cannot find or access a default page (canvas). DB structure error: {e}"
            )

    # --- Prepare Node Properties ---
    new_node_id = uuid.uuid4().hex
    
    applied_name = text if name is None else name
    applied_font_size = font_size if font_size is not None else 12.0
    applied_font_weight = font_weight if font_weight is not None else 400.0
    
    if font_color:
        applied_font_color_paint = {
            'type': 'SOLID',
            'color': {
                k: float(v) for k, v in font_color['color'].items()
            }
        }
        if 'visible' in font_color: # Retain 'visible' if specified at the paint level
             applied_font_color_paint['visible'] = font_color['visible']
    else:
        applied_font_color_paint = {
            'type': 'SOLID',
            'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}
        }

    parent_abs_x, parent_abs_y = 0.0, 0.0
    if parent_node_data:
        # For CANVAS type parents, their children's x/y are already relative to the canvas origin (0,0)
        # For other container types, their 'absoluteBoundingBox' gives the global origin.
        # The node's x,y are relative to its parent.
        # The absoluteBoundingBox of the new node is its own x,y offset from parent's absolute x,y.
        if parent_node_data.get('type') != 'CANVAS':
            parent_bbox = parent_node_data.get('absoluteBoundingBox')
            if isinstance(parent_bbox, dict):
                parent_abs_x = parent_bbox.get('x', 0.0)
                parent_abs_y = parent_bbox.get('y', 0.0)
        # If parent is CANVAS, parent_abs_x and parent_abs_y remain 0.0, which is correct.
    
    # Placeholder dimensions, actual text rendering would determine these more accurately.
    placeholder_width = max(10.0, len(text) * (applied_font_size * 0.6) + applied_font_size * 0.5) 
    placeholder_height = applied_font_size * 1.5 

    new_text_node_dict = {
        'id': new_node_id,
        'name': applied_name,
        'type': 'TEXT',
        'visible': True,
        'locked': False,
        'opacity': 1.0,
        'rotation': 0.0,
        'characters': text,
        'style': {
            'fontFamily': "Inter", 
            'fontPostScriptName': None,
            'fontWeight': applied_font_weight,
            'fontSize': applied_font_size,
            'textAlignHorizontal': "LEFT",
            'textAlignVertical': "TOP",
            'letterSpacing': 0.0,
            'lineHeightUnit': "AUTO",
            'textCase': "ORIGINAL",
            'textDecoration': "NONE",
            'textAutoResize': 'WIDTH_AND_HEIGHT', # Common default for text nodes
        },
        'fills': [applied_font_color_paint],
        'strokes': [],
        'strokeWeight': 0.0,
        'strokeAlign': 'INSIDE',
        'effects': [],
        'absoluteBoundingBox': {
            'x': parent_abs_x + x,
            'y': parent_abs_y + y,
            'width': placeholder_width,
            'height': placeholder_height
        },
        'constraints': {'vertical': 'TOP', 'horizontal': 'LEFT'},
        'children': [] # Text nodes typically don't have children
    }

    # --- Add Node to Parent in DB ---
    if parent_node_data and 'children' in parent_node_data and isinstance(parent_node_data['children'], list):
        parent_node_data['children'].append(new_text_node_dict)
    else:
        raise custom_errors.FigmaOperationError(
            f"Failed to add new text node to parent '{resolved_parent_id}'. Parent data is invalid or 'children' list is not accessible."
        )

    # --- Construct and Return Result Dictionary ---
    result_info = {
        'id': new_node_id,
        'name': applied_name,
        'type': 'TEXT',
        'parent_id': resolved_parent_id,
        'x': x,
        'y': y,
        'characters': text,
        'font_size': applied_font_size,
        'fills': [applied_font_color_paint]
    }
    
    # Automatically select the newly created text node
    DB["current_selection_node_ids"] = [new_node_id]
    
    return result_info