from common_utils.tool_spec_decorator import tool_spec
from figma.SimulationEngine import models
from .SimulationEngine.custom_errors import NodeNotFoundError, FigmaOperationError, InvalidInputError, ResizeError, DeleteError, NodeTypeError, InvalidColorError, NodeTypeSupportError
from .SimulationEngine.utils import find_node_and_parent_recursive
from typing import Optional, Dict, Any, List, Set, List
from .SimulationEngine import utils
from figma import DB
from .SimulationEngine.utils import find_node_and_parent_recursive
from .SimulationEngine import custom_errors
from pydantic import ValidationError

@tool_spec(
    spec={
        'name': 'move_node',
        'description': """ Move a node to a new position in Figma.
        
        This function moves a node, identified by node_id, to a new position
        in Figma defined by the x and y coordinates. Upon success, it
        returns a status message. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the node to be moved.'
                },
                'x': {
                    'type': 'number',
                    'description': "The new x-coordinate for the node's position."
                },
                'y': {
                    'type': 'number',
                    'description': "The new y-coordinate for the node's position."
                }
            },
            'required': [
                'node_id',
                'x',
                'y'
            ]
        }
    }
)
def move_node(node_id: str, x: float, y: float) -> str:
    """Move a node to a new position in Figma.

    This function moves a node, identified by node_id, to a new position
    in Figma defined by the x and y coordinates. Upon success, it
    returns a status message.

    Args:
        node_id (str): The unique identifier of the node to be moved.
        x (float): The new x-coordinate for the node's position.
        y (float): The new y-coordinate for the node's position.

    Returns:
        str: A status message indicating the node was successfully moved.

    Raises:
        TypeError: If node_id is not a string, or x or y are not numbers.
        ValueError: If node_id is an empty string.
        NodeNotFoundError: If the node with the given nodeId does not exist.
        FigmaOperationError: If there is an issue moving the node in Figma (e.g., node is locked, part of a restricted group).
    """

    # --- Input Validation Start ---
    if not isinstance(node_id, str):
        raise TypeError("node_id must be a string.")
    if not node_id.strip():
        raise ValueError("node_id cannot be an empty string.")

    if not isinstance(x, (int, float)):
        raise TypeError(f"x coordinate must be a number (int or float), got {type(x)}.")
    if not isinstance(y, (int, float)):
        raise TypeError(f"y coordinate must be a number (int or float), got {type(y)}.")
    # --- Input Validation End ---

    found_node_dict: Optional[Dict[str, Any]] = None
    parent_of_found_node_dict: Optional[Dict[str, Any]] = None

    files_list = DB.get('files')
    if not files_list or not isinstance(files_list, list):
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found (no files in DB or DB is malformed).")

    for file_data in files_list:
        if not isinstance(file_data, dict):
            continue # Skip malformed file entries

        document_node = file_data.get('document')
        if not isinstance(document_node, dict):
            continue # Skip file entries with malformed document

        # Check if the document node itself is the target
        if document_node.get('id') == node_id:
            found_node_dict = document_node
            # Document node's parent is conceptually the file, not another Figma node for layout purposes.
            parent_of_found_node_dict = None 
            break # Found the node, exit file loop

        # Search in the document's children (canvases)
        canvases_list = document_node.get('children')
        if canvases_list and isinstance(canvases_list, list):
            for canvas_node in canvases_list:
                if not isinstance(canvas_node, dict):
                    continue # Skip malformed canvas entries

                # Check if the canvas node itself is the target
                if canvas_node.get('id') == node_id:
                    found_node_dict = canvas_node
                    parent_of_found_node_dict = document_node # Parent of a canvas is the document
                    break # Found, break from canvas loop

                # Search in this canvas's children (frames, text, components, etc.)
                canvas_children = canvas_node.get('children')
                if canvas_children and isinstance(canvas_children, list):
                    # The parent for nodes directly on canvas is the canvas_node itself
                    result = find_node_and_parent_recursive(
                        canvas_children, node_id, parent_node=canvas_node
                    )
                    if result:
                        found_node_dict, parent_of_found_node_dict = result
                        break # Found, break from canvas loop

            if found_node_dict:
                break # Found, break from file loop (outer loop)

    if not found_node_dict:
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found in any file or canvas.")

    # Check if the node is locked
    if found_node_dict.get('locked') is True:
        raise FigmaOperationError(f"Node '{node_id}' (name: '{found_node_dict.get('name', 'Unnamed')}') is locked and cannot be moved.")

    # Check if the node is part of a restricted group (e.g., child of an auto-layout frame)
    if parent_of_found_node_dict:
        parent_layout_mode = parent_of_found_node_dict.get('layoutMode')
        # Auto-layout modes are 'HORIZONTAL', 'VERTICAL'. 'NONE' or absence means not auto-layout.
        if parent_layout_mode and parent_layout_mode != 'NONE': # 'NONE' is a string literal
            parent_name = parent_of_found_node_dict.get('name', parent_of_found_node_dict.get('id', 'Unknown parent'))
            raise FigmaOperationError(
                f"Node '{node_id}' (name: '{found_node_dict.get('name', 'Unnamed')}') is a child of an auto-layout frame "
                f"'{parent_name}' (layoutMode: '{parent_layout_mode}') and cannot be moved directly by setting absolute coordinates."
            )

    # Update the node's absoluteBoundingBox
    # Ensure 'absoluteBoundingBox' key exists and is a dictionary, or create it if missing/None.
    bbox_dict = found_node_dict.get('absoluteBoundingBox')
    if not isinstance(bbox_dict, dict): 
        bbox_dict = {} # Create a new dictionary if it's None or not a dictionary
        found_node_dict['absoluteBoundingBox'] = bbox_dict

    # Set the new x and y coordinates, ensuring they are floats
    bbox_dict['x'] = float(x)
    bbox_dict['y'] = float(y)

    node_name = found_node_dict.get('name', 'Unnamed')
    return f"Node '{node_id}' (name: '{node_name}') was successfully moved to ({x}, {y})."

@tool_spec(
    spec={
        'name': 'resize_node',
        'description': """ Resize a node in Figma.
        
        This function resizes a node, identified by node_id, to a target width and height
        determined by the width and height parameters. Upon successful resize, the function
        returns a dictionary containing the node_id, final_width and final_height of the node
        after the resize operation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma node to be resized.'
                },
                'width': {
                    'type': 'number',
                    'description': 'The target new width for the node in pixels. Must be a non-negative value.'
                },
                'height': {
                    'type': 'number',
                    'description': 'The target new height for the node in pixels. Must be a non-negative value.'
                }
            },
            'required': [
                'node_id',
                'width',
                'height'
            ]
        }
    }
)
def resize_node(node_id: str, width: float, height: float) -> Dict[str, Any]:
    """Resize a node in Figma.

    This function resizes a node, identified by node_id, to a target width and height
    determined by the width and height parameters. Upon successful resize, the function
    returns a dictionary containing the node_id, final_width and final_height of the node
    after the resize operation.

    Args:
        node_id (str): The unique identifier of the Figma node to be resized.
        width (float): The target new width for the node in pixels. Must be a non-negative value.
        height (float): The target new height for the node in pixels. Must be a non-negative value.

    Returns:
        Dict[str, Any]: A dictionary containing details of the node after the resize operation, with the following keys:
            node_id (str): The unique identifier of the resized node.
            final_width (float): The actual width of the node after the resize operation. This might differ from the requested width due to Figma's layout engine constraints (e.g., min/max dimensions, aspect ratio lock, parent constraints).
            final_height (float): The actual height of the node after the resize operation. This might differ from the requested height due to Figma's layout engine constraints.

    Raises:
        NodeNotFoundError: Raised if no node exists with the provided `node_id`.
        ResizeError: Raised if the specified node cannot be resized. Common reasons include the node being locked, being part of an auto-layout frame that dictates its size, or the node type itself not supporting arbitrary resizing.
        InvalidInputError: Raised if the provided `node_id` is an empty string, or either `width` or `height` are invalid (e.g., negative values).
        FigmaOperationError: Raised for any other unhandled errors encountered within the Figma environment or plugin during the resize process.
    """

    # --- Input Validation Start ---
    if not isinstance(node_id, str):
        raise InvalidInputError("node_id must be a string.")
        
    if not node_id.strip():
        raise InvalidInputError("node_id cannot be an empty string.")

    if not isinstance(width, (int, float)):
        raise InvalidInputError("width must be a number (int or float).")
    if not isinstance(height, (int, float)):
        raise InvalidInputError("height must be a number (int or float).")

    if width < 0.0 or height < 0.0:
        raise InvalidInputError("Width and height must be non-negative values.")

    # --- Input Validation End ---
    
    target_node: Optional[Dict[str, Any]] = None
    parent_node: Optional[Dict[str, Any]] = None 

    try:
        figma_files_list = DB.get('files')
        if figma_files_list:
            for figma_file_dict in figma_files_list:
                if not isinstance(figma_file_dict, dict): 
                    continue
                
                doc_node_dict = figma_file_dict.get('document')
                if not doc_node_dict or not isinstance(doc_node_dict, dict):
                    continue

                canvases_list = doc_node_dict.get('children') 
                if not canvases_list or not isinstance(canvases_list, list):
                    continue

                for canvas_node_dict in canvases_list: 
                    if not isinstance(canvas_node_dict, dict): 
                        continue
                    
                    canvas_children_list = canvas_node_dict.get('children')
                    if canvas_children_list and isinstance(canvas_children_list, list): 
                        candidate_node = utils.find_node_by_id(canvas_children_list, node_id)
                        if candidate_node:
                            target_node = candidate_node
                            # Attempt to find the direct parent within the canvas's children (e.g., an auto-layout frame)
                            candidate_parent_frame = utils.find_direct_parent_of_node(canvas_children_list, node_id)
                            if candidate_parent_frame:
                                parent_node = candidate_parent_frame
                            else:
                                # If not found within a child of the canvas (like a frame), the canvas is the parent context
                                parent_node = canvas_node_dict 
                            break 
                
                if target_node:
                    break 

        if not target_node:
            raise NodeNotFoundError(f"Node with ID '{node_id}' not found.")

        if target_node.get('locked'): 
            raise ResizeError(f"Node '{node_id}' is locked and cannot be resized.")

        if parent_node and isinstance(parent_node, dict) and \
           parent_node.get('layoutMode') and parent_node.get('layoutMode') != "NONE":
            
            parent_layout_mode = parent_node.get('layoutMode') 
            
            width_controlled_by_auto_layout = False
            height_controlled_by_auto_layout = False
            auto_layout_reasons = [] 

            node_layout_sizing_horizontal = target_node.get('layoutSizingHorizontal')
            node_layout_sizing_vertical = target_node.get('layoutSizingVertical')
            node_layout_grow = target_node.get('layoutGrow') # This can be 0 or 1 (or 0.0, 1.0)
            node_layout_align = target_node.get('layoutAlign')

            # Check for width constraints
            if node_layout_sizing_horizontal == "FILL":
                width_controlled_by_auto_layout = True
                auto_layout_reasons.append("layoutSizingHorizontal is FILL")
            
            if parent_layout_mode == "VERTICAL" and node_layout_align == 'STRETCH':
                width_controlled_by_auto_layout = True
                auto_layout_reasons.append("layoutAlign is STRETCH (fills cross-axis width)")

            if parent_layout_mode == "HORIZONTAL" and node_layout_grow == 1: 
                width_controlled_by_auto_layout = True
                auto_layout_reasons.append("layoutGrow is 1 (fills main-axis width)")

            if node_layout_sizing_vertical == "FILL":
                height_controlled_by_auto_layout = True
                auto_layout_reasons.append("layoutSizingVertical is FILL")

            if parent_layout_mode == "HORIZONTAL" and node_layout_align == 'STRETCH':
                height_controlled_by_auto_layout = True
                auto_layout_reasons.append("layoutAlign is STRETCH (fills cross-axis height)")
            
            if parent_layout_mode == "VERTICAL" and node_layout_grow == 1:
                height_controlled_by_auto_layout = True
                auto_layout_reasons.append("layoutGrow is 1 (fills main-axis height)")

            error_clauses = []
            if width_controlled_by_auto_layout:
                error_clauses.append("width is controlled by auto-layout parent")
            if height_controlled_by_auto_layout:
                error_clauses.append("height is controlled by auto-layout parent")

            if error_clauses:
                unique_reasons = sorted(list(set(auto_layout_reasons)))
                reason_details = f" (due to: {', '.join(unique_reasons)})" if unique_reasons else ""
                full_error_message = f"Node '{node_id}' cannot be resized: " + " and ".join(error_clauses) + reason_details + "."
                raise ResizeError(full_error_message)

        absolute_bounding_box = target_node.get('absoluteBoundingBox')
        if not absolute_bounding_box or not isinstance(absolute_bounding_box, dict):
            absolute_bounding_box = {'x': 0.0, 'y': 0.0} 
            target_node['absoluteBoundingBox'] = absolute_bounding_box
        
        if 'x' not in absolute_bounding_box:
            absolute_bounding_box['x'] = 0.0
        if 'y' not in absolute_bounding_box:
            absolute_bounding_box['y'] = 0.0
        # Also ensure width/height are present if bounding box existed but was partial
        if 'width' not in absolute_bounding_box:
             absolute_bounding_box['width'] = 0.0 # Default if missing before resize attempt
        if 'height' not in absolute_bounding_box:
             absolute_bounding_box['height'] = 0.0 # Default if missing before resize attempt


        absolute_bounding_box['width'] = width
        absolute_bounding_box['height'] = height

        final_width = absolute_bounding_box.get('width')
        final_height = absolute_bounding_box.get('height')

        return {
            "node_id": node_id,
            "final_width": float(final_width) if final_width is not None else 0.0,
            "final_height": float(final_height) if final_height is not None else 0.0,
        }

    except (NodeNotFoundError, ResizeError, InvalidInputError) as e:
        raise e
    except Exception as e:
        raise FigmaOperationError(f"An unexpected error occurred while resizing node '{node_id}': {str(e)}")

@tool_spec(
    spec={
        'name': 'delete_node',
        'description': """ Delete a node from Figma.
        
        Deletes a node from Figma using its unique identifier. This function
        takes the unique identifier of the Figma node to be deleted and returns
        an operation status message indicating successful deletion of the node. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma node to be deleted.'
                }
            },
            'required': [
                'node_id'
            ]
        }
    }
)
def delete_node(node_id: str) -> str:
    """Delete a node from Figma.

    Deletes a node from Figma using its unique identifier. This function
    takes the unique identifier of the Figma node to be deleted and returns
    an operation status message indicating successful deletion of the node.

    Args:
        node_id (str): The unique identifier of the Figma node to be deleted.

    Returns:
        str: Operation status message indicating successfull deletion of the node.

    Raises:
        NodeNotFoundError: If the node with the given nodeId does not exist.
        DeleteError: If the node cannot be deleted (e.g., it is locked or a critical system node that cannot be removed).
        FigmaOperationError: If there is an issue deleting the node in Figma.
    """
    if not DB.get('files'):
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found (no files in DB).")

    node_to_delete: Optional[Dict[str, Any]] = None
    parent_node: Optional[Dict[str, Any]] = None

    for figma_file in DB.get('files', []):
        if not isinstance(figma_file, dict) or 'document' not in figma_file:
            continue

        doc_node: Optional[Dict[str, Any]] = figma_file.get('document')
        if not isinstance(doc_node, dict):
            continue # Skip if document node itself is not a dict

        # Case 0: Is the node to delete the document node itself?
        if doc_node.get('id') == node_id:
            node_to_delete = doc_node
            # Parent for a document node isn't relevant for list-based removal.
            # Type check below will handle undeletable documents.
            parent_node = None 
            break

        # Case 1: The node to delete is a Canvas (direct child of the document)
        doc_children = doc_node.get('children')
        if isinstance(doc_children, list):
            for canvas_candidate in doc_children:
                if isinstance(canvas_candidate, dict) and canvas_candidate.get('id') == node_id:
                    node_to_delete = canvas_candidate
                    parent_node = doc_node
                    break
            if node_to_delete:
                break # Found in this file's canvases, stop searching files

        # Case 2: The node to delete is within a Canvas's children hierarchy
        if not node_to_delete and isinstance(doc_children, list):
            for canvas in doc_children:
                if not isinstance(canvas, dict) or not canvas.get('children'):
                    continue
                
                # Ensure canvas.children is a list before passing to find_node_by_id
                canvas_children_list = canvas.get('children')
                if not isinstance(canvas_children_list, list):
                    continue

                found_node_in_canvas = utils.find_node_by_id(canvas_children_list, node_id)
                if found_node_in_canvas:
                    node_to_delete = found_node_in_canvas
                    # Determine the direct parent of the found node
                    parent_candidate = utils.find_direct_parent_of_node([canvas], node_id)
                    if not parent_candidate:
                        canvas_id = canvas.get('id', 'Unknown Canvas')
                        raise FigmaOperationError(f"Internal error: Node '{node_id}' found within canvas '{canvas_id}', but its direct parent could not be determined.")
                    parent_node = parent_candidate
                    break # Found the node within this canvas
            if node_to_delete:
                break # Found in this file's canvas children, stop searching files
    
    if not node_to_delete:
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found.")

    node_type = node_to_delete.get('type')

    # Check for undeletable node types first
    if node_type == 'DOCUMENT':
        raise DeleteError(f"Node '{node_id}' ({node_type}) cannot be deleted directly.")
    if node_type == 'CANVAS':
        raise DeleteError(f"Node '{node_id}' ({node_type}) cannot be deleted directly.")

    # Then check if the node is locked
    if node_to_delete.get('locked'):
        raise DeleteError(f"Node '{node_id}' ({node_type}) is locked and cannot be deleted.")

    # If node_to_delete is of type DOCUMENT or CANVAS, we should have exited via DeleteError.
    # The following logic assumes node_to_delete is a child within a parent's 'children' list.
    
    if not parent_node:
        raise FigmaOperationError(f"Internal error: Node '{node_id}' ({node_type}) found, but its parent context is unexpectedly missing for deletion.")

    if not isinstance(parent_node, dict):
        # This would be a fundamental issue with the parent_node structure.
        raise FigmaOperationError(f"Internal error: Parent context for node '{node_id}' ({node_type}) is not a valid dictionary structure.")

    parent_id_for_error = parent_node.get('id', 'Unknown Parent')
    parent_type_for_error = parent_node.get('type', 'Unknown Type')

    if 'children' not in parent_node:
        raise FigmaOperationError(f"Internal error: Parent node '{parent_id_for_error}' (type: {parent_type_for_error}) of node '{node_id}' is missing the 'children' attribute.")
    
    parent_children_val = parent_node['children']

    if parent_children_val is None:
        raise FigmaOperationError(f"Internal error: Parent node '{parent_id_for_error}' (type: {parent_type_for_error}) of node '{node_id}' has a 'children' attribute that is None.")
    
    if not isinstance(parent_children_val, list):
        actual_type = type(parent_children_val).__name__
        raise FigmaOperationError(f"Internal error: The 'children' attribute of parent node '{parent_id_for_error}' (type: {parent_type_for_error}) is not a list (found type: {actual_type}).")

    initial_children_count = len(parent_children_val)
    
    new_children_list = []
    node_to_delete_id_val = node_to_delete.get('id') # Cache for comparison
    for child in parent_children_val:
        if isinstance(child, dict):
            if child.get('id') != node_to_delete_id_val:
                new_children_list.append(child)
        else:
            # Preserve non-dict items if they can exist and are not the target
            new_children_list.append(child) 
            
    if len(new_children_list) == initial_children_count:
        node_resolved_id = node_to_delete.get('id', 'Unknown ID')
        
        was_present_by_id = False
        was_present_by_ref = False
        for child_item in parent_children_val:
            if child_item is node_to_delete:
                 was_present_by_ref = True
            if isinstance(child_item, dict) and child_item.get('id') == node_resolved_id:
                 was_present_by_id = True
            if was_present_by_id and was_present_by_ref: # Optimization
                break
        
        if not (was_present_by_id or was_present_by_ref) :
             raise FigmaOperationError(f"Internal consistency error: Node '{node_id}' (resolved to ID '{node_resolved_id}') was not found (by ID or reference) in the children list of its identified parent '{parent_id_for_error}' (type: {parent_type_for_error}) prior to removal attempt.")
        else:
             raise FigmaOperationError(f"Internal error: Node '{node_id}' (resolved to ID '{node_resolved_id}') was not effectively removed from the children list of its identified parent '{parent_id_for_error}' (type: {parent_type_for_error}). Count unchanged, possibly due to ID mismatch or other logic error during filtering.")

    parent_node['children'] = new_children_list

    return f"Node '{node_id}' deleted successfully."


@tool_spec(
    spec={
        'name': 'set_fill_color',
        'description': """ Set the fill color of a node in Figma can be TextNode or FrameNode.
        
        This function sets the fill color of a specified node in Figma. The node
        can be either a TextNode or a FrameNode. The color is specified using
        red (r), green (g), blue (b), and optionally alpha (a) components.
        Each of these color components must have a value between 0.0 and 1.0,
        inclusive. If the alpha (a) component is omitted or provided as null
        (None in Python), it defaults to 1.0, representing full opacity. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': """ The unique identifier for the Figma node whose fill
                    color is to be set. This can be a TextNode or FrameNode. """
                },
                'r': {
                    'type': 'number',
                    'description': """ The red component of the RGBA color. Value must be
                    between 0.0 and 1.0 inclusive. """
                },
                'g': {
                    'type': 'number',
                    'description': """ The green component of the RGBA color. Value must be
                    between 0.0 and 1.0 inclusive. """
                },
                'b': {
                    'type': 'number',
                    'description': """ The blue component of the RGBA color. Value must be
                    between 0.0 and 1.0 inclusive. """
                },
                'a': {
                    'type': 'number',
                    'description': """ The alpha (opacity) component of the RGBA color.
                    Value must be between 0.0 and 1.0 inclusive. If omitted or
                    null, it defaults to 1.0 (fully opaque). """
                }
            },
            'required': [
                'node_id',
                'r',
                'g',
                'b'
            ]
        }
    }
)
def set_fill_color(node_id: str, r: float, g: float, b: float, a: Optional[float] = 1.0) -> Dict[str, Any]: 
    """Set the fill color of a node in Figma can be TextNode or FrameNode.
    This function sets the fill color of a specified node in Figma. The node
    can be either a TextNode or a FrameNode. The color is specified using
    red (r), green (g), blue (b), and optionally alpha (a) components.
    Each of these color components must have a value between 0.0 and 1.0,
    inclusive. If the alpha (a) component is omitted or provided as null
    (None in Python), it defaults to 1.0, representing full opacity.

    Args:
        node_id (str): The unique identifier for the Figma node whose fill
            color is to be set. This can be a TextNode or FrameNode.
        r (float): The red component of the RGBA color. Value must be
            between 0.0 and 1.0 inclusive.
        g (float): The green component of the RGBA color. Value must be
            between 0.0 and 1.0 inclusive.
        b (float): The blue component of the RGBA color. Value must be
            between 0.0 and 1.0 inclusive.
        a (Optional[float]): The alpha (opacity) component of the RGBA color.
            Value must be between 0.0 and 1.0 inclusive. If omitted or
            null, it defaults to 1.0 (fully opaque).

    Returns:
        Dict[str, Any]: An empty dictionary.

    Raises:
        NodeNotFoundError: If the node with the given nodeId does not exist.
        NodeTypeError: If the node type does not support fill color (e.g.,
            not a shape, text, or frame).
        InvalidColorError: If any of the color component values (r, g, b, a)
            are outside the valid range (0.0 to 1.0).
        ValidationError: If input arguments fail validation.
    """

    # --- Input Argument Type Validation ---
    if not isinstance(node_id, str):
        raise custom_errors.ValidationError("node_id must be a string.")
    
    color_args_rgba_values = {'r': r, 'g': g, 'b': b, 'a': a} 
    for name, value in color_args_rgba_values.items():
        if not isinstance(value, (int, float)): 
            raise custom_errors.ValidationError(
                f"Color component '{name}' must be a number (int or float). Received type: {type(value).__name__}."
            )
    
    # --- Color Component Range Validation ---
    color_model_for_validation = models.Color(r=r, g=g, b=b, a=a)
    all_color_components_from_model = color_model_for_validation.model_dump(exclude_none=False) 

    all_color_components_to_validate = {
        k: v for k, v in all_color_components_from_model.items() 
        if k in ['r', 'g', 'b', 'a'] and v is not None
    }

    for name, value_comp in all_color_components_to_validate.items(): 
        if not (0.0 <= value_comp <= 1.0): 
            raise custom_errors.InvalidColorError(f"Color component '{name}' value {value_comp} is outside the valid range [0.0, 1.0].")

    # --- Node Retrieval and Validation ---
    node = utils.find_node_dict_in_DB(DB, node_id) 

    if node is None: 
        raise custom_errors.NodeNotFoundError(f"Node with ID '{node_id}' not found.")

    # --- Node Type Validation ---
    node_type_str = node.get('type')
    
    try:
        models.FillableNodeType(node_type_str)
    except ValueError:
        supported_types_list_str = [e.value for e in models.FillableNodeType]
        raise custom_errors.NodeTypeError(
            f"Node with ID '{node_id}' (type: {node_type_str}) does not support direct fill color modification via this function. "
            f"Supported types for direct fill are: {', '.join(supported_types_list_str)}." 
        )

    # --- Apply Fill Color to Node using Pydantic Models ---
    fill_color_model_for_item = models.Color(r=r, g=g, b=b, a=a)

    new_fill_item_model = models.FillItem(
        type="SOLID",
        color=fill_color_model_for_item,
        opacity=a, 
        visible=True,
        blendMode="NORMAL"
    )
    new_solid_fill_dict = new_fill_item_model.model_dump(exclude_none=True)

    if 'fills' not in node or not isinstance(node.get('fills'), list):
        node['fills'] = []
    
    current_fills = node['fills']
    
    if current_fills and isinstance(current_fills[0], dict) and current_fills[0].get("type") == "SOLID":
        current_fills[0].update(new_solid_fill_dict) 
    else:
        current_fills.insert(0, new_solid_fill_dict)
        
    return {}


@tool_spec(
    spec={
        'name': 'delete_multiple_nodes',
        'description': """ Delete multiple nodes from Figma at once.
        
        This function deletes multiple nodes from Figma simultaneously. Based on a
        provided list of node identifiers, it attempts to delete each corresponding
        node. The function then returns a detailed status of these operations,
        specifying which nodes were successfully deleted and, for those that were
        not, the reasons for the failure. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_ids': {
                    'type': 'array',
                    'description': 'A list of unique identifiers for the nodes to be deleted from Figma.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'node_ids'
            ]
        }
    }
)
def delete_multiple_nodes(node_ids: List[str]) -> Dict[str, Any]:
    """Delete multiple nodes from Figma at once.

    This function deletes multiple nodes from Figma simultaneously. Based on a
    provided list of node identifiers, it attempts to delete each corresponding
    node. The function then returns a detailed status of these operations,
    specifying which nodes were successfully deleted and, for those that were
    not, the reasons for the failure.

    Args:
        node_ids (List[str]): A list of unique identifiers for the nodes to be deleted from Figma.

    Returns:
        Dict[str, Any]: Status of the delete operation for multiple nodes. This dictionary contains the following keys:
            successfully_deleted_ids (List[str]): A list of node IDs that were successfully deleted.
            failed_to_delete (List[Dict[str, Any]]): A list of dictionaries, where each dictionary represents a node that failed to delete. Each such dictionary contains:
                nodeId (str): The ID of the node that could not be deleted.
                reason (str): A brief explanation for the failure (e.g., 'Node not found', 'Node locked').

    Raises:
        FigmaOperationError: If there is a general issue deleting the nodes in Figma.
        InvalidInputError: If the `node_ids` list is empty or contains malformed IDs.
    """

    # 1. Input Validation
    if not node_ids:
        raise InvalidInputError("node_ids list cannot be empty.")
    if not all(isinstance(nid, str) and nid for nid in node_ids):
        # Ensure nid is a non-empty string
        raise InvalidInputError("All node IDs must be non-empty strings. Malformed or empty IDs found.")

    # 2. DB Integrity Check
    # These checks ensure the DB is in a minimally operable state.
    # The utils functions (get_node_from_db, get_parent_of_node_from_db) typically rely on DB['files'][0]['document'].
    if not DB or not isinstance(DB.get('files'), list) or not DB['files']:
        raise FigmaOperationError("Figma data store (DB) is uninitialized or 'files' list is empty.")

    current_file_data = utils.get_current_file()
    if not isinstance(current_file_data, dict) or not current_file_data.get('document'):
        raise FigmaOperationError("Essential Figma file data (e.g., document root) is missing in the first file entry.")

    document_node = current_file_data.get('document')
    if not isinstance(document_node, dict) or not document_node.get('id'):
        raise FigmaOperationError("Document root in the first file is malformed or missing its ID.")

    document_root_id = document_node['id']

    # 3. Initialize result containers
    successfully_deleted_ids: List[str] = []
    # Each item in failed_to_delete will be Dict[str, str] matching {"nodeId": ..., "reason": ...}
    failed_to_delete: List[Dict[str, str]] = [] 

    # Process unique node IDs from the input list, preserving first-seen order.
    # This ensures each node ID is processed for deletion status only once,
    # even if it appears multiple times in the input `node_ids` list.
    # The docstring implies `node_ids` contains unique identifiers, but this handles non-compliance gracefully.
    unique_node_ids_to_process = list(dict.fromkeys(node_ids))

    # 4. Process each unique node_id for deletion
    for node_id in unique_node_ids_to_process:
        # Attempt to find the node in the DB using the helper utility
        node_to_delete_dict = utils.get_node_from_db(DB, node_id)

        if not node_to_delete_dict:
            failed_to_delete.append({"nodeId": node_id, "reason": "Node not found"})
            continue

        # Check if trying to delete the document root node itself
        if node_id == document_root_id:
            failed_to_delete.append({"nodeId": node_id, "reason": "Cannot delete document root"})
            continue

        # Check if the node is locked
        if node_to_delete_dict.get('locked') is True:
            failed_to_delete.append({"nodeId": node_id, "reason": "Node locked"})
            continue

        # Find the parent of the node to modify its children list
        parent_node_dict = utils.get_parent_of_node_from_db(DB, node_id)

        if not parent_node_dict:
            # This implies the node was found (so it's not the document root), 
            # but its parent wasn't. This could indicate an orphaned node or a DB inconsistency.
            # Canvas nodes should have the document_node as their parent.
            failed_to_delete.append({
                "nodeId": node_id, 
                "reason": "Failed to find parent node (node may be orphaned or DB structure inconsistent)"
            })
            continue

        # Parent found, now try to remove the child from parent's 'children' list
        parent_children_list = parent_node_dict.get('children')
        if not isinstance(parent_children_list, list):
            # Parent's children attribute is missing or not a list, which is a structural issue.
            failed_to_delete.append({
                "nodeId": node_id, 
                "reason": "Parent node's children data is missing or malformed"
            })
            continue

        # Perform the deletion by creating a new list without the target node.
        # Ensure child_dict is a dictionary and has an 'id' key before comparison.
        initial_children_count = len(parent_children_list)
        updated_children_list = [
            child_dict for child_dict in parent_children_list 
            if not (isinstance(child_dict, dict) and child_dict.get('id') == node_id)
        ]

        if len(updated_children_list) == initial_children_count:
            # Node was not found in its identified parent's children list.
            # This indicates a DB inconsistency, as the node was found globally via get_node_from_db,
            # and its parent was also identified.
            failed_to_delete.append({
                "nodeId": node_id, 
                "reason": "Node inconsistency: Found globally but not in its parent's children list"
            })
            continue

        # Successfully prepared for deletion, update the parent node's children list in the DB
        parent_node_dict['children'] = updated_children_list
        successfully_deleted_ids.append(node_id)

    # 5. Return the results structured as per the docstring
    return {
        "successfully_deleted_ids": successfully_deleted_ids,
        "failed_to_delete": failed_to_delete  # List of Dict[str, str] which fits Dict[str, Any]
    }

@tool_spec(
    spec={
        'name': 'set_text_content',
        'description': """ Set the text content of an existing text node in Figma.
        
        This function sets the text content of an existing text node in Figma. It uses the `node_id` to identify the specific Figma node and applies the new `text` as its content. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma node to modify.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The new text content to set for the node. Defaults to None.'
                }
            },
            'required': [
                'node_id'
            ]
        }
    }
)
def set_text_content(node_id: str, text: Optional[str] = None) -> Dict[str, Any]:
    """Set the text content of an existing text node in Figma.

    This function sets the text content of an existing text node in Figma. It uses the `node_id` to identify the specific Figma node and applies the new `text` as its content.

    Args:
        node_id (str): The unique identifier of the Figma node to modify.
        text (Optional[str]): The new text content to set for the node. Defaults to None.

    Returns:
        Dict[str, Any]: An empty dictionary

    Raises:
        NodeNotFoundError: If the node with the given node_id does not exist.
        NodeTypeError: If the identified node is not a text node.
        FigmaOperationError: If there is an issue setting the text content in Figma (e.g., font issues, locked node).
        InvalidInputError:  Exception raised for errors in the input provided to the function.
    """

    # 1. Input Validation
    if not isinstance(node_id, str):
        # Validate if node_id is a string.
        raise InvalidInputError(f"node_id must be a string. Received type: {type(node_id).__name__}.")
    if not node_id: # Check for empty string
        raise InvalidInputError("node_id cannot be an empty string.")

    if text is not None and not isinstance(text, str):
        # Validate if text is either None or a string
        raise InvalidInputError(f"The 'text' argument must be a string or None. Received type: {type(text).__name__}.")

    node_dict = utils.get_node_dict_by_id(DB, node_id)

    if node_dict is None:
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found.")

    node_type = node_dict.get('type')
    if node_type != "TEXT":
        # Provide the actual node type in the error message if available.
        type_str = str(node_type) if node_type is not None else "unknown"
        raise NodeTypeError(f"Node with ID '{node_id}' is of type '{type_str}', not TEXT. Cannot set text content.")

    if node_dict.get('locked') is True:
        raise FigmaOperationError(f"Cannot set text content for node '{node_id}' because it is locked.")

    # The 'Node' Pydantic model (defined in the schema context) uses 'text' as an alias for 'characters'.
    # In the underlying dictionary representation (which DB stores and utils.get_node_dict_by_id returns),
    # the key for text content is 'characters'.
    # The 'text' argument to this function is Optional[str].
    # If `text` is `None`, `node_dict['characters']` will be set to `None`.
    # If `text` is a string (including an empty string), `node_dict['characters']` will be set to that string.
    # This aligns with the `Optional[str]` type of the 'characters' field in the Node model schema.
    node_dict['characters'] = text

    return {}

# List of node types that typically support stroke properties
SUPPORTED_NODE_TYPES_FOR_STROKE = [
    "RECTANGLE", "ELLIPSE", "POLYGON", "STAR", "LINE", "VECTOR",
    "TEXT", "FRAME", "COMPONENT", "INSTANCE", "COMPONENT_SET"
]

@tool_spec(
    spec={
        'name': 'set_stroke_color',
        'description': """ Set the stroke color of a node in Figma.
        
        This function sets the stroke color for a specified node within Figma. It requires the node's unique identifier (`node_id`) and the `red`, `green`, and `blue` components for the RGBA stroke color, where each component value must be between 0.0 and 1.0 inclusive.
        The `alpha` component, representing opacity, can also be provided (0.0 for fully transparent, 1.0 for fully opaque); if not specified, it defaults to 1.0.
        Optionally, the `stroke_weight` (thickness of the stroke) can be set using a non-negative value. If `stroke_weight` is not provided, the node's existing stroke weight will be maintained, or a default weight might be used if a stroke is being added to a node that does not currently have one. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma node whose stroke color is to be set.'
                },
                'red': {
                    'type': 'number',
                    'description': 'The red component of the RGBA stroke color. Value must be between 0.0 and 1.0 inclusive.'
                },
                'green': {
                    'type': 'number',
                    'description': 'The green component of the RGBA stroke color. Value must be between 0.0 and 1.0 inclusive.'
                },
                'blue': {
                    'type': 'number',
                    'description': 'The blue component of the RGBA stroke color. Value must be between 0.0 and 1.0 inclusive.'
                },
                'alpha': {
                    'type': 'number',
                    'description': 'The alpha (opacity) component of the RGBA stroke color. Value must be between 0.0 (fully transparent) and 1.0 (fully opaque). If not provided, defaults to 1.0 (fully opaque).'
                },
                'stroke_weight': {
                    'type': 'number',
                    'description': "The thickness of the stroke. Defaults to None. Must be a non-negative value. If provided, this weight will be applied. If not provided, the node's existing stroke weight will be maintained, or a default weight might be used if adding a stroke to a node that doesn't currently have one."
                }
            },
            'required': [
                'node_id',
                'red',
                'green',
                'blue'
            ]
        }
    }
)
def set_stroke_color(node_id: str, red: float, green: float, blue: float, alpha: Optional[float] = 1.0, stroke_weight: Optional[float] = None) -> Dict[str, Any]:
    """Set the stroke color of a node in Figma.

    This function sets the stroke color for a specified node within Figma. It requires the node's unique identifier (`node_id`) and the `red`, `green`, and `blue` components for the RGBA stroke color, where each component value must be between 0.0 and 1.0 inclusive.
    The `alpha` component, representing opacity, can also be provided (0.0 for fully transparent, 1.0 for fully opaque); if not specified, it defaults to 1.0.
    Optionally, the `stroke_weight` (thickness of the stroke) can be set using a non-negative value. If `stroke_weight` is not provided, the node's existing stroke weight will be maintained, or a default weight might be used if a stroke is being added to a node that does not currently have one.

    Args:
        node_id (str): The unique identifier of the Figma node whose stroke color is to be set.
        red (float): The red component of the RGBA stroke color. Value must be between 0.0 and 1.0 inclusive.
        green (float): The green component of the RGBA stroke color. Value must be between 0.0 and 1.0 inclusive.
        blue (float): The blue component of the RGBA stroke color. Value must be between 0.0 and 1.0 inclusive.
        alpha (Optional[float]): The alpha (opacity) component of the RGBA stroke color. Value must be between 0.0 (fully transparent) and 1.0 (fully opaque). If not provided, defaults to 1.0 (fully opaque).
        stroke_weight (Optional[float]): The thickness of the stroke. Defaults to None. Must be a non-negative value. If provided, this weight will be applied. If not provided, the node's existing stroke weight will be maintained, or a default weight might be used if adding a stroke to a node that doesn't currently have one.

    Returns:
        Dict[str, Any]: An empty dictionary.

    Raises:
        NodeNotFoundError: If the node with the given `node_id` does not exist.
        NodeTypeSupportError: If the specified node type does not support strokes (e.g., a Canvas node).
        InvalidColorError: If any of the color component values (red, green, blue, alpha) are out of the valid range (typically 0.0 to 1.0).
        InvalidInputError: If `node_id` is invalid, or `stroke_weight` is invalid (e.g., a negative value, or wrong type), or color components types are wrong.
        FigmaOperationError: If an unexpected error occurs within the Figma plugin while attempting to apply the stroke.
    """

    # --- Input Validation ---
    if not isinstance(node_id, str):
        raise InvalidInputError("Node ID must be a string.")
    if not node_id.strip(): # Check if it's empty or only whitespace
        raise InvalidInputError("Node ID cannot be empty or just whitespace.")

    # Validate and coerce RGB color components
    v_red, v_green, v_blue = red, green, blue # Use copies for validation/coercion
    color_components_to_validate = [("red", v_red), ("green", v_green), ("blue", v_blue)]
    for name, val in color_components_to_validate:
        if not isinstance(val, (int, float)):
            raise InvalidInputError(f"Color component '{name}' must be a number. Got type {type(val).__name__}.")
        if not (0.0 <= float(val) <= 1.0): # Coerce to float for comparison
            raise InvalidColorError(f"Color component '{name}' must be between 0.0 and 1.0. Got: {val}.")
    # Assign coerced float values
    v_red, v_green, v_blue = float(v_red), float(v_green), float(v_blue)

    # Validate and process alpha component
    v_alpha = alpha # Use copy for validation/coercion
    if v_alpha is None:
        v_alpha = 1.0  # Defaulting if None
    elif not isinstance(v_alpha, (int, float)):
        raise InvalidInputError(f"Alpha component must be a number if provided. Got type {type(v_alpha).__name__}.")
    elif not (0.0 <= float(v_alpha) <= 1.0): # Coerce to float for comparison
        raise InvalidColorError(f"Alpha component must be between 0.0 and 1.0. Got: {v_alpha}.")
    else:
        v_alpha = float(v_alpha) # Coerce to float

    # Validate and process stroke_weight
    v_stroke_weight = stroke_weight # Use copy for validation/coercion
    if v_stroke_weight is not None:
        if not isinstance(v_stroke_weight, (int, float)):
            raise InvalidInputError(f"Stroke weight must be a number if provided. Got type {type(v_stroke_weight).__name__}.")
        v_stroke_weight_float = float(v_stroke_weight) # Coerce to float for comparison
        if v_stroke_weight_float < 0:
            raise InvalidInputError(f"Stroke weight must be a non-negative value. Got: {v_stroke_weight}.")
        v_stroke_weight = v_stroke_weight_float # Assign coerced float value
    # --- End of Input Validation ---

    # Find the node dictionary using the provided utility
    node_data = utils.get_node_dict_by_id(DB, node_id)

    if node_data is None:
        raise NodeNotFoundError(f"Node with ID '{node_id}' not found.")

    # Check node type for stroke support
    node_type = node_data.get("type")
    if node_type not in SUPPORTED_NODE_TYPES_FOR_STROKE:
        raise NodeTypeSupportError(f"Node type '{node_type}' does not support strokes for node ID '{node_id}'.")

    # Capture initial state for stroke weight defaulting logic
    initial_node_had_no_effective_weight = node_data.get('strokeWeight') is None or node_data.get('strokeWeight') == 0.0

    # Prepare and apply stroke paint
    if not isinstance(node_data.get('strokes'), list):
        node_data['strokes'] = []

    strokes_list: List[Dict[str, Any]] = node_data['strokes']
    # Use validated and coerced color components
    new_color_dict = {"r": v_red, "g": v_green, "b": v_blue, "a": v_alpha}
    
    stroke_paint_updated = False # Flag if an existing paint was updated
    stroke_paint_was_added = False # Flag if a new paint was added

    # Priority 1: Find and update the first *visible* SOLID stroke
    target_paint_to_update = None
    for paint in strokes_list:
        if isinstance(paint, dict) and paint.get('type') == "SOLID" and paint.get('visible') is True:
            target_paint_to_update = paint
            break
    
    if target_paint_to_update:
        target_paint_to_update['color'] = new_color_dict
        if 'opacity' not in target_paint_to_update: target_paint_to_update['opacity'] = 1.0
        if 'blendMode' not in target_paint_to_update: target_paint_to_update['blendMode'] = "NORMAL"
        stroke_paint_updated = True
    else:
        # Priority 2: Find and update the first SOLID stroke (even if not visible)
        for paint in strokes_list:
            if isinstance(paint, dict) and paint.get('type') == "SOLID":
                target_paint_to_update = paint
                break
        
        if target_paint_to_update:
            target_paint_to_update['type'] = "SOLID"
            target_paint_to_update['visible'] = True
            target_paint_to_update['color'] = new_color_dict
            if 'opacity' not in target_paint_to_update: target_paint_to_update['opacity'] = 1.0
            if 'blendMode' not in target_paint_to_update: target_paint_to_update['blendMode'] = "NORMAL"
            stroke_paint_updated = True
        else:
            # Priority 3: No SOLID stroke found, add a new one
            new_stroke_paint = {
                "type": "SOLID",
                "visible": True,
                "color": new_color_dict,
                "opacity": 1.0,
                "blendMode": "NORMAL"
            }
            strokes_list.append(new_stroke_paint)
            stroke_paint_was_added = True

    # Update strokeWeight property on the node
    stroke_weight_was_updated = False
    if v_stroke_weight is not None: # Use validated and coerced stroke_weight
        node_data['strokeWeight'] = v_stroke_weight
        stroke_weight_was_updated = True
    else: # v_stroke_weight (and thus original stroke_weight param) was None
        if stroke_paint_was_added and initial_node_had_no_effective_weight:
            node_data['strokeWeight'] = 1.0  # Default stroke weight
            stroke_weight_was_updated = True

    # Construct and return success response
    message = "Stroke color updated successfully." # Default
    if stroke_weight_was_updated:
        if stroke_weight is not None: # Check original stroke_weight parameter for user intent
            message = "Stroke color and stroke weight updated successfully."
        else: # stroke_weight parameter was None, and stroke_weight_was_updated is true (meaning it was defaulted)
            message = "Stroke color updated successfully; stroke weight set to default (1.0) as it was previously undefined or zero."
    # This case is if only a new paint was added, but weight wasn't touched (e.g., node already had weight)
    # And the primary action was adding a stroke, not just updating color of an existing one.
    elif stroke_paint_was_added and not stroke_paint_updated : # (stroke_paint_updated implies we modified an existing one)
         message = "New stroke color added successfully."
    
    # If stroke_paint_updated is true, but stroke_paint_was_added is false, and stroke_weight_was_updated is false,
    # the default "Stroke color updated successfully." is appropriate.

    return {}