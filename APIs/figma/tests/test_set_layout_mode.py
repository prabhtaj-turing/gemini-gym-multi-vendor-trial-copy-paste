import copy
from typing import Optional, Dict, Any
from unittest.mock import patch

from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from ..SimulationEngine import utils 
from ..layout_operations import set_layout_mode
from common_utils.base_case import BaseTestCaseWithErrorHandler 
from ..SimulationEngine.models import LayoutModeEnum, LayoutWrapEnum 

class TestSetLayoutMode(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.user_id = "me" 
        self.file_key = "test_file_for_layout"
        self.doc_id = f"{self.file_key}_doc:0"
        self.page_id = f"{self.file_key}_page:1"

        DB["files"] = [
            {
                "fileKey": self.file_key,
                "name": "Test Layout File",
                "document": {
                    "id": self.doc_id,
                    "type": "DOCUMENT",
                    "children": [
                        {
                            "id": self.page_id,
                            "type": "CANVAS",
                            "name": "Page 1",
                            "children": [] 
                        }
                    ]
                }
            }
        ]
        DB["current_file_key"] = self.file_key

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_figma_node_to_page(self, node_id: str, node_type: str = "FRAME",
                                initial_layout_mode: str = "NONE", 
                                initial_layout_wrap: str = "NO_WRAP"):
        page_node = utils.find_node_dict_in_DB(DB, self.page_id)
        if page_node and isinstance(page_node.get("children"), list):
            node_data = {
                "id": node_id,
                "type": node_type,
                "name": f"Node {node_id}",
                "layoutMode": initial_layout_mode, 
                "layoutWrap": initial_layout_wrap, 
            }
            page_node["children"].append(node_data)
        else:
            raise Exception(f"Could not find or append to children of page {self.page_id} in setUp.")


    def _get_node_from_db(self, node_id: str) -> Optional[Dict[str, Any]]:
        return utils.find_node_dict_in_DB(DB, node_id)

    # Success Cases
    def test_set_layout_mode_none_success(self):
        node_id = "frame_1"
        self._add_figma_node_to_page(node_id, initial_layout_mode="HORIZONTAL", initial_layout_wrap="WRAP")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.NONE.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.NONE.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.NO_WRAP.value) # type: ignore

    def test_set_layout_mode_horizontal_no_wrap_param_success(self):
        node_id = "frame_2"
        self._add_figma_node_to_page(node_id, initial_layout_mode="NONE")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.HORIZONTAL.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.HORIZONTAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.NO_WRAP.value) # type: ignore

    def test_set_layout_mode_horizontal_with_no_wrap_success(self):
        node_id = "frame_3"
        self._add_figma_node_to_page(node_id, initial_layout_mode="VERTICAL", initial_layout_wrap="WRAP")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.HORIZONTAL.value, layout_wrap=LayoutWrapEnum.NO_WRAP.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.HORIZONTAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.NO_WRAP.value) # type: ignore

    def test_set_layout_mode_horizontal_with_wrap_success(self):
        node_id = "frame_4"
        self._add_figma_node_to_page(node_id, initial_layout_mode="NONE")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.HORIZONTAL.value, layout_wrap=LayoutWrapEnum.WRAP.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.HORIZONTAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.WRAP.value) # type: ignore

    def test_set_layout_mode_vertical_no_wrap_param_success(self):
        node_id = "frame_5"
        self._add_figma_node_to_page(node_id, initial_layout_mode="NONE")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.VERTICAL.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.VERTICAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.NO_WRAP.value) # type: ignore

    def test_set_layout_mode_vertical_with_no_wrap_success(self):
        node_id = "frame_6"
        self._add_figma_node_to_page(node_id, initial_layout_mode="HORIZONTAL", initial_layout_wrap="WRAP")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.VERTICAL.value, layout_wrap=LayoutWrapEnum.NO_WRAP.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.VERTICAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.NO_WRAP.value) # type: ignore

    def test_set_layout_mode_vertical_with_wrap_success(self):
        node_id = "frame_7"
        self._add_figma_node_to_page(node_id, initial_layout_mode="NONE")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.VERTICAL.value, layout_wrap=LayoutWrapEnum.WRAP.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.VERTICAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.WRAP.value) # type: ignore

    def test_set_layout_mode_to_none_with_valid_wrap_param_is_error(self):
        node_id = "frame_8"
        self._add_figma_node_to_page(node_id, initial_layout_mode="HORIZONTAL", initial_layout_wrap="WRAP")
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="layout_wrap parameter is not applicable and cannot be specified when layout_mode is 'NONE'.",
            node_id=node_id, 
            layout_mode=LayoutModeEnum.NONE.value, 
            layout_wrap=LayoutWrapEnum.WRAP.value 
        )

    def test_set_layout_mode_no_change_needed(self):
        node_id = "frame_9"
        self._add_figma_node_to_page(node_id, initial_layout_mode="HORIZONTAL", initial_layout_wrap="WRAP")
        result = set_layout_mode(node_id=node_id, layout_mode=LayoutModeEnum.HORIZONTAL.value, layout_wrap=LayoutWrapEnum.WRAP.value)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('layoutMode'), LayoutModeEnum.HORIZONTAL.value) # type: ignore
        self.assertEqual(node.get('layoutWrap'), LayoutWrapEnum.WRAP.value) # type: ignore

    # Error Cases - Node Issues
    def test_node_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.NodeNotFoundError,
            expected_message="Node with ID 'non_existent_node' not found.",
            node_id="non_existent_node",
            layout_mode=LayoutModeEnum.HORIZONTAL.value
        )

    def test_node_type_error_not_frame(self):
        node_id = "node_not_a_frame"
        self._add_figma_node_to_page(node_id, node_type="TEXT") 
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.NodeTypeError,
            expected_message=f"Node with ID '{node_id}' must be a FRAME to set layout mode. Actual type: TEXT.",
            node_id=node_id,
            layout_mode=LayoutModeEnum.HORIZONTAL.value
        )

    def test_node_type_error_missing_type_field(self):
        node_id = "node_missing_type"
        self._add_figma_node_to_page(node_id, node_type="FRAME")
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        if node:
            del node['type']

        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.NodeTypeError,
            expected_message=f"Node with ID '{node_id}' must be a FRAME to set layout mode. Actual type: type field missing.",
            node_id=node_id,
            layout_mode=LayoutModeEnum.HORIZONTAL.value
        )
        
    def test_plugin_error_if_node_is_not_dict(self):
        node_id = "frame_malformed"
        with patch('figma.layout_operations.utils') as mock_utils:
            mock_utils.find_node_dict_in_DB.return_value = "I am a string, not a dict"
            
            self.assert_error_behavior(
                func_to_call=set_layout_mode,
                expected_exception_type=custom_errors.PluginError,
                expected_message=f"Data for node ID '{node_id}' is not in the expected dictionary format. Type found: str.",
                node_id=node_id,
                layout_mode=LayoutModeEnum.HORIZONTAL.value
            )

    # Error Cases - Invalid Input
    def test_invalid_input_error_invalid_layout_mode(self):
        node_id = "frame_10"
        self._add_figma_node_to_page(node_id)
        invalid_mode = "INVALID_MODE"
        valid_modes_str = sorted([e.value for e in LayoutModeEnum])
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Invalid layout_mode: '{invalid_mode}'. Accepted values are {valid_modes_str}.",
            node_id=node_id,
            layout_mode=invalid_mode
        )

    def test_invalid_input_error_horizontal_invalid_layout_wrap(self):
        node_id = "frame_11"
        self._add_figma_node_to_page(node_id)
        invalid_wrap = "INVALID_WRAP"
        valid_wraps_str = sorted([e.value for e in LayoutWrapEnum])
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Invalid layout_wrap: '{invalid_wrap}'. Accepted values are {valid_wraps_str}.",
            node_id=node_id,
            layout_mode=LayoutModeEnum.HORIZONTAL.value,
            layout_wrap=invalid_wrap
        )

    # Error Cases - InvalidInputError (basic type checks)
    def test_validation_error_node_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="node_id must be a string.",
            node_id=123, 
            layout_mode=LayoutModeEnum.HORIZONTAL.value
        )

    def test_validation_error_node_id_empty_string(self):
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="node_id must be a non-empty string.",
            node_id="  ",
            layout_mode=LayoutModeEnum.HORIZONTAL.value
        )

    def test_validation_error_layout_mode_not_string(self):
        node_id = "frame_13"
        self._add_figma_node_to_page(node_id)
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="layout_mode must be a string.",
            node_id=node_id,
            layout_mode=123 
        )

    def test_validation_error_layout_wrap_not_string(self):
        node_id = "frame_14"
        self._add_figma_node_to_page(node_id)
        self.assert_error_behavior(
            func_to_call=set_layout_mode,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="layout_wrap must be a string if provided, or None.",
            node_id=node_id,
            layout_mode=LayoutModeEnum.HORIZONTAL.value,
            layout_wrap=123 
        )

    def test_validation_error_missing_node_id(self):
        with self.assertRaises(TypeError) as context: 
            set_layout_mode(layout_mode="HORIZONTAL") # type: ignore 
        self.assertTrue("required positional argument: 'node_id'" in str(context.exception) or "missing 1 required positional argument: 'node_id'" in str(context.exception))
     
    def test_validation_error_missing_layout_mode(self):
        node_id = "frame_15"
        self._add_figma_node_to_page(node_id)
        with self.assertRaises(TypeError) as context: 
            set_layout_mode(node_id=node_id) # type: ignore
        self.assertTrue("required positional argument: 'layout_mode'" in str(context.exception) or "missing 1 required positional argument: 'layout_mode'" in str(context.exception))