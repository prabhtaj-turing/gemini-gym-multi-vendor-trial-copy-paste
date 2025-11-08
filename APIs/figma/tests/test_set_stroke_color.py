# figma/tests/test_set_stroke_color.py

import unittest
import copy
import os  
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function to be tested
from figma import set_stroke_color 
from figma.SimulationEngine.db import DB 
from figma.SimulationEngine. utils import get_node_from_db
from figma.SimulationEngine.custom_errors import NodeNotFoundError, InvalidInputError, NodeTypeSupportError, InvalidColorError
from typing import Optional, List, Dict

import unittest
import copy


class TestSetStrokeColor(BaseTestCaseWithErrorHandler):

    def setUp(self):
        global DB
        self.DB = DB 
        self.DB.clear()
        self.DB['current_file_key'] = 'test_file_key_123'
        self.DB['files'] = [
            {
                'fileKey': 'test_file_key_123',
                'name': 'Test Figma File',
                'lastModified': '2024-01-15T10:00:00Z',
                'thumbnailUrl': 'https://example.com/thumbnail.png',
                'document': {
                    'id': 'doc-0:0', # Document node ID
                    'name': 'Main Document',
                    'type': 'DOCUMENT',
                    'children': [
                        {
                            'id': 'canvas-0:1', # Canvas node ID
                            'name': 'Page 1',
                            'type': 'CANVAS',
                            'children': [
                                {
                                    'id': '1:1',
                                    'name': 'Rectangle_NoStrokes_NoWeight',
                                    'type': 'RECTANGLE',
                                },
                                {
                                    'id': '1:2',
                                    'name': 'Rectangle_WithSolidStroke_WithWeight',
                                    'type': 'RECTANGLE',
                                    'strokes': [
                                        {'type': 'SOLID', 'visible': True, 'color': {'r': 0, 'g': 0, 'b': 0, 'a': 1}, 'opacity': 1.0, 'blendMode': 'NORMAL'}
                                    ],
                                    'strokeWeight': 2.0
                                },
                                {
                                    'id': '1:3',
                                    'name': 'Rectangle_EmptyStrokesList_NoWeight',
                                    'type': 'RECTANGLE',
                                    'strokes': [], 
                                },
                                {
                                    'id': '1:4',
                                    'name': 'Rectangle_InvisibleSolidStroke_WithWeight',
                                    'type': 'RECTANGLE',
                                    'strokes': [
                                        {'type': 'SOLID', 'visible': False, 'color': {'r': 0.1, 'g': 0.1, 'b': 0.1, 'a': 1}, 'opacity': 1.0, 'blendMode': 'NORMAL'}
                                    ],
                                    'strokeWeight': 1.0
                                },
                                {
                                    'id': '1:5',
                                    'name': 'Rectangle_NonSolidStroke_WithWeight',
                                    'type': 'RECTANGLE',
                                    'strokes': [
                                        {'type': 'GRADIENT_LINEAR', 'visible': True, 'gradientHandlePositions': [[0,0],[1,1]], 'gradientStops': [{'color':{'r':0,'g':0,'b':0,'a':1}, 'position':0}]}
                                    ],
                                    'strokeWeight': 1.5
                                },
                                {
                                    'id': '1:6',
                                    'name': 'TextNode_NoStrokes_NoWeight',
                                    'type': 'TEXT',
                                    'characters': 'Hello'
                                },
                                {
                                    'id': '1:7',
                                    'name': 'FrameNode_WithWeight_NoStrokesKey', 
                                    'type': 'FRAME',
                                    'strokeWeight': 3.0 
                                },
                                {
                                    'id': '1:8', 
                                    'name': 'Rectangle_MultipleStrokes_OneVisibleSolid',
                                    'type': 'RECTANGLE',
                                    'strokes': [
                                        {'type': 'SOLID', 'visible': False, 'color': {'r': 0, 'g': 0, 'b': 0, 'a': 1}, 'opacity': 0.5}, 
                                        {'type': 'SOLID', 'visible': True, 'color': {'r': 0.1, 'g': 0.1, 'b': 0.1, 'a': 1}, 'opacity': 1.0}, 
                                        {'type': 'GRADIENT_LINEAR', 'visible': True, 'gradientHandlePositions': [], 'gradientStops': []}, 
                                        {'type': 'SOLID', 'visible': True, 'color': {'r': 0.2, 'g': 0.2, 'b': 0.2, 'a': 1}, 'opacity': 0.8}
                                    ],
                                    'strokeWeight': 1.0
                                },
                                {
                                    'id': '1:9',
                                    'name': 'GroupNode', # Unsupported type for direct stroke
                                    'type': 'GROUP', 
                                    'children': []
                                }
                            ]
                        }
                    ]
                }
            }
        ]

    def assert_error_behavior(self, func_to_call, expected_exception_type, expected_message=None, **kwargs):
        with self.assertRaises(expected_exception_type) as cm:
            func_to_call(**kwargs)
        if expected_message:
            self.assertEqual(str(cm.exception), expected_message)

    # --- Success Test Cases ---

    def test_set_stroke_on_node_with_no_strokes_property(self):
        node_id = '1:1' # Rectangle_NoStrokes_NoWeight
        result = set_stroke_color(node_id, red=0.5, green=0.5, blue=0.5)
        self.assertIsInstance(result, dict)

        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertIn('strokes', node)
        self.assertEqual(len(node['strokes']), 1)
        expected_stroke = {'type': 'SOLID', 'visible': True, 'color': {'r': 0.5, 'g': 0.5, 'b': 0.5, 'a': 1.0}, 'blendMode': 'NORMAL', 'opacity': 1.0}
        self.assertDictEqual(node['strokes'][0], expected_stroke)

    def test_set_stroke_on_node_with_empty_strokes_list(self):
        node_id = '1:3' # Rectangle_EmptyStrokesList_NoWeight
        result = set_stroke_color(node_id, red=0.2, green=0.3, blue=0.4, alpha=0.8, stroke_weight=2.5)
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), 1)
        expected_color = {'r': 0.2, 'g': 0.3, 'b': 0.4, 'a': 0.8}
        self.assertDictEqual(node['strokes'][0]['color'], expected_color)
        self.assertTrue(node['strokes'][0]['visible'])
        self.assertEqual(node['strokes'][0]['type'], 'SOLID')

    def test_update_existing_solid_visible_stroke(self):
        node_id = '1:2' # Rectangle_WithSolidStroke_WithWeight
        original_stroke_weight = get_node_from_db(DB, node_id)['strokeWeight']

        result = set_stroke_color(node_id, red=0.7, green=0.7, blue=0.7, alpha=0.9) # No stroke_weight provided
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), 1) # Should update existing
        expected_color = {'r': 0.7, 'g': 0.7, 'b': 0.7, 'a': 0.9}
        self.assertDictEqual(node['strokes'][0]['color'], expected_color)
        self.assertTrue(node['strokes'][0]['visible'])
        self.assertEqual(node['strokes'][0]['type'], 'SOLID')
        self.assertEqual(node.get('strokeWeight'), original_stroke_weight) # Maintained

    def test_update_stroke_and_weight_on_existing_solid_stroke(self):
        node_id = '1:2'
        result = set_stroke_color(node_id, red=0.8, green=0.8, blue=0.8, stroke_weight=5.0)
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        expected_color = {'r': 0.8, 'g': 0.8, 'b': 0.8, 'a': 1.0} # Default alpha
        self.assertDictEqual(node['strokes'][0]['color'], expected_color)
        self.assertEqual(node.get('strokeWeight'), 5.0) # Updated

    def test_add_solid_stroke_if_only_invisible_exists(self):
        node_id = '1:4' # Rectangle_InvisibleSolidStroke_WithWeight
        original_stroke_weight = get_node_from_db(DB, node_id)['strokeWeight']
        # The current logic should update the first SOLID stroke and make it visible.
        # If the interpretation was to add a new one, this test would be different.
        # Based on "Set the stroke color", modifying the existing (but making it visible) seems plausible.
        # Let's assume it finds the invisible SOLID stroke, updates its color, and makes it visible.
        result = set_stroke_color(node_id, red=0.6, green=0.6, blue=0.6)
        self.assertIsInstance(result, dict)

        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), 1) # Should update the existing one
        expected_color = {'r': 0.6, 'g': 0.6, 'b': 0.6, 'a': 1.0}
        self.assertDictEqual(node['strokes'][0]['color'], expected_color)
        self.assertTrue(node['strokes'][0]['visible']) # Made visible
        self.assertEqual(node['strokes'][0]['type'], 'SOLID')
        self.assertEqual(node.get('strokeWeight'), original_stroke_weight) # Maintained

    def test_add_solid_stroke_if_only_non_solid_exists(self):
        node_id = '1:5' # Rectangle_NonSolidStroke_WithWeight

        result = set_stroke_color(node_id, red=0.5, green=0.4, blue=0.3, stroke_weight=0.0) # stroke_weight 0
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), 2)

        new_stroke = next(s for s in node['strokes'] if s['type'] == 'SOLID')
        expected_color = {'r': 0.5, 'g': 0.4, 'b': 0.3, 'a': 1.0}
        self.assertDictEqual(new_stroke['color'], expected_color)
        self.assertTrue(new_stroke['visible'])
        self.assertEqual(node.get('strokeWeight'), 0.0) # Updated

    def test_set_stroke_on_text_node(self):
        node_id = '1:6' # TextNode_NoStrokes_NoWeight
        result = set_stroke_color(node_id, red=0.1, green=0.9, blue=0.1, alpha=0.5, stroke_weight=1.5)
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), 1)
        expected_color = {'r': 0.1, 'g': 0.9, 'b': 0.1, 'a': 0.5}
        self.assertDictEqual(node['strokes'][0]['color'], expected_color)
        self.assertEqual(node.get('strokeWeight'), 1.5)

    def test_set_stroke_on_node_with_no_strokes_key_but_has_weight(self):
        node_id = '1:7' # FrameNode_WithWeight_NoStrokesKey
        original_stroke_weight = get_node_from_db(DB, node_id)['strokeWeight']

        result = set_stroke_color(node_id, red=0.3, green=0.3, blue=0.3) # No stroke_weight provided
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), 1)
        expected_color = {'r': 0.3, 'g': 0.3, 'b': 0.3, 'a': 1.0}
        self.assertDictEqual(node['strokes'][0]['color'], expected_color)
        # Since a new stroke object is added and stroke_weight arg is None,
        # existing strokeWeight should be maintained.
        self.assertEqual(node.get('strokeWeight'), original_stroke_weight)

    def test_set_stroke_on_node_with_multiple_strokes_updates_first_visible_solid(self):
        node_id = '1:8' # Rectangle_MultipleStrokes_OneVisibleSolid
        original_node = copy.deepcopy(get_node_from_db(DB, node_id))

        result = set_stroke_color(node_id, red=0.9, green=0.1, blue=0.1, alpha=0.7)
        self.assertIsInstance(result, dict)
        node = get_node_from_db(DB, node_id)
        self.assertIsNotNone(node)
        self.assertEqual(len(node['strokes']), len(original_node['strokes']))

        # The second stroke in the original list was the first visible SOLID one.
        # original_node['strokes'][0] was SOLID, visible:False
        # original_node['strokes'][1] was SOLID, visible:True <- this one should be updated
        # original_node['strokes'][2] was GRADIENT_LINEAR
        # original_node['strokes'][3] was SOLID, visible:True

        # Check that the first stroke (originally invisible solid) is untouched
        self.assertDictEqual(node['strokes'][0], original_node['strokes'][0])

        # Check that the second stroke (first visible solid) is updated
        expected_color = {'r': 0.9, 'g': 0.1, 'b': 0.1, 'a': 0.7}
        self.assertDictEqual(node['strokes'][1]['color'], expected_color)
        self.assertTrue(node['strokes'][1]['visible']) # Should remain/be set visible
        self.assertEqual(node['strokes'][1]['type'], 'SOLID')
        if 'opacity' in original_node['strokes'][1]: # Preserve other properties like opacity
             self.assertEqual(node['strokes'][1].get('opacity'), original_node['strokes'][1].get('opacity'))


        # Check that other strokes are untouched
        self.assertDictEqual(node['strokes'][2], original_node['strokes'][2])
        self.assertDictEqual(node['strokes'][3], original_node['strokes'][3])

        self.assertEqual(node.get('strokeWeight'), original_node.get('strokeWeight')) # Maintained

    def test_alpha_zero_and_one(self):
        node_id = '1:1'
        set_stroke_color(node_id, red=0.5, green=0.5, blue=0.5, alpha=0.0)
        node = get_node_from_db(DB, node_id)
        self.assertEqual(node['strokes'][0]['color']['a'], 0.0)

        set_stroke_color(node_id, red=0.5, green=0.5, blue=0.5, alpha=1.0)
        node = get_node_from_db(DB, node_id)
        self.assertEqual(node['strokes'][0]['color']['a'], 1.0)

    def test_stroke_weight_zero(self):
        node_id = '1:1'
        set_stroke_color(node_id, red=0.5, green=0.5, blue=0.5, stroke_weight=0.0)
        node = get_node_from_db(DB, node_id)
        self.assertEqual(node.get('strokeWeight'), 0.0)

    # --- Error Test Cases ---

    def test_node_not_found_error(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=NodeNotFoundError,
            node_id='non_existent_node', red=0.5, green=0.5, blue=0.5
        )

    def test_node_type_support_error_for_group(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=NodeTypeSupportError,
            node_id='1:9', red=0.5, green=0.5, blue=0.5 # Targeting GROUP node
        )

    def test_invalid_color_error_red_low(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=-0.1, green=0.5, blue=0.5
        )

    def test_invalid_color_error_red_high(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=1.1, green=0.5, blue=0.5
        )

    def test_invalid_color_error_green_low(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=0.5, green=-0.1, blue=0.5
        )

    def test_invalid_color_error_green_high(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=0.5, green=1.1, blue=0.5
        )

    def test_invalid_color_error_blue_low(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=0.5, green=0.5, blue=-0.1
        )

    def test_invalid_color_error_blue_high(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=0.5, green=0.5, blue=1.1
        )

    def test_invalid_color_error_alpha_low(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=0.5, green=0.5, blue=0.5, alpha=-0.1
        )

    def test_invalid_color_error_alpha_high(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidColorError,
            node_id='1:1', red=0.5, green=0.5, blue=0.5, alpha=1.1
        )

    def test_invalid_input_error_negative_stroke_weight(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidInputError,
            node_id='1:1', red=0.5, green=0.5, blue=0.5, stroke_weight=-1.0
        )

    def test_invalid_input_error_node_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidInputError,
            node_id=123, red=0.5, green=0.5, blue=0.5
        )

    def test_invalid_input_error_node_id_empty(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidInputError,
            node_id="", red=0.5, green=0.5, blue=0.5
        )

    def test_invalid_input_error_color_component_not_numeric(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidInputError,
            node_id='1:1', red='not a number', green=0.5, blue=0.5
        )

    def test_invalid_input_error_stroke_weight_not_numeric(self):
        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=InvalidInputError,
            node_id='1:1', red=0.5, green=0.5, blue=0.5, stroke_weight='not a number'
        )

    def test_node_not_found_with_malformed_db(self):
        # Malform the DB by removing the 'files' key, which is necessary for finding any node.
        # This simulates a state where the file data is inaccessible.
        if 'files' in self.DB:
            del self.DB['files']

        self.assert_error_behavior(
            func_to_call=set_stroke_color,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID '1:1' not found.",
            node_id='1:1', red=0.5, green=0.5, blue=0.5
        )

if __name__ == '__main__':
    unittest.main()