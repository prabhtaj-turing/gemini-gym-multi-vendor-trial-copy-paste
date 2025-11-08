import unittest
import copy
from unittest.mock import patch
from typing import List, Dict, Any, Optional

from figma.SimulationEngine import custom_errors
from figma.SimulationEngine.db import DB
from figma.document_context import get_local_components
from common_utils.base_case import BaseTestCaseWithErrorHandler

# --- Helper functions ---
def create_document_with_nodes(nodes_on_canvas: Optional[List[Dict[str, Any]]] = None,
                               document_id: str = "0:0",
                               canvas_id: str = "1:1") -> Dict[str, Any]:
    """
    Creates a basic Figma document structure with a single canvas,
    containing the provided nodes.
    """
    if nodes_on_canvas is None:
        nodes_on_canvas = []
    return {
        'id': document_id,
        'type': 'DOCUMENT',
        'name': 'Test Document',
        'children': [
            {
                'id': canvas_id,
                'type': 'CANVAS',
                'name': 'Page 1',
                'children': nodes_on_canvas
            }
        ]
    }

def create_file_with_document(file_key: str,
                              nodes_on_canvas: Optional[List[Dict[str, Any]]] = None,
                              document_data: Optional[Dict[str, Any]] = None,
                              **kwargs: Any) -> Dict[str, Any]:
    """
    Creates a complete file object structure as expected by the functions,
    including a nested document. It allows for additional top-level file
    properties to be passed via kwargs.
    If document_data is provided, it's used directly; otherwise,
    create_document_with_nodes is called.
    """
    file_obj: Dict[str, Any] = {
        'fileKey': file_key,
        'name': f'Test File {file_key}',
    }
    if document_data is not None:
        file_obj['document'] = document_data
    else:
        file_obj['document'] = create_document_with_nodes(nodes_on_canvas=nodes_on_canvas)

    file_obj.update(kwargs) # For other top-level file properties if needed
    return file_obj


class TestGetLocalComponents(BaseTestCaseWithErrorHandler):
    """Test suite for the get_local_components function."""

    def setUp(self):
        """Set up for each test."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.file_key = "test_file_components_key"
        DB['current_file_key'] = self.file_key
        # Default to a file with an empty document to avoid setup in every test
        # This ensures 'files' and 'current_file_key' are always minimally populated.
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=[])]

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_local_components_success_no_components(self):
        """Test retrieving components when none exist in an open document."""
        # DB is already set up with an empty document in setUp
        result = get_local_components()
        self.assertEqual(result, [])

    def test_get_local_components_success_single_component_all_fields(self):
        """Test retrieving a single component with all fields populated."""
        component_node = {
            'id': '2:1', 'type': 'COMPONENT', 'name': 'Primary Button',
            'key': 'compKey1', 'description': 'A main CTA button.',
            'parentId': '1:1' # Assuming '1:1' is the canvas_id
        }
        DB['files'] = [
            create_file_with_document(file_key=self.file_key, nodes_on_canvas=[component_node])
        ]
        expected_component = {
            'id': '2:1', 'key': 'compKey1', 'name': 'Primary Button',
            'description': 'A main CTA button.', 'componentSetId': None,
            'parentId': '1:1'
        }
        result = get_local_components()
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], expected_component)

    def test_get_local_components_success_single_component_minimal_fields(self):
        """Test retrieving a component with minimal fields, expecting normalization."""
        minimal_component_node = {
            'id': '2:3', 'type': 'COMPONENT', 'name': 'Icon',
            'key': 'compKey2', 'parentId': '1:1'
        }
        DB['files'] = [
            create_file_with_document(file_key=self.file_key, nodes_on_canvas=[minimal_component_node])
        ]
        expected_component = {
            'id': '2:3', 'key': 'compKey2', 'name': 'Icon',
            'description': None, 'componentSetId': None,
            'parentId': '1:1'
        }
        result = get_local_components()
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], expected_component)

    def test_get_local_components_success_component_in_component_set(self):
        """Test retrieving a component that is part of a COMPONENT_SET."""
        component_set_node = {
            'id': 'CS:1', 'type': 'COMPONENT_SET', 'name': 'Button Set', 'parentId': '1:1',
            'children': [
                {
                    'id': '3:1', 'type': 'COMPONENT', 'name': 'Variant A',
                    'key': 'variantKey1', 'description': 'Button variant A.',
                    'parentId': 'CS:1' # Parent is the COMPONENT_SET
                }
            ]
        }
        DB['files'] = [
            create_file_with_document(file_key=self.file_key, nodes_on_canvas=[component_set_node])
        ]
        expected_component = {
            'id': '3:1', 'key': 'variantKey1', 'name': 'Variant A',
            'description': 'Button variant A.', 'componentSetId': 'CS:1',
            'parentId': 'CS:1'
        }
        result = get_local_components()
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], expected_component)

    def test_get_local_components_multiple_components_mixed(self):
        """Test retrieving multiple components, some in sets, some not."""
        nodes = [
            {'id': '10:1', 'type': 'COMPONENT', 'name': 'Standalone', 'key': 'keyS', 'parentId': '1:1'},
            {'id': 'CS:X', 'type': 'COMPONENT_SET', 'name': 'Set X', 'parentId': '1:1', 'children': [
                {'id': '10:2', 'type': 'COMPONENT', 'name': 'InSet1', 'key': 'keyIS1', 'parentId': 'CS:X'},
                {'id': '10:3', 'type': 'FRAME', 'name': 'NotAComponent', 'parentId': 'CS:X', 'children': [
                     {'id': '10:4', 'type': 'COMPONENT', 'name': 'NestedInFrame', 'key': 'keyNIF', 'parentId': '10:3'}
                ]}
            ]},
            {'id': '10:5', 'type': 'COMPONENT', 'name': 'AnotherStandalone', 'key': 'keyAS', 'parentId': '1:1', 'description': ''}
        ]
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=nodes)]

        expected_components = [
            {'id': '10:1', 'key': 'keyS', 'name': 'Standalone', 'description': None, 'componentSetId': None, 'parentId': '1:1'},
            {'id': '10:2', 'key': 'keyIS1', 'name': 'InSet1', 'description': None, 'componentSetId': 'CS:X', 'parentId': 'CS:X'},
            {'id': '10:4', 'key': 'keyNIF', 'name': 'NestedInFrame', 'description': None, 'componentSetId': None, 'parentId': '10:3'},
            {'id': '10:5', 'key': 'keyAS', 'name': 'AnotherStandalone', 'description': "", 'componentSetId': None, 'parentId': '1:1'},
        ]
        result = get_local_components()
        self.assertCountEqual(result, expected_components)


    def test_error_current_file_key_not_found_in_db(self):
        """Test FigmaOperationError if 'current_file_key' is not in DB."""
        del DB['current_file_key']
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "Current file key not found in DB."
        )

    def test_error_current_file_not_found_for_key(self):
        """Test FigmaOperationError if no file matches 'current_file_key'."""
        DB['current_file_key'] = "non_existent_key"
        DB['files'] = [create_file_with_document(file_key="some_other_key")]
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "Current file with key 'non_existent_key' not found."
        )

    def test_error_file_missing_document_object(self):
        """Test FigmaOperationError if the current file dict has no 'document' key."""
        current_file_data = DB['files'][0]
        del current_file_data['document'] # Remove document from the file data
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "Current file is missing a 'document' object."
        )

    def test_error_document_is_none(self):
        """Test NoDocumentOpenError if 'document' object is None."""
        DB['files'][0]['document'] = None
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "Current file is missing a 'document' object."
        )

    def test_error_document_not_a_dict(self):
        """Test FigmaOperationError if 'document' object is not a dictionary."""
        DB['files'][0]['document'] = "this is not a document dictionary"
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "Figma document data is not in the expected format (root must be a dictionary)."
        )
    
    def test_document_root_missing_children_handled_by_build_map(self):
        """Test when document root is valid dict but missing 'children'.
           _build_node_map_recursive should handle this (e.g., by not finding nodes).
           get_local_components should return empty list if no components found.
        """
        DB['files'][0]['document'] = {'id': '0:0', 'type': 'DOCUMENT', 'name': 'Doc without children'}
        # Expect no error, just no components found.
        result = get_local_components()
        self.assertEqual(result, [])

    @patch('figma.document_context._build_node_map_recursive')
    def test_error_during_build_node_map(self, mock_build_map):
        """Test FigmaOperationError if _build_node_map_recursive raises an Exception."""
        mock_build_map.side_effect = Exception("Recursive error in build map")
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "Failed to process document structure while building node map: Recursive error in build map"
        )

    @patch('figma.document_context._collect_components_recursive')
    def test_error_keyerror_during_collect_components(self, mock_collect_components):
        """Test FigmaOperationError if _collect_components_recursive raises a KeyError."""
        # This simulates _collect_components_recursive trying to access a missing key in a node.
        mock_collect_components.side_effect = KeyError("mocked_key_error")
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "'mocked_key_error'" # The message becomes str(e)
        )

    @patch('figma.document_context._collect_components_recursive')
    def test_error_other_exception_during_collect_components(self, mock_collect_components):
        """Test FigmaOperationError if _collect_components_recursive raises a non-KeyError Exception."""
        mock_collect_components.side_effect = ValueError("Some other collection error")
        self.assert_error_behavior(
            get_local_components,
            custom_errors.FigmaOperationError,
            "An unexpected error occurred while retrieving local components: Some other collection error"
        )

    def test_deeply_nested_component_discovery(self):
        """Test discovery of a component nested several levels deep."""
        deep_nodes = [{
            'id': 'level1_frame', 'type': 'FRAME', 'parentId': '1:1', 'children': [{
                'id': 'level2_group', 'type': 'GROUP', 'parentId': 'level1_frame', 'children': [{
                    'id': 'level3_frame', 'type': 'FRAME', 'parentId': 'level2_group', 'children': [{
                        'id': 'comp_deep', 'type': 'COMPONENT', 'key': 'k_deep',
                        'name': 'Deeply Nested Component', 'parentId': 'level3_frame'
                    }]
                }]
            }]
        }]
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=deep_nodes)]
        result = get_local_components()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'comp_deep')
        self.assertEqual(result[0]['name'], 'Deeply Nested Component')
        self.assertEqual(result[0]['parentId'], 'level3_frame')
        self.assertIsNone(result[0]['componentSetId'])

    def test_robustness_non_dict_item_in_children_list(self):
        """Test that traversal skips non-dictionary items in a 'children' list."""
        nodes_with_malformed_child = [
            {'id': 'frame_A', 'type': 'FRAME', 'parentId': '1:1', 'children': [
                {'id': 'comp_A1', 'type': 'COMPONENT', 'key': 'kA1', 'name': 'Comp A1', 'parentId': 'frame_A'},
                "this is not a node object", # Malformed child
                None, # Malformed child
                {'id': 'comp_A2', 'type': 'COMPONENT', 'key': 'kA2', 'name': 'Comp A2', 'parentId': 'frame_A'}
            ]}
        ]
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=nodes_with_malformed_child)]
        result = get_local_components()
        self.assertEqual(len(result), 2)
        component_ids = sorted([c['id'] for c in result])
        self.assertEqual(component_ids, ['comp_A1', 'comp_A2'])

    def test_robustness_children_attribute_not_a_list(self):
        """Test that traversal handles a node where 'children' attribute is not a list."""
        nodes_with_malformed_children_attr = [
            {'id': 'frame_B', 'type': 'FRAME', 'parentId': '1:1', 'children': "should be a list, not string"},
            {'id': 'comp_B1', 'type': 'COMPONENT', 'key': 'kB1', 'name': 'Comp B1', 'parentId': '1:1'}
        ]
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=nodes_with_malformed_children_attr)]
        result = get_local_components()
        # Only comp_B1 should be found, as children of frame_B cannot be processed.
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'comp_B1')

    def test_component_with_empty_string_description(self):
        """Test component with description as an empty string."""
        component_node = {
            'id': 'C1', 'type': 'COMPONENT', 'name': 'EmptyDesc', 'key': 'kED',
            'parentId': '1:1', 'description': ""
        }
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=[component_node])]
        result = get_local_components()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['description'], "")

    def test_component_description_is_non_string(self):
        """Test component description normalization if it's not a string (e.g. int).
           _collect_components_recursive is responsible for this normalization.
           This test assumes _collect_components_recursive will normalize it to None or handle it.
           If _collect_components_recursive doesn't normalize, this might pass if no error occurs.
        """
        component_node = {
            'id': 'C2', 'type': 'COMPONENT', 'name': 'NonStrDesc', 'key': 'kNSD',
            'parentId': '1:1', 'description': 12345
        }
        DB['files'] = [create_file_with_document(file_key=self.file_key, nodes_on_canvas=[component_node])]
        result = get_local_components()
        self.assertEqual(len(result), 1)
        # The expected behavior for description depends on _collect_components_recursive.
        # A robust _collect_components_recursive might convert it to str("12345") or None.
        # Assuming it normalizes to None if not a string.
        self.assertIsNone(result[0]['description'])


if __name__ == '__main__':
    unittest.main()