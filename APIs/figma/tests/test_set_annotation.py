import copy
import unittest
from datetime import datetime, timezone
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors, utils
from ..annotation_operations import set_annotation
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestSetAnnotation(BaseTestCaseWithErrorHandler):
    DEFAULT_TEST_USER_ID = "test_user_123"
    EXISTING_NODE_ID = "node1"
    EXISTING_CATEGORY_ID = "cat1"
    EXISTING_ANNOTATION_ID = "anno1"

    def setUp(self):
        """Set up a mock DB that reflects the correct nested schema."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        DB.update({
            "current_file_key": "file_key_1",
            "CurrentUserId": self.DEFAULT_TEST_USER_ID,
            "files": [
                {
                    "fileKey": "file_key_1",
                    "name": "Test File For Set",
                    "annotation_categories": [
                        {"id": self.EXISTING_CATEGORY_ID, "name": "Bug", "color": {"r":1,"g":0,"b":0,"a":1}},
                        {"id": "cat2", "name": "Feature", "color": {"r":0,"g":1,"b":0,"a":1}},
                    ],
                    "document": {
                        "id": "0:0", "type": "DOCUMENT", "children": [
                            {
                                "id": "1:1", "type": "CANVAS", "children": [
                                    {
                                        "id": self.EXISTING_NODE_ID, "type": "FRAME", "annotations": [
                                            {
                                                'annotationId': self.EXISTING_ANNOTATION_ID, 'labelMarkdown': 'Initial label',
                                                'resolvedAt': None, 'userId': 'user_original', 'categoryId': self.EXISTING_CATEGORY_ID,
                                                'properties': [{'name': 'status', 'value': 'Open'}]
                                            }
                                        ]
                                    },
                                    {"id": "node2", "type": "FRAME"}
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
    
    def _find_annotation_in_db_node(self, node_id, annotation_id):
        """Helper to find an annotation directly in the DB for verification."""
        file = utils.get_current_file()
        node = utils.find_node_by_id(file['document']['children'], node_id)
        if node and 'annotations' in node:
            return next((ann for ann in node['annotations'] if ann.get('annotationId') == annotation_id), None)
        return None

    # --- Success Scenarios ---

    def test_create_annotation_minimal(self):
        node_id = "node2"
        label = "A new minimal annotation"
        
        result = set_annotation(nodeId=node_id, labelMarkdown=label)
        
        self.assertEqual(result['labelMarkdown'], label)
        self.assertEqual(result['nodeId'], node_id)
        self.assertIsNone(result['categoryId'])
        self.assertIsNone(result['properties'])
        
        # Verify it was written to the DB correctly
        db_annotation = self._find_annotation_in_db_node(node_id, result['annotationId'])
        self.assertIsNotNone(db_annotation)
        self.assertEqual(db_annotation['labelMarkdown'], label)

    def test_create_annotation_with_category_and_properties(self):
        node_id = "node2"
        label = "A full new annotation"
        cat_id = "cat2"
        props = [{"name": "priority", "value": "Low"}]
        
        result = set_annotation(nodeId=node_id, labelMarkdown=label, categoryId=cat_id, properties=props)
        
        self.assertEqual(result['categoryId'], cat_id)
        self.assertEqual(result['properties'], props)
        
        db_annotation = self._find_annotation_in_db_node(node_id, result['annotationId'])
        self.assertIsNotNone(db_annotation)
        self.assertEqual(db_annotation['categoryId'], cat_id)
        self.assertEqual(db_annotation['properties'], props)

    def test_update_existing_annotation_label(self):
        new_label = "This label has been updated"
        

        result = set_annotation(nodeId=self.EXISTING_NODE_ID, 
                                labelMarkdown=new_label, 
                                annotationId=self.EXISTING_ANNOTATION_ID)
        
        self.assertEqual(result['annotationId'], self.EXISTING_ANNOTATION_ID)
        self.assertEqual(result['labelMarkdown'], new_label)
        
        db_annotation = self._find_annotation_in_db_node(self.EXISTING_NODE_ID, self.EXISTING_ANNOTATION_ID)
        self.assertEqual(db_annotation['labelMarkdown'], new_label)

    def test_update_existing_annotation_remove_category(self):
        result = set_annotation(nodeId=self.EXISTING_NODE_ID,
                                labelMarkdown="Same label",
                                annotationId=self.EXISTING_ANNOTATION_ID,
                                categoryId=None) # Explicitly remove category
        
        self.assertEqual(result['annotationId'], self.EXISTING_ANNOTATION_ID)
        self.assertIsNone(result['categoryId'])
        
        db_annotation = self._find_annotation_in_db_node(self.EXISTING_NODE_ID, self.EXISTING_ANNOTATION_ID)
        self.assertIsNone(db_annotation['categoryId'])
        
    # --- Error Scenarios ---
    
    def test_error_node_not_found_on_create(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.NodeNotFoundError,
            expected_message="Node with ID 'non_existent_node' not found.",
            nodeId="non_existent_node",
            labelMarkdown="Some label"
        )
        
    def test_error_annotation_not_found_on_update(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.AnnotationNotFoundError,
            expected_message=f"Annotation with ID 'non_existent_anno' not found on node '{self.EXISTING_NODE_ID}'.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Some label",
            annotationId="non_existent_anno"
        )
        
    def test_error_category_not_found_on_create(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.CategoryNotFoundError,
            expected_message="Category with ID 'non_existent_cat' not found.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Some label",
            categoryId="non_existent_cat"
        )

    def test_error_invalid_input_empty_label(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='labelMarkdown cannot be empty.',
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="  " # Whitespace only
        )

    def test_error_invalid_input_properties_not_a_list(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Properties must be a list of dictionaries.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties={"name": "prop", "value": "val"} # Should be a list
        )

    def test_error_invalid_input_properties_item_malformed(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Malformed property at index 0. Must be a dict with 'name' and 'value'.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties=[{"value": "v1"}] # Missing 'name'
        )
    
    def test_error_invalid_input_empty_nodeid(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='nodeId must be a non-empty string.',
            nodeId="  ", # Whitespace only
            labelMarkdown="Some label"
        )

    def test_error_invalid_input_non_string_nodeid(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='nodeId must be a non-empty string.',
            nodeId=123,
            labelMarkdown="Some label"
        )

    def test_error_invalid_input_properties_item_malformed_at_index_1(self):
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Malformed property at index 1. Must be a dict with 'name' and 'value'.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties=[
                {'name': 'p1', 'value': 'v1'}, 
                {'name': 'p2'} # Missing 'value' at index 1
            ]
        )

    def test_error_could_not_retrieve_current_file(self):
        """Tests FigmaOperationError when the current_file_key is invalid."""
        DB['current_file_key'] = 'non_existent_key'
        self.assert_error_behavior(
            func_to_call=set_annotation,
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Test label",
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="An unexpected error occurred: Could not retrieve the current file."
        )

    def test_update_add_properties_to_annotation_that_had_none(self):
        """Tests updating an annotation to add properties where none existed before."""
        # Create an annotation with no properties
        result_create = set_annotation(nodeId="node2", labelMarkdown="Annotation without properties")
        self.assertIsNone(result_create.get('properties'))

        # Now, update it to add properties
        new_properties = [{"name": "status", "value": "In Review"}]
        result_update = set_annotation(nodeId="node2",
                                    labelMarkdown="Annotation with new properties",
                                    annotationId=result_create['annotationId'],
                                    properties=new_properties)

        self.assertIsNotNone(result_update['properties'])
        self.assertEqual(result_update['properties'], new_properties)
        db_annotation = self._find_annotation_in_db_node("node2", result_create['annotationId'])
        self.assertEqual(db_annotation['properties'], new_properties)

    def test_update_remove_properties_by_passing_none(self):
        """Tests that passing `properties=None` on an update removes existing properties."""
        self.assertIsNotNone(self._find_annotation_in_db_node(self.EXISTING_NODE_ID, self.EXISTING_ANNOTATION_ID)['properties'])

        result = set_annotation(nodeId=self.EXISTING_NODE_ID,
                                labelMarkdown="Updated label",
                                annotationId=self.EXISTING_ANNOTATION_ID,
                                properties=None) # Explicitly pass None

        self.assertIsNone(result['properties'])
        db_annotation = self._find_annotation_in_db_node(self.EXISTING_NODE_ID, self.EXISTING_ANNOTATION_ID)
        self.assertIsNone(db_annotation['properties'])

    def test_create_with_diverse_property_value_types(self):
        """Tests creating an annotation with various data types for property values."""
        diverse_properties = [
            {"name": "is_active", "value": True},
            {"name": "user_count", "value": 150},
            {"name": "completion_rate", "value": 0.95},
            {"name": "review_details", "value": {"status": "pending", "reviewer": "John Doe"}},
            {"name": "tags", "value": ["urgent", "ux"]},
            {"name": "extra_notes", "value": None}
        ]
        
        result = set_annotation(nodeId="node2",
                                labelMarkdown="Diverse properties test",
                                properties=diverse_properties)
        
        self.assertIsInstance(result['properties'], list)
        # Sort for deterministic comparison
        result_props_sorted = sorted(result['properties'], key=lambda x: x['name'])
        expected_props_sorted = sorted(diverse_properties, key=lambda x: x['name'])
        self.assertListEqual(result_props_sorted, expected_props_sorted)

    
    def test_error_when_file_has_no_document(self):
        """
        Tests that a FigmaOperationError is raised if the current file is missing the 'document' key.
        This covers line 191.
        """
        # Remove the 'document' key from the current file in the mock DB
        del utils.get_current_file()['document']

        self.assert_error_behavior(
            func_to_call=set_annotation,
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Test label",
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="An unexpected error occurred: Current file has no document."
        )

    def test_create_annotation_on_node_without_annotations_key(self):
        """
        Tests creating an annotation on a node that does not initially have an 'annotations' key.
        This covers lines 206 and 209.
        """
        # 'node2' is set up without an 'annotations' key
        node_id_to_test = "node2"
        node_in_db = utils.find_node_by_id(utils.get_current_file()['document']['children'], node_id_to_test)
        self.assertNotIn('annotations', node_in_db)

        # Call the function to create the annotation
        result = set_annotation(nodeId=node_id_to_test, labelMarkdown="First annotation")

        # Verify the annotation was created successfully
        self.assertEqual(result['labelMarkdown'], "First annotation")
        
        # Verify that the 'annotations' key was created on the node in the DB
        node_in_db_after = utils.find_node_by_id(utils.get_current_file()['document']['children'], node_id_to_test)
        self.assertIn('annotations', node_in_db_after)
        self.assertIsInstance(node_in_db_after['annotations'], list)
        self.assertEqual(len(node_in_db_after['annotations']), 1)
        self.assertEqual(node_in_db_after['annotations'][0]['annotationId'], result['annotationId'])

    def test_update_all_fields_simultaneously(self):
        """
        Tests updating the label, category, and properties of an annotation in a single call.
        This covers line 224.
        """
        new_label = "Fully updated annotation"
        new_category_id = "cat2"
        new_properties = [{"name": "status", "value": "Closed"}, {"name": "resolution", "value": "Done"}]
        
        result = set_annotation(nodeId=self.EXISTING_NODE_ID,
                                labelMarkdown=new_label,
                                annotationId=self.EXISTING_ANNOTATION_ID,
                                categoryId=new_category_id,
                                properties=new_properties)

        # Verify the returned object is fully updated
        self.assertEqual(result['labelMarkdown'], new_label)
        self.assertEqual(result['categoryId'], new_category_id)
        self.assertEqual(result['properties'], new_properties)

        # Verify the object in the DB is also fully updated
        db_annotation = self._find_annotation_in_db_node(self.EXISTING_NODE_ID, self.EXISTING_ANNOTATION_ID)
        self.assertEqual(db_annotation['labelMarkdown'], new_label)
        self.assertEqual(db_annotation['categoryId'], new_category_id)
        self.assertEqual(db_annotation['properties'], new_properties)

    def test_figma_operation_error_on_unexpected_exception(self):
        """
        Tests that a generic Exception is caught and wrapped in a FigmaOperationError.
        This covers lines 276-277.
        """
        # Corrupt the DB state in a way the function doesn't expect,
        # by making the annotations attribute not a list.
        node = utils.find_node_by_id(utils.get_current_file()['document']['children'], self.EXISTING_NODE_ID)
        node['annotations'] = 12345  # Not an iterable

        self.assert_error_behavior(
            func_to_call=set_annotation,
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Triggering an unexpected error",
            annotationId=self.EXISTING_ANNOTATION_ID,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="An unexpected error occurred: 'int' object is not iterable"
        )

    # --- New tests for missing coverage lines ---

    def test_error_invalid_input_nodeid_not_string(self):
        """Tests that passing a non-string nodeId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="nodeId must be a non-empty string.",
            nodeId=123,  # Non-string type
            labelMarkdown="Valid label"
        )

    def test_error_invalid_input_annotationid_not_string(self):
        """Tests that passing a non-string annotationId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="annotationId must be a string.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            annotationId=456  # Non-string type
        )

    def test_error_invalid_input_annotationid_empty_string(self):
        """Tests that passing an empty string annotationId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="annotationId cannot be empty.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            annotationId=""  # Empty string
        )

    def test_error_invalid_input_annotationid_whitespace_only(self):
        """Tests that passing whitespace-only annotationId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="annotationId cannot be empty.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            annotationId="   "  # Whitespace only
        )

    def test_error_invalid_input_categoryid_not_string(self):
        """Tests that passing a non-string categoryId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="categoryId must be a string.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            categoryId=789  # Non-string type
        )

    def test_error_invalid_input_categoryid_empty_string(self):
        """Tests that passing an empty string categoryId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="categoryId cannot be empty.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            categoryId=""  # Empty string
        )

    def test_error_invalid_input_categoryid_whitespace_only(self):
        """Tests that passing whitespace-only categoryId raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="categoryId cannot be empty.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            categoryId="  \t  "  # Whitespace only
        )

    def test_error_invalid_input_property_name_not_string(self):
        """Tests that passing a non-string property name raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Property name at index 0 must be a string.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties=[{"name": 123, "value": "test"}]  # Non-string name
        )

    def test_error_invalid_input_property_name_empty_string(self):
        """Tests that passing an empty string property name raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Property name at index 0 cannot be empty.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties=[{"name": "", "value": "test"}]  # Empty string name
        )

    def test_error_invalid_input_property_name_whitespace_only(self):
        """Tests that passing whitespace-only property name raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Property name at index 1 cannot be empty.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties=[
                {"name": "valid_name", "value": "test1"},
                {"name": "   ", "value": "test2"}  # Whitespace only name
            ]
        )

    def test_error_invalid_input_multiple_property_validation_errors(self):
        """Tests validation of multiple properties with various name validation errors."""
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Property name at index 0 must be a string.",
            nodeId=self.EXISTING_NODE_ID,
            labelMarkdown="Valid label",
            properties=[
                {"name": None, "value": "test1"},  # Non-string name
                {"name": "valid_name", "value": "test2"},
                {"name": "", "value": "test3"}  # Empty string name
            ]
        )

    def test_error_figma_operation_error_no_current_file(self):
        """Tests that FigmaOperationError is raised when no current file can be retrieved."""
        # Clear the DB to simulate no current file
        DB.clear()
        
        self.assert_error_behavior(
            func_to_call=set_annotation,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="An unexpected error occurred: Current file key not found in DB.",
            nodeId="some_node",
            labelMarkdown="Valid label"
        )