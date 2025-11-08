from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors
from .SimulationEngine import utils 
from .SimulationEngine import models

@tool_spec(
    spec={
        'name': 'set_layout_mode',
        'description': """ Set the layout mode and wrap behavior of a frame in Figma.
        
        This function sets the layout mode for a specified Figma frame node, identified by `node_id`.
        The `layout_mode` parameter determines the primary layout direction and accepts 'NONE', 'HORIZONTAL', or 'VERTICAL'.
        The `layout_wrap` parameter is optional and defines the wrap behavior for auto-layout, accepting 'NO_WRAP' or 'WRAP'.
        It is only applicable if `layout_mode` is 'HORIZONTAL' or 'VERTICAL', and defaults to 'NO_WRAP' if omitted in these cases.
        When `layout_mode` is 'NONE', the `layoutWrap` property is always set to 'NO_WRAP' regardless of the `layout_wrap` parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'node_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the Figma node (frame) whose layout mode is to be set.'
                },
                'layout_mode': {
                    'type': 'string',
                    'description': 'The layout mode to apply. Must be one of: "NONE", "HORIZONTAL", "VERTICAL".'
                },
                'layout_wrap': {
                    'type': 'string',
                    'description': """ The wrap behavior for auto-layout. Must be one of: "NO_WRAP", "WRAP" if provided. This parameter is only applicable if
                    `layout_mode` is 'HORIZONTAL' or 'VERTICAL'. If omitted for these modes, it defaults to 'NO_WRAP'.
                    When `layout_mode` is 'NONE', this parameter is ignored and the `layoutWrap` property is set to 'NO_WRAP'. """
                }
            },
            'required': [
                'node_id',
                'layout_mode'
            ]
        }
    }
)
def set_layout_mode(node_id: str, layout_mode: str, layout_wrap: Optional[str] = None) -> Dict[str, Any]:
    """Set the layout mode and wrap behavior of a frame in Figma.

    This function sets the layout mode for a specified Figma frame node, identified by `node_id`.
    The `layout_mode` parameter determines the primary layout direction and accepts 'NONE', 'HORIZONTAL', or 'VERTICAL'.
    The `layout_wrap` parameter is optional and defines the wrap behavior for auto-layout, accepting 'NO_WRAP' or 'WRAP'.
    It is only applicable if `layout_mode` is 'HORIZONTAL' or 'VERTICAL', and defaults to 'NO_WRAP' if omitted in these cases.
    When `layout_mode` is 'NONE', the `layoutWrap` property is always set to 'NO_WRAP' regardless of the `layout_wrap` parameter.

    Args:
        node_id (str): The unique identifier of the Figma node (frame) whose layout mode is to be set.
        layout_mode (str): The layout mode to apply. Must be one of: "NONE", "HORIZONTAL", "VERTICAL".
        layout_wrap (Optional[str]): The wrap behavior for auto-layout. Must be one of: "NO_WRAP", "WRAP" if provided. This parameter is only applicable if
            `layout_mode` is 'HORIZONTAL' or 'VERTICAL'. If omitted for these modes, it defaults to 'NO_WRAP'.
            When `layout_mode` is 'NONE', this parameter is ignored and the `layoutWrap` property is set to 'NO_WRAP'.

    Returns:
        Dict[str, Any]: An empty dictionary.

    Raises:
        NodeNotFoundError: Raised if the node with the given `node_id` does not exist.
        NodeTypeError: Raised if the node identified by `node_id` is not a frame or does not support auto-layout modification.
        InvalidInputError: Raised if the `layout_mode` value is not a valid mode or if `layout_wrap`
            (when provided) is not a valid wrap behavior, or if `layout_wrap` is specified when `layout_mode` is 'NONE'.
        PluginError: Raised if an internal error occurs within Figma while attempting to apply the layout mode.
    """

    # --- Input Argument Type Validation ---
    if not isinstance(node_id, str):
        raise custom_errors.InvalidInputError("node_id must be a string.")
    if not node_id.strip():
        raise custom_errors.InvalidInputError("node_id must be a non-empty string.")
        
    if not isinstance(layout_mode, str):
        raise custom_errors.InvalidInputError("layout_mode must be a string.")
    if layout_wrap is not None and not isinstance(layout_wrap, str):
        raise custom_errors.InvalidInputError("layout_wrap must be a string if provided, or None.")

    # Validate layout_mode value against LayoutModeEnum
    try:
        valid_layout_mode = models.LayoutModeEnum(layout_mode)
    except ValueError:
        valid_modes_str = [e.value for e in models.LayoutModeEnum]
        raise custom_errors.InvalidInputError(
            f"Invalid layout_mode: '{layout_mode}'. Accepted values are {sorted(valid_modes_str)}."
        )

    # Validate layout_wrap value if it has been provided
    valid_layout_wrap = None
    if layout_wrap is not None:
        try:
            valid_layout_wrap = models.LayoutWrapEnum(layout_wrap)
        except ValueError:
            valid_wraps_str = [e.value for e in models.LayoutWrapEnum]
            raise custom_errors.InvalidInputError(
                f"Invalid layout_wrap: '{layout_wrap}'. Accepted values are {sorted(valid_wraps_str)}."
            )

    # Validate applicability of layout_wrap based on layout_mode
    if valid_layout_mode == models.LayoutModeEnum.NONE and valid_layout_wrap is not None:
        raise custom_errors.InvalidInputError(
            "layout_wrap parameter is not applicable and cannot be specified when layout_mode is 'NONE'."
        )

    # --- Node Retrieval and Validation ---
    node = utils.find_node_dict_in_DB(DB, node_id)

    if node is None:
        raise custom_errors.NodeNotFoundError(f"Node with ID '{node_id}' not found.")

    if not isinstance(node, dict):
        raise custom_errors.PluginError( 
            f"Data for node ID '{node_id}' is not in the expected dictionary format. Type found: {type(node).__name__}."
        )

    # --- Node Type Validation ---
    node_type = node.get('type')
    expected_node_type_for_layout = "FRAME" 
    
    if node_type != expected_node_type_for_layout: 
        actual_type_str = str(node_type) if node_type is not None else "type field missing"
        raise custom_errors.NodeTypeError(
            f"Node with ID '{node_id}' must be a {expected_node_type_for_layout} to set layout mode. Actual type: {actual_type_str}."
        )

    # Apply layout settings to the node.
    node['layoutMode'] = valid_layout_mode.value 

    if valid_layout_mode == models.LayoutModeEnum.HORIZONTAL or valid_layout_mode == models.LayoutModeEnum.VERTICAL:
        node['layoutWrap'] = valid_layout_wrap.value if valid_layout_wrap is not None else models.LayoutWrapEnum.NO_WRAP.value
    else: 
        node['layoutWrap'] = models.LayoutWrapEnum.NO_WRAP.value 
    
    return {}
