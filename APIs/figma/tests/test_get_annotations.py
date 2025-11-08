import copy
import unittest
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors, utils
from ..annotation_operations import get_annotations
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestGetAnnotations(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up a mock DB that reflects the correct nested schema."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        DB.update({
            "current_file_key": "file_key_1",
            "files": [
                {
                    "fileKey": "file_key_1",
                    "name": "Test File",
                    "annotation_categories": [
                        {"id": "cat1", "name": "Bug", "color": {"r": 1.0, "g": 0.2, "b": 0.2, "a": 1}}, # #ff3333
                        {"id": "cat2", "name": "Feature Request", "color": {"r": 0.2, "g": 0.8, "b": 0.2, "a": 1}} # #33cc33
                    ],
                    "document": {
                        "id": "0:0", "type": "DOCUMENT", "children": [
                            {
                                "id": "1:1", "type": "CANVAS", "children": [
                                    {
                                        "id": "node1", "type": "FRAME", "annotations": [
                                            {
                                                'annotationId': 'anno1', 
                                                'labelMarkdown': 'Annotation for node 1, category Bug',
                                                'categoryId': 'cat1',
                                                'properties': [{'name': 'priority', 'value': 'High'}]
                                            },
                                            {
                                                'annotationId': 'anno3', 
                                                'labelMarkdown': 'Second annotation for node 1',
                                                
                                                'categoryId': 'cat2'
                                            }
                                        ]
                                    },
                                    {
                                        "id": "node2", "type": "TEXT", "annotations": [
                                            {
                                                'annotationId': 'anno2', 
                                                'labelMarkdown': 'Annotation for node 2, no category',
                                                'categoryId': None,
                                                'properties': None
                                            },
                                            {
                                                'annotationId': 'anno4', 
                                                'labelMarkdown': 'Annotation with non-existent category',
                                                'categoryId': 'cat_non_existent'
                                            }
                                        ]
                                    },
                                    {"id": "node_no_annotations", "type": "RECTANGLE"}
                                ]
                            }
                        ]
                    }
                }
            ]
        })

    def tearDown(self):
        """Restore the original DB state to ensure test isolation."""
        DB.clear()
        DB.update(self._original_DB_state)

    def _find_annotation_by_id(self, annotations_list, anno_id):
        """Helper to find an annotation in the list returned by the function."""
        return next((anno for anno in annotations_list if anno.get('annotationId') == anno_id), None)

    # --- Success Cases ---
    def test_get_all_annotations_no_nodeid(self):
        annotations = get_annotations()
        self.assertEqual(len(annotations), 4)
        ids_found = {anno['annotationId'] for anno in annotations}
        self.assertEqual(ids_found, {'anno1', 'anno2', 'anno3', 'anno4'})
        
        anno1_result = self._find_annotation_by_id(annotations, 'anno1')
        self.assertIsNotNone(anno1_result)
        self.assertEqual(anno1_result['nodeId'], 'node1')
        self.assertNotIn('category', anno1_result) # includeCategories is false by default

    def test_get_all_annotations_include_categories(self):
        annotations = get_annotations(includeCategories=True)
        self.assertEqual(len(annotations), 4)

        anno1_result = self._find_annotation_by_id(annotations, 'anno1')
        self.assertIsNotNone(anno1_result)
        self.assertEqual(anno1_result['categoryId'], 'cat1')
        self.assertIn('category', anno1_result)
        self.assertIsNotNone(anno1_result['category'])
        self.assertEqual(anno1_result['category']['id'], 'cat1')
        self.assertEqual(anno1_result['category']['name'], 'Bug')
        self.assertEqual(anno1_result['category']['color'], '#ff3333') # Check hex conversion

        anno4_result = self._find_annotation_by_id(annotations, 'anno4')
        self.assertIsNotNone(anno4_result)
        self.assertEqual(anno4_result['categoryId'], 'cat_non_existent')
        self.assertIn('category', anno4_result)
        self.assertIsNone(anno4_result['category'], "Category should be None for non-existent categoryId")

    def test_get_annotations_for_specific_node(self):
        annotations = get_annotations(nodeId='node1')
        self.assertEqual(len(annotations), 2)
        ids_found = {anno['annotationId'] for anno in annotations}
        self.assertEqual(ids_found, {'anno1', 'anno3'})
        for anno in annotations:
            self.assertEqual(anno['nodeId'], 'node1')

    def test_get_annotations_for_node_with_no_annotations(self):
        annotations = get_annotations(nodeId='node_no_annotations')
        self.assertEqual(len(annotations), 0)

    def test_get_all_annotations_when_no_annotations_exist_in_file(self):
        # Clear annotations from the mock DB for this test
        current_file = utils.get_current_file()
        node1 = utils.find_node_by_id(current_file['document']['children'], 'node1')
        node2 = utils.find_node_by_id(current_file['document']['children'], 'node2')
        del node1['annotations']
        del node2['annotations']
        
        annotations = get_annotations()
        self.assertEqual(len(annotations), 0)
    
    def test_annotation_structure_is_correct(self):
        annotations = get_annotations(nodeId='node2', includeCategories=True)
        anno2_result = self._find_annotation_by_id(annotations, 'anno2')

        expected_anno2 = {
            'annotationId': 'anno2', 'nodeId': 'node2', 'labelMarkdown': 'Annotation for node 2, no category',
             'categoryId': None,
            'properties': None
        }
        self.assertEqual(anno2_result, expected_anno2)

    # --- Error Cases ---
    def test_error_node_not_found(self):
        self.assert_error_behavior(
            func_to_call=get_annotations,
            nodeId='non_existent_node',
            expected_exception_type=custom_errors.NodeNotFoundError,
            expected_message="Node with ID 'non_existent_node' not found."
        )

    def test_error_invalid_node_id_type(self):
        self.assert_error_behavior(
            func_to_call=get_annotations,
            nodeId=12345,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'nodeId' must be of type string."
        )

    def test_error_invalid_include_categories_type(self):
        self.assert_error_behavior(
            func_to_call=get_annotations,
            includeCategories="true",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'includeCategories' must be of type boolean."
        )
    
    def test_plugin_error_if_annotation_in_db_is_malformed(self):
        # Add a malformed annotation (missing 'id')
        current_file = utils.get_current_file()
        node1 = utils.find_node_by_id(current_file['document']['children'], 'node1')
        node1['annotations'].append({'labelMarkdown': 'Malformed annotation'})

        self.assert_error_behavior(
            func_to_call=get_annotations,
            nodeId='node1',
            expected_exception_type=custom_errors.PluginError,
            expected_message="An internal plugin error occurred: Malformed annotation data in DB."
        )

    def test_get_annotations_for_deeply_nested_node(self):
        """Tests retrieving annotations from a node several levels deep."""
        # Add a deeply nested node to the DB for this test
        current_file = utils.get_current_file()
        node1 = utils.find_node_by_id(current_file['document']['children'], 'node1')
        node1['children'] = [{
            "id": "deep_node_parent", "type": "GROUP", "children": [{
                "id": "deep_node_child", "type": "VECTOR", "annotations": [{
                    'annotationId': 'anno_deep', 'labelMarkdown': 'Deeply nested annotation',
                     'categoryId': 'cat1'
                }]
            }]
        }]

        annotations = get_annotations(nodeId='deep_node_child')
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0]['annotationId'], 'anno_deep')

    def test_ignores_annotations_in_other_files(self):
        """Ensures the function only scans the file specified by current_file_key."""
        # Add a second file to the DB with its own annotations
        DB['files'].append({
            "fileKey": "file_key_2", "name": "Another File", "document": {
                "id": "0:0", "type": "DOCUMENT", "children": [{
                    "id": "node_other_file", "type": "FRAME", "annotations": [
                        {'annotationId': 'anno_other_file', 'labelMarkdown': 'Should not be found'}
                    ]
                }]
            }
        })
        # Ensure we are pointed to the first file
        DB['current_file_key'] = 'file_key_1'

        annotations = get_annotations()
        # Should only contain the 4 annotations from file_key_1
        self.assertEqual(len(annotations), 4)
        found_ids = {ann['annotationId'] for ann in annotations}
        self.assertNotIn('anno_other_file', found_ids)

    def test_handles_malformed_category_in_db(self):
        """
        Tests behavior when a category object is missing a required key like 'name'.
        The category object in the result should be None.
        """
        # Add a malformed category (missing 'name' key)
        utils.get_current_file()['annotation_categories'].append({'id': 'cat_malformed','color': {'r':0,'g':0,'b':1,'a':1}})
        # Add an annotation that uses it
        node = utils.find_node_by_id(utils.get_current_file()['document']['children'], 'node_no_annotations')
        node['annotations'] = [{'annotationId': 'anno_malformed_cat', 'labelMarkdown': 'Test', 'categoryId': 'cat_malformed'}]

        annotations = get_annotations(nodeId='node_no_annotations', includeCategories=True)
        self.assertEqual(len(annotations), 1)
        # The function should gracefully handle the error and return None for the category
        self.assertIsNone(annotations[0]['category'])

    def test_error_when_current_file_key_is_invalid(self):
        """Tests that a PluginError is raised if the current file key does not exist."""
        DB['current_file_key'] = 'non_existent_file_key'
        self.assert_error_behavior(
            func_to_call=get_annotations,
            expected_exception_type=custom_errors.PluginError,
            expected_message="An internal plugin error occurred: Could not retrieve the current file."
        )

    def test_handles_empty_document_children_list(self):
        """Ensures function works correctly when a document has no children (no canvases)."""
        utils.get_current_file()['document']['children'] = []
        annotations = get_annotations()
        self.assertEqual(len(annotations), 0)

    def test_structure_with_empty_properties_list(self):
        """Ensures an annotation with an empty properties list is returned correctly."""
        node = utils.find_node_by_id(utils.get_current_file()['document']['children'], 'node_no_annotations')
        node['annotations'] = [{
            'annotationId': 'anno_empty_props', 'labelMarkdown': 'Test',  'properties': []
        }]
        annotations = get_annotations(nodeId='node_no_annotations')
        self.assertEqual(len(annotations), 1)
        self.assertListEqual(annotations[0]['properties'], [])

    def test_plugin_error_when_annotation_item_is_not_dict(self):
        """
        Tests that a PluginError is raised if an item in a node's 'annotations' list is not a dictionary.
        This covers the error handling path for line 78.
        """
        # Manually add a non-dictionary item to an annotations list
        node = utils.find_node_by_id(utils.get_current_file()['document']['children'], 'node1')
        node['annotations'].append("this is not a dict")

        self.assert_error_behavior(
            func_to_call=get_annotations,
            nodeId='node1',
            expected_exception_type=custom_errors.PluginError,
            expected_message="An internal plugin error occurred: 'str' object has no attribute 'copy'"
        )

    def test_error_when_current_file_has_no_document(self):
        """Tests PluginError when the current file dictionary is missing the 'document' key."""
        current_file = utils.get_current_file()
        # To trigger the error, we can either remove the document or set it to None/empty
        del current_file['document']

        self.assert_error_behavior(
            func_to_call=get_annotations,
            expected_exception_type=custom_errors.PluginError,
            expected_message="An internal plugin error occurred: Current file has no document."
        )