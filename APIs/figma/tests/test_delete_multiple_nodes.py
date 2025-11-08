# figma/tests/test_delete_multiple_nodes.py

import unittest
import copy
from unittest.mock import patch # Added for potential mocking

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function to be tested
from figma import delete_multiple_nodes
from figma.SimulationEngine import utils
from figma.SimulationEngine.db import DB
from figma.SimulationEngine.utils import node_exists_in_db, find_node_in_list_recursive
from figma.SimulationEngine.custom_errors import FigmaOperationError, InvalidInputError
from figma.SimulationEngine.models import DeleteMultipleNodesResponse, FailedNodeDeletionDetail

class TestDeleteMultipleNodes(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a fresh DB for each test."""
        self.DB = DB  # Use the global DB
        self.DB.clear()
        # Deepcopy is critical to ensure each test gets a pristine version of the DB structure
        self.initial_db_structure = self._get_initial_db_structure()
        self.DB.update(copy.deepcopy(self.initial_db_structure))


    def _get_initial_db_structure(self):
        return {
            'files': [{
                'fileKey': 'test_file_key',
                'name': 'Test File',
                'lastModified': '2023-01-01T00:00:00Z',
                'thumbnailUrl': 'http://example.com/thumb.png',
                'document': {
                    'id': 'doc-0',
                    'type': 'DOCUMENT',
                    'children': [ # Canvases
                        {
                            'id': 'canvas-0',
                            'type': 'CANVAS',
                            'name': 'Page 1',
                            'locked': True, # Canvas is locked
                            'children': [ # Nodes on canvas
                                {'id': '1:1', 'name': 'Frame 1', 'type': 'FRAME', 'locked': False, 'children': [
                                    {'id': '1:2', 'name': 'Rectangle 1A (child of 1:1)', 'type': 'RECTANGLE', 'locked': False, 'children': []},
                                    {'id': '1:3', 'name': 'Text 1B (child of 1:1, locked)', 'type': 'TEXT', 'locked': True, 'children': []},
                                ]},
                                {'id': '2:1', 'name': 'Frame 2 (empty)', 'type': 'FRAME', 'locked': False, 'children': []},
                                {'id': '2:2', 'name': 'Locked Frame 3', 'type': 'FRAME', 'locked': True, 'children': [
                                     {'id': '2:3', 'name': 'Child of Locked Frame 3', 'type': 'RECTANGLE', 'locked': False, 'children': []}
                                ]},
                                {'id': '3:1', 'name': 'Group 1', 'type': 'GROUP', 'locked': False, 'children': [
                                    {'id': '3:2', 'name': 'Shape A (child of 3:1)', 'type': 'ELLIPSE', 'locked': False, 'children': []},
                                    {'id': '3:3', 'name': 'Shape B (child of 3:1)', 'type': 'POLYGON', 'locked': False, 'children': []},
                                ]},
                                {'id': '4:1', 'name': 'Component X', 'type': 'COMPONENT', 'locked': False, 'children': []},
                                {'id': 'node-with-malformed-child-list', 'name': 'Frame with malformed children', 'type': 'FRAME', 'locked': False, 'children': "not a list"},
                                {'id': 'node-with-no-child-list-attr', 'name': 'Frame with no children attr', 'type': 'FRAME', 'locked': False},

                            ]
                        }
                    ]
                },
                'components': {},
                'componentSets': {},
                'globalVars': {}
            }],
            "current_file_key":"test_file_key"
        }

    def test_delete_single_node_successfully(self):
        node_id_to_delete = '1:2'
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete))

        result = delete_multiple_nodes([node_id_to_delete])

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[node_id_to_delete],
            failed_to_delete=[]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertFalse(node_exists_in_db(DB,node_id_to_delete))

        # Verify parent is updated
        doc_children = self.DB['files'][0]['document']['children'][0]['children'] # nodes on canvas
        parent_node_of_1_2 = find_node_in_list_recursive(doc_children, '1:1')
        self.assertIsNotNone(parent_node_of_1_2)
        self.assertFalse(any(child.get('id') == node_id_to_delete for child in parent_node_of_1_2.get('children', [])))


    def test_delete_multiple_nodes_successfully(self):
        nodes_to_delete = ['1:2', '3:2']
        for node_id in nodes_to_delete:
            self.assertTrue(node_exists_in_db(DB,node_id))

        result = delete_multiple_nodes(nodes_to_delete)

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=sorted(nodes_to_delete),
            failed_to_delete=[]
        ).model_dump()

        result['successfully_deleted_ids'].sort()
        self.assertEqual(result, expected_response)

        for node_id in nodes_to_delete:
            self.assertFalse(node_exists_in_db(DB,node_id))

    def test_delete_all_children_of_a_node_successfully(self):
        parent_id = '3:1'
        children_ids = ['3:2', '3:3']

        for node_id in children_ids:
            self.assertTrue(node_exists_in_db(DB,node_id))

        result = delete_multiple_nodes(children_ids)

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=sorted(children_ids),
            failed_to_delete=[]
        ).model_dump()
        result['successfully_deleted_ids'].sort()
        self.assertEqual(result, expected_response)

        for node_id in children_ids:
            self.assertFalse(node_exists_in_db(DB,node_id))

        canvas_node_list = self.DB['files'][0]['document']['children'][0]['children']
        parent_node = find_node_in_list_recursive(canvas_node_list, parent_id)
        self.assertIsNotNone(parent_node)
        self.assertEqual(parent_node.get('children', []), [])

    def test_delete_node_with_no_children_successfully(self):
        node_id_to_delete = '2:1' # Frame 2 (empty)
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete))

        result = delete_multiple_nodes([node_id_to_delete])

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[node_id_to_delete],
            failed_to_delete=[]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertFalse(node_exists_in_db(DB,node_id_to_delete))

    def test_delete_non_existent_node(self):
        node_id_to_delete = 'id-does-not-exist'
        self.assertFalse(node_exists_in_db(DB,node_id_to_delete))

        result = delete_multiple_nodes([node_id_to_delete])

        expected_failure = FailedNodeDeletionDetail(nodeId=node_id_to_delete, reason='Node not found').model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()
        self.assertEqual(result, expected_response)

    def test_delete_locked_node(self):
        node_id_to_delete = '1:3' # Text 1B (child of 1:1, locked)
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete))

        result = delete_multiple_nodes([node_id_to_delete])

        expected_failure = FailedNodeDeletionDetail(nodeId=node_id_to_delete, reason='Node locked').model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete)) # Ensure it's still there

    def test_delete_child_of_locked_node_if_child_is_not_locked(self):
        # Parent '2:2' is locked, child '2:3' is not.
        node_id_to_delete = '2:3'
        parent_locked_node_id = '2:2'
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete))
        self.assertTrue(node_exists_in_db(DB, parent_locked_node_id))

        result = delete_multiple_nodes([node_id_to_delete])

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[node_id_to_delete],
            failed_to_delete=[]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertFalse(node_exists_in_db(DB,node_id_to_delete))
        self.assertTrue(node_exists_in_db(DB,parent_locked_node_id)) # Parent should still exist

    def test_attempt_to_delete_document_root_fails(self):
        node_id_to_delete = 'doc-0' # Document root
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete)) # Document node itself

        result = delete_multiple_nodes([node_id_to_delete])

        expected_failure = FailedNodeDeletionDetail(nodeId=node_id_to_delete, reason='Cannot delete document root').model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertTrue(node_exists_in_db(DB,node_id_to_delete))

    def test_attempt_to_delete_canvas_node_fails_due_to_lock(self):
        # In this setup, canvas-0 is locked.
        node_id_to_delete = 'canvas-0'
        self.assertTrue(node_exists_in_db(DB, node_id_to_delete))

        result = delete_multiple_nodes([node_id_to_delete])

        # The function checks for lock status before checking if it's a canvas that can't be deleted.
        # If canvas was not locked, it might fail for other reasons (e.g. parent being document).
        # Here, it's explicitly locked in the test data.
        expected_failure = FailedNodeDeletionDetail(nodeId=node_id_to_delete, reason='Node locked').model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertTrue(node_exists_in_db(DB, node_id_to_delete))


    def test_delete_mixed_valid_non_existent_and_locked_nodes(self):
        valid_node = '1:2' # Rectangle 1A
        non_existent_node = 'id-does-not-exist'
        locked_node = '1:3' # Text 1B (locked)

        nodes_to_delete = [valid_node, non_existent_node, locked_node]

        # Initial states
        self.assertTrue(node_exists_in_db(DB,valid_node))
        self.assertFalse(node_exists_in_db(DB,non_existent_node))
        self.assertTrue(node_exists_in_db(DB,locked_node))

        result = delete_multiple_nodes(nodes_to_delete)

        expected_failures = [
            FailedNodeDeletionDetail(nodeId=non_existent_node, reason='Node not found').model_dump(),
            FailedNodeDeletionDetail(nodeId=locked_node, reason='Node locked').model_dump()
        ]
        # Sort for consistent comparison
        expected_failures.sort(key=lambda x: x['nodeId'])

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[valid_node], # Only valid_node should be deleted
            failed_to_delete=expected_failures
        ).model_dump()

        # Sort results for consistent comparison
        result['failed_to_delete'].sort(key=lambda x: x['nodeId'])
        result['successfully_deleted_ids'].sort() # Should only be [valid_node]
        expected_response['successfully_deleted_ids'].sort()


        self.assertEqual(result, expected_response)

        # Verify final states
        self.assertFalse(node_exists_in_db(DB,valid_node)) # Should be deleted
        self.assertTrue(node_exists_in_db(DB,locked_node)) # Should still exist

    def test_delete_empty_node_ids_list_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=InvalidInputError,
            expected_message="node_ids list cannot be empty.",
            node_ids=[]
        )

    def test_delete_node_ids_with_empty_string_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=InvalidInputError,
            expected_message="All node IDs must be non-empty strings. Malformed or empty IDs found.",
            node_ids=['1:1', ""] # One valid, one empty
        )

    def test_delete_node_ids_with_non_string_id_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=InvalidInputError,
            expected_message="All node IDs must be non-empty strings. Malformed or empty IDs found.",
            node_ids=['1:1', 123] # One valid, one non-string
        )

    def test_delete_node_ids_with_none_id_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=InvalidInputError,
            expected_message="All node IDs must be non-empty strings. Malformed or empty IDs found.",
            node_ids=['1:1', None] # One valid, one None
        )

    def test_figma_operation_error_if_db_is_empty(self):
        self.DB.clear() # Make DB an empty dict
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            expected_message="Figma data store (DB) is uninitialized or 'files' list is empty.",
            node_ids=['1:1'] # Node ID content doesn't matter here
        )

    def test_figma_operation_error_if_files_list_is_empty_in_db(self):
        self.DB['files'] = [] # Files list exists but is empty
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            expected_message="Figma data store (DB) is uninitialized or 'files' list is empty.",
            node_ids=['1:1']
        )

    def test_figma_operation_error_if_document_is_missing(self):
        # Ensure 'files' exists and has an item, but that item lacks 'document'
        self.DB['files'] = [{}] # First file data is an empty dict
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            expected_message="Essential Figma file data (e.g., document root) is missing in the first file entry.",
            node_ids=['1:1']
        )

    def test_figma_operation_error_if_document_node_is_malformed_missing_id(self):
        self.DB['files'][0]['document'] = {'type': 'DOCUMENT'} # Document exists but no 'id'
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            expected_message="Document root in the first file is malformed or missing its ID.",
            node_ids=['1:1']
        )

    def test_figma_operation_error_if_document_node_id_is_none(self):
        self.DB['files'][0]['document'] = {'id': None, 'type': 'DOCUMENT'} # Document 'id' is None
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            expected_message="Document root in the first file is malformed or missing its ID.",
            node_ids=['1:1']
        )

    @patch('figma.SimulationEngine.utils.get_parent_of_node_from_db')
    def test_delete_node_fails_if_parent_not_found_after_node_is_found(self, mock_get_parent):
        node_id_to_delete = '1:2' # A valid, unlocked node
        mock_get_parent.return_value = None # Simulate parent not found for this node

        # Ensure node '1:2' exists so it passes the initial get_node_from_db check
        self.assertTrue(node_exists_in_db(DB, node_id_to_delete))
        # Ensure it's not locked
        node_obj = utils.get_node_from_db(DB, node_id_to_delete)
        self.assertFalse(node_obj.get('locked', False))


        result = delete_multiple_nodes([node_id_to_delete])

        expected_failure = FailedNodeDeletionDetail(
            nodeId=node_id_to_delete,
            reason="Failed to find parent node (node may be orphaned or DB structure inconsistent)"
        ).model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()

        self.assertEqual(result, expected_response)
        self.assertTrue(node_exists_in_db(DB, node_id_to_delete)) # Node should not be deleted
        mock_get_parent.assert_called_with(DB, node_id_to_delete)


    @patch('figma.SimulationEngine.utils.get_node_from_db')
    @patch('figma.SimulationEngine.utils.get_parent_of_node_from_db')
    def test_delete_node_fails_if_parent_children_attribute_is_missing(self, mock_get_parent, mock_get_node):
        node_id_to_delete = '1:2'
        parent_id = '1:1'

        # --- DB Setup for the test ---
        # 1. Get original node and parent data BEFORE modification
        # This assumes your initial DB structure has '1:2' under '1:1'
        canvas_children_orig = self._get_initial_db_structure()['files'][0]['document']['children'][0]['children']
        original_node_data = copy.deepcopy(find_node_in_list_recursive(canvas_children_orig, node_id_to_delete))
        original_parent_data = copy.deepcopy(find_node_in_list_recursive(canvas_children_orig, parent_id))

        self.assertIsNotNone(original_node_data, "Original node '1:2' must exist in the initial DB structure for this test.")
        self.assertIsNotNone(original_parent_data, "Original parent '1:1' must exist in the initial DB structure for this test.")

        # 2. Create the modified parent state (children key missing) for the mock
        modified_parent_data_for_mock = copy.deepcopy(original_parent_data)
        if 'children' in modified_parent_data_for_mock:
            del modified_parent_data_for_mock['children']

        # --- Configure Mocks ---
        # get_node_from_db should return the original node data
        mock_get_node.return_value = original_node_data
        # get_parent_of_node_from_db should return the parent whose 'children' key is missing
        mock_get_parent.return_value = modified_parent_data_for_mock

        # --- Execute ---
        result = delete_multiple_nodes([node_id_to_delete])

        # --- Assertions ---
        expected_failure = FailedNodeDeletionDetail(
            nodeId=node_id_to_delete,
            reason="Parent node's children data is missing or malformed"
        ).model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()

        self.assertEqual(result, expected_response)
        
        # Verify mocks were called as expected
        mock_get_node.assert_called_with(DB, node_id_to_delete)
        mock_get_parent.assert_called_with(DB, node_id_to_delete)

        # Verify the actual DB state: the node should not have been removed from its original parent in the live DB
        # because the operation should have failed before attempting to modify the DB.
        # The DB itself (self.DB) was not directly modified in the setup for this test case for parent '1:1',
        # as the mocks handled the view for the function under test.
        self.assertTrue(node_exists_in_db(self.DB, node_id_to_delete), 
                        "Node '1:2' should still be findable in the DB as it wasn't deleted.")


    @patch('figma.SimulationEngine.utils.get_node_from_db')
    @patch('figma.SimulationEngine.utils.get_parent_of_node_from_db')
    def test_delete_node_fails_if_parent_children_attribute_is_not_a_list(self, mock_get_parent, mock_get_node):
        node_id_to_delete = '1:2'
        parent_id = '1:1' 

        # --- DB Setup: Modify parent '1:1' in the actual DB to prepare for mock_get_parent ---
        # We need a representation of the parent as it would be if its children attribute was a string
        canvas_children_orig = self._get_initial_db_structure()['files'][0]['document']['children'][0]['children']
        original_node_data = copy.deepcopy(find_node_in_list_recursive(canvas_children_orig, node_id_to_delete))
        parent_data_for_mock = copy.deepcopy(find_node_in_list_recursive(canvas_children_orig, parent_id))
        self.assertIsNotNone(parent_data_for_mock, "Parent '1:1' must exist in initial structure for mock setup.")
        
        parent_data_for_mock['children'] = "this is not a list" # Corrupt the children attribute for the mock

        # --- Configure Mocks ---
        mock_get_node.return_value = original_node_data # Assume node '1:2' is found
        mock_get_parent.return_value = parent_data_for_mock # Parent has corrupted children

        # --- Execute ---
        result = delete_multiple_nodes([node_id_to_delete])

        # --- Assertions ---
        expected_failure = FailedNodeDeletionDetail(
            nodeId=node_id_to_delete,
            reason="Parent node's children data is missing or malformed"
        ).model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure]
        ).model_dump()
        self.assertEqual(result, expected_response)

        # Verify that the actual parent's 'children' attribute in the live DB was not changed to "this is not a list"
        # by the delete_multiple_nodes function (it should have failed before that).
        # The live DB's parent should still have its original children list.
        live_parent_node_in_db = find_node_in_list_recursive(self.DB['files'][0]['document']['children'][0]['children'], parent_id)
        self.assertIsNotNone(live_parent_node_in_db)
        self.assertIsInstance(live_parent_node_in_db.get('children'), list,
                             "Parent's children attribute in the live DB should remain a list.")
        self.assertTrue(node_exists_in_db(self.DB, node_id_to_delete),
                        "Node '1:2' should still exist in the DB as the operation failed.") 


    @patch('figma.SimulationEngine.utils.get_node_from_db')
    @patch('figma.SimulationEngine.utils.get_parent_of_node_from_db') # Mocking parent too for full control
    def test_delete_node_fails_if_node_not_in_parents_children_list_due_to_malformed_entry(self, mock_get_parent, mock_get_node):
        node_id_to_delete = '1:2'
        parent_id = '1:1'

        # --- Prepare data for mocks ---
        # 1. Original node data (what get_node_from_db will return)
        # Fetched from a clean structure to ensure it's pristine
        initial_canvas_children = self._get_initial_db_structure()['files'][0]['document']['children'][0]['children']
        original_node_data_for_mock = copy.deepcopy(
            find_node_in_list_recursive(initial_canvas_children, node_id_to_delete)
        )
        self.assertIsNotNone(original_node_data_for_mock, "Original node '1:2' data for mock not found.")
        # Ensure it's not locked for this test path
        original_node_data_for_mock['locked'] = False 

        # 2. Parent data with the malformed child entry (what get_parent_of_node_from_db will return)
        parent_data_for_mock = copy.deepcopy(
            find_node_in_list_recursive(initial_canvas_children, parent_id)
        )
        self.assertIsNotNone(parent_data_for_mock, "Original parent '1:1' data for mock not found.")
        self.assertIsInstance(parent_data_for_mock.get('children'), list, "Parent's children must be a list.")

        # Malform the specific child entry within this parent_data_for_mock
        found_child_to_malform_in_mock_parent = False
        for child_entry in parent_data_for_mock['children']:
            if child_entry.get('id') == node_id_to_delete: # Find '1:2'
                child_entry.pop('id') # Malform by removing 'id'
                child_entry['name'] = 'Formerly 1:2 but id removed in mock'
                found_child_to_malform_in_mock_parent = True
                break
        self.assertTrue(found_child_to_malform_in_mock_parent, "Child '1:2' to malform not found in parent_data_for_mock.")

        # --- Configure Mocks ---
        mock_get_node.return_value = original_node_data_for_mock
        mock_get_parent.return_value = parent_data_for_mock

        # --- Execute ---
        result = delete_multiple_nodes([node_id_to_delete])

        # --- Assertions ---
        expected_failure_detail = FailedNodeDeletionDetail(
            nodeId=node_id_to_delete,
            reason="Node inconsistency: Found globally but not in its parent's children list"
        ).model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[],
            failed_to_delete=[expected_failure_detail]
        ).model_dump()

        # If this assertEqual fails, print result and expected_response to see the difference
        # print("Actual result:", result)
        # print("Expected response:", expected_response)
        self.assertEqual(result, expected_response)
        
        mock_get_node.assert_called_with(self.DB, node_id_to_delete)
        mock_get_parent.assert_called_with(self.DB, node_id_to_delete)

        # --- Verify DB State (Optional but good for sanity) ---
        # The live DB should NOT have been modified by delete_multiple_nodes because it should have failed early.
        # The malformation we did was on 'parent_data_for_mock', not directly on 'self.DB' for this version of the test.
        # So, node '1:2' should still fully exist and be correctly parented in self.DB.
        
        live_parent_after_op = find_node_in_list_recursive(self.DB['files'][0]['document']['children'][0]['children'], parent_id)
        self.assertIsNotNone(live_parent_after_op)
        
        node_still_in_live_parent = False
        for child in live_parent_after_op.get('children', []):
            if child.get('id') == node_id_to_delete:
                node_still_in_live_parent = True
                break
        self.assertTrue(node_still_in_live_parent, "Node '1:2' should still be in its parent's children list in the live DB.")
        self.assertTrue(node_exists_in_db(self.DB, node_id_to_delete), "Node '1:2' should still fully exist in the live DB.")

    def test_delete_node_succeeds_when_sibling_in_parent_list_is_malformed(self):
        node_to_delete = '3:2' # Child of '3:1'
        parent_id = '3:1'
        sibling_to_keep = '3:3'

        # Malform a sibling of '3:2'. Let's replace '3:3' with a string.
        canvas_children = self.DB['files'][0]['document']['children'][0]['children']
        parent_node = find_node_in_list_recursive(canvas_children, parent_id)
        self.assertIsNotNone(parent_node)
        self.assertIsInstance(parent_node.get('children'), list)

        new_children = []
        found_target_for_malformation = False
        for child in parent_node['children']:
            if child.get('id') == sibling_to_keep: # '3:3'
                new_children.append("this is a malformed sibling string")
                found_target_for_malformation = True
            elif child.get('id') == node_to_delete: # '3:2'
                new_children.append(child) # Keep the node to delete as is
            else:
                new_children.append(child) # Keep other children
        self.assertTrue(found_target_for_malformation, "Sibling '3:3' must be found to malform it.")
        parent_node['children'] = new_children

        self.assertTrue(node_exists_in_db(DB, node_to_delete))

        result = delete_multiple_nodes([node_to_delete])

        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[node_to_delete],
            failed_to_delete=[]
        ).model_dump()
        self.assertEqual(result, expected_response)
        self.assertFalse(node_exists_in_db(DB, node_to_delete))

        # Check parent's children: malformed sibling should remain, '3:2' should be gone
        parent_node_after = find_node_in_list_recursive(canvas_children, parent_id)
        self.assertIsNotNone(parent_node_after)
        children_after = parent_node_after.get('children', [])
        self.assertIn("this is a malformed sibling string", children_after)
        self.assertFalse(any(c.get('id') == node_to_delete for c in children_after if isinstance(c, dict)))


    def test_delete_parent_then_child_in_same_call(self):
        # Parent '1:1', child '1:2'. Order: parent first.
        parent_id = '1:1'
        child_id = '1:2'

        self.assertTrue(node_exists_in_db(DB, parent_id))
        self.assertTrue(node_exists_in_db(DB, child_id)) # Child of 1:1

        result = delete_multiple_nodes([parent_id, child_id])

        # When parent '1:1' is deleted, '1:2' is also gone.
        # So, when '1:2' is processed, it will be "Node not found".
        expected_failure_child = FailedNodeDeletionDetail(nodeId=child_id, reason='Node not found').model_dump()
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=[parent_id],
            failed_to_delete=[expected_failure_child]
        ).model_dump()
        
        # The order of processing unique_node_ids preserves input order of first appearance
        # So parent_id is processed first.
        self.assertEqual(result['successfully_deleted_ids'], expected_response['successfully_deleted_ids'])
        self.assertEqual(len(result['failed_to_delete']), 1)
        self.assertIn(expected_failure_child, result['failed_to_delete'])

        self.assertFalse(node_exists_in_db(DB, parent_id)) # Parent deleted
        self.assertFalse(node_exists_in_db(DB, child_id)) # Child also gone because parent was deleted


    def test_delete_child_then_parent_in_same_call(self):
        # Child '1:2', parent '1:1'. Order: child first.
        parent_id = '1:1'
        child_id = '1:2'

        self.assertTrue(node_exists_in_db(DB, parent_id))
        self.assertTrue(node_exists_in_db(DB, child_id))

        result = delete_multiple_nodes([child_id, parent_id])

        # Both should be deleted successfully. '1:2' is deleted from '1:1'. Then '1:1' is deleted.
        expected_response = DeleteMultipleNodesResponse(
            successfully_deleted_ids=sorted([child_id, parent_id]),
            failed_to_delete=[]
        ).model_dump()

        result['successfully_deleted_ids'].sort()
        self.assertEqual(result, expected_response)

        self.assertFalse(node_exists_in_db(DB, parent_id)) # Parent deleted
        self.assertFalse(node_exists_in_db(DB, child_id)) # Child deleted

    # Add these methods to your TestDeleteMultipleNodes class

    def test_figma_operation_error_if_files_key_is_not_list(self):
        # This test targets: not isinstance(DB.get('files'), list)
        # To isolate this, DB must exist, DB.get('files') must exist, but not be a list.
        self.DB.clear() 
        self.DB['files'] = "this is not a list" # 'files' key exists, but its value is not a list
        
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            # The error message is generic for several initial DB problems
            expected_message="Figma data store (DB) is uninitialized or 'files' list is empty.",
            node_ids=['1:1'] # node_ids content doesn't matter much here
        )

    def test_figma_operation_error_if_document_key_in_file_is_not_dict(self):
        # This test targets: not isinstance(document_node, dict)
        # DB, DB['files'], DB['files'][0] must be valid, 
        # but DB['files'][0]['document'] is not a dict.
        self.DB.clear()
        self.DB.update({
            'files': [{
                'fileKey': 'test_file_key', # Make the file entry somewhat valid
                'name': 'Test File',
                'document': "this is not a dict" # 'document' is not a dictionary
            }],
            "current_file_key":"test_file_key"
        })
        self.assert_error_behavior(
            func_to_call=delete_multiple_nodes,
            expected_exception_type=FigmaOperationError,
            expected_message="Document root in the first file is malformed or missing its ID.",
            node_ids=['1:1']
        )
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)