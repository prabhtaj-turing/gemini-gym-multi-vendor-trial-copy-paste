"""
Figma API Simulation

This package provides a simulation of the Figma API functionality.
It allows for fetching figma files and basic operations in a simulated environment.
"""

from .SimulationEngine.db import DB, load_state, save_state
from typing import Optional, Dict, Any, List, Tuple

from .SimulationEngine.utils import filter_none_values_from_dict
from .SimulationEngine.custom_errors import NotFoundError, InvalidInputError, DownloadError

from . import file_management
from . import node_editing
from . import node_creation
from . import document_context
from . import node_reading
from . import annotation_operations
from . import layout_operations

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from figma.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    'get_figma_data':'figma.file_management.get_figma_data',
    'download_figma_images':'figma.file_management.download_figma_images',
    'move_node':'figma.node_editing.move_node',
    'clone_node':'figma.node_creation.clone_node',
    'resize_node':'figma.node_editing.resize_node',
    'delete_node':'figma.node_editing.delete_node',
    'get_styles':'figma.document_context.get_styles',
    'create_rectangle':'figma.node_creation.create_rectangle',
    'set_fill_color':'figma.node_editing.set_fill_color',
    'delete_multiple_nodes':'figma.node_editing.delete_multiple_nodes',
    'set_text_content':'figma.node_editing.set_text_content',
    'set_stroke_color':'figma.node_editing.set_stroke_color',
    'set_layout_mode':'figma.layout_operations.set_layout_mode',
    'get_local_components': 'figma.document_context.get_local_components',
    'scan_nodes_by_types':'figma.node_reading.scan_nodes_by_types',
    'get_selection':'figma.node_reading.get_selection',
    'get_node_info':'figma.node_reading.get_node_info',
    'get_annotations':'figma.annotation_operations.get_annotations',
    'set_annotation':'figma.annotation_operations.set_annotation',
    'create_frame':'figma.node_creation.create_frame',
    'set_current_file':'figma.file_management.set_current_file',
    'create_text':'figma.node_creation.create_text',
}

# Separate utils map for utility functions
_utils_map = {
    'get_file_by_key': 'figma.SimulationEngine.utils.get_file_by_key',
    'find_node_by_id': 'figma.SimulationEngine.utils.find_node_by_id',
    'find_nodes_by_type': 'figma.SimulationEngine.utils.find_nodes_by_type',
    'find_nodes_by_name': 'figma.SimulationEngine.utils.find_nodes_by_name',
    'find_direct_parent_of_node': 'figma.SimulationEngine.utils.find_direct_parent_of_node',
    'get_node_text_content': 'figma.SimulationEngine.utils.get_node_text_content',
    'get_node_fill_colors': 'figma.SimulationEngine.utils.get_node_fill_colors',
    'get_node_dimensions': 'figma.SimulationEngine.utils.get_node_dimensions',
    'is_node_visible': 'figma.SimulationEngine.utils.is_node_visible',
    'get_instance_main_component_id': 'figma.SimulationEngine.utils.get_instance_main_component_id',
    'get_instance_variant_properties': 'figma.SimulationEngine.utils.get_instance_variant_properties',
    'get_component_property_definitions': 'figma.SimulationEngine.utils.get_component_property_definitions',
    'get_resolved_style_for_node': 'figma.SimulationEngine.utils.get_resolved_style_for_node',
    'get_variable_value_for_mode': 'figma.SimulationEngine.utils.get_variable_value_for_mode',
    'get_default_mode_id_for_variable': 'figma.SimulationEngine.utils.get_default_mode_id_for_variable',
    'get_auto_layout_properties': 'figma.SimulationEngine.utils.get_auto_layout_properties',
    'get_node_constraints': 'figma.SimulationEngine.utils.get_node_constraints',
    'get_node_prototype_interactions': 'figma.SimulationEngine.utils.get_node_prototype_interactions',
    'get_canvas_flow_starting_points': 'figma.SimulationEngine.utils.get_canvas_flow_starting_points',
    'get_canvas_prototype_device': 'figma.SimulationEngine.utils.get_canvas_prototype_device',
    'filter_none_values_from_dict': 'figma.SimulationEngine.utils.filter_none_values_from_dict',
    'find_node_and_parent_recursive': 'figma.SimulationEngine.utils.find_node_and_parent_recursive',
    'find_node_recursive': 'figma.SimulationEngine.utils.find_node_recursive',
    'get_node_from_db': 'figma.SimulationEngine.utils.get_node_from_db',
    'get_parent_of_node_from_db': 'figma.SimulationEngine.utils.get_parent_of_node_from_db',
    'get_node_dict_by_id': 'figma.SimulationEngine.utils.get_node_dict_by_id',
    'find_node_in_list_recursive': 'figma.SimulationEngine.utils.find_node_in_list_recursive',
    'node_exists_in_db': 'figma.SimulationEngine.utils.node_exists_in_db',
    'find_node_dict_recursively_in_list': 'figma.SimulationEngine.utils.find_node_dict_recursively_in_list',
    'find_node_dict_in_DB': 'figma.SimulationEngine.utils.find_node_dict_in_DB',
    'list_available_files': 'figma.SimulationEngine.utils.list_available_files',
    'create_file': 'figma.SimulationEngine.utils.create_file',
    'create_project': 'figma.SimulationEngine.utils.create_project',
    'get_current_file': 'figma.SimulationEngine.utils.get_current_file',
    'find_annotation_in_db': 'figma.SimulationEngine.utils.find_annotation_in_db',
    '_scan_descendants_recursively': 'figma.SimulationEngine.utils._scan_descendants_recursively',
    '_build_node_map_recursive': 'figma.SimulationEngine.utils._build_node_map_recursive',
    '_collect_components_recursive': 'figma.SimulationEngine.utils._collect_components_recursive',
    '_recursive_scan_node_children': 'figma.SimulationEngine.utils._recursive_scan_node_children',
    '_validate_and_process_paint_dict': 'figma.SimulationEngine.utils._validate_and_process_paint_dict',
    '_rgba_to_hex': 'figma.SimulationEngine.utils._rgba_to_hex',
    '_collect_annotations_recursively': 'figma.SimulationEngine.utils._collect_annotations_recursively',
}

# You could potentially generate this map dynamically by inspecting the package,
# but that adds complexity and potential fragility. A manual map is often safer.
# --- Implement __getattr__ ---

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())