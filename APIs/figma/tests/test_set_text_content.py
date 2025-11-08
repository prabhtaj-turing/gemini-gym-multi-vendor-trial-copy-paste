# figma/tests/test_set_text_content.py

import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function to be tested
from figma import set_text_content 
from figma.SimulationEngine.db import DB 
from figma.SimulationEngine. utils import get_node_from_db
from figma.SimulationEngine.custom_errors import NodeNotFoundError, NodeTypeError, FigmaOperationError, InvalidInputError
from typing import Optional

class TestSetTextContent(BaseTestCaseWithErrorHandler):   
    """
    Test suite for the set_text_content function.
    """
    def setUp(self):
        """
        Set up the test environment before each test method.
        Initializes self.DB and populates it with test data.
        """
        self.DB = DB # type: ignore # DB is globally available
        self.DB.clear()

        self.file_key = "test_file_figma_settext_123"
        self.doc_id = "doc_settext_0:0"
        self.canvas_id = "canvas_settext_0:1"

        self.text_node_id = "node_settext_1:1_text"
        self.frame_node_id = "node_settext_1:2_frame"
        self.locked_text_node_id = "node_settext_1:3_lockedtext"
        self.text_node_no_chars_id = "node_settext_1:4_text_no_chars"
        self.nested_text_node_id = "node_settext_1:5_nested_text"
        
        self.DB['current_file_key'] = self.file_key
        self.DB['files'] = [
            {
                'fileKey': self.file_key,
                'name': 'Test File for Set Text',
                'lastModified': '2023-10-27T14:00:00Z',
                'thumbnailUrl': 'https://example.com/thumb_settext.png',
                'version': '1.1',
                'role': 'editor',
                'editorType': 'figma',
                'linkAccess': 'view',
                'schemaVersion': 0,
                'document': {
                    'id': self.doc_id,
                    'name': 'Main Document',
                    'type': 'DOCUMENT',
                    'children': [
                        {
                            'id': self.canvas_id,
                            'name': 'Primary Canvas',
                            'type': 'CANVAS',
                            'children': [
                                {
                                    'id': self.text_node_id,
                                    'name': 'Editable Text Label',
                                    'type': 'TEXT',
                                    'characters': 'Initial text content',
                                    'locked': False,
                                    'visible': True,
                                },
                                {
                                    'id': self.frame_node_id,
                                    'name': 'Container Frame',
                                    'type': 'FRAME',
                                    'locked': False,
                                    'visible': True,
                                    'children': [
                                        {
                                            'id': self.nested_text_node_id,
                                            'name': 'Nested Text Label',
                                            'type': 'TEXT',
                                            'characters': 'Initial nested text',
                                            'locked': False,
                                            'visible': True,
                                        }
                                    ]
                                },
                                {
                                    'id': self.locked_text_node_id,
                                    'name': 'Locked Text Label',
                                    'type': 'TEXT',
                                    'characters': 'This text is locked',
                                    'locked': True,
                                    'visible': True,
                                },
                                {
                                    'id': self.text_node_no_chars_id,
                                    'name': 'Text Node Without Initial Chars',
                                    'type': 'TEXT',
                                    'locked': False,
                                    'visible': True,
                                    # 'characters' field is initially absent for this node
                                }
                            ],
                            'backgroundColor': {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0},
                        }
                    ]
                },
                'components': {},
                'componentSets': {},
                'globalVars': {
                     'styles': {}, 'variables': {}, 'variableCollections': {}
                },
            }
        ]

    def test_set_text_content_success(self):
        new_text = "Updated text content successfully!"
        result = set_text_content(node_id=self.text_node_id, text=new_text)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")
        updated_node = get_node_from_db(DB, self.text_node_id)
        self.assertIsNotNone(updated_node, "Node should still exist in DB.")
        self.assertEqual(updated_node.get('characters'), new_text)
        self.assertTrue('characters' in updated_node, "'characters' field should be added.")

    def test_set_text_content_nested_node_success(self):
        new_text = "Updated nested text."
        result = set_text_content(node_id=self.nested_text_node_id, text=new_text)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")
        updated_node = get_node_from_db(DB, self.nested_text_node_id)
        self.assertIsNotNone(updated_node)
        self.assertEqual(updated_node.get('characters'), new_text)
        self.assertTrue('characters' in updated_node, "'characters' field should be added.")

    def test_set_text_content_to_empty_string(self):
        new_text = ""
        result = set_text_content(node_id=self.text_node_id, text=new_text)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")

        updated_node = get_node_from_db(DB, self.text_node_id)
        self.assertIsNotNone(updated_node)
        self.assertEqual(updated_node.get('characters'), new_text)
        self.assertTrue('characters' in updated_node, "'characters' field should be added.")

    def test_set_text_content_to_none(self):
        new_text = None        
        result = set_text_content(node_id=self.text_node_id, text=new_text)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")

        updated_node = get_node_from_db(DB, self.text_node_id)
        self.assertIsNotNone(updated_node)
        self.assertEqual(updated_node.get('characters'), new_text)
        self.assertTrue('characters' in updated_node, "'characters' field should be added.")

    def test_set_text_content_for_node_without_initial_characters_field(self):
        new_text = "Text for a node that had no characters field."
        result = set_text_content(node_id=self.text_node_no_chars_id, text=new_text)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")

        updated_node = get_node_from_db(DB, self.text_node_no_chars_id)
        self.assertIsNotNone(updated_node)
        self.assertEqual(updated_node.get('characters'), new_text)
        self.assertTrue('characters' in updated_node, "'characters' field should be added.")

    def test_set_text_content_long_text_and_special_chars(self):
        long_text = "Lng text with spci@l ch@r and \n newlines \t tabs. " * 20 # Shorter for test speed
        result = set_text_content(node_id=self.text_node_id, text=long_text)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")

        updated_node = get_node_from_db(DB, self.text_node_id)
        self.assertIsNotNone(updated_node)
        self.assertEqual(updated_node.get('characters'), long_text)

    def test_set_text_content_node_id_is_none_raises_error(self):
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=InvalidInputError,     
            expected_message="node_id must be a string. Received type: NoneType.",       
            node_id=None,
            text="Some text"
        )

    def test_set_text_content_node_id_is_empty_string_raises_error(self):
        empty_id = ""
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=InvalidInputError,  
            expected_message=f"node_id cannot be an empty string.",          
            node_id=empty_id,
            text="Some text"
        )

    def test_set_text_content_node_not_found_raises_error(self):
        non_existent_id = "non-existent-node-id-999xyz"
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=NodeNotFoundError,            
            expected_message=f"Node with ID '{non_existent_id}' not found.",
            node_id=non_existent_id,
            text="Some text"
        )

    def test_set_text_content_node_is_not_text_type_raises_error(self):
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=NodeTypeError,  
            expected_message=f"Node with ID '{self.frame_node_id}' is of type 'FRAME', not TEXT. Cannot set text content.",          
            node_id=self.frame_node_id,
            text="Trying to set text on a frame"
        )
        frame_node = get_node_from_db(DB, self.frame_node_id)
        self.assertIsNotNone(frame_node)
        self.assertNotIn('characters', frame_node, "Non-text node should not have 'characters' field added.")

    def test_set_text_content_node_is_locked_raises_error(self):
        original_node_state = get_node_from_db(DB, self.locked_text_node_id)
        original_text = original_node_state.get('characters') if original_node_state else "fallback"
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=FigmaOperationError,   
            expected_message=f"Cannot set text content for node '{self.locked_text_node_id}' because it is locked.",         
            node_id=self.locked_text_node_id,
            text="Attempting to change locked text"
        )

        locked_node_after_attempt = get_node_from_db(DB, self.locked_text_node_id)
        self.assertIsNotNone(locked_node_after_attempt)
        self.assertEqual(locked_node_after_attempt.get('characters'), original_text, "Locked node's text should not change.")

    def test_set_text_content_db_no_files_raises_node_not_found(self):
        self.DB['files'] = []
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=NodeNotFoundError,            
            expected_message=f"Node with ID '{self.text_node_id}' not found.",
            node_id=self.text_node_id,
            text="Some text"
        )

    def test_set_text_content_db_file_has_no_document_raises_node_not_found(self):
        self.DB['files'][0]['document'] = None        
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=NodeNotFoundError,  
            expected_message=f"Node with ID '{self.text_node_id}' not found.",          
            node_id=self.text_node_id,
            text="Some text"
        )

    def test_set_text_content_db_document_has_no_children_raises_node_not_found(self):
        self.DB['files'][0]['document']['children'] = [] # No canvases
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=NodeNotFoundError,    
            expected_message=f"Node with ID '{self.text_node_id}' not found.",        
            node_id=self.text_node_id,
            text="Some text"
        )

    def test_set_text_content_db_canvas_has_no_children_raises_node_not_found(self):
        self.DB['files'][0]['document']['children'][0]['children'] = [] # No nodes on canvas
        self.assert_error_behavior(
            func_to_call=set_text_content,            
            expected_exception_type=NodeNotFoundError,  
            expected_message=f"Node with ID '{self.text_node_id}' not found.",          
            node_id=self.text_node_id,
            text="Some text"
        )

    def test_set_text_content_optional_text_arg_not_provided(self):
        # This tests behavior when text argument defaults (presumably to None)
        result = set_text_content(node_id=self.text_node_id)
        self.assertIsInstance(result, dict, "Return value should be a dictionary.")

        updated_node = get_node_from_db(DB, self.text_node_id)
        self.assertIsNotNone(updated_node)
        self.assertIsNone(updated_node.get('characters'))

    def test_set_text_content_node_id_not_string_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=set_text_content,
            expected_exception_type=InvalidInputError,
            expected_message="node_id must be a string. Received type: int.",
            node_id=12345,
            text="Some text"
        )

if __name__ == '__main__':
    unittest.main()