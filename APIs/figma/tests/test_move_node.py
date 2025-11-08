# figma/tests/test_move_node.py

import unittest
import copy

from figma import move_node, DB
from figma.SimulationEngine.custom_errors import NodeNotFoundError, FigmaOperationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from figma.SimulationEngine.utils import get_node_dict_by_id # Assuming this utility

class TestMoveNode(BaseTestCaseWithErrorHandler):

    def setUp(self):
        # Access the globally available DB dictionary
        self.DB = DB
        self.DB.clear()

        # Populate self.DB with test data
        self.DB['current_file_key'] = 'file1_key'
        self.DB['files'] = [
            {
                'fileKey': 'file1_key',
                'name': 'Test File 1',
                'lastModified': '2023-01-01T12:00:00Z',
                'thumbnailUrl': 'http://example.com/thumb.png',
                'version': '1.2.3',
                'role': 'owner',
                'editorType': 'figma',
                'linkAccess': 'edit',
                'schemaVersion': 1,
                'document': {
                    'id': 'doc_id_1:0',
                    'name': 'Main Document',
                    'type': 'DOCUMENT',
                    'visible': True,
                    'absoluteBoundingBox': {'x': 0, 'y': 0, 'width': 1000, 'height': 1000}, # Added for doc move test
                    'children': [
                        {  # Canvas 1
                            'id': 'canvas1:0',
                            'name': 'Page 1',
                            'type': 'CANVAS',
                            'visible': True,
                            'absoluteBoundingBox': {'x': 0, 'y': 0, 'width': 800, 'height': 600}, # Added for canvas move test
                            'children': [
                                {
                                    'id': 'node1:1',
                                    'name': 'Rectangle 1',
                                    'type': 'RECTANGLE',
                                    'visible': True,
                                    'locked': False,
                                    'opacity': 1.0,
                                    'absoluteBoundingBox': {'x': 10.0, 'y': 20.0, 'width': 100.0, 'height': 50.0},
                                    'fills': [{'type': 'SOLID', 'color': {'r': 1.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}}],
                                    'children': []
                                },
                                {
                                    'id': 'node1:2',
                                    'name': 'Locked Shape',
                                    'type': 'ELLIPSE',
                                    'visible': True,
                                    'locked': True,
                                    'absoluteBoundingBox': {'x': 50.0, 'y': 60.0, 'width': 30.0, 'height': 30.0},
                                    'children': []
                                },
                                {
                                    'id': 'node1:3',
                                    'name': 'Shape No BBox',
                                    'type': 'FRAME',
                                    'visible': True,
                                    'locked': False,
                                    'absoluteBoundingBox': None,
                                    'children': []
                                },
                                {
                                    'id': 'node1:4',
                                    'name': 'Shape BBox Null XY',
                                    'type': 'TEXT',
                                    'visible': True,
                                    'locked': False,
                                    'text': 'Hello',
                                    'absoluteBoundingBox': {'x': None, 'y': None, 'width': 70.0, 'height': 20.0},
                                    'children': []
                                },
                                {
                                    'id': 'node1:5',
                                    'name': 'Shape BBox Empty Dict',
                                    'type': 'VECTOR',
                                    'visible': True,
                                    'locked': False,
                                    'absoluteBoundingBox': {},
                                    'children': []
                                },
                                { # Node for auto-layout tests
                                    'id': 'parent_layout_none:0',
                                    'name': 'Parent Layout None',
                                    'type': 'FRAME',
                                    'layoutMode': 'NONE',
                                    'absoluteBoundingBox': {'x': 300, 'y': 10, 'width': 200, 'height': 200},
                                    'children': [
                                        {
                                            'id': 'child_of_layout_none:1',
                                            'name': 'Child of Layout None',
                                            'type': 'RECTANGLE',
                                            'absoluteBoundingBox': {'x': 310, 'y': 20, 'width': 50, 'height': 50},
                                        }
                                    ]
                                },
                                { # Node for auto-layout tests
                                    'id': 'parent_no_layout_key:0',
                                    'name': 'Parent No Layout Key',
                                    'type': 'FRAME',
                                    'absoluteBoundingBox': {'x': 300, 'y': 220, 'width': 200, 'height': 200},
                                    'children': [
                                        {
                                            'id': 'child_of_no_layout_key:1',
                                            'name': 'Child of No Layout Key',
                                            'type': 'RECTANGLE',
                                            'absoluteBoundingBox': {'x': 310, 'y': 230, 'width': 50, 'height': 50},
                                        }
                                    ]
                                },
                                { # Node for auto-layout tests - HORIZONTAL
                                    'id': 'parent_horizontal_auto:0',
                                    'name': 'Parent Horizontal Auto',
                                    'type': 'FRAME',
                                    'layoutMode': 'HORIZONTAL',
                                    'absoluteBoundingBox': {'x': 10, 'y': 300, 'width': 200, 'height': 100},
                                    'children': [
                                        {
                                            'id': 'child_horizontal:1',
                                            'name': 'Child Horizontal',
                                            'type': 'RECTANGLE',
                                            'absoluteBoundingBox': {'x': 20, 'y': 310, 'width': 50, 'height': 50},
                                        }
                                    ]
                                },
                                { # Node for auto-layout tests - VERTICAL
                                    'id': 'parent_vertical_auto:0',
                                    'name': 'Parent Vertical Auto',
                                    'type': 'FRAME',
                                    'layoutMode': 'VERTICAL',
                                    'absoluteBoundingBox': {'x': 250, 'y': 300, 'width': 100, 'height': 200},
                                    'children': [
                                        {
                                            'id': 'child_vertical:1',
                                            'name': 'Child Vertical',
                                            'type': 'RECTANGLE',
                                            'absoluteBoundingBox': {'x': 260, 'y': 310, 'width': 50, 'height': 50},
                                        }
                                    ]
                                },
                                { # Node for auto-layout tests - Unnamed Parent
                                    'id': 'unnamed_parent_auto:0', # Parent ID
                                    # 'name': 'Unnamed Parent Auto', # Deliberately no name
                                    'type': 'FRAME',
                                    'layoutMode': 'HORIZONTAL',
                                    'absoluteBoundingBox': {'x': 10, 'y': 500, 'width': 200, 'height': 100},
                                    'children': [
                                        {
                                            'id': 'child_of_unnamed_auto:1',
                                            'name': 'Child of Unnamed Auto',
                                            'type': 'RECTANGLE',
                                            'absoluteBoundingBox': {'x': 20, 'y': 510, 'width': 50, 'height': 50},
                                        }
                                    ]
                                },
                                {
                                    'id': 'node_no_name:1',
                                    # 'name': 'This node has no name', # Deliberately missing
                                    'type': 'RECTANGLE',
                                    'visible': True,
                                    'locked': False,
                                    'absoluteBoundingBox': {'x': 500.0, 'y': 20.0, 'width': 100.0, 'height': 50.0},
                                    'children': []
                                },
                                {
                                    'id': 'node_bbox_not_dict:1',
                                    'name': 'BBox Not Dict',
                                    'type': 'FRAME',
                                    'visible': True,
                                    'locked': False,
                                    'absoluteBoundingBox': "invalid_bbox_string",
                                    'children': []
                                },
                            ]
                        },
                        {  # Canvas 2
                            'id': 'canvas2:0',
                            'name': 'Page 2',
                            'type': 'CANVAS',
                            'visible': True,
                            'children': [
                                {
                                    'id': 'node2:1',
                                    'name': 'Nested Parent',
                                    'type': 'GROUP',
                                    'visible': True,
                                    'locked': False,
                                    'absoluteBoundingBox': {'x': 200.0, 'y': 200.0, 'width': 150.0, 'height': 150.0},
                                    'children': [
                                        {
                                            'id': 'node2:2', # Existing nested child
                                            'name': 'Nested Child',
                                            'type': 'RECTANGLE',
                                            'visible': True,
                                            'locked': False,
                                            'absoluteBoundingBox': {'x': 210.0, 'y': 210.0, 'width': 50.0, 'height': 50.0},
                                            'children': []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                'components': {},
                'componentSets': {},
                'globalVars': {}
            },
            { # Second file for testing multi-file search
                'fileKey': 'file2_key',
                'name': 'Test File 2',
                'document': {
                    'id': 'doc_id_2:0',
                    'name': 'Second Document',
                    'type': 'DOCUMENT',
                    'children': [
                        {
                            'id': 'canvas_in_file2:0',
                            'name': 'Canvas in File 2',
                            'type': 'CANVAS',
                            'children': [
                                {
                                    'id': 'node_in_file2:1',
                                    'name': 'Node in File 2',
                                    'type': 'RECTANGLE',
                                    'absoluteBoundingBox': {'x': 10.0, 'y': 10.0, 'width': 30.0, 'height': 30.0},
                                }
                            ]
                        }
                    ]
                }
            }
        ]
        self.initial_db_state = copy.deepcopy(self.DB)

    # --- Existing Tests (ensure they still pass or adjust if necessary) ---
    def test_move_node_success_basic(self):
        node_id_to_move = 'node1:1'
        # node_name = get_node_dict_by_id(DB,node_id_to_move)['name'] # Redundant, name is fixed
        node_name = 'Rectangle 1'
        new_x, new_y = 100.0, 150.0

        status_message = move_node(node_id_to_move, new_x, new_y)

        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)

        self.assertEqual(moved_node_dict['absoluteBoundingBox']['width'], 100.0)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['height'], 50.0)

        self.assertEqual(moved_node_dict['name'], 'Rectangle 1')
        self.assertEqual(moved_node_dict['type'], 'RECTANGLE')
        self.assertTrue(moved_node_dict['fills'])

    def test_move_nested_node_success(self):
        node_id_to_move = 'node2:2'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = 250.5, 275.75

        status_message = move_node(node_id_to_move, new_x, new_y)

        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['width'], 50.0)

    def test_move_node_to_negative_coordinates(self):
        node_id_to_move = 'node1:1'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = -10.5, -20.25

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)

    def test_move_node_to_zero_coordinates(self):
        node_id_to_move = 'node1:1'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = 0.0, 0.0

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)

    def test_move_node_initializes_bounding_box_if_none(self):
        node_id_to_move = 'node1:3'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = 30.0, 40.0

        original_node_data = copy.deepcopy(get_node_dict_by_id(DB,node_id_to_move))

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)
        self.assertNotIn('width', moved_node_dict['absoluteBoundingBox'])
        self.assertNotIn('height', moved_node_dict['absoluteBoundingBox'])

        self.assertEqual(moved_node_dict['name'], original_node_data['name'])
        self.assertEqual(moved_node_dict['type'], original_node_data['type'])


    def test_move_node_updates_bounding_box_with_none_xy(self):
        node_id_to_move = 'node1:4'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = 70.0, 80.0

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['width'], 70.0)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['height'], 20.0)

    def test_move_node_updates_empty_dict_bounding_box(self):
        node_id_to_move = 'node1:5'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = 5.0, 15.0

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)
        self.assertNotIn('width', moved_node_dict['absoluteBoundingBox'])
        self.assertNotIn('height', moved_node_dict['absoluteBoundingBox'])

    def test_move_node_id_not_found_raises_node_not_found_error(self):
        non_existent_id = "nonexistent:node"
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{non_existent_id}' not found in any file or canvas.",
            node_id=non_existent_id, x=0.0, y=0.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_empty_id_raises_value_error(self): # Renamed for clarity, was NodeNotFoundError
        empty_node_id = ""
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=ValueError,
            expected_message="node_id cannot be an empty string.",
            node_id=empty_node_id, x=0.0, y=0.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_with_none_id_raises_type_error(self): # Renamed for clarity
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=TypeError,
            expected_message="node_id must be a string.",
            node_id=None, x=0.0, y=0.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_locked_node_raises_figma_operation_error(self): # Renamed for consistency
        locked_node_id = 'node1:2'
        node_name = get_node_dict_by_id(DB,locked_node_id)['name']
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=FigmaOperationError,
            expected_message=f"Node '{locked_node_id}' (name: '{node_name}') is locked and cannot be moved.",
            node_id=locked_node_id, x=100.0, y=100.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_preserves_all_other_node_properties(self):
        node_id_to_move = 'node1:1'
        # node_name = get_node_dict_by_id(DB,node_id_to_move)['name'] # Unused
        original_node_full_data = copy.deepcopy(get_node_dict_by_id(DB,node_id_to_move))

        new_x, new_y = 123.45, 678.90
        move_node(node_id_to_move, new_x, new_y)

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)

        expected_node_data = copy.deepcopy(original_node_full_data)
        expected_node_data['absoluteBoundingBox']['x'] = new_x
        expected_node_data['absoluteBoundingBox']['y'] = new_y

        self.assertEqual(moved_node_dict, expected_node_data)

    def test_move_node_with_large_float_coordinates(self):
        node_id_to_move = 'node1:1'
        node_name = get_node_dict_by_id(DB,node_id_to_move)['name']
        new_x, new_y = 1.23456789e+20, -9.87654321e+19

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)

    def test_move_node_no_files_in_db(self):
        self.DB.clear()
        node_id_to_move = 'node1:1'
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found (no files in DB or DB is malformed).",
            node_id=node_id_to_move, x=0.0, y=0.0
        )

    def test_move_node_file_without_document(self):
        self.DB['files'] = [{'fileKey': 'key_no_doc'}] # No 'document' key
        node_id_to_move = 'node1:1' # This ID won't be found
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found in any file or canvas.",
            node_id=node_id_to_move, x=0.0, y=0.0
        )

    def test_move_node_document_without_children(self):
        self.DB['files'][0]['document'] = {'id': 'doc2', 'type': 'DOCUMENT', 'children': None}
        node_id_to_move = 'node1:1' # This ID was in original children, now won't be found
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found in any file or canvas.",
            node_id=node_id_to_move, x=0.0, y=0.0
        )

    def test_move_node_canvas_without_children(self): # This test means canvas.children = []
        self.DB['files'][0]['document']['children'] = [{'id': 'canvas3', 'type': 'CANVAS', 'children': []}]
        node_id_to_move = 'node1:1' # This ID was in original canvas children
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found in any file or canvas.",
            node_id=node_id_to_move, x=0.0, y=0.0
        )

    # --- New Tests for Increased Coverage ---

    def test_move_node_invalid_x_type_raises_type_error(self):
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=TypeError,
            expected_message="x coordinate must be a number (int or float), got <class 'str'>.",
            node_id="node1:1", x="not_a_float", y=0.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_invalid_y_type_raises_type_error(self):
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=TypeError,
            expected_message="y coordinate must be a number (int or float), got <class 'list'>.",
            node_id="node1:1", x=0.0, y=[]
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_whitespace_node_id_raises_value_error(self):
        whitespace_node_id = "   "
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=ValueError,
            expected_message="node_id cannot be an empty string.",
            node_id=whitespace_node_id, x=0.0, y=0.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_db_files_is_dict_raises_node_not_found_error(self):
        self.DB['files'] = {} # Malformed: files should be a list
        node_id_to_move = 'node1:1'
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found (no files in DB or DB is malformed).",
            node_id=node_id_to_move, x=0.0, y=0.0
        )


    def test_move_node_document_node_is_not_dict(self):
        self.DB['files'][0]['document'] = "not_a_dictionary_document_entry" # Malformed
        node_id_to_move = 'node1:1'
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found in any file or canvas.",
            node_id=node_id_to_move, x=0.0, y=0.0
        )

    def test_move_node_target_is_document_node_success(self):
        node_id_to_move = 'doc_id_1:0' # Document node ID
        node_name = 'Main Document'
        new_x, new_y = 100.0, 200.0
        
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        modified_doc_node = None
        if self.DB.get('files') and isinstance(self.DB['files'], list) and len(self.DB['files']) > 0:
            file_data = self.DB['files'][0]
            if isinstance(file_data, dict) and isinstance(file_data.get('document'), dict):
                if file_data['document'].get('id') == node_id_to_move:
                    modified_doc_node = file_data['document']
        
        self.assertIsNotNone(modified_doc_node, f"Document node '{node_id_to_move}' could not be manually retrieved for verification.")
        
        # Now check the 'absoluteBoundingBox'
        self.assertIn('absoluteBoundingBox', modified_doc_node, "absoluteBoundingBox key missing in document node after move.")
        bbox = modified_doc_node['absoluteBoundingBox']
        self.assertIsInstance(bbox, dict, "absoluteBoundingBox is not a dictionary.")
        
        self.assertEqual(bbox.get('x'), new_x)
        self.assertEqual(bbox.get('y'), new_y)
        # Document's parent is None conceptually for layout, so no auto-layout check applies.

    def test_move_node_target_is_canvas_node_success(self):
        node_id_to_move = 'canvas1:0' # Canvas node ID
        node_name = 'Page 1'
        new_x, new_y = 50.0, 75.0
        
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")

        modified_canvas_node = None
        if self.DB.get('files') and isinstance(self.DB['files'], list) and len(self.DB['files']) > 0:
            file_data = self.DB['files'][0]
            if isinstance(file_data, dict) and isinstance(file_data.get('document'), dict):
                document_node = file_data['document']
                if isinstance(document_node.get('children'), list):
                    for canvas in document_node['children']:
                        if isinstance(canvas, dict) and canvas.get('id') == node_id_to_move:
                            modified_canvas_node = canvas
                            break
        
        self.assertIsNotNone(modified_canvas_node, f"Canvas node '{node_id_to_move}' could not be manually retrieved for verification.")
        self.assertIn('absoluteBoundingBox', modified_canvas_node, "absoluteBoundingBox key missing in canvas node after move.")
        bbox = modified_canvas_node['absoluteBoundingBox']
        self.assertIsInstance(bbox, dict, "absoluteBoundingBox is not a dictionary.")

        self.assertEqual(bbox.get('x'), new_x)
        self.assertEqual(bbox.get('y'), new_y)

    def test_move_node_canvases_list_is_dict_continues_search(self):
        self.DB['files'][0]['document']['children'] = {"key": "not_a_list_of_canvases"} # Malformed
        node_id_to_move = 'node1:1'
        self.assert_error_behavior( # Node won't be found as its path is now broken
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found in any file or canvas.",
            node_id=node_id_to_move, x=0.0, y=0.0
        )

    def test_move_node_canvas_data_in_list_is_not_dict(self):
        # Malformed: one canvas entry is not a dict, but target node is in another valid canvas
        valid_canvas_entry = self.initial_db_state['files'][0]['document']['children'][1] # 'canvas2:0'
        self.DB['files'][0]['document']['children'] = [
            "not_a_dictionary_canvas_entry", # This should be skipped
            valid_canvas_entry # Contains 'node2:1' -> 'node2:2'
        ]
        node_id_to_move = 'node2:2'
        node_name = 'Nested Child'
        new_x, new_y = 222.0, 333.0
        status = move_node(node_id_to_move, new_x, new_y)
        self.assertIn(node_name, status)
        moved_node = get_node_dict_by_id(self.DB, node_id_to_move)
        self.assertEqual(moved_node['absoluteBoundingBox']['x'], new_x)

    def test_move_node_canvas_children_is_none_continues_search(self):
        # First canvas has children = None, target is in second canvas
        self.DB['files'][0]['document']['children'][0]['children'] = None # Canvas 'canvas1:0' has no children
        node_id_to_move = 'node2:2' # This node is in 'canvas2:0'
        node_name = 'Nested Child'
        new_x, new_y = 205.0, 215.0

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_canvas_children_is_dict_continues_search(self):
        # First canvas has children = dict (malformed), target is in second canvas
        self.DB['files'][0]['document']['children'][0]['children'] = {"id": "not_a_list"}
        node_id_to_move = 'node2:2' # This node is in 'canvas2:0'
        node_name = 'Nested Child'
        new_x, new_y = 205.0, 215.0

        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_child_of_horizontal_auto_layout_raises_figma_op_error(self):
        node_id_to_move = 'child_horizontal:1'
        node_name = 'Child Horizontal'
        parent_name = 'Parent Horizontal Auto'
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=FigmaOperationError,
            expected_message=(
                f"Node '{node_id_to_move}' (name: '{node_name}') is a child of an auto-layout frame "
                f"'{parent_name}' (layoutMode: 'HORIZONTAL') and cannot be moved directly by setting absolute coordinates."
            ),
            node_id=node_id_to_move, x=100.0, y=100.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_child_of_vertical_auto_layout_raises_figma_op_error(self):
        node_id_to_move = 'child_vertical:1'
        node_name = 'Child Vertical'
        parent_name = 'Parent Vertical Auto'
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=FigmaOperationError,
            expected_message=(
                f"Node '{node_id_to_move}' (name: '{node_name}') is a child of an auto-layout frame "
                f"'{parent_name}' (layoutMode: 'VERTICAL') and cannot be moved directly by setting absolute coordinates."
            ),
            node_id=node_id_to_move, x=100.0, y=100.0
        )
        self.assertEqual(self.DB, self.initial_db_state)

    def test_move_node_child_of_unnamed_auto_layout_parent_error_message(self):
        node_id_to_move = 'child_of_unnamed_auto:1'
        node_name = 'Child of Unnamed Auto'
        parent_id = 'unnamed_parent_auto:0' # Parent ID is used as it has no name
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=FigmaOperationError,
            expected_message=(
                f"Node '{node_id_to_move}' (name: '{node_name}') is a child of an auto-layout frame "
                f"'{parent_id}' (layoutMode: 'HORIZONTAL') and cannot be moved directly by setting absolute coordinates."
            ),
            node_id=node_id_to_move, x=100.0, y=100.0
        )
        self.assertEqual(self.DB, self.initial_db_state)


    def test_move_node_child_of_parent_with_layout_mode_none_success(self):
        node_id_to_move = 'child_of_layout_none:1'
        node_name = 'Child of Layout None'
        new_x, new_y = 350.0, 50.0
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_child_of_parent_without_layout_mode_success(self):
        node_id_to_move = 'child_of_no_layout_key:1'
        node_name = 'Child of No Layout Key'
        new_x, new_y = 360.0, 260.0
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_absolute_bounding_box_is_string_replaces_it(self):
        node_id_to_move = 'node_bbox_not_dict:1'
        node_name = 'BBox Not Dict'
        new_x, new_y = 55.0, 65.0
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertIsInstance(moved_node_dict['absoluteBoundingBox'], dict)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], new_y)
        self.assertNotIn('width', moved_node_dict['absoluteBoundingBox']) # Original bbox was string, so new one is minimal

    def test_move_node_with_unnamed_node_success_message(self):
        node_id_to_move = 'node_no_name:1'
        # This node has no 'name' key, so 'Unnamed' should be used.
        new_x, new_y = 505.0, 25.0
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: 'Unnamed') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_found_in_second_file_success(self):
        self.DB['current_file_key'] = 'file2_key'
        node_id_to_move = 'node_in_file2:1'
        node_name = 'Node in File 2'
        new_x, new_y = 11.0, 12.0
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB, node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_found_in_second_canvas_success(self):
        # 'node2:2' is in 'canvas2:0', which is the second canvas of the first file.
        node_id_to_move = 'node2:2'
        node_name = 'Nested Child'
        new_x, new_y = 220.0, 230.0
        status_message = move_node(node_id_to_move, new_x, new_y)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({new_x}, {new_y}).")
        moved_node_dict = get_node_dict_by_id(DB, node_id_to_move)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], new_x)

    def test_move_node_with_integer_coordinates_success(self):
        node_id_to_move = 'node1:1'
        node_name = 'Rectangle 1'
        new_x_int, new_y_int = 150.0, 170.0 # Integer coordinates

        status_message = move_node(node_id_to_move, new_x_int, new_y_int)
        # Function stores them as float
        expected_x_float, expected_y_float = float(new_x_int), float(new_y_int)
        self.assertEqual(status_message, f"Node '{node_id_to_move}' (name: '{node_name}') was successfully moved to ({expected_x_float}, {expected_y_float}).")

        moved_node_dict = get_node_dict_by_id(DB,node_id_to_move)
        self.assertIsNotNone(moved_node_dict)
        self.assertIsNotNone(moved_node_dict.get('absoluteBoundingBox'))
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['x'], expected_x_float)
        self.assertIsInstance(moved_node_dict['absoluteBoundingBox']['x'], float)
        self.assertEqual(moved_node_dict['absoluteBoundingBox']['y'], expected_y_float)
        self.assertIsInstance(moved_node_dict['absoluteBoundingBox']['y'], float)

    def test_move_node_file_data_is_not_dict(self):
        # Malformed DB: files list contains a non-dictionary item
        self.DB['files'] = ["not_a_dictionary_file_entry"]
        node_id_to_move = 'node1:1'
        self.assert_error_behavior(
            func_to_call=move_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_to_move}' not found in any file or canvas.",
            node_id=node_id_to_move, x=0.0, y=0.0
        )


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False) # Adjusted for environments like Jupyter