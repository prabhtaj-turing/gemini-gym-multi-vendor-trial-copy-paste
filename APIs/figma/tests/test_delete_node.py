# figma/tests/test_delete_node.py

import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function to be tested
from figma import delete_node
from figma.SimulationEngine.db import DB
from figma.SimulationEngine.utils import get_node_from_db
from figma.SimulationEngine.custom_errors import FigmaOperationError, DeleteError, NodeNotFoundError
from unittest.mock import patch


class TestDeleteNode(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a fresh DB for each test."""
        self.DB = DB  # Use the global DB instance
        self.DB.clear()

        self.base_figma_data = {
            'files': [
                {
                    'fileKey': 'file_key_1',
                    'name': 'Test File 1',
                    'document': {
                        'id': 'doc_0:1',
                        'name': 'Page 1 Document',
                        'type': 'DOCUMENT',
                        'locked': False,
                        'children': [ # Canvases
                            {
                                'id': 'canvas_1:1',
                                'name': 'Canvas 1',
                                'type': 'CANVAS',
                                'locked': False,
                                'children': [ # Nodes in Canvas 1
                                    {
                                        'id': 'node_2:1', 'name': 'Deletable Frame', 'type': 'FRAME',
                                        'locked': False, 'children': []
                                    },
                                    {
                                        'id': 'node_2:2', 'name': 'Locked Frame', 'type': 'FRAME',
                                        'locked': True, 'children': []
                                    },
                                    {
                                        'id': 'node_2:3', 'name': 'Parent Frame with Child', 'type': 'FRAME',
                                        'locked': False,
                                        'children': [
                                            {'id': 'node_3:1', 'name': 'Child Text of Parent Frame', 'type': 'TEXT', 'locked': False, 'text': 'Hello'}
                                        ]
                                    },
                                    {
                                        'id': 'node_for_plugin_error_corruption',
                                        'name': 'Node for PE (corrupt parent children) test',
                                        'type': 'ELLIPSE', 'locked': False, 'children': []
                                    }
                                ]
                            },
                            {
                                'id': 'canvas_1:2',
                                'name': 'Empty Canvas',
                                'type': 'CANVAS',
                                'locked': False,
                                'children': []
                            },
                            {
                                'id': 'canvas_1:3_parent_of_plugin_error_node_none',
                                'name': 'Canvas for PE (None children) test',
                                'type': 'CANVAS',
                                'locked': False,
                                'children': [
                                     {
                                         'id': 'node_for_plugin_error_none_children',
                                         'name': 'Node in PE (None children) test',
                                         'type': 'RECTANGLE', 'locked': False, 'children': []
                                     }
                                ]
                            }
                        ]
                    }
                }
            ],
            "current_file_key":"file_key_1"
        }
        self.DB.update(copy.deepcopy(self.base_figma_data))


    # --- Success Cases ---
    def test_delete_simple_node_success(self):
        node_id_to_delete = 'node_2:1'
        self.assertIsNotNone(get_node_from_db(DB,node_id_to_delete), "Pre-condition: Node should exist.")

        result_message = delete_node(node_id_to_delete)

        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB,node_id_to_delete), "Node should be deleted.")

        # Verify it's removed from parent's children list
        parent_canvas = get_node_from_db(DB,'canvas_1:1')
        self.assertIsNotNone(parent_canvas)
        self.assertFalse(any(n['id'] == node_id_to_delete for n in parent_canvas['children']))

    def test_delete_node_with_children_success(self):
        node_id_to_delete = 'node_2:3' # This node has child 'node_3:1'
        child_node_id = 'node_3:1'

        self.assertIsNotNone(get_node_from_db(DB,node_id_to_delete), "Pre-condition: Parent node should exist.")
        self.assertIsNotNone(get_node_from_db(DB,child_node_id), "Pre-condition: Child node should exist.")

        result_message = delete_node(node_id_to_delete)

        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB,node_id_to_delete), "Parent node should be deleted.")
        self.assertIsNone(get_node_from_db(DB,child_node_id), "Child node should also be gone as part of parent's deletion.")

    def test_delete_child_node_success(self):
        node_id_to_delete = 'node_3:1' # Child of 'node_2:3'
        parent_node_id = 'node_2:3'

        self.assertIsNotNone(get_node_from_db(DB,node_id_to_delete), "Pre-condition: Node should exist.")

        result_message = delete_node(node_id_to_delete)

        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB,node_id_to_delete), "Node should be deleted.")

        parent_node = get_node_from_db(DB,parent_node_id)
        self.assertIsNotNone(parent_node, "Parent node should still exist.")
        self.assertFalse(any(n['id'] == node_id_to_delete for n in parent_node['children']), "Node should be removed from parent's children.")

    def test_delete_last_child_of_parent_success(self):
        # 'node_3:1' is the only child of 'node_2:3'. Deleting it.
        node_id_to_delete = 'node_3:1'
        parent_node_id = 'node_2:3'

        parent_node_before = get_node_from_db(DB,parent_node_id)
        self.assertEqual(len(parent_node_before['children']), 1, "Pre-condition: Parent has one child.")

        result_message = delete_node(node_id_to_delete)

        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB,node_id_to_delete))

        parent_node_after = get_node_from_db(DB,parent_node_id)
        self.assertIsNotNone(parent_node_after)
        self.assertEqual(len(parent_node_after['children']), 0, "Parent should now have zero children.")

    # --- NodeNotFoundError Cases ---
    def test_delete_node_not_found_non_existent_id(self):
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'non_existent_node_id' not found.",
            node_id='non_existent_node_id'
        )

    def test_delete_node_not_found_empty_string_id(self):
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID '' not found.", # Or ValueError depending on implementation detail
            node_id=''
        )

    def test_delete_node_not_found_db_files_empty(self):
        self.DB['files'] = []
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'node_2:1' not found (no files in DB).",
            node_id='node_2:1'
        )

    def test_delete_node_not_found_db_document_none(self):
        self.DB['files'][0]['document'] = None
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'node_2:1' not found.",
            node_id='node_2:1'
        )

    def test_delete_node_not_found_document_children_none(self): # No canvases
        self.DB['files'][0]['document']['children'] = None
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'node_2:1' not found.",
            node_id='node_2:1' # Node that would have been in a canvas
        )

    def test_delete_node_not_found_canvas_children_none(self): # Canvas exists but its children list is None
        self.DB['files'][0]['document']['children'][0]['children'] = None # Canvas_1:1 children set to None
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'node_2:1' not found.",
            node_id='node_2:1' # Node that would have been in that canvas
        )

    def test_delete_node_not_found_in_empty_canvas(self):
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'node_in_empty_canvas' not found.",
            node_id='node_in_empty_canvas' # Trying to delete from canvas_1:2 which is empty
        )

    # --- DeleteError Cases ---
    def test_delete_node_locked_raises_delete_error(self):
        node_id_locked = 'node_2:2'
        self.assertTrue(get_node_from_db(DB,node_id_locked)['locked'], "Pre-condition: Node should be locked.")

        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=DeleteError,
            expected_message=f"Node '{node_id_locked}' (FRAME) is locked and cannot be deleted.",
            node_id=node_id_locked
        )
        self.assertIsNotNone(get_node_from_db(DB,node_id_locked), "Locked node should not be deleted.")

    def test_delete_node_critical_document_node_raises_delete_error(self):
        document_id = 'doc_0:1'
        self.assertEqual(get_node_from_db(DB,document_id)['type'], 'DOCUMENT', "Pre-condition: Node is DOCUMENT.")

        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=DeleteError,
            expected_message=f"Node '{document_id}' (DOCUMENT) cannot be deleted directly.",
            node_id=document_id
        )
        self.assertIsNotNone(get_node_from_db(DB,document_id), "Document node should not be deleted.")

    def test_delete_node_critical_canvas_node_raises_delete_error(self):
        canvas_id = 'canvas_1:1'
        self.assertEqual(get_node_from_db(DB,canvas_id)['type'], 'CANVAS', "Pre-condition: Node is CANVAS.")

        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=DeleteError,
            expected_message=f"Node '{canvas_id}' (CANVAS) cannot be deleted directly.",
            node_id=canvas_id
        )
        self.assertIsNotNone(get_node_from_db(DB,canvas_id), "Canvas node should not be deleted.")

    # --- FigmaOperationError Cases ---
    @patch('figma.SimulationEngine.utils.find_direct_parent_of_node')
    @patch('figma.SimulationEngine.utils.find_node_by_id')
    def test_delete_node_plugin_error_parent_children_not_list(self, mock_find_node, mock_find_parent):
        node_id_for_test = 'node_for_plugin_error_corruption'
        parent_canvas_id = 'canvas_1:1'
        parent_canvas_type = 'CANVAS'

        # Prepare the data that the mocks will return
        # These are references to data within self.DB
        node_to_delete_data = get_node_from_db(DB,node_id_for_test)
        parent_canvas_data = get_node_from_db(DB,parent_canvas_id)
        
        self.assertIsNotNone(node_to_delete_data, "Test setup: Node to delete must exist in test data.")
        self.assertIsNotNone(parent_canvas_data, "Test setup: Parent canvas must exist in test data.")

        # Configure mocks to return these (potentially modified) references
        mock_find_node.return_value = node_to_delete_data
        mock_find_parent.return_value = parent_canvas_data
        
        # Corrupt the 'children' attribute of parent_canvas_data.
        # Since parent_canvas_data is a reference into self.DB, self.DB is now also corrupted.
        corrupted_children_value = "this is not a list"
        parent_canvas_data['children'] = corrupted_children_value

        expected_msg = (f"Internal error: The 'children' attribute of parent node '{parent_canvas_id}' "
                        f"(type: {parent_canvas_type}) is not a list (found type: str).")
        
        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=FigmaOperationError,
            expected_message=expected_msg,
            node_id=node_id_for_test
        )
        
        # Assert the state of the parent in the DB *as it was during the call to delete_node*
        # At this point, self.DB contains the corrupted parent_canvas_data.
        parent_as_it_was_during_test = get_node_from_db(DB,parent_canvas_id)
        self.assertIsNotNone(parent_as_it_was_during_test, "Parent should still be findable in the corrupted DB state.")
        self.assertEqual(parent_as_it_was_during_test['children'], corrupted_children_value,
                         "Parent's children attribute should be corrupted in the DB state seen by delete_node.")

        # Now, reset the DB for subsequent assertions about node existence in a clean state
        self.DB.clear() 
        self.DB.update(copy.deepcopy(self.base_figma_data))

        # Assert that the node itself still exists (as it shouldn't have been deleted)
        self.assertIsNotNone(get_node_from_db(DB,node_id_for_test), "Node should still exist after FigmaOperationError and DB reset.")


    @patch('figma.SimulationEngine.utils.find_direct_parent_of_node')
    @patch('figma.SimulationEngine.utils.find_node_by_id')
    def test_delete_node_plugin_error_parent_children_is_none(self, mock_find_node, mock_find_parent):
        node_id_for_test = 'node_for_plugin_error_none_children'
        parent_canvas_id = 'canvas_1:3_parent_of_plugin_error_node_none'
        parent_canvas_type = 'CANVAS'

        # These are references to data within self.DB
        node_to_delete_data = get_node_from_db(DB,node_id_for_test)
        parent_canvas_data = get_node_from_db(DB,parent_canvas_id)

        self.assertIsNotNone(node_to_delete_data, "Test setup: Node to delete must exist in test data.")
        self.assertIsNotNone(parent_canvas_data, "Test setup: Parent canvas must exist in test data.")

        # Configure mocks
        mock_find_node.return_value = node_to_delete_data
        mock_find_parent.return_value = parent_canvas_data
        
        # Corrupt parent_canvas_data (and thus self.DB)
        corrupted_children_value = None
        parent_canvas_data['children'] = corrupted_children_value 

        expected_msg = (f"Internal error: Parent node '{parent_canvas_id}' (type: {parent_canvas_type}) "
                        f"of node '{node_id_for_test}' has a 'children' attribute that is None.")

        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=FigmaOperationError,
            expected_message=expected_msg,
            node_id=node_id_for_test
        )

        # Assert the state of the parent in the DB *as it was during the call to delete_node*
        parent_as_it_was_during_test = get_node_from_db(DB,parent_canvas_id)
        self.assertIsNotNone(parent_as_it_was_during_test, "Parent should still be findable in the corrupted DB state.")
        self.assertEqual(parent_as_it_was_during_test['children'], corrupted_children_value,
                         "Parent's children attribute should be None in the DB state seen by delete_node.")

        # Now, reset the DB
        self.DB.clear()
        self.DB.update(copy.deepcopy(self.base_figma_data)) 

        # Assert that the node itself still exists in the clean DB
        self.assertIsNotNone(get_node_from_db(DB,node_id_for_test), "Node should still exist after FigmaOperationError and DB reset.")

    @patch('figma.SimulationEngine.utils.get_current_file')
    def test_delete_node_db_file_not_dict_continues_search(self, mock_get_current_file):
        # Malform the DB by making a file entry not a dictionary
        correct_file = self.base_figma_data['files'][0]
        self.DB['files'] = ["not_a_dict", correct_file]
        mock_get_current_file.return_value = correct_file
        
        node_id_to_delete = 'node_2:1'
        self.assertIsNotNone(get_node_from_db(DB, node_id_to_delete), "Pre-condition: Node should exist.")
        result_message = delete_node(node_id_to_delete)
        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB, node_id_to_delete), "Node should be deleted.")

    def test_delete_node_file_missing_document_key_continues_search(self):
        # Malform the DB by removing the 'document' key from the first file
        self.DB['files'] = [{'fileKey': 'no_doc_key'}, self.base_figma_data['files'][0]]
        node_id_to_delete = 'node_2:1'
        self.assertIsNotNone(get_node_from_db(DB, node_id_to_delete), "Pre-condition: Node should exist.")
        result_message = delete_node(node_id_to_delete)
        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB, 'node_2:1'), "Node should still be deleted from the second valid file.")

    def test_delete_node_document_not_dict_continues_search(self):
        # Malform the DB by making the 'document' not a dictionary
        self.DB['files'] = [{'fileKey': 'doc_not_dict', 'document': 'not_a_dict'}, self.base_figma_data['files'][0]]
        node_id_to_delete = 'node_2:1'
        self.assertIsNotNone(get_node_from_db(DB, node_id_to_delete), "Pre-condition: Node should exist.")
        result_message = delete_node(node_id_to_delete)
        self.assertEqual(result_message, f"Node '{node_id_to_delete}' deleted successfully.")
        self.assertIsNone(get_node_from_db(DB, node_id_to_delete), "Node should be deleted.")

    @patch('figma.node_editing.utils.find_direct_parent_of_node')
    @patch('figma.node_editing.utils.find_node_by_id')
    def test_delete_node_parent_missing_children_key_raises_figma_operation_error(self, mock_find_node, mock_find_parent):
        # Test for FigmaOperationError when parent node is missing 'children' key
        node_id_to_delete = 'node_2:1'
        parent_id = 'canvas_1:1'
        
        parent_node = get_node_from_db(DB, parent_id)
        node_to_delete_obj = get_node_from_db(DB, node_id_to_delete)
        
        # Mock the find functions to return these nodes regardless of DB state
        mock_find_node.return_value = node_to_delete_obj
        mock_find_parent.return_value = parent_node
        
        # Now, corrupt the parent node
        del parent_node['children'] 

        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=FigmaOperationError,
            expected_message=f"Internal error: Parent node '{parent_id}' (type: CANVAS) of node '{node_id_to_delete}' is missing the 'children' attribute.",
            node_id=node_id_to_delete
        )

    @patch('figma.node_editing.utils.find_direct_parent_of_node')
    @patch('figma.node_editing.utils.find_node_by_id')
    def test_delete_node_parent_children_not_a_list_raises_figma_operation_error(self, mock_find_node, mock_find_parent):
        # Test for FigmaOperationError when parent node's 'children' is not a list
        node_id_to_delete = 'node_2:1'
        parent_id = 'canvas_1:1'
        
        parent_node = get_node_from_db(DB, parent_id)
        node_to_delete_obj = get_node_from_db(DB, node_id_to_delete)
        
        # Mock the find functions to return these nodes regardless of DB state
        mock_find_node.return_value = node_to_delete_obj
        mock_find_parent.return_value = parent_node
        
        # Now, corrupt the parent node's children attribute
        parent_node['children'] = "not_a_list" # Set children to a non-list value

        self.assert_error_behavior(
            func_to_call=delete_node,
            expected_exception_type=FigmaOperationError,
            expected_message=f"Internal error: The 'children' attribute of parent node '{parent_id}' (type: CANVAS) is not a list (found type: str).",
            node_id=node_id_to_delete
        )


if __name__ == '__main__':
    unittest.main()