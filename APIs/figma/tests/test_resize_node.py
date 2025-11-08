# figma/tests/test_resize_node.py

import unittest
import copy
import os  
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function to be tested
from figma import resize_node 
from figma.SimulationEngine.db import DB 
from figma.SimulationEngine. utils import get_node_from_db
from figma.SimulationEngine.models import ResizeNodeResponse 
from figma.SimulationEngine.custom_errors import NodeNotFoundError, InvalidInputError, ResizeError
from typing import Optional, List, Dict


class TestResizeNode(BaseTestCaseWithErrorHandler):

    def _create_node_dict(self, node_id: str, width: float = 100.0, height: float = 50.0,
                          x: float = 0.0, y: float = 0.0, locked: bool = False,
                          layout_grow: float = 0.0, # Figma uses 0 or 1 for layoutGrow (0 for fixed, 1 for fill)
                          layout_align: str = "INHERIT", # Default, other options: STRETCH, MIN, CENTER, MAX
                          layout_sizing_horizontal: str = "FIXED",
                          layout_sizing_vertical: str = "FIXED",
                          abs_bounding_box_present: bool = True,
                          custom_abs_bounding_box: Optional[dict] = None,
                          node_type: str = 'RECTANGLE',
                          children: Optional[List[Dict]] = None,
                          layout_mode: str = "NONE" # For frames
                          ) -> dict:
        node = {
            'id': node_id,
            'type': node_type,
            'name': f'Node {node_id}',
            'visible': True,
            'locked': locked,
            'opacity': 1.0,
            'blendMode': 'NORMAL',
            'isMask': False,
            'layoutGrow': layout_grow if node_type != 'FRAME' else 0, # layoutGrow is for items in auto-layout
            'layoutAlign': layout_align if node_type != 'FRAME' else 'INHERIT', # layoutAlign is for items in auto-layout
            'layoutSizingHorizontal': layout_sizing_horizontal,
            'layoutSizingVertical': layout_sizing_vertical,
            'constraints': {'vertical': 'TOP', 'horizontal': 'LEFT'},
            'fills': [{'type': 'SOLID', 'color': {'r': 0.5, 'g': 0.5, 'b': 0.5, 'a': 1.0}, 'visible': True}],
            'strokes': [],
            'strokeWeight': 0.0,
            'strokeAlign': 'INSIDE',
            'effects': [],
            'children': children if children is not None else [],
        }
        if node_type == 'FRAME':
            node['layoutMode'] = layout_mode
            node['clipsContent'] = True
            # Auto-layout specific properties for frame itself
            node['primaryAxisSizingMode'] = "AUTO" # HUG
            node['counterAxisSizingMode'] = "AUTO" # HUG
            node['paddingLeft'] = 0
            node['paddingRight'] = 0
            node['paddingTop'] = 0
            node['paddingBottom'] = 0
            node['itemSpacing'] = 0


        if abs_bounding_box_present:
            if custom_abs_bounding_box is not None:
                 node['absoluteBoundingBox'] = custom_abs_bounding_box
            else:
                # For items in auto-layout, x,y in absoluteBoundingBox are relative to canvas,
                # but their actual position is determined by layout.
                # Width/height in absoluteBoundingBox for auto-layout children can be what they *would* be if not for overrides.
                node['absoluteBoundingBox'] = {'x': x, 'y': y, 'width': width, 'height': height}
        elif node_type != 'FRAME': # Frames often have bounding boxes even if children define size
             node['absoluteBoundingBox'] = None # Explicitly set to None if not present for non-frames
        
        # If it's a frame and abs_bounding_box_present is true, ensure it has one
        if node_type == 'FRAME' and abs_bounding_box_present and 'absoluteBoundingBox' not in node:
             node['absoluteBoundingBox'] = {'x': x, 'y': y, 'width': width, 'height': height}


        return node

    def _add_file_with_canvas_and_nodes(self, file_key: str, nodes_on_canvas: list):
        if 'files' not in self.DB or not isinstance(self.DB.get('files'), list):
            self.DB['files'] = []
            self.DB['current_file_key'] = file_key 

        self.DB['files'].append({
            'fileKey': file_key,
            'name': f'Test File {file_key}',
            'document': {
                'id': f'0:{file_key}', 
                'name': 'Page 1',
                'type': 'DOCUMENT',
                'children': [
                    {
                        'id': f'1:{file_key}', 
                        'name': 'Canvas 1',
                        'type': 'CANVAS',
                        'children': nodes_on_canvas, # These are the direct children of the canvas
                        'backgroundColor': {'r': 0.9, 'g': 0.9, 'b': 0.9, 'a': 1.0},
                    }
                ]
            },
        })

    def setUp(self):
        global DB 
        self.DB = DB 
        self.DB.clear()

        self.file_key = "test_file_key_1"
        self.node1_id = "10:1" 
        self.node2_id = "10:2" 
        self.node3_id = "10:3" 
        
        self.auto_layout_frame_id = "20:1" # Parent frame for auto-layout tests
        self.node4_id = "10:4" # layoutGrow = 1.0, child of auto_layout_frame_id (Horizontal Layout)
        self.node5_id = "10:5" # layoutSizingHorizontal = "FILL", child of auto_layout_frame_id
        
        self.auto_layout_frame_vertical_id = "20:2" # Parent frame for vertical auto-layout tests
        self.node6_id = "10:6" # layoutSizingVertical = "FILL", child of auto_layout_frame_vertical_id (Vertical Layout)
        self.node6b_id = "10:6b" # layoutGrow = 1.0, child of auto_layout_frame_vertical_id (Vertical Layout)


        self.node7_id = "10:7" 
        self.node8_id = "10:8" 
        self.node9_id = "10:9" 
        self.node10_id = "10:10" 


        node1 = self._create_node_dict(self.node1_id, width=100.0, height=50.0, x=10.0, y=20.0)
        node2 = self._create_node_dict(self.node2_id, width=60.0, height=60.0, locked=True)
        node3 = self._create_node_dict(self.node3_id, abs_bounding_box_present=False)
        
        # Children for the HORIZONTAL auto-layout frame
        node4_child = self._create_node_dict(self.node4_id, width=10.0, height=55.0, layout_grow=1.0, layout_sizing_vertical="FIXED")
        node5_child = self._create_node_dict(self.node5_id, width=10.0, height=65.0, layout_sizing_horizontal="FILL", layout_sizing_vertical="FIXED")
        
        auto_layout_frame_horizontal = self._create_node_dict(
            self.auto_layout_frame_id,
            node_type='FRAME',
            layout_mode='HORIZONTAL',
            x=50.0, y=50.0, width=200.0, height=100.0, # BBox for the frame itself
            children=[node4_child, node5_child]
        )

        # Children for the VERTICAL auto-layout frame
        node6_child = self._create_node_dict(self.node6_id, width=130.0, height=10.0, layout_sizing_horizontal="FIXED", layout_sizing_vertical="FILL")
        node6b_child = self._create_node_dict(self.node6b_id, width=100.0, height=10.0, layout_grow=1.0, layout_sizing_horizontal="FIXED")

        auto_layout_frame_vertical = self._create_node_dict(
            self.auto_layout_frame_vertical_id,
            node_type='FRAME',
            layout_mode='VERTICAL',
            x=50.0, y=200.0, width=150.0, height=200.0, # BBox for the frame itself
            children=[node6_child, node6b_child]
        )

        node7 = self._create_node_dict(self.node7_id, custom_abs_bounding_box={'x':5.0, 'y':15.0, 'width':30.0}) 
        node8 = self._create_node_dict(self.node8_id, custom_abs_bounding_box={'x':8.0, 'y':18.0, 'height':40.0}) 
        node9 = self._create_node_dict(self.node9_id, custom_abs_bounding_box={'width':20.0, 'height':25.0}) 

        node10 = self._create_node_dict(self.node10_id, custom_abs_bounding_box={'x':10.0, 'y':20.0, 'width':100.0, 'height':50.0}, layout_align='STRETCH') 

        nodes_for_file = [
            node1, node2, node3, 
            auto_layout_frame_horizontal, # This frame contains node4 and node5
            auto_layout_frame_vertical,   # This frame contains node6 and node6b
            node7, node8, node9, node10
        ]
        self._add_file_with_canvas_and_nodes(self.file_key, nodes_for_file)

    def test_resize_existing_node_successful(self):
        new_width, new_height = 150.0, 75.0
        response = resize_node(self.node1_id, new_width, new_height)

        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.node_id, self.node1_id)
        self.assertEqual(validated_response.final_width, new_width)
        self.assertEqual(validated_response.final_height, new_height)

        updated_node_db = get_node_from_db(DB,self.node1_id)
        self.assertIsNotNone(updated_node_db)
        self.assertIsNotNone(updated_node_db.get('absoluteBoundingBox'))
        self.assertEqual(updated_node_db['absoluteBoundingBox']['width'], new_width)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['height'], new_height)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['x'], 10.0) 
        self.assertEqual(updated_node_db['absoluteBoundingBox']['y'], 20.0)

    def test_resize_node_to_zero_dimensions(self):
        new_width, new_height = 0.0, 0.0
        response = resize_node(self.node1_id, new_width, new_height)

        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.final_width, new_width)
        self.assertEqual(validated_response.final_height, new_height)

        updated_node_db = get_node_from_db(DB,self.node1_id)
        self.assertIsNotNone(updated_node_db)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['width'], new_width)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['height'], new_height)

    def test_resize_node_without_initial_bounding_box(self):
        new_width, new_height = 80.0, 40.0
        response = resize_node(self.node3_id, new_width, new_height)

        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.node_id, self.node3_id)
        self.assertEqual(validated_response.final_width, new_width)
        self.assertEqual(validated_response.final_height, new_height)

        updated_node_db = get_node_from_db(DB,self.node3_id)
        self.assertIsNotNone(updated_node_db)
        self.assertIsNotNone(updated_node_db.get('absoluteBoundingBox'))
        self.assertEqual(updated_node_db['absoluteBoundingBox']['width'], new_width)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['height'], new_height)
        self.assertEqual(updated_node_db['absoluteBoundingBox'].get('x', 0.0), 0.0) 
        self.assertEqual(updated_node_db['absoluteBoundingBox'].get('y', 0.0), 0.0) 

    def test_resize_node_with_partial_bounding_box_missing_height(self):
        new_width, new_height = 60.0, 70.0
        response = resize_node(self.node7_id, new_width, new_height)

        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.node_id, self.node7_id)
        self.assertEqual(validated_response.final_width, new_width)
        self.assertEqual(validated_response.final_height, new_height)

        updated_node_db = get_node_from_db(DB,self.node7_id)
        self.assertIsNotNone(updated_node_db)
        self.assertIsNotNone(updated_node_db.get('absoluteBoundingBox'))
        self.assertEqual(updated_node_db['absoluteBoundingBox']['width'], new_width)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['height'], new_height)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['x'], 5.0) 
        self.assertEqual(updated_node_db['absoluteBoundingBox']['y'], 15.0)

    def test_resize_node_with_partial_bounding_box_missing_width(self):
        new_width, new_height = 65.0, 75.0
        response = resize_node(self.node8_id, new_width, new_height)

        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.node_id, self.node8_id)
        self.assertEqual(validated_response.final_width, new_width)
        self.assertEqual(validated_response.final_height, new_height)

        updated_node_db = get_node_from_db(DB,self.node8_id)
        self.assertIsNotNone(updated_node_db)
        self.assertIsNotNone(updated_node_db.get('absoluteBoundingBox'))
        self.assertEqual(updated_node_db['absoluteBoundingBox']['width'], new_width)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['height'], new_height)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['x'], 8.0) 
        self.assertEqual(updated_node_db['absoluteBoundingBox']['y'], 18.0)

    def test_resize_node_with_partial_bounding_box_missing_xy(self):
        new_width, new_height = 55.0, 65.0
        response = resize_node(self.node9_id, new_width, new_height)

        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.node_id, self.node9_id)
        self.assertEqual(validated_response.final_width, new_width)
        self.assertEqual(validated_response.final_height, new_height)

        updated_node_db = get_node_from_db(DB,self.node9_id)
        self.assertIsNotNone(updated_node_db)
        self.assertIsNotNone(updated_node_db.get('absoluteBoundingBox'))
        self.assertEqual(updated_node_db['absoluteBoundingBox']['width'], new_width)
        self.assertEqual(updated_node_db['absoluteBoundingBox']['height'], new_height)
        self.assertEqual(updated_node_db['absoluteBoundingBox'].get('x', 0.0), 0.0) 
        self.assertEqual(updated_node_db['absoluteBoundingBox'].get('y', 0.0), 0.0) 

    def test_resize_node_not_found(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=NodeNotFoundError,
            expected_message="Node with ID 'nonexistent:node:id' not found.",
            node_id="nonexistent:node:id",
            width=100.0,
            height=100.0
        )

    def test_resize_invalid_input_negative_width(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=InvalidInputError,
            expected_message="Width and height must be non-negative values.",
            node_id=self.node1_id,
            width=-10.0,
            height=100.0
        )

    def test_resize_invalid_input_negative_height(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=InvalidInputError,
            expected_message="Width and height must be non-negative values.",
            node_id=self.node1_id,
            width=100.0,
            height=-10.0
        )

    def test_resize_invalid_input_both_negative(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=InvalidInputError,
            expected_message="Width and height must be non-negative values.",
            node_id=self.node1_id,
            width=-5.0,
            height=-10.0
        )

    def test_resize_error_node_locked(self):
        original_node_copy = copy.deepcopy(get_node_from_db(DB,self.node2_id))
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=ResizeError,
            expected_message=f"Node '{self.node2_id}' is locked and cannot be resized.",
            node_id=self.node2_id, 
            width=100.0,
            height=100.0
        )
        updated_node_db = get_node_from_db(DB,self.node2_id)
        self.assertEqual(updated_node_db, original_node_copy, "DB should not be modified for locked node.")


    def test_resize_error_node_layout_grow_in_horizontal_frame(self):
        """Test resizing a node with layoutGrow=1 in a HORIZONTAL auto-layout parent."""
        original_node_copy = copy.deepcopy(get_node_from_db(DB,self.node4_id))
        expected_msg = f"Node '{self.node4_id}' cannot be resized: width is controlled by auto-layout parent (due to: layoutGrow is 1 (fills main-axis width))."
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=ResizeError,
            expected_message=expected_msg,
            node_id=self.node4_id, # Child of auto_layout_frame_horizontal
            width=100.0,
            height=100.0 
        )
        updated_node_db = get_node_from_db(DB,self.node4_id)
        self.assertEqual(updated_node_db, original_node_copy, "DB should not be modified for layoutGrow node in horizontal layout.")

    def test_resize_error_node_layout_sizing_horizontal_fill(self):
        """Test resizing a node with layoutSizingHorizontal='FILL' in an auto-layout parent."""
        original_node_copy = copy.deepcopy(get_node_from_db(DB,self.node5_id))
        expected_msg = f"Node '{self.node5_id}' cannot be resized: width is controlled by auto-layout parent (due to: layoutSizingHorizontal is FILL)."
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=ResizeError,
            expected_message=expected_msg,
            node_id=self.node5_id, # Child of auto_layout_frame_horizontal
            width=100.0,
            height=100.0
        )
        updated_node_db = get_node_from_db(DB,self.node5_id)
        self.assertEqual(updated_node_db, original_node_copy, "DB should not be modified for layoutSizingHorizontal FILL node.")

    def test_resize_error_node_layout_sizing_vertical_fill_in_vertical_frame(self):
        """Test resizing a node with layoutSizingVertical='FILL' in a VERTICAL auto-layout parent."""
        original_node_copy = copy.deepcopy(get_node_from_db(DB,self.node6_id))
        expected_msg = f"Node '{self.node6_id}' cannot be resized: height is controlled by auto-layout parent (due to: layoutSizingVertical is FILL)."
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=ResizeError,
            expected_message=expected_msg,
            node_id=self.node6_id, # Child of auto_layout_frame_vertical
            width=100.0,
            height=100.0
        )
        updated_node_db = get_node_from_db(DB,self.node6_id)
        self.assertEqual(updated_node_db, original_node_copy, "DB should not be modified for layoutSizingVertical FILL node in vertical layout.")

    def test_resize_error_node_layout_grow_in_vertical_frame(self):
        """Test resizing a node with layoutGrow=1 in a VERTICAL auto-layout parent."""
        original_node_copy = copy.deepcopy(get_node_from_db(DB,self.node6b_id))
        # In a vertical layout, layoutGrow=1 affects height.
        expected_msg = f"Node '{self.node6b_id}' cannot be resized: height is controlled by auto-layout parent (due to: layoutGrow is 1 (fills main-axis height))."
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=ResizeError,
            expected_message=expected_msg,
            node_id=self.node6b_id, # Child of auto_layout_frame_vertical
            width=100.0, 
            height=100.0 
        )
        updated_node_db = get_node_from_db(DB,self.node6b_id)
        self.assertEqual(updated_node_db, original_node_copy, "DB should not be modified for layoutGrow node in vertical layout.")

    def test_resize_node_with_layout_align_stretch(self):
        """Test resizing a node with layoutAlign='STRETCH'."""
        response = resize_node(self.node10_id, 150.0, 150.0)
        validated_response = ResizeNodeResponse(**response)
        self.assertEqual(validated_response.node_id, self.node10_id)
        self.assertEqual(validated_response.final_width, 150.0)
        self.assertEqual(validated_response.final_height, 150.0)

        updated_node_db = get_node_from_db(DB,self.node10_id)
        self.assertIsNotNone(updated_node_db)
        self.assertIsNotNone(updated_node_db.get('absoluteBoundingBox'))

    def test_resize_node_with_invalid_node_id(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=InvalidInputError,
            expected_message="node_id must be a string.",
            node_id=123,
            width=100.0,
            height=100.0
        )

    def test_resize_node_with_invalid_width(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=InvalidInputError,
            expected_message="width must be a number (int or float).",
            node_id=self.node1_id,
            width="not_a_number",
            height=100.0
        )
    
    def test_resize_node_with_invalid_height(self):
        self.assert_error_behavior(
            func_to_call=resize_node,
            expected_exception_type=InvalidInputError,
            expected_message="height must be a number (int or float).",
            node_id=self.node1_id,
            width=100.0,
            height="not_a_number"
        )

if __name__ == '__main__':
    unittest.main()
