import copy
from datetime import datetime, timezone 
import uuid 

from figma.SimulationEngine import utils 
from figma.SimulationEngine.db import DB
from figma.SimulationEngine import custom_errors
from figma.node_editing import set_fill_color 
from common_utils.base_case import BaseTestCaseWithErrorHandler
from figma.SimulationEngine import models 
from figma.SimulationEngine.models import FillableNodeType # Import the new Enum
from typing import Any, Dict, Optional, List

class TestSetFillColor(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        # Define the list of supported types using the Enum for constructing expected messages
        self.supported_node_types_for_fill_strings = [member.value for member in FillableNodeType]

        DB["files"] = [
            {
                "fileKey": "file_key_for_set_fill",
                "name": "Test File for Set Fill",
                "document": {
                    "id": "doc_fill_test:0", "type": "DOCUMENT",
                    "children": [
                        {
                            "id": "canvas_fill_test:1", "type": "CANVAS",
                            "children": [
                                {
                                    "id": "text_node_1", "type": "TEXT", "name": "Text Node 1",
                                    "fills": [{"type": "SOLID", "color": {"r": 0.1, "g": 0.1, "b": 0.1}, "opacity": 0.5, "visible": True, "blendMode": "NORMAL"}]
                                },
                                {
                                    "id": "frame_node_1", "type": "FRAME", "name": "Frame Node 1",
                                    "fills": [] 
                                },
                                {
                                    "id": "frame_node_gradient", "type": "FRAME", "name": "Frame Node Gradient",
                                    "fills": [{"type": "GRADIENT_LINEAR", "gradientStops": [{"color":{"r":0,"g":0,"b":1,"a":1}, "position":0}]}]
                                },
                                {
                                    "id": "unsupported_node_1", "type": "GROUP", "name": "Group Node 1", 
                                    "children": []
                                },
                                {
                                    "id": "unsupported_node_no_fills", "type": "SLICE", "name": "Slice Node"
                                },
                                {
                                    "id": "text_node_malformed_fills_none", "type": "TEXT", "name": "Text Node Malformed Fills (None)",
                                    "fills": None 
                                },
                                {
                                    "id": "text_node_no_fills_key", "type": "TEXT", "name": "Text Node No Fills Key"
                                },
                                {
                                    "id": "text_node_fills_is_dict", "type": "TEXT", "name": "Text Node Fills Is Dict",
                                    "fills": {} 
                                },
                                {
                                    "id": "text_node_malformed_fill_item", "type": "TEXT", "name": "Text Node Malformed Fill Item",
                                    "fills": [{"type": "SOLID"}] 
                                },
                                {
                                    "id": "text_node_fill_item_not_dict", "type": "TEXT", "name": "Text Node Fill Item Not Dict",
                                    "fills": [None] 
                                }
                            ]
                        }
                    ]
                }
            }
        ]

        DB["current_file_key"] = 'file_key_for_set_fill'


    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_node_from_db(self, node_id: str) -> Optional[Dict[str, Any]]:
        return utils.find_node_dict_in_DB(DB, node_id)


    # Success Cases (remain the same)
    def test_set_fill_text_node_rgb_alpha_defaults_to_one(self):
        node_id = "text_node_1"
        result = set_fill_color(node_id, 0.2, 0.3, 0.4, a=1.0) 
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node); self.assertIn('fills', node); self.assertTrue(len(node['fills']) > 0) # type: ignore
        fill = node['fills'][0] # type: ignore
        self.assertEqual(fill['type'], "SOLID")
        self.assertAlmostEqual(fill['color']['r'], 0.2)
        self.assertAlmostEqual(fill['color']['g'], 0.3)
        self.assertAlmostEqual(fill['color']['b'], 0.4)
        self.assertAlmostEqual(fill['opacity'], 1.0)

    def test_set_fill_frame_node_with_empty_fills_rgba(self):
        node_id = "frame_node_1" 
        result = set_fill_color(node_id, 0.5, 0.6, 0.7, 0.8)
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node); self.assertEqual(len(node['fills']), 1) # type: ignore
        fill = node['fills'][0] # type: ignore
        self.assertEqual(fill['type'], "SOLID")
        self.assertAlmostEqual(fill['color']['r'], 0.5)
        self.assertAlmostEqual(fill['color']['g'], 0.6)
        self.assertAlmostEqual(fill['color']['b'], 0.7)
        self.assertAlmostEqual(fill['opacity'], 0.8)

    def test_set_fill_updates_existing_solid_fill(self):
        node_id = "text_node_1" 
        node_before = self._get_node_from_db(node_id)
        self.assertIsNotNone(node_before)
        original_fills_count = len(node_before.get('fills', [])) # type: ignore
        result = set_fill_color(node_id, 0.9, 0.8, 0.7, 0.6)
        self.assertEqual(result, {})
        node_after = self._get_node_from_db(node_id)
        self.assertIsNotNone(node_after)
        self.assertEqual(len(node_after['fills']), original_fills_count if original_fills_count > 0 else 1) # type: ignore
        fill = node_after['fills'][0] # type: ignore
        self.assertEqual(fill['type'], "SOLID")
        self.assertAlmostEqual(fill['color']['r'], 0.9)
        self.assertAlmostEqual(fill['color']['g'], 0.8)
        self.assertAlmostEqual(fill['color']['b'], 0.7)
        self.assertAlmostEqual(fill['opacity'], 0.6)

    def test_set_fill_prepends_solid_fill_if_first_is_not_solid(self):
        node_id = "frame_node_gradient" 
        node_before = self._get_node_from_db(node_id)
        self.assertIsNotNone(node_before)
        original_fills = copy.deepcopy(node_before.get('fills',[])) # type: ignore
        original_fills_count = len(original_fills)
        result = set_fill_color(node_id, 0.1, 0.2, 0.3, 0.4)
        self.assertEqual(result, {})
        node_after = self._get_node_from_db(node_id)
        self.assertIsNotNone(node_after)
        self.assertEqual(len(node_after['fills']), original_fills_count + 1) # type: ignore
        new_solid_fill = node_after['fills'][0] # type: ignore
        self.assertEqual(new_solid_fill['type'], "SOLID")
        self.assertAlmostEqual(new_solid_fill['color']['r'], 0.1)
        self.assertAlmostEqual(new_solid_fill['color']['g'], 0.2)
        self.assertAlmostEqual(new_solid_fill['color']['b'], 0.3)
        self.assertAlmostEqual(new_solid_fill['opacity'], 0.4)
        self.assertEqual(node_after['fills'][1:], original_fills) # type: ignore

    def test_set_fill_with_alpha_explicitly_default(self): 
        node_id = "frame_node_1"
        result = set_fill_color(node_id, 0.2, 0.3, 0.4) 
        self.assertEqual(result, {})
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        fill = node['fills'][0] # type: ignore
        self.assertAlmostEqual(fill['opacity'], 1.0) 

    def test_set_fill_with_alpha_zero_and_one(self):
        node_id = "frame_node_1"
        set_fill_color(node_id, 0.2, 0.3, 0.4, a=0.0)
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        fill = node['fills'][0] # type: ignore
        self.assertAlmostEqual(fill['opacity'], 0.0)
        set_fill_color(node_id, 0.3, 0.4, 0.5, a=1.0) 
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        fill = node['fills'][0] # type: ignore
        self.assertAlmostEqual(fill['color']['r'], 0.3)
        self.assertAlmostEqual(fill['opacity'], 1.0)

    def test_set_fill_with_rgb_components_at_boundaries(self):
        node_id = "frame_node_1"
        set_fill_color(node_id, 0.0, 0.0, 0.0, a=0.5) 
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        fill = node['fills'][0] # type: ignore
        self.assertAlmostEqual(fill['color']['r'], 0.0); self.assertAlmostEqual(fill['color']['g'], 0.0); self.assertAlmostEqual(fill['color']['b'], 0.0)
        self.assertAlmostEqual(fill['opacity'], 0.5)
        set_fill_color(node_id, 1.0, 1.0, 1.0, a=0.7) 
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        fill = node['fills'][0] # type: ignore
        self.assertAlmostEqual(fill['color']['r'], 1.0); self.assertAlmostEqual(fill['color']['g'], 1.0); self.assertAlmostEqual(fill['color']['b'], 1.0)
        self.assertAlmostEqual(fill['opacity'], 0.7)

    # Error Cases: NodeNotFoundError
    def test_node_not_found_error(self):
        node_id = "non_existent_node_id"
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.NodeNotFoundError,
            expected_message=f"Node with ID '{node_id}' not found.",
            node_id=node_id, r=0.5, g=0.5, b=0.5
        )

    # Error Cases: NodeTypeError
    def test_node_type_error_for_unsupported_type_with_fills_prop(self):
        node_id = "unsupported_node_1" # GROUP type
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node) 
        node_type_str = node.get('type', 'UNKNOWN')
        supported_types_str = ", ".join(self.supported_node_types_for_fill_strings)

        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.NodeTypeError,
            expected_message=f"Node with ID '{node_id}' (type: {node_type_str}) does not support direct fill color modification via this function. Supported types for direct fill are: {supported_types_str}.",
            node_id=node_id, r=0.5, g=0.5, b=0.5
        )

    def test_node_type_error_for_unsupported_type_without_fills_prop(self):
        node_id = "unsupported_node_no_fills" # SLICE type
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node)
        node_type_str = node.get('type', 'UNKNOWN')
        supported_types_str = ", ".join(self.supported_node_types_for_fill_strings)
        
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.NodeTypeError,
            expected_message=f"Node with ID '{node_id}' (type: {node_type_str}) does not support direct fill color modification via this function. Supported types for direct fill are: {supported_types_str}.",
            node_id=node_id, r=0.5, g=0.5, b=0.5
        )

    # Error Cases: InvalidColorError (r, g, b, a outside [0.0, 1.0])
    def _test_invalid_color_component(self, comp_name: str, invalid_value: float, **kwargs):
        base_args = {"node_id": "text_node_1", "r": 0.5, "g": 0.5, "b": 0.5, "a": 0.5}
        base_args.update(kwargs)
        base_args[comp_name] = invalid_value
        
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.InvalidColorError,
            expected_message=f"Color component '{comp_name}' value {invalid_value} is outside the valid range [0.0, 1.0].",
            **base_args
        )

    def test_invalid_color_r_too_low(self): self._test_invalid_color_component('r', -0.1)
    def test_invalid_color_r_too_high(self): self._test_invalid_color_component('r', 1.1)
    def test_invalid_color_g_too_low(self): self._test_invalid_color_component('g', -0.1)
    def test_invalid_color_g_too_high(self): self._test_invalid_color_component('g', 1.1)
    def test_invalid_color_b_too_low(self): self._test_invalid_color_component('b', -0.1)
    def test_invalid_color_b_too_high(self): self._test_invalid_color_component('b', 1.1)
    def test_invalid_color_a_too_low(self): self._test_invalid_color_component('a', -0.1, a=-0.1)
    def test_invalid_color_a_too_high(self): self._test_invalid_color_component('a', 1.1, a=1.1)

    # Error Cases: FigmaOperationError (malformed DB state)
    def test_figma_operation_error_fills_property_is_none(self):
        node_id = "text_node_malformed_fills_none" 
        set_fill_color(node_id=node_id, r=0.5, g=0.5, b=0.5)
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node); self.assertIsInstance(node.get('fills'), list) # type: ignore
        self.assertEqual(len(node.get('fills')), 1) # type: ignore
        self.assertEqual(node.get('fills')[0].get('type'), "SOLID") # type: ignore

    def test_figma_operation_error_fills_key_missing(self):
        node_id = "text_node_no_fills_key"
        set_fill_color(node_id=node_id, r=0.5, g=0.5, b=0.5)
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node); self.assertIsInstance(node.get('fills'), list) # type: ignore
        self.assertEqual(len(node.get('fills')), 1) # type: ignore
        self.assertEqual(node.get('fills')[0].get('type'), "SOLID") # type: ignore

    def test_figma_operation_error_fills_property_is_dict_not_list(self):
        node_id = "text_node_fills_is_dict" 
        set_fill_color(node_id=node_id, r=0.5, g=0.5, b=0.5)
        node = self._get_node_from_db(node_id)
        self.assertIsNotNone(node); self.assertIsInstance(node.get('fills'), list) # type: ignore
        self.assertEqual(len(node.get('fills')), 1) # type: ignore
        self.assertEqual(node.get('fills')[0].get('type'), "SOLID") # type: ignore

    # Error Cases: ValidationError (argument type validation, missing arguments)
    def test_validation_error_node_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="node_id must be a string.", 
            node_id=12345, r=0.5, g=0.5, b=0.5 # type: ignore
        )

    def test_validation_error_g_not_float(self):
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Color component 'g' must be a number (int or float). Received type: NoneType.",
            node_id="text_node_1", r=0.5, g=None, b=0.5 # type: ignore
        )

    def test_validation_error_b_not_float(self):
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Color component 'b' must be a number (int or float). Received type: dict.",
            node_id="text_node_1", r=0.5, g=0.5, b={"value": 0.5} # type: ignore
        )

    def test_validation_error_a_not_float_when_provided(self):
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Color component 'a' must be a number (int or float). Received type: str.",
            node_id="text_node_1", r=0.5, g=0.5, b=0.5, a="not_a_float" # type: ignore
        )

    def test_validation_error_missing_node_id(self):
        with self.assertRaises(TypeError) as context: 
            set_fill_color(r=0.5, g=0.5, b=0.5) # type: ignore 
        self.assertIn("required positional argument: 'node_id'", str(context.exception))

    def test_validation_error_missing_r(self):
        with self.assertRaises(TypeError) as context:
            set_fill_color(node_id="text_node_1", g=0.5, b=0.5) # type: ignore
        self.assertIn("required positional argument: 'r'", str(context.exception))

    def test_validation_error_missing_g(self):
        with self.assertRaises(TypeError) as context:
            set_fill_color(node_id="text_node_1", r=0.5, b=0.5) # type: ignore
        self.assertIn("required positional argument: 'g'", str(context.exception))

    def test_validation_error_missing_b(self):
        with self.assertRaises(TypeError) as context:
            set_fill_color(node_id="text_node_1", r=0.5, g=0.5) # type: ignore
        self.assertIn("required positional argument: 'b'", str(context.exception))

    def test_set_fill_color_with_malformed_db(self):
        # Malform the DB to not have 'files' key
        DB.clear()
        self.assert_error_behavior(
            func_to_call=set_fill_color,
            expected_exception_type=custom_errors.NodeNotFoundError,
            expected_message="Node with ID 'text_node_1' not found.",
            node_id="text_node_1", r=0.5, g=0.5, b=0.5
        )