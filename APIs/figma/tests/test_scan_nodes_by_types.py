# APIs/figma/tests/test_scan_nodes_by_types.py

import unittest
import copy
from unittest.mock import patch
from pydantic import BaseModel, ValidationError

from ..SimulationEngine import custom_errors
from figma import DB
from ..node_reading import scan_nodes_by_types, _KNOWN_FIGMA_TYPES, _CONTAINER_NODE_TYPES

from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestScanNodesByTypes(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.file_key_1 = "testFileKey1"

        # Define nodes hierarchically
        self.deep_text_node = {'id': 'deep_text', 'name': 'Deep Text', 'type': 'TEXT', 'parentId': 'frame2_child_frame'}
        self.frame2_child_frame_node = {'id': 'frame2_child_frame', 'name': 'Nested Frame', 'type': 'FRAME', 'parentId': 'frame2', 'children': [self.deep_text_node]}
        self.text2_node = {'id': 'text2', 'name': 'Text Two', 'type': 'TEXT', 'parentId': 'frame2'}

        self.rect2_node = {'id': 'rect2', 'name': 'Rectangle Two', 'type': 'RECTANGLE', 'parentId': 'group1'}
        self.ellipse1_node = {'id': 'ellipse1', 'name': 'Ellipse One', 'type': 'ELLIPSE', 'parentId': 'group1'}
        self.group1_node = {'id': 'group1', 'name': 'Group One', 'type': 'GROUP', 'parentId': 'frame1', 'children': [self.rect2_node, self.ellipse1_node]}
        self.rect1_node = {'id': 'rect1', 'name': 'Rectangle One', 'type': 'RECTANGLE', 'parentId': 'frame1'}
        self.text1_node = {'id': 'text1', 'name': 'Text One', 'type': 'TEXT', 'parentId': 'frame1'}

        self.frame1_node = {'id': 'frame1', 'name': 'Frame One', 'type': 'FRAME', 'parentId': 'canvas1', 'children': [self.rect1_node, self.text1_node, self.group1_node]}
        self.frame2_node = {'id': 'frame2', 'name': 'Frame Two', 'type': 'FRAME', 'parentId': 'canvas1', 'children': [self.text2_node, self.frame2_child_frame_node]}

        self.text_node_root_canvas_child = {'id': 'text_node_root_canvas_child', 'name': 'Text Node Canvas Child', 'type': 'TEXT', 'parentId': 'canvas1'}
        self.empty_frame_node = {'id': 'empty_frame', 'name': 'Empty Frame', 'type': 'FRAME', 'parentId': 'canvas1', 'children': []}
        
        self.frame_with_malformed_child_entry = {'id': 'frame_with_malformed_child_entry', 'name': 'Frame Malformed Child Entry', 'type': 'FRAME', 'parentId': 'canvas1', 'children': ["not_a_dict_child"]}

        self.frame_with_cycle2_node = {'id': 'frame_with_cycle2', 'name': 'Frame Cycle 2', 'type': 'FRAME', 'parentId': 'frame_with_cycle1'}
        self.frame_with_cycle1_node = {'id': 'frame_with_cycle1', 'name': 'Frame Cycle 1', 'type': 'FRAME', 'parentId': 'canvas1', 'children': [self.frame_with_cycle2_node]}
        self.frame_with_cycle2_node['children'] = [self.frame_with_cycle1_node] 

        self.no_name_rect_node = {'id': 'no_name_rect', 'name': None, 'type': 'RECTANGLE', 'parentId': 'frame_with_no_name_child'}
        self.frame_with_no_name_child_node = {'id': 'frame_with_no_name_child', 'name': 'Frame with No-Name Child', 'type': 'FRAME', 'parentId': 'canvas1', 'children': [self.no_name_rect_node]}
        
        self.frame_with_bad_children_attr_node = {'id': 'frame_with_bad_children_attr', 'name': 'Frame with Bad Children Attr', 'type': 'FRAME', 'parentId': 'canvas1', 'children': "not-a-list"}
        
        self.frame_lacking_children_key_node_data = {'id': 'frame_lacking_children_key_attr', 'name': 'Frame Lacking Children Key Attribute', 'type': 'FRAME', 'parentId': 'canvas1'}

        self.type_none_child_node_data = {'id': 'child_with_type_none', 'name': 'Child Type None', 'type': None, 'parentId': 'parent_frame_for_none_type_child_test'}
        self.valid_rect_for_none_test_node_data = {'id': 'valid_rect_in_same_frame_for_none', 'name': 'Valid Rect for None Test', 'type': 'RECTANGLE', 'parentId': 'parent_frame_for_none_type_child_test'}
        self.parent_for_type_none_node_data = {'id': 'parent_frame_for_none_type_child_test', 'name': 'Parent For Type None Test', 'type': 'FRAME', 'parentId': 'canvas1', 'children': [self.type_none_child_node_data, self.valid_rect_for_none_test_node_data]}

        self.canvas1_node = {'id': 'canvas1', 'name': 'Canvas 1', 'type': 'CANVAS', 'parentId': 'doc1',
                           'children': [
                               self.frame1_node, self.frame2_node, self.text_node_root_canvas_child,
                               self.empty_frame_node, self.frame_with_malformed_child_entry,
                               self.frame_with_cycle1_node, self.frame_with_no_name_child_node,
                               self.frame_with_bad_children_attr_node,
                               self.frame_lacking_children_key_node_data, # Node that lacks 'children' key
                               self.parent_for_type_none_node_data # Node that has a child with type: None
                           ]}
        self.document1_node = {'id': 'doc1', 'name': 'Document 1', 'type': 'DOCUMENT', 'children': [self.canvas1_node]}

        DB['files'] = [{"fileKey": self.file_key_1, "name": "Test File 1", "document": self.document1_node}]
        DB['current_file_key'] = self.file_key_1

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Success Cases ---
    def test_scan_single_type_found_multiple_depths(self):
        result = scan_nodes_by_types(node_id='frame1', types=['RECTANGLE'])
        expected = [
            {'id': 'rect1', 'name': 'Rectangle One', 'type': 'RECTANGLE', 'parentId': 'frame1'},
            {'id': 'rect2', 'name': 'Rectangle Two', 'type': 'RECTANGLE', 'parentId': 'group1'},
        ]
        self.assertCountEqual(result, expected)

    def test_scan_multiple_types_found(self):
        result = scan_nodes_by_types(node_id='frame1', types=['RECTANGLE', 'TEXT'])
        expected = [
            {'id': 'rect1', 'name': 'Rectangle One', 'type': 'RECTANGLE', 'parentId': 'frame1'},
            {'id': 'text1', 'name': 'Text One', 'type': 'TEXT', 'parentId': 'frame1'},
            {'id': 'rect2', 'name': 'Rectangle Two', 'type': 'RECTANGLE', 'parentId': 'group1'},
        ]
        self.assertCountEqual(result, expected)

    def test_scan_type_present_in_children(self):
        result = scan_nodes_by_types(node_id='frame1', types=['ELLIPSE'])
        expected = [{'id': 'ellipse1', 'name': 'Ellipse One', 'type': 'ELLIPSE', 'parentId': 'group1'}]
        self.assertCountEqual(result, expected)

    def test_scan_type_completely_absent_in_hierarchy(self):
        result = scan_nodes_by_types(node_id='frame1', types=['COMPONENT'])
        self.assertEqual(result, [])

    def test_scan_container_with_no_matching_children_of_type(self):
        result = scan_nodes_by_types(node_id='frame2', types=['RECTANGLE'])
        self.assertEqual(result, [])

    def test_scan_empty_container_node(self):
        result = scan_nodes_by_types(node_id='empty_frame', types=['TEXT'])
        self.assertEqual(result, [])

    def test_scan_deeply_nested_nodes(self):
        # Isolate this test from cyclic data that might be encountered by _scan_descendants_recursively
        original_canvas_children = list(self.canvas1_node['children'])
        self.canvas1_node['children'] = [
            child for child in original_canvas_children if child.get('id') not in [
                'frame_with_cycle1', # Exclude cycle starter
                'frame_with_malformed_child_entry', # Exclude other error causers not relevant here
                'frame_with_bad_children_attr',
                'frame_lacking_children_key_attr',
                'parent_frame_for_none_type_child_test'
            ]
        ]
        # Ensure frame1 and frame2 (which contain the nested text) are present
        if not any(c.get('id') == 'frame1' for c in self.canvas1_node['children']): self.canvas1_node['children'].append(self.frame1_node)
        if not any(c.get('id') == 'frame2' for c in self.canvas1_node['children']): self.canvas1_node['children'].append(self.frame2_node)
        if not any(c.get('id') == 'text_node_root_canvas_child' for c in self.canvas1_node['children']): self.canvas1_node['children'].append(self.text_node_root_canvas_child)


        try:
            result = scan_nodes_by_types(node_id='canvas1', types=['TEXT'])
            expected = [
                {'id': 'text_node_root_canvas_child', 'name': 'Text Node Canvas Child', 'type': 'TEXT', 'parentId': 'canvas1'},
                {'id': 'text1', 'name': 'Text One', 'type': 'TEXT', 'parentId': 'frame1'},
                {'id': 'text2', 'name': 'Text Two', 'type': 'TEXT', 'parentId': 'frame2'},
                {'id': 'deep_text', 'name': 'Deep Text', 'type': 'TEXT', 'parentId': 'frame2_child_frame'},
            ]
            self.assertCountEqual(result, expected)
        finally:
            self.canvas1_node['children'] = original_canvas_children


    def test_scan_target_node_itself_not_returned(self):
        original_frame1_children = list(self.frame1_node.get('children', []))
        child_frame_temp_id = 'child_frame_of_frame1_temp'
        child_frame_temp_node = {'id': child_frame_temp_id, 'name': 'Child Frame of Frame1 Temp', 'type': 'FRAME', 'parentId': 'frame1', 'children': []}
        
        # Ensure frame1_node is correctly referenced from self
        self.frame1_node['children'].append(child_frame_temp_node)
        try:
            result = scan_nodes_by_types(node_id='frame1', types=['FRAME'])
            expected = [{'id': child_frame_temp_id, 'name': 'Child Frame of Frame1 Temp', 'type': 'FRAME', 'parentId': 'frame1'}]
            self.assertCountEqual(result, expected, "Should find child frames, not the scanned node itself.")
        finally:
            # Clean up: remove the temporarily added child
            self.frame1_node['children'] = [child for child in self.frame1_node['children'] if child.get('id') != child_frame_temp_id]


    def test_scan_with_cycles_first_part_invalid_type(self):
        example_known_types = ", ".join(list(_KNOWN_FIGMA_TYPES)[:3]) + ", etc."
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Unrecognized node type 'NON_EXISTENT_TYPE_FOR_CYCLE_TEST' in 'types' list. Known types include: {example_known_types}",
            node_id='frame_with_cycle1',
            types=['NON_EXISTENT_TYPE_FOR_CYCLE_TEST']
        )

    def test_scan_with_cycles_leads_to_plugin_error(self):
        # This test assumes _scan_descendants_recursively does NOT have cycle detection
        # and will hit Python's recursion limit.
        # get_node_from_db should find 'frame_with_cycle1' successfully due to its own cycle detection.
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.PluginError,
            expected_message="An unexpected error occurred during node scanning: maximum recursion depth exceeded while calling a Python object",
            node_id='frame_with_cycle1', 
            types=['FRAME'] 
        )

    # --- Error Cases ---
    def test_node_not_found_error(self):
        # Assumes get_node_from_db (with cycle detection) works and returns None for this.
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.NodeNotFoundError,
            expected_message="Node with ID 'non_existent_node' not found in any file in the DB.",
            node_id='non_existent_node',
            types=['TEXT']
        )

    def test_node_type_error_for_non_container_scan_root(self):
        example_containers = ", ".join(list(_CONTAINER_NODE_TYPES)[:3]) + ", etc."
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.NodeTypeError,
            expected_message=f"Node 'text1' (type: 'TEXT') cannot contain child nodes. Scanning requires a container type like {example_containers}.",
            node_id='text1', 
            types=['RECTANGLE']
        )

    def test_invalid_input_error_empty_types_list(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Argument 'types' list cannot be empty.",
            node_id='frame1', types=[]
        )

    def test_invalid_input_error_unrecognized_node_type(self):
        example_known_types = ", ".join(list(_KNOWN_FIGMA_TYPES)[:3]) + ", etc."
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Unrecognized node type 'TOTALLY_INVALID_TYPE_STRING' in 'types' list. Known types include: {example_known_types}",
            node_id='frame1', types=['RECTANGLE', 'TOTALLY_INVALID_TYPE_STRING']
        )
    
    def test_invalid_input_error_all_types_unrecognized(self):
        example_known_types = ", ".join(list(_KNOWN_FIGMA_TYPES)[:3]) + ", etc."
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Unrecognized node type 'TOTALLY_BOGUS_TYPE' in 'types' list. Known types include: {example_known_types}",
            node_id='frame1', types=['TOTALLY_BOGUS_TYPE', 'ANOTHER_ONE']
        )

    # --- ValidationErrors ---
    def test_validation_error_node_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'node_id' must be a string.",
            node_id=123, types=['TEXT']
        )

    def test_validation_error_node_id_is_none(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'node_id' must be a string.",
            node_id=None, types=['TEXT']
        )

    def test_validation_error_node_id_is_empty(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'node_id' cannot be empty.",
            node_id="", types=['TEXT']
        )

    def test_validation_error_types_not_list(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'types' must be a list.",
            node_id='frame1', types="TEXT"
        )

    def test_validation_error_types_is_none(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'types' must be a list.",
            node_id='frame1', types=None
        )

    def test_validation_error_types_list_contains_non_string(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="All elements in 'types' list must be strings.",
            node_id='frame1', types=['TEXT', 123]
        )

    def test_validation_error_types_list_contains_empty_string(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Elements in 'types' list cannot be empty strings.",
            node_id='frame1', types=['TEXT', '']
        )

    # --- PluginError Cases ---
    def test_plugin_error_node_missing_name(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.PluginError,
            expected_message="Node 'no_name_rect' (type: RECTANGLE) is missing 'name' attribute.",
            node_id='frame_with_no_name_child', 
            types=['RECTANGLE']
        )

    @patch('figma.node_reading.utils._scan_descendants_recursively')
    def test_plugin_error_on_pydantic_validation_error(self, mock_scan_recursive):
        """Test that a Pydantic validation error from the recursive scan is caught and wrapped."""
        # Create a pydantic validation error to be raised by the mock
        class DummyModel(BaseModel):
            required_field: str
        
        validation_error = None
        try:
            DummyModel() # This will raise a validation error because required_field is missing
        except ValidationError as e:
            validation_error = e

        self.assertIsNotNone(validation_error, "Failed to create a mock validation error for the test.")

        mock_scan_recursive.side_effect = validation_error
        
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.PluginError,
            expected_message=f"An unexpected error occurred during node scanning: {validation_error}",
            node_id='frame1', # This node must be a valid container to pass initial checks
            types=['TEXT']
        )

    def test_plugin_error_children_attr_not_list(self):
        self.assert_error_behavior(
            func_to_call=scan_nodes_by_types,
            expected_exception_type=custom_errors.PluginError,
            expected_message="Data inconsistency: 'children' attribute of node 'frame_with_bad_children_attr' is not a list.",
            node_id='frame_with_bad_children_attr',
            types=['TEXT']
        )
        
    def test_plugin_error_db_not_dict(self): 
        with patch('figma.node_reading.DB', "not_a_dict") as actual_mock_db_replacement:
            self.assert_error_behavior(
                func_to_call=scan_nodes_by_types,
                expected_exception_type=custom_errors.PluginError,
                expected_message="Internal error: DB object is not a dictionary.",
                node_id='frame1', # Argument for scan_nodes_by_types
                types=['TEXT']    # Argument for scan_nodes_by_types
            )


    def test_plugin_error_db_files_key_missing(self):
        # get_node_from_db returns None if 'files' is missing.
        # scan_nodes_by_types then raises NodeNotFoundError.
        original_files = DB.pop('files', None)
        try:
            self.assert_error_behavior(
                func_to_call=scan_nodes_by_types,
                expected_exception_type=custom_errors.NodeNotFoundError, 
                expected_message="Node with ID 'frame1' not found in any file in the DB.", # As start_node_obj will be None
                node_id='frame1', types=['TEXT']
            )
        finally:
            if original_files is not None:
                DB['files'] = original_files


    def test_plugin_error_start_node_missing_type(self):
        node_no_type_id = 'frame_no_type_temp'
        _malformed_node = {'id': node_no_type_id, 'name': 'Frame No Type', 'parentId': 'canvas1'}
        # Note: _malformed_node has no 'children' key. If it's scanned, _scan_descendants_recursively will just return for it.
        # The error is about the start_node_obj itself missing 'type'.
        
        # Add this malformed node to the DB structure for get_node_from_db to find it.
        # It needs to be findable. Add it as a child of canvas1 for this test.
        original_canvas_children = list(self.canvas1_node['children'])
        self.canvas1_node['children'].append(_malformed_node)
        try:
            self.assert_error_behavior(
                func_to_call=scan_nodes_by_types,
                expected_exception_type=custom_errors.PluginError,
                expected_message=f"Starting node '{node_no_type_id}' is missing 'type' attribute.",
                node_id=node_no_type_id,
                types=['TEXT']
            )
        finally:
            self.canvas1_node['children'] = original_canvas_children

    # --- New Tests for Increased Coverage ---
    def test_scan_start_node_is_container_but_lacks_children_key(self):
        node_id_to_test = 'frame_lacking_children_key_attr' 
        # This node is added to canvas1's children in setUp, and it lacks the 'children' key.
        result = scan_nodes_by_types(node_id=node_id_to_test, types=['TEXT'])
        self.assertEqual(result, [], "Should return empty list if start node is container but has no 'children' key attribute")

    def test_scan_ignores_child_with_none_type_and_finds_others(self):
        parent_id = 'parent_frame_for_none_type_child_test'
        # This parent and its children (one with type:None, one RECTANGLE) are set up in self.setUp
        # and added to canvas1's children.
        result = scan_nodes_by_types(node_id=parent_id, types=['RECTANGLE', 'TEXT'])
        
        expected_nodes = [{
            'id': 'valid_rect_in_same_frame_for_none', 
            'name': 'Valid Rect for None Test', 
            'type': 'RECTANGLE', 
            'parentId': parent_id
        }]
        self.assertCountEqual(result, expected_nodes)


if __name__ == '__main__':
    unittest.main()