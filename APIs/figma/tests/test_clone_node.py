# figma/tests/test_clone_node.py

import unittest
import copy
from datetime import datetime
from typing import Dict, Any

# Import the function to be tested
from figma import clone_node, DB
from figma.SimulationEngine.custom_errors import NodeNotFoundError, FigmaOperationError, CloneError, InvalidInputError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from unittest.mock import Mock, patch
from figma.SimulationEngine.utils import get_node_from_db, get_parent_of_node_from_db


class TestCloneNode(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self.DB = DB 
        self.DB.clear()

        self.file_key = "test_file_key_clone_node"
        self.doc_id = "doc-0:0"
        self.canvas_id = "canvas-0:1"
        self.parent_frame_id = "frame-1:2"
        self.original_node_id = "rect-1:3"
        self.node_no_bbox_id = "ellipse-1:4"
        self.locked_node_id = "locked-rect-1:5"

        self.original_node_x = 100.0
        self.original_node_y = 150.0
        self.original_node_width = 80.0
        self.original_node_height = 60.0
        self.original_node_name = "OriginalRectangle"
        self.original_node_type = "RECTANGLE"
        self.original_node_fills = [{'type': 'SOLID', 'visible': True, 'opacity': 1.0, 'blendMode': 'NORMAL', 'color': {'r': 0.8, 'g': 0.2, 'b': 0.2, 'a': 1.0}}]

        # Populate self.DB, which is assumed to be the DB instance used by clone_node
        self.DB['files'] = [
            {
                'fileKey': self.file_key,
                'name': 'Cloning Test File',
                'lastModified': datetime.utcnow().isoformat() + "Z",
                'thumbnailUrl': 'http://example.com/thumb_clone.png',
                'version': '2.0',
                'role': 'editor',
                'editorType': 'figma',
                'linkAccess': 'edit',
                'schemaVersion': 0,
                'document': {
                    'id': self.doc_id,
                    'name': 'Test Document Root',
                    'type': 'DOCUMENT',
                    'children': [
                        {
                            'id': self.canvas_id,
                            'name': 'Test Canvas Sheet',
                            'type': 'CANVAS',
                            'children': [
                                {
                                    'id': self.parent_frame_id,
                                    'name': 'Primary Container',
                                    'type': 'FRAME',
                                    'locked': False,
                                    'absoluteBoundingBox': {'x': 10.0, 'y': 10.0, 'width': 800.0, 'height': 600.0},
                                    'fills': [{'type': 'SOLID', 'color': {'r': 0.9, 'g': 0.9, 'b': 0.9, 'a': 1.0}}],
                                    'children': [
                                        {
                                            'id': self.original_node_id,
                                            'name': self.original_node_name,
                                            'type': self.original_node_type,
                                            'locked': False,
                                            'absoluteBoundingBox': {
                                                'x': self.original_node_x,
                                                'y': self.original_node_y,
                                                'width': self.original_node_width,
                                                'height': self.original_node_height
                                            },
                                            'fills': copy.deepcopy(self.original_node_fills),
                                            'children': []
                                        },
                                        {
                                            'id': self.node_no_bbox_id,
                                            'name': "EllipseWithoutBBox",
                                            'type': "ELLIPSE",
                                            'locked': False,
                                            # No 'absoluteBoundingBox'
                                            'fills': [{'type': 'SOLID', 'color': {'r': 0.2, 'g': 0.8, 'b': 0.2, 'a': 1.0}}],
                                            'children': []
                                        },
                                        {
                                            'id': self.locked_node_id,
                                            'name': "ImmutableRectangle",
                                            'type': "RECTANGLE",
                                            'locked': True, # This node is marked as locked
                                            'absoluteBoundingBox': {'x': 200.0, 'y': 250.0, 'width': 40.0, 'height': 30.0},
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
            }
        ]
        self.doc_data_root = self.DB['files'][0]['document']
        self.DB["current_file_key"] = self.file_key

    def _validate_cloned_node_info_structure(self, result: Dict[str, Any], original_node_id_for_comparison: str):
        self.assertIsInstance(result, dict, "Result should be a dictionary.")
        
        expected_keys = ["id", "name", "type", "parentId", "x", "y"]
        for key in expected_keys:
            self.assertIn(key, result, f"Result missing expected key: '{key}'")

        self.assertIsInstance(result.get('id'), str, "Cloned node 'id' must be a string.")
        self.assertNotEqual(result.get('id'), original_node_id_for_comparison, "Cloned node ID must be different from original.")
        self.assertTrue(len(result.get('id', "")) > 0, "Cloned node ID must not be empty.")
        
        self.assertIsInstance(result.get('name'), str, "Cloned node 'name' must be a string.")
        self.assertIsInstance(result.get('type'), str, "Cloned node 'type' must be a string.")
        self.assertIsInstance(result.get('parentId'), str, "Cloned node 'parentId' must be a string.")
        
        self.assertIsInstance(result.get('x'), float, "Cloned node 'x' coordinate must be a float.")
        self.assertIsInstance(result.get('y'), float, "Cloned node 'y' coordinate must be a float.")


    def test_clone_node_success_no_coordinates(self):
        original_node_from_db = get_node_from_db(DB,self.original_node_id)
        self.assertIsNotNone(original_node_from_db, "Test setup: Original node not found in DB.")

        parent_node_from_db = get_parent_of_node_from_db(DB,self.original_node_id)
        self.assertIsNotNone(parent_node_from_db, "Test setup: Parent of original node not found.")
        initial_children_count = len(parent_node_from_db.get('children', []))

        result = clone_node(node_id=self.original_node_id)
        self._validate_cloned_node_info_structure(result, self.original_node_id)

        self.assertEqual(result['name'], f"{self.original_node_name} copy", "Cloned node name mismatch.")
        self.assertEqual(result['type'], self.original_node_type, "Cloned node type mismatch.")
        self.assertEqual(result['parentId'], self.parent_frame_id, "Cloned node parentId mismatch.")
        self.assertEqual(result['x'], self.original_node_x, "Cloned node x-coordinate mismatch.")
        self.assertEqual(result['y'], self.original_node_y, "Cloned node y-coordinate mismatch.")

        cloned_node_in_db = get_node_from_db(DB,result['id'])
        self.assertIsNotNone(cloned_node_in_db, "Cloned node not found in DB after operation.")
        self.assertEqual(cloned_node_in_db.get('name'), result['name'])
        self.assertEqual(cloned_node_in_db.get('type'), result['type'])
        self.assertIn('absoluteBoundingBox', cloned_node_in_db, "Cloned node in DB missing absoluteBoundingBox.")
        bbox_in_db = cloned_node_in_db.get('absoluteBoundingBox', {})
        self.assertEqual(bbox_in_db.get('x'), result['x'])
        self.assertEqual(bbox_in_db.get('y'), result['y'])
        self.assertEqual(bbox_in_db.get('width'), self.original_node_width)
        self.assertEqual(bbox_in_db.get('height'), self.original_node_height)

        parent_of_cloned_node_in_db = get_parent_of_node_from_db(DB,result['id'])
        self.assertIsNotNone(parent_of_cloned_node_in_db, "Parent of cloned node not found in DB.")
        self.assertEqual(parent_of_cloned_node_in_db.get('id'), self.parent_frame_id)
        self.assertEqual(len(parent_node_from_db.get('children', [])), initial_children_count + 1, "Children count of parent node not updated correctly.")
        self.assertTrue(any(child.get('id') == result['id'] for child in parent_node_from_db.get('children', [])), "Cloned node not found in parent's children list.")

        self.assertIn('fills', cloned_node_in_db, "Cloned node in DB missing 'fills'.")
        self.assertEqual(cloned_node_in_db.get('fills'), self.original_node_fills, "'fills' property not copied correctly.")
        if self.original_node_fills and cloned_node_in_db.get('fills'):
            self.assertIsNot(cloned_node_in_db['fills'][0], self.original_node_fills[0], "'fills' property should be deep copied, not referenced.")

    def test_clone_node_figma_operation_error_if_parent_has_no_id(self):
        clean_original_node_dict = copy.deepcopy(get_node_from_db(DB, self.original_node_id))
        self.assertIsNotNone(clean_original_node_dict, "Test setup: Could not retrieve original node for mocking.")

        parent_without_id = {
            'name': 'Parent Frame Without ID',
            'type': 'FRAME',
            'children': [clean_original_node_dict]
        }

        mock_find_node = Mock(return_value=clean_original_node_dict)
        mock_find_parent = Mock(return_value=parent_without_id)

        patch_target_find_node = 'figma.node_creation.utils.find_node_by_id'
        patch_target_find_parent = 'figma.node_creation.utils.find_direct_parent_of_node'

        with patch(patch_target_find_node, mock_find_node), \
             patch(patch_target_find_parent, mock_find_parent):
            self.assert_error_behavior(
                func_to_call=clone_node,
                expected_exception_type=FigmaOperationError,
                expected_message=f"Parent of node '{self.original_node_id}' (ID: N/A) does not have a valid ID.",
                node_id=self.original_node_id
            )

    @patch('figma.node_creation.copy.deepcopy')
    def test_clone_node_figma_operation_error_on_deepcopy_failure(self, mock_deepcopy):
        error_message = "Testing deepcopy failure"
        mock_deepcopy.side_effect = Exception(error_message)

        self.assert_error_behavior(
            func_to_call=clone_node,
            expected_exception_type=FigmaOperationError,
            expected_message=f"Failed to deep copy node '{self.original_node_id}': {error_message}",
            node_id=self.original_node_id
        )

    def test_clone_node_success_with_new_coordinates(self):
        new_x, new_y = 250.5, 350.75
        result = clone_node(node_id=self.original_node_id, x=new_x, y=new_y)
        self._validate_cloned_node_info_structure(result, self.original_node_id)

        self.assertEqual(result['x'], new_x)
        self.assertEqual(result['y'], new_y)
        self.assertEqual(result['parentId'], self.parent_frame_id)

        cloned_node_in_db = get_node_from_db(DB,result['id'])
        self.assertIsNotNone(cloned_node_in_db)
        bbox_in_db = cloned_node_in_db.get('absoluteBoundingBox', {})
        self.assertEqual(bbox_in_db.get('x'), new_x)
        self.assertEqual(bbox_in_db.get('y'), new_y)

    def test_clone_node_success_with_new_x_only(self):
        new_x = 275.0
        result = clone_node(node_id=self.original_node_id, x=new_x) 
        self._validate_cloned_node_info_structure(result, self.original_node_id)

        self.assertEqual(result['x'], new_x)
        self.assertEqual(result['y'], self.original_node_y)

        cloned_node_in_db = get_node_from_db(DB,result['id'])
        self.assertIsNotNone(cloned_node_in_db)
        bbox_in_db = cloned_node_in_db.get('absoluteBoundingBox', {})
        self.assertEqual(bbox_in_db.get('x'), new_x)
        self.assertEqual(bbox_in_db.get('y'), self.original_node_y)

    def test_clone_node_success_with_new_y_only(self):
        new_y = 375.0
        result = clone_node(node_id=self.original_node_id, y=new_y)
        self._validate_cloned_node_info_structure(result, self.original_node_id)

        self.assertEqual(result['x'], self.original_node_x) 
        self.assertEqual(result['y'], new_y)

        cloned_node_in_db = get_node_from_db(DB,result['id'])
        self.assertIsNotNone(cloned_node_in_db)
        bbox_in_db = cloned_node_in_db.get('absoluteBoundingBox', {})
        self.assertEqual(bbox_in_db.get('x'), self.original_node_x)
        self.assertEqual(bbox_in_db.get('y'), new_y)

    def test_clone_node_original_has_no_bbox_no_coords_provided(self):
        original_node_no_bbox_data = get_node_from_db(DB,self.node_no_bbox_id)
        self.assertIsNotNone(original_node_no_bbox_data)
        self.assertNotIn('absoluteBoundingBox', original_node_no_bbox_data)

        result = clone_node(node_id=self.node_no_bbox_id)
        self._validate_cloned_node_info_structure(result, self.node_no_bbox_id)

        self.assertEqual(result['x'], 0.0, "Default x for node with no bbox mismatch.")
        self.assertEqual(result['y'], 0.0, "Default y for node with no bbox mismatch.")
        self.assertEqual(result['parentId'], self.parent_frame_id)
        self.assertEqual(result['name'], f"{original_node_no_bbox_data.get('name')} copy")
        self.assertEqual(result['type'], original_node_no_bbox_data.get('type'))

        cloned_node_in_db = get_node_from_db(DB,result['id'])
        self.assertIsNotNone(cloned_node_in_db)
        self.assertIn('absoluteBoundingBox', cloned_node_in_db, "Cloned node from no-bbox original should have a bbox.")
        bbox_in_db = cloned_node_in_db.get('absoluteBoundingBox', {})
        self.assertEqual(bbox_in_db.get('x'), 0.0)
        self.assertEqual(bbox_in_db.get('y'), 0.0)
        # Width/Height are not added by clone_node if original bbox was missing
        self.assertNotIn('width', bbox_in_db)
        self.assertNotIn('height', bbox_in_db)
        self.assertEqual(cloned_node_in_db.get('fills'), original_node_no_bbox_data.get('fills'))


    def test_clone_node_invalid_input_node_id_not_string_or_empty(self):
        self.assert_error_behavior(
            func_to_call=clone_node,
            expected_exception_type=InvalidInputError,
            expected_message="node_id must be a non-empty string.",
            node_id=12345
        )

    def test_clone_node_invalid_input_x_not_numeric(self):
        self.assert_error_behavior(
            func_to_call=clone_node,
            expected_exception_type=InvalidInputError,
            expected_message="x coordinate must be a number if provided.",
            node_id=self.original_node_id,
            x="not a number"
        )

    def test_clone_node_invalid_input_y_not_numeric(self):
        self.assert_error_behavior(
            func_to_call=clone_node,
            expected_exception_type=InvalidInputError,
            expected_message="y coordinate must be a number if provided.",
            node_id=self.original_node_id,
            y=[100.0]
        )

    def test_clone_node_node_not_found(self):
        node_id_not_in_db="id-that-does-not-exist-in-db"
        self.assert_error_behavior(
            func_to_call=clone_node,
            expected_exception_type=NodeNotFoundError,
            expected_message=f"Node with ID '{node_id_not_in_db}' not found.",
            node_id=node_id_not_in_db
        )

    def test_clone_node_error_cloning_document_node(self):
        doc_node_data = get_node_from_db(DB,self.doc_id)
        self.assertIsNotNone(doc_node_data, "Test setup: Document node not found in DB for mocking.")
        self.assertEqual(doc_node_data.get('type'), "DOCUMENT", "Test setup: Node is not of type DOCUMENT.")

        mock_find_node = Mock(return_value=doc_node_data)
        mock_find_parent = Mock(return_value=doc_node_data) 

        patch_target_find_node = 'figma.utils.find_node_by_id'
        patch_target_find_parent = 'figma.utils.find_direct_parent_of_node'

        with patch(patch_target_find_node, mock_find_node), \
             patch(patch_target_find_parent, mock_find_parent):
            self.assert_error_behavior(
                func_to_call=clone_node,
                expected_exception_type=CloneError,
                expected_message="Nodes of type 'DOCUMENT' cannot be cloned.",
                node_id=self.doc_id 
            )

    def test_clone_node_error_cloning_canvas_node(self):
        self.assert_error_behavior(
            func_to_call=clone_node,
            expected_exception_type=CloneError,
            expected_message="Nodes of type 'CANVAS' cannot be cloned.",
            node_id=self.canvas_id
        )

    def test_clone_locked_node_succeeds_if_not_prevented_by_function(self):
        """
        Tests cloning a node marked 'locked': True.
        The current clone_node function does not check the 'locked' status,
        so this is expected to succeed. If clone_node is updated to prevent
        cloning locked nodes, this test will need to change to expect CloneError.
        """
        locked_node_data = get_node_from_db(DB,self.locked_node_id)
        self.assertIsNotNone(locked_node_data, "Test setup: Locked node not found.")
        self.assertTrue(locked_node_data.get('locked'), "Test setup: Node is not marked as locked.")

        parent_node_from_db = get_parent_of_node_from_db(DB,self.locked_node_id)
        self.assertIsNotNone(parent_node_from_db, "Test setup: Parent of locked node not found.")
        initial_children_count = len(parent_node_from_db.get('children', []))

        # Expect success because clone_node doesn't currently check 'locked'
        result = clone_node(node_id=self.locked_node_id) 
        self._validate_cloned_node_info_structure(result, self.locked_node_id)

        self.assertEqual(result['name'], f"{locked_node_data.get('name')} copy")
        self.assertEqual(result['type'], locked_node_data.get('type'))
        self.assertEqual(result['parentId'], self.parent_frame_id)
        # Check coordinates (should be original's as none are provided)
        original_bbox = locked_node_data.get('absoluteBoundingBox', {})
        self.assertEqual(result['x'], original_bbox.get('x'))
        self.assertEqual(result['y'], original_bbox.get('y'))
        
        cloned_node_in_db = get_node_from_db(DB,result['id'])
        self.assertIsNotNone(cloned_node_in_db, "Cloned locked node not found in DB.")
        self.assertEqual(len(parent_node_from_db.get('children', [])), initial_children_count + 1)


    def test_clone_node_figma_operation_error_if_parent_children_is_malformed(self):
        # 1. Get clean original node data (as a copy) before any malformation
        #    This node is what the mocked find_node_by_id will return.
        clean_original_node_dict = copy.deepcopy(get_node_from_db(DB,self.original_node_id))
        self.assertIsNotNone(clean_original_node_dict, "Test setup: Could not retrieve original node for mocking.")

        # 2. Get the parent node dictionary (this is a reference to the dict in self.DB)
        #    This parent_node_data is what the mocked find_direct_parent_of_node will return.
        #    Its 'children' attribute will be malformed.
        parent_node_data = get_node_from_db(DB,self.parent_frame_id)
        self.assertIsNotNone(parent_node_data, "Test setup: Parent node for malformation test not found.")

        original_children_backup = copy.deepcopy(parent_node_data.get('children'))
        self.assertIsInstance(original_children_backup, list, "Parent node's children is not a list before malformation.")
        
        # 3. Malform the 'children' attribute of parent_node_data IN THE DB.
        parent_node_data['children'] = "not-a-list-of-nodes" 

        # 4. Setup Mocks
        #    The mocked find_node_by_id returns the clean original node.
        #    The mocked find_direct_parent_of_node returns the parent_node_data,
        #    which is a reference to the dict in self.DB that now has malformed children.
        mock_find_node = Mock(return_value=clean_original_node_dict)
        mock_find_parent = Mock(return_value=parent_node_data) 
        patch_target_find_node = 'figma.SimulationEngine.utils.find_node_by_id'
        patch_target_find_parent = 'figma.SimulationEngine.utils.find_direct_parent_of_node'
        
        try:
            with patch(patch_target_find_node, mock_find_node), \
                    patch(patch_target_find_parent, mock_find_parent):
                self.assert_error_behavior(
                    func_to_call=clone_node,
                    expected_exception_type=FigmaOperationError,
                    expected_message=f"Parent node '{self.parent_frame_id}' has a 'children' field that is not a list, but type <class 'str'>.",
                    node_id=self.original_node_id 
                )
        finally:
            # Restore DB state
            # Ensure parent_node_data still refers to the correct dict in self.DB
            parent_node_data_restored = get_node_from_db(DB,self.parent_frame_id)
            if parent_node_data_restored:
                    parent_node_data_restored['children'] = original_children_backup
            else:
                print(f"Warning: Could not find parent node {self.parent_frame_id} during test cleanup.")



if __name__ == '__main__':
    unittest.main()
