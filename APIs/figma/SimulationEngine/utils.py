from common_utils.print_log import print_log
import re
from typing import List, Optional, Dict, Any, Tuple, Set
from ..SimulationEngine import custom_errors
from ..SimulationEngine.models import (
    Node,
    FigmaData,
    Color,
    FillItem,
    ComponentProperty,
    StyleDefinition,
    DBCanvasNode,  # For canvas-specific prototype info
    FlowStartingPoint,  # For canvas-specific prototype info
    VariableMetadata,  # If available in FigmaData.globalVars
    VariableValueResolved,  # If available in FigmaData.globalVars
    FigmaFile,
    FigmaDB,
    FoundNodeInfo,
)
from ..SimulationEngine.db import DB
from . import models
from pydantic import ValidationError
import uuid
import datetime

def get_file_by_key(db: Dict[str, Any], file_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a specific Figma file (as a dictionary) from a database dictionary
    using its fileKey.

    Args:
        db (Dict[str, Any]): The database dictionary. It's expected to have a 'files' key
            containing a list of dictionaries, where each dictionary
            represents a Figma file.
        file_key (str): The unique identifier (fileKey) of the Figma file to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The dictionary representing the Figma file if found, otherwise None.
    """
    # Ensure db is a dictionary
    if not isinstance(db, dict):
        # You might want to log a warning or raise an error here depending on desired strictness
        return None

    # Safely get the list of files from the db dictionary
    files_list = db.get("files")

    # Check if 'files' key exists, its value is a list, and the list is not empty
    if not files_list or not isinstance(files_list, list):
        return None

    for file_data_dict in files_list:
        # Ensure each item in the list is a dictionary
        if isinstance(file_data_dict, dict):
            # Safely get 'fileKey' from the file_data_dict
            # and compare with the target file_key
            if file_data_dict.get("fileKey") == file_key:
                return file_data_dict  # Return the dictionary itself
    
    return None


# --- Node Traversal and Search Utilities ---

def find_node_by_id(node_list: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
    """
    Recursively searches a list of node dictionaries and their children to find a
    node with a specific ID.

    Args:
        node_list (List[Dict[str, Any]]): A list of node dictionaries to search through. Each node can
                   have a 'children' key containing another list of nodes.
        node_id (str): The ID of the node to find.

    Returns:
        Optional[Dict[str, Any]]: The dictionary of the found node, or None if no node with the given ID
        is found.
    """
    for node_dict in node_list:
        if not isinstance(node_dict, dict):
            continue
        if node_dict.get('id') == node_id:
            return node_dict
        
        children = node_dict.get('children')
        if isinstance(children, list):
            found_in_children = find_node_by_id(children, node_id)
            if found_in_children:
                return found_in_children
    return None


def find_nodes_by_type(node_list: List[Dict[str, Any]], node_type: str) -> List[Dict[str, Any]]:
    """
    Recursively finds all node dictionaries of a specific type.

    Args:
        node_list (List[Dict[str, Any]]): The list of node dictionaries to search through.
        node_type (str): The type of nodes to find (e.g., "TEXT", "FRAME").

    Returns:
        List[Dict[str, Any]]: A list of node dictionaries that match the specified type.
    """
    result_nodes = []
    for node_dict in node_list:
        if not isinstance(node_dict, dict):
            continue
        if node_dict.get('type') == node_type:
            result_nodes.append(node_dict)
        
        children = node_dict.get('children')
        if isinstance(children, list):
            result_nodes.extend(find_nodes_by_type(children, node_type))
    return result_nodes


def find_nodes_by_name(
    node_list: List[Dict[str, Any]], name_pattern: str, exact_match: bool = True
) -> List[Dict[str, Any]]:
    """
    Recursively finds all node dictionaries whose name matches a given pattern.

    Args:
        node_list (List[Dict[str, Any]]): The list of node dictionaries to search through.
        name_pattern (str): The name pattern to match against node names.
        exact_match (Optional[bool]): If True, performs an exact match. If False, searches for
                     the pattern within the node name. Defaults to True.

    Returns:
        List[Dict[str, Any]]: A list of node dictionaries that match the name pattern.
    """
    result_nodes = []
    for node_dict in node_list:
        if not isinstance(node_dict, dict):
            continue
        
        node_name = node_dict.get('name')
        if isinstance(node_name, str): # Ensure name exists and is a string
            if exact_match:
                if node_name == name_pattern:
                    result_nodes.append(node_dict)
            else:
                if re.search(name_pattern, node_name):
                    result_nodes.append(node_dict)
        
        children = node_dict.get('children')
        if isinstance(children, list):
            result_nodes.extend(
                find_nodes_by_name(children, name_pattern, exact_match)
            )
    return result_nodes


def find_direct_parent_of_node(
    root_node_list: List[Dict[str, Any]], target_child_id: str
) -> Optional[Dict[str, Any]]:
    """
    Finds the direct parent of a node with a specific ID within a tree.

    Args:
        root_node_list (List[Dict[str, Any]]): The root list of node dictionaries representing the tree.
        target_child_id (str): The ID of the child node whose parent is to be found.

    Returns:
        Optional[Dict[str, Any]]: The parent node dictionary, or None if the parent is not found.
    """
    for node_dict in root_node_list:
        if not isinstance(node_dict, dict):
            continue
            
        children = node_dict.get('children')
        if isinstance(children, list):
            for child_dict in children:
                if not isinstance(child_dict, dict):
                    continue
                if child_dict.get('id') == target_child_id:
                    return node_dict  # node_dict is the direct parent
                
                # Recurse to check if child_dict is an ancestor
                # Pass child_dict as a list to the recursive call
                parent = find_direct_parent_of_node([child_dict], target_child_id)
                if parent:
                    return parent
    return None


# --- Node Property Extraction Utilities ---

def get_node_text_content(node_dict: Dict[str, Any]) -> Optional[str]:
    """
    Safely extracts the text content from a "TEXT" node dictionary.

    Args:
        node_dict (Dict[str, Any]): The "TEXT" node dictionary.

    Returns:
        Optional[str]: The text content of the node, or None if the node is not a "TEXT" node
        or doesn't have text content.
    """
    if not isinstance(node_dict, dict):
        return None
    # The 'text' attribute in the Node model was an alias for 'characters'.
    # So, in the dictionary, the key is expected to be 'characters'.
    if node_dict.get('type') == "TEXT":
        return node_dict.get('characters') # Or 'text' if that's the actual key in your dicts
    return None


def get_node_fill_colors(node_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts all visible solid fill color dictionaries from a node.

    This function checks both the 'fills' and 'backgroundColor' properties of the
    node dictionary.

    Args:
        node_dict (Dict[str, Any]): The node dictionary to extract colors from.

    Returns:
        List[Dict[str, Any]]: A list of color dictionaries.
    """
    colors = []
    if not isinstance(node_dict, dict):
        return colors

    fills_data = node_dict.get('fills') # This could be a string or a dict (from RootModel) or List
    
    actual_fills_list = None
    if isinstance(fills_data, dict) and 'root' in fills_data: # Handle RootModel structure {'root': value}
        actual_fills_list = fills_data.get('root')
    elif isinstance(fills_data, list): # Handle if fills is directly a list
        actual_fills_list = fills_data
        
    if isinstance(actual_fills_list, list):
        for fill_dict in actual_fills_list:
            if isinstance(fill_dict, dict) and\
               fill_dict.get('type') == "SOLID" and\
               fill_dict.get('visible') is not False: # True or None (default visible)
                color_dict = fill_dict.get('color')
                if isinstance(color_dict, dict):
                    colors.append(color_dict)

    # Also consider backgroundColor for frames, canvases etc.
    background_color_dict = node_dict.get('backgroundColor')
    node_type = node_dict.get('type')
    if isinstance(background_color_dict, dict) and\
       node_type in ["FRAME", "CANVAS", "COMPONENT", "INSTANCE", "COMPONENT_SET"]:
        colors.append(background_color_dict)
        
    return colors


def get_node_dimensions(node_dict: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extracts dimensions from a node's 'absoluteBoundingBox'.

    Args:
        node_dict (Dict[str, Any]): The node dictionary.

    Returns:
        Optional[Dict[str, float]]: A dictionary with 'x', 'y', 'width', and 'height' of the node,
        or None if 'absoluteBoundingBox' is not present or invalid.
    """
    if not isinstance(node_dict, dict):
        return None
        
    bbox_dict = node_dict.get('absoluteBoundingBox')
    if isinstance(bbox_dict, dict):
        width = bbox_dict.get('width')
        height = bbox_dict.get('height')
        if isinstance(width, (int, float)) and isinstance(height, (int, float)):
            return {
                "x": bbox_dict.get('x', 0.0), # Default to 0.0 if x or y is None
                "y": bbox_dict.get('y', 0.0),
                "width": float(width),
                "height": float(height),
            }
    return None


def is_node_visible(node_dict: Dict[str, Any]) -> bool:
    """
    Checks if a node is marked as visible.

    Figma defaults to visible if the 'visible' property is absent.

    Args:
        node_dict (Dict[str, Any]): The node dictionary to check.

    Returns:
        bool: True if the node is visible, False otherwise.
    """
    if not isinstance(node_dict, dict):
        return True # Or False, depending on desired behavior for invalid input
    return node_dict.get('visible') is not False


# --- Component & Instance Utilities ---

def get_instance_main_component_id(node_dict: Dict[str, Any]) -> Optional[str]:
    """
    Gets the main component ID of an instance node.

    Args:
        node_dict (Dict[str, Any]): The node dictionary, expected to be an "INSTANCE" type.

    Returns:
        Optional[str]: The component ID if the node is an instance, otherwise None.
    """
    if not isinstance(node_dict, dict):
        return None
    if node_dict.get('type') == "INSTANCE":
        return node_dict.get('componentId')
    return None


def get_instance_variant_properties(node_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts the variant properties of an instance node.

    Args:
        node_dict (Dict[str, Any]): The instance node dictionary.

    Returns:
        Optional[Dict[str, Any]]: A dictionary of variant properties, or None if the node is not a
        valid instance with properties.
    """
    if not isinstance(node_dict, dict):
        return None
        
    if node_dict.get('type') == "INSTANCE":
        comp_props_map = node_dict.get('componentProperties')
        if isinstance(comp_props_map, dict):
            return {
                key: prop_value_dict.get('value')
                for key, prop_value_dict in comp_props_map.items()
                if isinstance(prop_value_dict, dict) # Each prop_value_dict was a ComponentProperty model
            }
    return None


def get_component_property_definitions(node_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts property definitions from a main component node.

    Args:
        node_dict (Dict[str, Any]): The main component node dictionary.

    Returns:
        Optional[Dict[str, Any]]: A dictionary of component property definitions, or None if not a
        component or no definitions are found.
    """
    if not isinstance(node_dict, dict):
        return None
        
    prop_defs_data = node_dict.get('componentPropertyDefinitions')
    # ComponentPropertyDefinitions was RootModel[Dict[str, ComponentPropertyDefinitionValue]]
    if isinstance(prop_defs_data, dict):
        if 'root' in prop_defs_data and isinstance(prop_defs_data.get('root'), dict):
            return prop_defs_data.get('root')
        # If not nested under 'root' and prop_defs_data itself is the map of definitions
        # (this depends on how the RootModel was serialized to dict)
        # Heuristic: if it doesn't have 'root' but looks like the definitions map, return it.
        # A better check might be to see if its values look like ComponentPropertyDefinitionValue dicts.
        # For simplicity, if not 'root', we assume it's the direct map.
        elif 'root' not in prop_defs_data: 
            # Check if values are dictionaries (as ComponentPropertyDefinitionValue would be)
            if all(isinstance(v, dict) for v in prop_defs_data.values()):
                 return prop_defs_data
    return None


# --- Style and Variable Utilities ---

def get_resolved_style_for_node(
    node_dict: Dict[str, Any], style_attribute_name: str, figma_data_dict: Dict[str, Any]
) -> Optional[Any]:
    """
    Retrieves the resolved style object for a given style attribute on a node.

    Args:
        node_dict (Dict[str, Any]): The node dictionary containing the style reference.
        style_attribute_name (str): The name of the style attribute (e.g., 'fills').
        figma_data_dict (Dict[str, Any]): The Figma data dictionary containing global styles.

    Returns:
        Optional[Any]: The resolved style object (dict, list, or value), or None if not found.
    """
    if not isinstance(node_dict, dict) or not isinstance(figma_data_dict, dict):
        return None

    styles_ref_dict = node_dict.get('styles')
    global_vars_dict = figma_data_dict.get('globalVars')

    if not isinstance(styles_ref_dict, dict) or not isinstance(global_vars_dict, dict):
        return None

    all_styles_map = global_vars_dict.get('styles')
    if not isinstance(all_styles_map, dict):
        return None

    style_id = styles_ref_dict.get(style_attribute_name)
    if isinstance(style_id, str):
        style_definition_data = all_styles_map.get(style_id)
        # StyleDefinition was RootModel[Union[List[Union[str, FillItem]], NodeStyle, Dict[str, Any]]]
        if isinstance(style_definition_data, dict) and 'root' in style_definition_data:
            return style_definition_data.get('root')
        # If not a dict with 'root', it might be the direct value (e.g., if RootModel unwrapped)
        return style_definition_data 
    return None


def get_variable_value_for_mode(
    variable_id: str, mode_id: str, figma_data_dict: Dict[str, Any]
) -> Optional[Any]:
    """
    Retrieves a variable's value (as dict/list/value) for a specific mode.

    Args:
        variable_id (str): The ID of the variable.
        mode_id (str): The ID of the mode.
        figma_data_dict (Dict[str, Any]): The Figma data dictionary containing global variables.

    Returns:
        Optional[Any]: The variable's value for the specified mode, or None if not found.
    """
    if not isinstance(figma_data_dict, dict):
        return None

    global_vars_dict = figma_data_dict.get('globalVars')
    if not isinstance(global_vars_dict, dict):
        return None

    variables_map = global_vars_dict.get('variables')
    if not isinstance(variables_map, dict):
        return None
    
    variable_dict = variables_map.get(variable_id)
    if not isinstance(variable_dict, dict):
        return None

    values_by_mode_map = variable_dict.get('valuesByMode')
    if not isinstance(values_by_mode_map, dict):
        return None
        
    value_data = values_by_mode_map.get(mode_id)
    # VariableValueResolved was RootModel[Union[Color, str, float, bool, Dict[str, Any]]]
    if isinstance(value_data, dict) and 'root' in value_data:
        return value_data.get('root')
    return value_data # Return direct data if not a {'root': ...} structure

def get_default_mode_id_for_variable(
    variable_id: str, figma_data_dict: Dict[str, Any]
) -> Optional[str]:
    """
    Retrieves the default mode ID for a variable's collection.

    Args:
        variable_id (str): The ID of the variable.
        figma_data_dict (Dict[str, Any]): The Figma data dictionary containing global variables.

    Returns:
        Optional[str]: The default mode ID as a string, or None if not found.
    """
    if not isinstance(figma_data_dict, dict):
        return None

    global_vars_dict = figma_data_dict.get('globalVars')
    if not isinstance(global_vars_dict, dict):
        return None

    variables_map = global_vars_dict.get('variables')
    if not isinstance(variables_map, dict):
        return None

    variable_dict = variables_map.get(variable_id)
    if not isinstance(variable_dict, dict):
        return None
    
    collection_id = variable_dict.get('variableCollectionId')
    if not isinstance(collection_id, str):
        return None

    variable_collections_map = global_vars_dict.get('variableCollections')
    if not isinstance(variable_collections_map, dict):
        return None
        
    collection_dict = variable_collections_map.get(collection_id)
    if isinstance(collection_dict, dict):
        return collection_dict.get('defaultModeId')
    return None


# --- Layout and Constraint Analysis Utilities ---

def get_auto_layout_properties(node_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts auto-layout properties from a node if it's an auto-layout frame.

    Args:
        node_dict (Dict[str, Any]): The node dictionary to check for auto-layout properties.

    Returns:
        Optional[Dict[str, Any]]: A dictionary of auto-layout properties if the node is an auto-layout
        frame, otherwise None.
    """
    if not isinstance(node_dict, dict):
        return None
        
    if node_dict.get('layoutMode') and node_dict.get('layoutMode') != "NONE":
        # layoutGrids were objects, now they are dicts. We can return them as is.
        layout_grids_list = node_dict.get('layoutGrids')
        if not isinstance(layout_grids_list, list): # Ensure it's a list or default to empty
            layout_grids_list = []
            
        return {
            "layoutMode": node_dict.get('layoutMode'),
            "primaryAxisSizingMode": node_dict.get('primaryAxisSizingMode'),
            "counterAxisSizingMode": node_dict.get('counterAxisSizingMode'),
            "primaryAxisAlignItems": node_dict.get('primaryAxisAlignItems'),
            "counterAxisAlignItems": node_dict.get('counterAxisAlignItems'),
            "paddingTop": node_dict.get('paddingTop'),
            "paddingBottom": node_dict.get('paddingBottom'),
            "paddingLeft": node_dict.get('paddingLeft'),
            "paddingRight": node_dict.get('paddingRight'),
            "itemSpacing": node_dict.get('itemSpacing'),
            "strokesIncludedInLayout": node_dict.get('strokesIncludedInLayout'),
            "itemReverseZIndex": node_dict.get('itemReverseZIndex'),
            "layoutGrids": layout_grids_list, # List of dicts
        }
    return None


def get_node_constraints(node_dict: Dict[str, Any]) -> Optional[Dict[str, Optional[str]]]:
    """
    Extracts the horizontal and vertical constraint types from a node_dict.

    Args:
        node_dict (Dict[str, Any]): The node dictionary to extract constraints from.

    Returns:
        Optional[Dict[str, Optional[str]]]: A dictionary with 'horizontal' and 'vertical' constraint types, or
        None if constraints are not found.
    """
    if not isinstance(node_dict, dict):
        return None
        
    constraints_dict = node_dict.get('constraints')
    if isinstance(constraints_dict, dict):
        return {
            "horizontal": constraints_dict.get('horizontal'),
            "vertical": constraints_dict.get('vertical'),
        }
    return None


# --- Prototyping Information Utilities ---

def get_node_prototype_interactions(node_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Retrieves all prototype interaction dictionaries defined directly on a node_dict.

    Args:
        node_dict (Dict[str, Any]): The node dictionary to get prototype interactions from.

    Returns:
        List[Dict[str, Any]]: A list of prototype interaction dictionaries.
    """
    interactions = []
    if not isinstance(node_dict, dict):
        return interactions
        
    interactions_list = node_dict.get('prototypeInteractions')
    if isinstance(interactions_list, list):
        for ia_dict in interactions_list:
            if isinstance(ia_dict, dict): # Ensure items in list are dicts
                interactions.append(ia_dict) # Dictionaries are returned as is
    return interactions


def get_canvas_flow_starting_points(canvas_node_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts flow starting point dictionaries from a canvas_node_dict.

    Args:
        canvas_node_dict (Dict[str, Any]): The canvas node dictionary to extract flow starting
                          points from.

    Returns:
        List[Dict[str, Any]]: A list of flow starting point dictionaries.
    """
    flows = []
    if not isinstance(canvas_node_dict, dict):
        return flows
        
    # Original check was hasattr(canvas_node, "flowStartingPoints")
    if 'flowStartingPoints' in canvas_node_dict:
        flows_list = canvas_node_dict.get('flowStartingPoints')
        if isinstance(flows_list, list):
            for flow_dict in flows_list:
                 # Original check was isinstance(flow_model, FlowStartingPoint)
                if isinstance(flow_dict, dict):
                    flows.append(flow_dict) # Dictionaries are returned as is
    return flows


def get_canvas_prototype_device(canvas_node_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts prototype device dictionary from a canvas_node_dict.

    Args:
        canvas_node_dict (Dict[str, Any]): The canvas node dictionary to extract the prototype
                          device from.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the prototype device, or None if not found.
    """
    if 'prototypeDevice' in canvas_node_dict:
        device_dict = canvas_node_dict.get('prototypeDevice')
    if isinstance(device_dict, dict):
        return device_dict # Dictionary is returned as is
    return None

def filter_none_values_from_dict(data_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Helper function to create a new dict excluding keys with None values.
    
    Args:
        data_dict (Optional[Dict[str, Any]]): The dictionary to filter.
        
    Returns:
        Dict[str, Any]: A new dictionary with None values removed.
    """
    if not data_dict or not isinstance(data_dict, dict):
        return {}
    return {k: v for k, v in data_dict.items() if v is not None}

def find_node_and_parent_recursive(
    nodes_list: List[Dict[str, Any]],
    target_id: str,
    parent_node: Optional[Dict[str, Any]] = None
) -> Optional[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
    """
    Helper function to find a node and its parent node recursively.

    Args:
        nodes_list (List[Dict[str, Any]]): The list of nodes to search through.
        target_id (str): The ID of the node to find.
        parent_node (Optional[Dict[str, Any]], optional): The parent of the current list of nodes. Defaults to None.

    Returns:
        Optional[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]: A tuple containing the found node and its parent, or None.
    """
    for node_dict in nodes_list:
        if not isinstance(node_dict, dict):
            continue  # Skip malformed entries, ensuring robustness

        if node_dict.get('id') == target_id:
            return node_dict, parent_node

        children_list = node_dict.get('children')
        if children_list and isinstance(children_list, list):
            # When recursing, the current node_dict becomes the parent for its children
            found_result = find_node_and_parent_recursive(
                children_list, target_id, parent_node=node_dict
            )
            if found_result:
                return found_result
    return None

def find_node_recursive(
    nodes_list: List[Dict[str, Any]], 
    node_id_to_find: str, 
    _visited_ids_in_current_path: Optional[Set[str]] = None # For cycle detection
) -> Optional[Dict[str, Any]]:
    """
    Recursively finds a node with a specific ID, with cycle detection.

    Args:
        nodes_list (List[Dict[str, Any]]): The list of nodes to search in.
        node_id_to_find (str): The ID of the node to find.
        _visited_ids_in_current_path (Optional[Set[str]], optional): A set of visited node IDs to prevent
                                      infinite loops in case of cycles. Defaults to None.

    Returns:
        Optional[Dict[str, Any]]: The found node dictionary, or None.
    """
    if _visited_ids_in_current_path is None:
        _visited_ids_in_current_path = set()

    for node in nodes_list:
        if not isinstance(node, dict):
            continue
        
        current_node_id = node.get('id')
        if not current_node_id or not isinstance(current_node_id, str): # Node must have a valid ID
            continue

        if current_node_id in _visited_ids_in_current_path: # Cycle detected for this path
            continue 
        
        if current_node_id == node_id_to_find:
            return node
        
        _visited_ids_in_current_path.add(current_node_id) # Add to visited set for current path

        children = node.get('children')
        if isinstance(children, list):
            found_in_children = find_node_recursive(children, node_id_to_find, _visited_ids_in_current_path)
            if found_in_children:
                return found_in_children
        
        _visited_ids_in_current_path.remove(current_node_id) # Backtrack: remove from visited set
        
    return None

def get_node_from_db(DB: Dict[str, Any], node_id_to_find: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a node by its ID from the database.

    Args:
        DB (Dict[str, Any]): The database dictionary.
        node_id_to_find (str): The ID of the node to find.

    Returns:
        Optional[Dict[str, Any]]: The node dictionary if found, otherwise None.
    """

    file_entry = get_current_file()
    if not file_entry:
        return None
    doc_root = file_entry['document']

    if doc_root.get('id') == node_id_to_find:
        return doc_root

    # Start each document search with a fresh visited set for find_node_recursive
    found_node = find_node_recursive(doc_root.get('children', []), node_id_to_find, set()) 
    if found_node:
        return found_node

    return None

def get_parent_of_node_from_db(DB: dict[str, Any], child_node_id: str) -> Optional[Dict[str, Any]]:
    """
    Finds the parent of a node by the child's ID in the database.

    Args:
        DB (dict[str, Any]): The database dictionary.
        child_node_id (str): The ID of the child node.

    Returns:
        Optional[Dict[str, Any]]: The parent node dictionary if found, otherwise None.
    """
    current_file = get_current_file()

    if not current_file:
        return None
    
    doc_root = current_file['document']
    q: List[Dict[str, Any]] = [doc_root]
    head = 0
    while head < len(q):
        current_parent_candidate = q[head]
        head += 1
        if not isinstance(current_parent_candidate, dict): continue

        if 'children' in current_parent_candidate and isinstance(current_parent_candidate.get('children'), list):
            for child in current_parent_candidate['children']:
                if isinstance(child, dict) and child.get('id') == child_node_id:
                    return current_parent_candidate
                if isinstance(child, dict) and child.get('children') is not None: # Add valid children containers to queue
                    q.append(child)
    return None


def get_node_dict_by_id(DB:Dict[str,Any], node_id: str) -> Optional[Dict]:
    """
    Finds a node dictionary by its ID within the database.

    Args:
        DB (Dict[str,Any]): The database dictionary.
        node_id (str): The ID of the node to find.

    Returns:
        Optional[Dict]: The node dictionary if found, otherwise None.
    """

    current_file = get_current_file()

    if not current_file:
        return None

    doc_node_data = current_file['document']
    if not doc_node_data or not isinstance(doc_node_data.get('children'), list):
        return None

    for canvas_data in doc_node_data['children']:
        if not (canvas_data and isinstance(canvas_data, dict)and isinstance(canvas_data.get('children'), list)):
            continue

        def find_in_list(nodes_list, target_id):
            for n_dict in nodes_list:
                if not isinstance(n_dict, dict): 
                    continue
                if n_dict.get('id') == target_id:
                    return n_dict
                if isinstance(n_dict.get('children'), list) and n_dict['children']:
                    found = find_in_list(n_dict['children'], target_id)
                    if found:
                        return found
            return None

        found_node = find_in_list(canvas_data['children'], node_id)
        if found_node:
            return found_node
    return None


def find_node_in_list_recursive(nodes_list: list, node_id: str) -> Optional[Dict]:
    """
    Recursively finds a node in a list of nodes.

    Args:
        nodes_list (list): The list of nodes to search in.
        node_id (str): The ID of the node to find.

    Returns:
        Optional[Dict]: The found node dictionary, or None.
    """
    for node in nodes_list:
        if not isinstance(node, dict): continue
        if node.get('id') == node_id:
            return node
        children = node.get('children')
        if isinstance(children, list):
            found_in_children = find_node_in_list_recursive(children, node_id)
            if found_in_children:
                return found_in_children
    return None

def node_exists_in_db(DB:Dict[str,Any], node_id: str) -> bool:
    """
    Checks if a node exists anywhere in the document hierarchy in the database.

    Args:
        DB (Dict[str,Any]): The database dictionary.
        node_id (str): The ID of the node to check for existence.

    Returns:
        bool: True if the node exists, False otherwise.
    """

    file_data = get_current_file() # type: ignore
    if not isinstance(file_data, dict): 
        return False

    doc_node = file_data.get('document')
    if not isinstance(doc_node, dict):
        return False

    if doc_node.get('id') == node_id:
        return True 

    canvases = doc_node.get('children', [])
    if not isinstance(canvases, list):
        return False 

    for canvas in canvases:
        if not isinstance(canvas, dict): continue
        if canvas.get('id') == node_id:
            return True 

        canvas_children = canvas.get('children')
        if isinstance(canvas_children, list):
            if find_node_in_list_recursive(canvas_children, node_id):
                return True
    return False

def find_node_dict_recursively_in_list(nodes_list: Optional[List[Dict[str, Any]]], node_id_to_find: str) -> Optional[Dict[str, Any]]:
    """
    Recursively finds a node dictionary in a list of nodes.

    Args:
        nodes_list (Optional[List[Dict[str, Any]]]): The list of nodes to search in.
        node_id_to_find (str): The ID of the node to find.

    Returns:
        Optional[Dict[str, Any]]: The node dictionary if found, otherwise None.
    """
    if not isinstance(nodes_list, list):
        return None
        
    for node_dict in nodes_list:
        if not isinstance(node_dict, dict):
            continue # Skip malformed entries in the children list
        if node_dict.get('id') == node_id_to_find:
            return node_dict
        
        # Recursively search children of this node
        found_in_children = find_node_dict_recursively_in_list(node_dict.get('children'), node_id_to_find)
        if found_in_children:
            return found_in_children
    return None

# Helper function to find a node dictionary by ID within the entire DB dictionary structure
def find_node_dict_in_DB(db_dict: Dict[str, Any], node_id_to_find: str) -> Optional[Dict[str, Any]]:
    """
    Finds a node dictionary by its ID within the entire database structure.

    Args:
        db_dict (Dict[str, Any]): The database dictionary.
        node_id_to_find (str): The ID of the node to find.

    Returns:
        Optional[Dict[str, Any]]: The node dictionary if found, otherwise None.
    """
    if not db_dict or not isinstance(db_dict, dict):
        return None

    file_dict = get_current_file()
    if not isinstance(file_dict, dict):
        return None # Skip malformed file entries
    
    doc_dict = file_dict.get('document')
    if isinstance(doc_dict, dict):
        # Check if the document node itself is the target
        if doc_dict.get('id') == node_id_to_find:
            return doc_dict
        
        # Check children of document (canvases)
        canvases_list = doc_dict.get('children')
        if isinstance(canvases_list, list):
            for canvas_dict in canvases_list:
                if not isinstance(canvas_dict, dict):
                    continue # Skip malformed canvas entries
                # Check if the canvas node itself is the target
                if canvas_dict.get('id') == node_id_to_find:
                    return canvas_dict
                
                # Recursively search children of this canvas
                node_in_canvas = find_node_dict_recursively_in_list(canvas_dict.get('children'), node_id_to_find)
                if node_in_canvas:
                    return node_in_canvas
    return None


def _build_node_map_recursive(node: Dict[str, Any], node_map: Dict[str, Dict[str, Any]]) -> None:
    """
    Recursively builds a map of node IDs to node objects.

    Args:
        node (Dict[str, Any]): The current node dictionary to process.
        node_map (Dict[str, Dict[str, Any]]): The dictionary to populate with node ID to node object mappings.
    """
    if not isinstance(node, dict): # Ensure node is a dictionary
        return

    node_id = node.get('id')
    if node_id and isinstance(node_id, str): # Node must have a string ID to be mapped
        node_map[node_id] = node
    
    # Recursively process children
    children = node.get('children')
    if isinstance(children, list):
        for child in children:
            # Ensure child is a dictionary before recursing to prevent errors with malformed data
            if isinstance(child, dict): 
                _build_node_map_recursive(child, node_map)
            # else: Malformed child data (e.g., child is not a dict). Silently skipping.

# Helper function to recursively find and collect component data.
def _collect_components_recursive(
    node: Dict[str, Any],
    collected_components: List[Dict[str, Any]],
    all_nodes_map: Dict[str, Dict[str, Any]]
) -> None:
    """
    Recursively collects component data from a node tree.

    Args:
        node (Dict[str, Any]): The current node to process.
        collected_components (List[Dict[str, Any]]): A list to append found component data to.
        all_nodes_map (Dict[str, Dict[str, Any]]): A map of all node IDs to node objects for efficient lookup.

    Raises:
        KeyError: If a component node is missing essential fields.
    """
    if not isinstance(node, dict): # Ensure node is a dictionary
        return

    node_type = node.get('type')

    if node_type == 'COMPONENT':
        # Extract essential fields. These must exist and be strings.
        component_id = node.get('id')
        component_key = node.get('key')
        component_name = node.get('name')
        parent_id = node.get('parentId')

        # Validate mandatory fields and their types
        if not component_id or not isinstance(component_id, str):
            raise KeyError(f"Component node (ID: {component_id or 'Unknown'}) is missing 'id' or 'id' is not a string.")
        if not component_key or not isinstance(component_key, str):
            raise KeyError(f"Component node '{component_id}' is missing 'key' or 'key' is not a string.")
        # A component name can be an empty string, but it must exist and be a string.
        if component_name is None or not isinstance(component_name, str):
            raise KeyError(f"Component node '{component_id}' is missing 'name' or 'name' is not a string.")
        if not parent_id or not isinstance(parent_id, str):
            raise KeyError(f"Component node '{component_id}' is missing 'parentId' or 'parentId' is not a string.")

        # Extract optional description. If present but not a string, treat as None.
        description = node.get('description')
        if description is not None and not isinstance(description, str):
            description = None 
            # Alternative: raise TypeError if strict type adherence for description is required.
            # For "Optional[str]", treating invalid type as absent is a common approach.

        # Determine componentSetId by checking the type of the parent node
        component_set_id: Optional[str] = None
        parent_node = all_nodes_map.get(parent_id)
        if parent_node and isinstance(parent_node, dict) and parent_node.get('type') == 'COMPONENT_SET':
            # The parent is a COMPONENT_SET, so this component is a variant.
            # The componentSetId is the ID of its parent (the component set itself).
            parent_component_set_node_id = parent_node.get('id')
            if parent_component_set_node_id and isinstance(parent_component_set_node_id, str):
                 component_set_id = parent_component_set_node_id
            # else: The parent COMPONENT_SET node is malformed (e.g., missing its own ID or ID is not a string).
            # In this case, componentSetId remains None, treating it as if not part of a valid set.

        collected_components.append(models.LocalComponent(
            id=component_id,
            key=component_key,
            name=component_name,
            description=description,
            componentSetId=component_set_id,
            parentId=parent_id,
        ).model_dump())

    # Recursively process children to find components at any level of the hierarchy
    children = node.get('children')
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict): # Ensure child is a dictionary before recursing
                _collect_components_recursive(child, collected_components, all_nodes_map)
            # else: Malformed child data. Silently skipping.



# Define constants for node types. These are typically part of a larger configuration
# or schema definition related to Figma integration.
_KNOWN_FIGMA_TYPES: Set[str] = {
    "DOCUMENT", "CANVAS", "FRAME", "GROUP", "VECTOR", "BOOLEAN_OPERATION",
    "STAR", "LINE", "ELLIPSE", "REGULAR_POLYGON", "RECTANGLE", "TEXT",
    "SLICE", "COMPONENT", "COMPONENT_SET", "INSTANCE", "PAGE", "SECTION",
}

_CONTAINER_NODE_TYPES: Set[str] = {
    "FRAME", "GROUP", "COMPONENT", "COMPONENT_SET", "INSTANCE", "PAGE", "SECTION", "CANVAS",
    "BOOLEAN_OPERATION", "DOCUMENT", # DOCUMENT is a container, typically the root.
}


def _recursive_scan_node_children(
    current_parent_id: str,
    types_to_match: Set[str],
    all_nodes_map: Dict[str, Dict[str, Any]],
    found_nodes_list: List[Dict[str, Any]]
) -> None:
    """
    Recursively scans children of a node for matching types.Modifies found_nodes_list in place.

    Args:
        current_parent_id (str): The ID of the parent node whose children are to be scanned.
        types_to_match (Set[str]): A set of node types to match.
        all_nodes_map (Dict[str, Dict[str, Any]]): A map of all node IDs to node objects.
        found_nodes_list (List[Dict[str, Any]]): A list to append found nodes to.
    """
    parent_node = all_nodes_map.get(current_parent_id)

    # If parent_node is not found (should not happen if called with a valid ID from all_nodes_map)
    # or has no 'children' key, there's nothing to scan further down this path.
    if not parent_node or 'children' not in parent_node:
        return

    # Ensure 'children' is iterable, defaulting to an empty list if it's None or missing.
    # If 'children' exists but is not a list (e.g., int), iteration will fail.
    # This failure will be caught by the general try-except in the main function.
    children_ids = parent_node.get('children', [])
    if not isinstance(children_ids, list):
        raise custom_errors.PluginError(
            f"Data inconsistency: 'children' attribute of node '{current_parent_id}' is not a list."
        )

    for child_id in children_ids:
        child_node = all_nodes_map.get(child_id)

        if not child_node:
            # Data integrity issue: a child ID is listed, but the node data is missing.
            raise custom_errors.PluginError(
                f"Data inconsistency: Child node with ID '{child_id}' "
                f"referenced by parent '{current_parent_id}' not found in DB."
            )

        child_node_type = child_node.get('type')
        
        # Check if this child's type is one of the types we're looking for.
        if child_node_type in types_to_match:
            child_node_name = child_node.get('name')
            
            # Ensure essential attributes are present for the output structure.
            if child_node_name is None:
                raise custom_errors.PluginError(
                    f"Node '{child_id}' (type: {child_node_type}) is missing 'name' attribute."
                )
            # child_node_type is confirmed by `in types_to_match`, so it's not None here.

            node_data = {
                'id': child_id,
                'name': child_node_name,
                'type': child_node_type,
                'parentId': current_parent_id  # The parent under which this node was found.
            }
            found_nodes_list.append(FoundNodeInfo(**node_data).model_dump())

        # If this child is itself a container type and has children, recurse.
        # Check 'children' key existence to avoid recursing on leaf container nodes without children.
        if child_node_type in _CONTAINER_NODE_TYPES and 'children' in child_node:
            _recursive_scan_node_children(
                child_id,  # This child becomes the parent for the next level of recursion
                types_to_match,
                all_nodes_map,
                found_nodes_list
            )



def _validate_rgba_color_dict(color_dict: Dict[str, Any], arg_name_prefix: str) -> None:
    """
    Validates the structure and values of an RGBA color dictionary.

    Args:
        color_dict (Dict[str, Any]): The RGBA color dictionary to validate.
        arg_name_prefix (str): A prefix for error messages to indicate the context.

    Raises:
        custom_errors.InvalidInputError: If the color dictionary is invalid.
        
    Returns:
        None
    """
    if not isinstance(color_dict, dict):
        raise custom_errors.InvalidInputError(f"{arg_name_prefix} color must be a dictionary.")
    
    required_keys = {'r', 'g', 'b', 'a'}
    for key in required_keys:
        if key not in color_dict:
            raise custom_errors.InvalidInputError(f"{arg_name_prefix} color missing '{key}' component.")
        
        val = color_dict[key]
        if not isinstance(val, (int, float)):
            raise custom_errors.InvalidInputError(f"{arg_name_prefix} color component '{key}' must be a number, got {type(val).__name__}.")
        if not (0.0 <= val <= 1.0):
            raise custom_errors.InvalidInputError(f"color component {key} must be between 0.0 and 1.0")

# Helper for validating Paint dictionary structure and values, and applying defaults
def _validate_and_process_paint_dict(paint_dict: Dict[str, Any], arg_name: str) -> Dict[str, Any]:
    """
    Validates a Paint dictionary and processes it by adding defaults.

    Args:
        paint_dict (Dict[str, Any]): The Paint dictionary to validate and process.
        arg_name (str): The argument name for error messages.

    Returns:
        Dict[str, Any]: The processed Paint dictionary with defaults applied.

    Raises:
        InvalidInputError: If the Paint dictionary is invalid.
    """
    if not isinstance(paint_dict, dict):
        raise custom_errors.InvalidInputError(f"{arg_name} must be a dictionary.")

    if 'type' not in paint_dict or not isinstance(paint_dict['type'], str):
        raise custom_errors.InvalidInputError(f"{arg_name} missing or invalid 'type' field.")

    # Create a copy to avoid modifying the input dictionary
    processed_paint = paint_dict.copy()

    if processed_paint['type'] == 'SOLID':
        if 'color' not in processed_paint:
            raise custom_errors.InvalidInputError(f"{arg_name} of type SOLID missing 'color' field.")
        _validate_rgba_color_dict(processed_paint['color'], f"{arg_name} 'SOLID'")
    # Add validation for other paint types (e.g., GRADIENT_LINEAR) if they become supported

    # Ensure default values for opacity and visibility if not provided
    if 'opacity' in processed_paint:
        opacity = processed_paint['opacity']
        if not isinstance(opacity, (int, float)):
            raise custom_errors.InvalidInputError(f"{arg_name} 'opacity' must be a number.")
        if not (0.0 <= opacity <= 1.0):
            raise custom_errors.InvalidInputError(f"{arg_name} 'opacity' ({opacity}) must be between 0.0 and 1.0.")
    else:
        processed_paint['opacity'] = 1.0 # Default opacity
        
    if 'visible' in processed_paint:
        if not isinstance(processed_paint['visible'], bool):
            raise custom_errors.InvalidInputError(f"{arg_name} 'visible' must be a boolean.")
    else:
        processed_paint['visible'] = True # Default visibility
        
    return processed_paint



def list_available_files() -> List[Dict]:
    """
    Retrieves and validates all available file data from the database,
    returning a list of fully structured FigmaFileComplete model instances.

    Note: This function now returns the complete data for each file,
    parsed into the FigmaFileComplete model, not just a summary.

    Returns:
        List[Dict]: A list of FigmaFileComplete model instances.
        Returns an empty list if 'files' key is not found, is not a list,
        or if no files can be successfully parsed.
    """
    files_data_list = DB.get("files")
    if not isinstance(files_data_list, list):
        # Optionally, log a warning or raise an error if the structure is unexpected
        print_log("Warning: 'files' key not found in DB or is not a list.")
        return []

    parsed_files: List[Dict] = []
    for i, file_data_dict in enumerate(files_data_list):
        if not isinstance(file_data_dict, dict):
            print_log(f"Warning: Item at index {i} in 'files' list is not a dictionary. Skipping.")
            continue

        try:
            # Validate and parse the dictionary into the FigmaFileComplete model
            # This assumes FigmaFileComplete and all its nested models are correctly defined
            # and imported.
            parsed_files.append(file_data_dict)
        except ValidationError as e:
            file_key = file_data_dict.get('fileKey', f"unknown_file_at_index_{i}")
            print_log(f"Validation Error for file '{file_key}':\n{e}\nSkipping this file.")
            # Depending on strictness, you might want to collect errors or re-raise
            continue
        except Exception as ex: # Catch any other unexpected errors during parsing
            file_key = file_data_dict.get('fileKey', f"unknown_file_at_index_{i}")
            print_log(f"An unexpected error occurred while processing file '{file_key}': {ex}\nSkipping this file.")
            continue
            
    return parsed_files

def _scan_descendants_recursively( # Can be a local helper or imported
    current_parent_node_obj: Dict[str, Any],
    types_to_match: Set[str],
    found_nodes_accumulator: List[Dict[str, Any]]
) -> None:
    """
    Recursively scans descendant nodes for matching types.

    Args:
        current_parent_node_obj (Dict[str, Any]): The parent node object to start scanning from.
        types_to_match (Set[str]): A set of node types to match.
        found_nodes_accumulator (List[Dict[str, Any]]): A list to accumulate found nodes.

    """
    parent_id_for_children = current_parent_node_obj.get('id')
    if current_parent_node_obj.get('type') not in _CONTAINER_NODE_TYPES: # Defensive check
        return

    children_node_objects = current_parent_node_obj.get('children')
    if not isinstance(children_node_objects, list):
        if 'children' in current_parent_node_obj and parent_id_for_children: # Check if key exists but not list
            raise custom_errors.PluginError(
                f"Data inconsistency: 'children' attribute of node '{parent_id_for_children}' is not a list."
            )
        return

    for child_obj in children_node_objects:
        if not isinstance(child_obj, dict):
            continue

        child_id = child_obj.get('id')
        child_type = child_obj.get('type')
        child_name = child_obj.get('name')

        if not child_id or not isinstance(child_id, str):
            print_log(f"Warning: Skipping child of '{parent_id_for_children}' due to missing/invalid ID.")
            continue
        
        if child_type in types_to_match:
            if child_name is None:
                raise custom_errors.PluginError(
                    f"Node '{child_id}' (type: {child_type}) is missing 'name' attribute."
                )
            if child_type is None: # Should be caught by "not in types_to_match" if types_to_match doesn't contain None
                 raise custom_errors.PluginError(
                    f"Node '{child_id}' (name: {child_name}) is missing 'type' attribute."
                )

            node_data = {
                'id': child_id,
                'name': child_name,
                'type': child_type,
                'parentId': parent_id_for_children
            }
            if FoundNodeInfo and ValidationError:
                try:
                    found_nodes_accumulator.append(FoundNodeInfo(**node_data).model_dump())
                except ValidationError as e:
                    raise custom_errors.PluginError(f"Data for node '{child_id}' failed FoundNodeInfo validation: {e}")
            else:
                found_nodes_accumulator.append(node_data)

        if child_type in _CONTAINER_NODE_TYPES:
            _scan_descendants_recursively(
                child_obj,
                types_to_match,
                found_nodes_accumulator
            )


# --- Utility function to create a file ---
def create_file(
    fileKey: str,
    name: str,
    projectId: str,
    role: str = "owner",
    editorType: str = "figma",
    linkAccess: str = "edit",
    thumbnailUrl: str = "https://example.com/thumbnails/new_default.png",
    custom_annotation_categories: list = None,
    make_current_file: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Creates a new file object and adds it to the DB.

    Args:
        fileKey (str): The unique key for the file.
        name (str): The name of the file.
        projectId (str): The ID of the project this file belongs to.
        role (str, optional): The user's role for this file. Defaults to "owner".
        editorType (str, optional): The type of editor. Defaults to "figma".
        linkAccess (str, optional): Default link access. Defaults to "edit".
        thumbnailUrl (str, optional): URL for the file thumbnail. Defaults to placeholder.
        custom_annotation_categories (list, optional): Optional list of custom annotation categories.
                                      If None, default empty list is used. Defaults to None.
        make_current_file (bool, optional): If True, sets this new file as the current_file_key. Defaults to False.

    Returns:
        Optional[Dict[str, Any]]: The created file dictionary if successful, None otherwise.
    """
    global DB

    # 1. Check if projectId exists
    if not any(p["projectId"] == projectId for p in DB.get("projects", [])):
        raise ValidationError(f"Error: Project with ID '{projectId}' not found.")

    # 2. Check if fileKey is unique
    if any(f["fileKey"] == fileKey for f in DB.get("files", [])):
        raise ValidationError(f"Error: File with key '{fileKey}' already exists.")

    # 3. Generate default canvas details
    default_canvas_id = f"canvas:{uuid.uuid4()}" # Unique ID for the first canvas
    current_time_iso = datetime.datetime.utcnow().isoformat() + "Z"

    new_file = {
        "fileKey": fileKey,
        "name": name,
        "lastModified": current_time_iso,
        "thumbnailUrl": thumbnailUrl,
        "version": str(int(datetime.datetime.utcnow().timestamp())), # Using timestamp as version
        "role": role,
        "editorType": editorType,
        "linkAccess": linkAccess,
        "schemaVersion": 0, 
        "projectId": projectId,
        "annotation_categories": custom_annotation_categories if custom_annotation_categories is not None else [],
        "default_connector_id": None, # No default connector initially
        "document": {
            "id": "0:0", # Standard document ID within a file
            "name": "Document",
            "type": "DOCUMENT",
            "scrollBehavior": "SCROLLS",
            "currentPageId": default_canvas_id, # Set current page to the new canvas
            "children": [
                {
                    "id": default_canvas_id,
                    "name": "Page 1", # Default name for the first page/canvas
                    "type": "CANVAS",
                    "scrollBehavior": "SCROLLS",
                    "backgroundColor": {"r": 1, "g": 1, "b": 1, "a": 1}, # Default white background
                    "prototypeStartNodeID": None,
                    "flowStartingPoints": [],
                    "prototypeDevice": { # Default device settings
                        "type": "NONE", # Or a common one like "DESKTOP" or "GOOGLE_PIXEL_6_PRO"
                        "rotation": "NONE",
                        "size": {"width": 1920, "height": 1080}, # Default desktop size
                        "presetIdentifier": "DESKTOP_1920x1080",
                    },
                    "exportSettings": [],
                    "children": [] # No elements on the canvas initially
                }
            ]
        },
        "globalVars": {
            "styles": {},
            "variables": {},
            "variableCollections": {}
        },
        "components": {},
        "componentSets": {}
    }

    DB["files"].append(new_file)
    print_log(f"File '{name}' (Key: {fileKey}) created successfully and added to project '{projectId}'.")

    if make_current_file:
        DB["current_file_key"] = fileKey
        # Clear the current selection since the new file doesn't have those nodes
        DB["current_selection_node_ids"] = []
        print_log(f"File '{name}' is now the current file.")

    return new_file

def get_current_file() -> Optional[Dict[str, Any]]:
    """
    Retrieves current file from DB

    This function searches through the 'files' list in the global DB object.
    It compares the 'fileKey' of each file with the provided current_file_key.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the current file's data, or None if not found.

    Raises:
        FigmaOperationError: If the current file key is not set in the database.
    """

    current_file_key = DB.get('current_file_key')
    if not current_file_key:
        raise custom_errors.FigmaOperationError("Current file key not found in DB.")
    
    for file in DB.get("files", []):
        # Safely access 'fileKey' and compare with the input
        if file.get("fileKey") == current_file_key:
            return file
    # Return None if the loop completes without finding a match
    return None

def find_annotation_in_db(self, annotation_id) -> Optional[Dict[str, Any]]:
    """
    Finds an annotation by its ID in the database.

    Args:
        self: The instance of the class.
        annotation_id (str): The ID of the annotation to find.

    Returns:
        Optional[Dict[str, Any]]: The annotation dictionary if found, otherwise None.
    """
    current_file = get_current_file()
    
    def find_recursive(node):
        if node.get("annotations"):
            for ann in node["annotations"]:
                if ann.get("annotationId") == annotation_id:
                    return ann
        if node.get("children"):
            for child in node["children"]:
                found = find_recursive(child)
                if found:
                    return found
        return None

    return find_recursive(current_file['document'])

def _rgba_to_hex(color: Dict[str, float]) -> str:
    """
    Converts an RGBA color dictionary to a #RRGGBB hex string.

    Args:
        color (Dict[str, float]): A dictionary with 'r', 'g', 'b' keys (and optionally 'a'),
               with values between 0.0 and 1.0.

    Returns:
        str: The hex color string.
    """
    if not all(k in color for k in ['r', 'g', 'b']):
        return "#000000" # Return a default color for malformed input
    try:
        r = int(color.get('r', 0) * 255)
        g = int(color.get('g', 0) * 255)
        b = int(color.get('b', 0) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, TypeError):
        return "#000000" # Return default on conversion error

def _collect_annotations_recursively(node: Dict[str, Any], all_annotations: List[Dict[str, Any]]) -> None:
    """
    Recursively collects all annotations from a node tree.

    Args:
        node (Dict[str, Any]): The node to start collecting annotations from.
        all_annotations (List[Dict[str, Any]]): A list to accumulate the found annotations.
    """
    if 'annotations' in node and isinstance(node.get('annotations'), list):
        for ann in node['annotations']:
            # Create a copy and add the parent nodeId for context, as required by the return spec
            if isinstance(ann, dict):
                ann_with_context = ann.copy()
                ann_with_context['nodeId'] = node.get('id')
                all_annotations.append(ann_with_context)

    for child in node.get('children', []):
        if isinstance(child, dict):
            _collect_annotations_recursively(child, all_annotations)

def create_project(project_id: str, name: str) -> Dict[str, str]:
    """
    Creates a new project with the given project_id and name.

    Args:
        project_id (str): The ID of the project.
        name (str): The name of the project.

    Returns:
        Dict[str, str]: The created project. Project dictionary can have the following keys:
        - projectId (str): The ID of the project.
        - name (str): The name of the project.
    
    Raises:
        ValueError: If the project name is empty or not a string.
        ValueError: If the project ID is empty or not a string.
        ValueError: If the project ID already exists.
    """
    
    if not isinstance(name, str):
        raise ValueError("Project name must be a string.")
    if not name.strip():
        raise ValueError("Project name cannot be empty.")

    if not isinstance(project_id, str):
        raise ValueError("Project ID must be a string.")
    if not project_id.strip():
        raise ValueError("Project ID cannot be empty.")
    
    for projects in DB['projects']:
        if projects['projectId'] == project_id:
            raise ValueError(f"Project with ID '{project_id}' already exists.")

    new_project = {
        'projectId': project_id,
        'name': name
    }
    
    DB["projects"].append(new_project)

    return new_project
