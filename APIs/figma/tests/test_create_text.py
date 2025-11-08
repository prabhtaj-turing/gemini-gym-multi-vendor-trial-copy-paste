import unittest
import copy
from typing import Optional, Dict, Any, List
from pydantic import ValidationError
# from datetime import datetime # Not used in this test suite
from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..node_creation import create_text


class TestCreateText(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.default_file_key = 'test_file_key_123'
        self.default_doc_id = 'doc_id_0:0'
        self.default_page_id = "page_id_0:1" # Default parent if parent_id is None
        self.another_page_id = "page_id_0:2"
        self.valid_parent_frame_id = "frame_id_10:1"
        self.valid_parent_group_id = "group_id_10:2"
        self.non_container_node_id = "rect_id_10:3" # e.g., a RECTANGLE, not a valid parent

        # Assumed default values by the function if not provided
        self.default_font_size = 12.0
        self.default_font_weight = 400.0
        self.default_font_color_fill = {'type': 'SOLID', 'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}}


        DB['files'] = [
            {
                'fileKey': self.default_file_key,
                'name': 'Test File',
                'lastModified': '2023-10-26T10:00:00Z',
                'thumbnailUrl': 'https://example.com/thumb.png',
                'document': {
                    'id': self.default_doc_id,
                    'type': 'DOCUMENT',
                    'name': 'Test Document',
                    'children': [
                        { # Current page / Default parent
                            'id': self.default_page_id,
                            'type': 'CANVAS',
                            'name': 'Page 1',
                            'children': [
                                {
                                    'id': self.valid_parent_frame_id,
                                    'type': 'FRAME',
                                    'name': 'Test Frame',
                                    'children': [],  
                                    'absoluteBoundingBox': {'x': 50.0, 'y': 50.0, 'width': 200.0, 'height': 100.0}
                                },
                                {
                                    'id': self.valid_parent_group_id,
                                    'type': 'GROUP',
                                    'name': 'Test Group',
                                    'children': [], 
                                    'absoluteBoundingBox': {'x': 300.0, 'y': 50.0, 'width': 150.0, 'height': 150.0}
                                },
                                {
                                    'id': self.non_container_node_id,
                                    'type': 'RECTANGLE', 
                                    'name': 'Test Rectangle',
                                    'absoluteBoundingBox': {'x': 10.0, 'y': 200.0, 'width': 50.0, 'height': 50.0}
                                }
                            ],
                            'backgroundColor': {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0},
                        },
                        { 
                            'id': self.another_page_id,
                            'type': 'CANVAS',
                            'name': 'Page 2',
                            'children': [],
                            'backgroundColor': {'r': 0.9, 'g': 0.9, 'b': 0.9, 'a': 1.0},
                        }
                    ]
                },
                'components': {},
                'componentSets': {},
                'globalVars': {
                    'styles': {}, 'variables': {}, 'variableCollections': {}
                }
            }
        ]
        DB['current_selection_node_ids'] = []
        DB['current_file_key'] = self.default_file_key

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _find_node_in_db(self, node_id_to_find: str) -> Optional[Dict[str, Any]]:
        if not DB.get('files') or not isinstance(DB['files'], list) or not DB['files']:
            return None
        
        file_data = DB['files'][0]
        if not isinstance(file_data, dict) or not file_data.get('document'):
            return None
        
        doc_node = file_data['document']
        
        queue = []
        if doc_node.get('id') == node_id_to_find: return doc_node

        if doc_node.get('children') and isinstance(doc_node['children'], list):
            queue.extend(doc_node['children']) 

        visited_ids = {doc_node.get('id')}
        head = 0
        while head < len(queue):
            current_node = queue[head]; head += 1
            if not isinstance(current_node, dict): continue
            
            current_id = current_node.get('id')
            if current_id == node_id_to_find: return current_node
            
            if current_id in visited_ids: continue
            if current_id: visited_ids.add(current_id)

            if current_node.get('children') and isinstance(current_node['children'], list):
                queue.extend(current_node['children'])
        return None

    def _get_children_list_from_parent_in_db(self, parent_id_to_check: str) -> Optional[List[Dict[str, Any]]]:
        parent_node = self._find_node_in_db(parent_id_to_check)
        if parent_node and 'children' in parent_node and isinstance(parent_node['children'], list):
            return parent_node['children']
        return None

    # --- Success Test Cases ---

    def test_create_text_minimal_args_success(self):
        x_coord = 10.0
        y_coord = 20.0
        text_content = "Hello Minimal World"

        result = create_text(x=x_coord, y=y_coord, text=text_content)

        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        new_node_id = result['id']
        self.assertIsInstance(new_node_id, str)

        self.assertEqual(result['name'], text_content)
        self.assertEqual(result['type'], 'TEXT')
        self.assertEqual(result['parent_id'], self.default_page_id)
        self.assertEqual(result['characters'], text_content)
        self.assertEqual(result['font_size'], self.default_font_size)
        self.assertEqual(result['fills'], [self.default_font_color_fill])

        parent_children_list = self._get_children_list_from_parent_in_db(self.default_page_id)
        self.assertIsNotNone(parent_children_list)
        created_node_in_db = next((n for n in parent_children_list if n.get('id') == new_node_id), None)
        
        self.assertIsNotNone(created_node_in_db)
        self.assertEqual(created_node_in_db.get('name'), text_content)
        self.assertEqual(created_node_in_db.get('type'), 'TEXT')
        self.assertEqual(created_node_in_db.get('characters'), text_content)
        
        node_style_in_db = created_node_in_db.get('style', {})
        self.assertEqual(node_style_in_db.get('fontSize'), self.default_font_size)
        self.assertEqual(node_style_in_db.get('fontWeight'), self.default_font_weight)

        db_fills = created_node_in_db.get('fills')
        if isinstance(db_fills, dict) and 'root' in db_fills:
            db_fills = db_fills['root']
        self.assertEqual(db_fills, [self.default_font_color_fill])

    def test_create_text_all_optional_args_success(self):
        x_coord = 55.5
        y_coord = 77.7
        text_content = "Fully Styled Text"
        font_size_val = 18.0
        font_weight_val = 700.0
        font_color_val = {'type': 'SOLID', 'color': {'r': 0.2, 'g': 0.4, 'b': 0.6, 'a': 0.8}}
        node_name = "My Awesome Text Node"
        
        result = create_text(
            x=x_coord, y=y_coord, text=text_content,
            font_size=font_size_val, font_weight=font_weight_val,
            font_color=font_color_val, name=node_name, parent_id=self.valid_parent_frame_id
        )

        self.assertIsInstance(result, dict)
        new_node_id = result['id']
        self.assertEqual(result['name'], node_name)
        self.assertEqual(result['type'], 'TEXT')
        self.assertEqual(result['parent_id'], self.valid_parent_frame_id)
        self.assertEqual(result['characters'], text_content)
        self.assertEqual(result['font_size'], font_size_val)
        self.assertEqual(result['fills'], [font_color_val])

        parent_children_list = self._get_children_list_from_parent_in_db(self.valid_parent_frame_id)
        self.assertIsNotNone(parent_children_list)
        created_node_in_db = next((n for n in parent_children_list if n.get('id') == new_node_id), None)
        
        self.assertIsNotNone(created_node_in_db)
        self.assertEqual(created_node_in_db.get('name'), node_name)
        node_style_in_db = created_node_in_db.get('style', {})
        self.assertEqual(node_style_in_db.get('fontSize'), font_size_val)
        self.assertEqual(node_style_in_db.get('fontWeight'), font_weight_val)
        db_fills = created_node_in_db.get('fills')
        if isinstance(db_fills, dict) and 'root' in db_fills:
            db_fills = db_fills['root']
        self.assertEqual(db_fills, [font_color_val])

    def test_create_text_parented_to_group_success(self):
        result = create_text(x=1.0, y=2.0, text="In Group", parent_id=self.valid_parent_group_id)
        self.assertEqual(result['parent_id'], self.valid_parent_group_id)
        parent_children_list = self._get_children_list_from_parent_in_db(self.valid_parent_group_id)
        self.assertTrue(any(n.get('id') == result['id'] for n in parent_children_list if isinstance(n, dict)))

    def test_create_text_parented_to_another_page_success(self):
        result = create_text(x=3.0, y=4.0, text="On Page 2", parent_id=self.another_page_id)
        self.assertEqual(result['parent_id'], self.another_page_id)
        parent_children_list = self._get_children_list_from_parent_in_db(self.another_page_id)
        self.assertTrue(any(n.get('id') == result['id'] for n in parent_children_list if isinstance(n, dict)))

    def test_create_text_with_explicit_none_name_uses_text_content_as_name(self):
        text_content = "This is also the name"
        result = create_text(x=10.0, y=10.0, text=text_content, name=None)
        self.assertEqual(result['name'], text_content)
        created_node_in_db = self._find_node_in_db(result['id'])
        self.assertEqual(created_node_in_db.get('name'), text_content)

    def test_create_text_with_empty_string_name_success(self):
        text_content = "Content for empty name"
        result = create_text(x=10.0, y=10.0, text=text_content, name="")
        self.assertEqual(result['name'], "")
        created_node_in_db = self._find_node_in_db(result['id'])
        self.assertEqual(created_node_in_db.get('name'), "")

    # --- Error Test Cases ---

    def test_create_text_empty_text_content_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="String should have at least 1 character",
            x=10.0, y=10.0, text=""
        )

    def test_create_text_non_positive_font_size_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be greater than 0",
            x=10.0, y=10.0, text="Test", font_size=0.0
        )
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be greater than 0",
            x=10.0, y=10.0, text="Test", font_size=-10.0
        )

    def test_create_text_non_positive_font_weight_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be greater than 0",
            x=10.0, y=10.0, text="Test", font_weight=0.0
        )
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be greater than 0",
            x=10.0, y=10.0, text="Test", font_weight=-400.0
        )
    
    def test_create_text_malformed_font_color_missing_type_raises_invalid_input_error(self):
        malformed_color = {'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}}
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Field required",
            x=10.0, y=10.0, text="Test", font_color=malformed_color
        )

    def test_create_text_malformed_font_color_missing_color_dict_raises_invalid_input_error(self):
        malformed_color = {'type': 'SOLID'}
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Field required",
            x=10.0, y=10.0, text="Test", font_color=malformed_color
        )
    
    def test_create_text_malformed_font_color_type_not_solid_raises_invalid_input_error(self):
        malformed_color = {'type': 'GRADIENT_LINEAR', 'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 1.0}}
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="String should match pattern '^SOLID$'",
            x=10.0, y=10.0, text="Test", font_color=malformed_color
        )

    def test_create_text_font_color_rgba_component_missing_raises_invalid_input_error(self):
        for comp in ['r', 'g', 'b', 'a']:
            color_missing_comp = {'type': 'SOLID', 'color': {'r': 0.5, 'g': 0.5, 'b': 0.5, 'a': 1.0}}
            del color_missing_comp['color'][comp]
            self.assert_error_behavior(
                func_to_call=create_text,
                expected_exception_type=ValidationError,
                expected_message="Field required",
                x=10.0, y=10.0, text="Test", font_color=color_missing_comp
            )

    def test_create_text_font_color_rgba_component_wrong_type_raises_invalid_input_error(self):
        color_b_wrong_type = {'type': 'SOLID', 'color': {'r': 0.5, 'g': 0.5, 'b': "blue", 'a': 1.0}}
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be a valid number",
            x=10.0, y=10.0, text="Test", font_color=color_b_wrong_type
        )

    def test_create_text_font_color_rgba_component_out_of_range_raises_invalid_input_error(self):
        color_r_too_high = {'type': 'SOLID', 'color': {'r': 1.1, 'g': 0.5, 'b': 0.5, 'a': 1.0}}
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be less than or equal to 1",
            x=10.0, y=10.0, text="Test", font_color=color_r_too_high
        )
        color_g_too_low = {'type': 'SOLID', 'color': {'r': 0.5, 'g': -0.1, 'b': 0.5, 'a': 1.0}}
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=ValidationError,
            expected_message="Input should be greater than or equal to 0",
            x=10.0, y=10.0, text="Test", font_color=color_g_too_low
        )

    def test_create_text_non_existent_parent_id_raises_parent_not_found_error(self):
        non_existent_id = "id_that_does_not_exist_12345"
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.ParentNotFoundError,
            expected_message=f"Parent node with ID '{non_existent_id}' not found.",
            x=10.0, y=10.0, text="Test", parent_id=non_existent_id
        )

    def test_create_text_parent_id_not_a_container_raises_parent_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.ParentNotFoundError,
            expected_message=f"Node with ID '{self.non_container_node_id}' is not a valid container type (e.g., FRAME, GROUP, COMPONENT, INSTANCE, CANVAS).",
            x=10.0, y=10.0, text="Test", parent_id=self.non_container_node_id
        )

    # --- FigmaOperationError Tests for Malformed DB ---

    def test_create_text_no_files_in_db_raises_figma_operation_error(self):
        DB['files'] = []
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="Cannot find or access a default page (canvas). DB structure error: DB structure for default page is invalid or incomplete.",
            x=10.0, y=10.0, text="Test"
        )

    def test_create_text_no_document_in_file_raises_figma_operation_error(self):
        del DB['files'][0]['document']
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="Cannot find or access a default page (canvas). DB structure error: DB structure for default page is invalid or incomplete.",
            x=10.0, y=10.0, text="Test"
        )

    def test_create_text_document_no_children_raises_figma_operation_error(self):
        DB['files'][0]['document']['children'] = []
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="Cannot find or access a default page (canvas). DB structure error: DB structure for default page is invalid or incomplete.",
            x=10.0, y=10.0, text="Test"
        )

    def test_create_text_default_page_missing_id_raises_figma_operation_error(self):
        del DB['files'][0]['document']['children'][0]['id']
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message="Default page (first canvas) is missing an ID.",
            x=10.0, y=10.0, text="Test"
        )

    def test_create_text_default_page_invalid_type_raises_figma_operation_error(self):
        invalid_type = "RECTANGLE"
        DB['files'][0]['document']['children'][0]['type'] = invalid_type
        self.assert_error_behavior(
            func_to_call=create_text,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message=f"Default page is not a valid container type: {invalid_type}.",
            x=10.0, y=10.0, text="Test"
        )

if __name__ == '__main__':
    unittest.main()