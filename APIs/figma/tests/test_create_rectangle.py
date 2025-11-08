import unittest
import copy
from datetime import datetime, timezone 
import uuid 

from figma.SimulationEngine import utils 
from figma.SimulationEngine.db import DB
from figma.SimulationEngine import custom_errors
from figma.node_creation import create_rectangle 
from common_utils.base_case import BaseTestCaseWithErrorHandler
# Updated import to get the Enum
from figma.SimulationEngine.models import ValidParentNodeType, Node # Assuming Node model might be useful for type checking if needed

class TestCreateRectangle(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.user_id = "me" # Not directly used by create_rectangle, but good for context
        
        DB["files"] = [
            {
                "fileKey": "file_key_1",
                "name": "Test File 1",
                "lastModified": "2023-01-01T12:00:00Z", 
                "thumbnailUrl": "https://example.com/thumb.png",
                "version": "1.0",
                "role": "owner",
                "editorType": "figma",
                "linkAccess": "view",
                "schemaVersion": 0,
                "document": {
                    "id": "doc_id_1:0", "name": "Document Node", "type": "DOCUMENT",
                    "scrollBehavior": "SCROLLS",
                    "currentPageId":"page_id_1:1",
                    "children": [
                        {
                            "id": "page_id_1:1", "name": "Page 1", "type": "CANVAS",
                            "scrollBehavior": "SCROLLS",
                            "children": [
                                {
                                    "id": "frame_id_1:10", "name": "Test Frame", "type": "FRAME",
                                    "visible": True, "locked": False, "opacity": 1.0,
                                    "blendMode": "PASS_THROUGH", "isMask": False,
                                    "absoluteBoundingBox": {"x": 50.0, "y": 50.0, "width": 200.0, "height": 150.0},
                                    "constraints": {"vertical": "TOP", "horizontal": "LEFT"},
                                    "fills": [{"type": "SOLID", "visible": True, "color": {"r": 0.8, "g": 0.8, "b": 0.8, "a": 1}}],
                                    "children": [], "clipsContent": True,
                                    "backgroundColor": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 0.0},
                                },
                                {
                                    "id": "text_id_1:20", "name": "Test Text Node", "type": "TEXT",
                                    "visible": True, "locked": False,
                                    "absoluteBoundingBox": {"x": 10.0, "y": 10.0, "width": 50.0, "height": 20.0},
                                    "fills": [{"type": "SOLID", "visible": True, "color": {"r": 0.0, "g": 0.0, "b": 0.0, "a": 1.0}}],
                                    "text": "Hello World", # Using 'text' as per your model's alias for 'characters'
                                }
                            ],
                            "backgroundColor": {"r": 0.9, "g": 0.9, "b": 0.9, "a": 1.0},
                            "prototypeStartNodeID": None,
                            "flowStartingPoints": [],
                            "prototypeDevice": {"type": "NONE", "rotation": "NONE"}
                        }
                    ]
                },
                "components": {}, "componentSets": {}, "styles": {}, 
                "globalVars": {"styles": {}, "variables": {}, "variableCollections": {}}
            }
        ]
        self.current_page_id = "page_id_1:1"
        self.valid_parent_id = "frame_id_1:10" 
        self.invalid_parent_type_id = "text_id_1:20"
        DB["current_file_key"] = "file_key_1"

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _find_node_by_id_recursive(self, nodes_list, node_id_to_find):
        for node in nodes_list:
            if not isinstance(node, dict): continue
            if node.get("id") == node_id_to_find:
                return node
            if "children" in node and isinstance(node["children"], list):
                found_in_children = self._find_node_by_id_recursive(node["children"], node_id_to_find)
                if found_in_children:
                    return found_in_children
        return None

    def _find_node_in_db(self, node_id_to_find):
        if not DB.get("files"): return None
        for f_data in DB.get("files", []):
            doc = f_data.get("document")
            if doc:
                if doc.get("id") == node_id_to_find: return doc
                if isinstance(doc.get("children"), list):
                    found_node = self._find_node_by_id_recursive(doc.get("children", []), node_id_to_find)
                    if found_node:
                        return found_node
        return None

    # --- Success Cases ---
    def test_create_minimal_rectangle_on_default_page(self):
        x, y, width, height = 10.0, 20.0, 100.0, 50.0
        result = create_rectangle(x=x, y=y, width=width, height=height)

        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        rect_id = result["id"]
        self.assertIsInstance(rect_id, str)
        self.assertTrue(len(rect_id) > 0, "Rectangle ID should not be empty")
        
        self.assertEqual(result["name"], "Rectangle") 
        self.assertEqual(result["type"], "RECTANGLE")
        self.assertEqual(result["parentId"], self.current_page_id)
        self.assertEqual(result["x"], x)
        self.assertEqual(result["y"], y)
        self.assertEqual(result["width"], width)
        self.assertEqual(result["height"], height)

        created_node_in_db = self._find_node_in_db(rect_id)
        self.assertIsNotNone(created_node_in_db, f"Node with id {rect_id} not found in DB")
        self.assertEqual(created_node_in_db.get("name"), "Rectangle")
        self.assertEqual(created_node_in_db.get("type"), "RECTANGLE")
        self.assertDictEqual(created_node_in_db.get("absoluteBoundingBox"), {"x": x, "y": y, "width": width, "height": height})

        parent_node_in_db = self._find_node_in_db(self.current_page_id)
        self.assertIsNotNone(parent_node_in_db)
        self.assertIsInstance(parent_node_in_db.get("children"), list)
        self.assertTrue(any(child.get("id") == rect_id for child in parent_node_in_db.get("children", [])),
                        f"Rectangle {rect_id} not found in children of page {self.current_page_id}")

    def test_create_rectangle_with_name_on_default_page(self):
        x, y, width, height = 15.0, 25.0, 110.0, 55.0
        name = "MyCustomRect"
        result = create_rectangle(x=x, y=y, width=width, height=height, name=name)

        self.assertEqual(result["name"], name)
        self.assertEqual(result["parentId"], self.current_page_id)
        rect_id = result["id"]

        created_node_in_db = self._find_node_in_db(rect_id)
        self.assertIsNotNone(created_node_in_db)
        self.assertEqual(created_node_in_db.get("name"), name)
        self.assertDictEqual(created_node_in_db.get("absoluteBoundingBox"), {"x": x, "y": y, "width": width, "height": height})

        parent_node_in_db = self._find_node_in_db(self.current_page_id)
        self.assertTrue(any(child.get("id") == rect_id for child in parent_node_in_db.get("children", [])))

    def test_create_rectangle_with_valid_parent_id(self):
        x, y, width, height = 5.0, 5.0, 30.0, 30.0
        name = "ChildRect"
        result = create_rectangle(x=x, y=y, width=width, height=height, name=name, parent_id=self.valid_parent_id)

        self.assertEqual(result["name"], name)
        self.assertEqual(result["parentId"], self.valid_parent_id)
        rect_id = result["id"]

        created_node_in_db = self._find_node_in_db(rect_id)
        self.assertIsNotNone(created_node_in_db)
        self.assertEqual(created_node_in_db.get("name"), name)
        self.assertDictEqual(created_node_in_db.get("absoluteBoundingBox"), {"x": x, "y": y, "width": width, "height": height})
        
        parent_node_in_db = self._find_node_in_db(self.valid_parent_id)
        self.assertIsNotNone(parent_node_in_db)
        self.assertIsInstance(parent_node_in_db.get("children"), list)
        self.assertTrue(any(child.get("id") == rect_id for child in parent_node_in_db.get("children", [])),
                        f"Rectangle {rect_id} not found in children of parent {self.valid_parent_id}")

    def test_create_rectangle_with_empty_name_string(self):
        x, y, width, height = 10.0, 20.0, 100.0, 50.0
        name = "" 
        result = create_rectangle(x=x, y=y, width=width, height=height, name=name)
        self.assertEqual(result["name"], "")
        rect_id = result["id"]
        created_node_in_db = self._find_node_in_db(rect_id)
        self.assertIsNotNone(created_node_in_db)
        self.assertEqual(created_node_in_db.get("name"), "")

    def test_create_rectangle_with_name_none(self):
        x, y, width, height = 10.0, 20.0, 100.0, 50.0
        result = create_rectangle(x=x, y=y, width=width, height=height, name=None)
        self.assertEqual(result["name"], "Rectangle") 
        rect_id = result["id"]
        created_node_in_db = self._find_node_in_db(rect_id)
        self.assertIsNotNone(created_node_in_db)
        self.assertEqual(created_node_in_db.get("name"), "Rectangle")

    def test_create_rectangle_with_zero_x_y_coordinates(self):
        x, y, width, height = 0.0, 0.0, 100.0, 50.0
        result = create_rectangle(x=x, y=y, width=width, height=height)
        self.assertEqual(result["x"], 0.0)
        self.assertEqual(result["y"], 0.0)
        rect_id = result["id"]
        created_node_in_db = self._find_node_in_db(rect_id)
        self.assertIsNotNone(created_node_in_db)
        self.assertDictEqual(created_node_in_db.get("absoluteBoundingBox"), {"x": x, "y": y, "width": width, "height": height})

    # --- Invalid Input Error Cases ---
    def test_create_rectangle_negative_width_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Rectangle width and height must be positive values.",
            x=10.0, y=20.0, width=-100.0, height=50.0
        )

    def test_create_rectangle_zero_width_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Rectangle width and height must be positive values.",
            x=10.0, y=20.0, width=0.0, height=50.0
        )

    def test_create_rectangle_negative_height_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Rectangle width and height must be positive values.",
            x=10.0, y=20.0, width=100.0, height=-50.0
        )

    def test_create_rectangle_zero_height_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Rectangle width and height must be positive values.",
            x=10.0, y=20.0, width=100.0, height=0.0
        )
    
    def test_create_rectangle_non_numeric_width_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input coordinates (x, y) and dimensions (width, height) must be valid numbers.",
            x=10.0, y=20.0, width="not-a-float", height=50.0
        )

    def test_create_rectangle_non_numeric_height_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input coordinates (x, y) and dimensions (width, height) must be valid numbers.",
            x=10.0, y=20.0, width=100.0, height=[50.0] 
        )

    def test_create_rectangle_non_numeric_x_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input coordinates (x, y) and dimensions (width, height) must be valid numbers.",
            x={"coord": 10.0}, y=20.0, width=100.0, height=50.0
        )

    def test_create_rectangle_non_numeric_y_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input coordinates (x, y) and dimensions (width, height) must be valid numbers.",
            x=10.0, y=None, width=100.0, height=50.0 
        )

    def test_create_rectangle_with_non_string_name_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Name must be a string if provided.",
            x=10.0, y=20.0, width=100.0, height=50.0, name=123
        )

    def test_create_rectangle_with_non_string_parent_id_raises_invalid_input_error(self):
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Parent ID must be a string if provided.",
            x=10.0, y=20.0, width=100.0, height=50.0, parent_id=12345
        )
    
    # --- Parent Not Found Error Cases ---
    def test_create_rectangle_non_existent_parent_id_raises_parent_not_found_error(self):
        parent_id="id_that_does_not_exist"
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.ParentNotFoundError,
            expected_message=f"Parent node with ID '{parent_id}' not found.",
            x=10.0, y=20.0, width=100.0, height=50.0, parent_id=parent_id
        )

    def test_create_rectangle_parent_id_is_not_container_raises_parent_not_found_error(self):
        parent_node = self._find_node_in_db(self.invalid_parent_type_id)
        parent_type = parent_node.get('type') if parent_node else "UNKNOWN"
        # Construct list of valid parent type strings from the Enum for the message
        valid_types_list_str = [e.value for e in ValidParentNodeType]
        
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.ParentNotFoundError,
            expected_message=f"Node with ID '{self.invalid_parent_type_id}' and type '{parent_type}' cannot be a parent. Valid parent types are: {valid_types_list_str}.",
            x=10.0, y=20.0, width=100.0, height=50.0, parent_id=self.invalid_parent_type_id
        )

    def test_create_rectangle_parent_id_is_empty_string_uses_default_parent(self):
        """Test that empty string parent_id is treated the same as None (uses default parent)."""
        parent_id=""
        result = create_rectangle(x=10.0, y=20.0, width=100.0, height=50.0, parent_id=parent_id)
        
        # Verify the rectangle was created successfully
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'RECTANGLE')
        self.assertEqual(result['x'], 10.0)
        self.assertEqual(result['y'], 20.0)
        self.assertEqual(result['width'], 100.0)
        self.assertEqual(result['height'], 50.0)
        # Should have a parent ID (the default canvas)
        self.assertIsNotNone(result['parentId'])
        # Should not be the empty string
        self.assertNotEqual(result['parentId'], "")
    
    # --- Figma Operation Error Cases for Default Parent ---
    def test_create_rectangle_db_file_not_dict_raises_figma_operation_error(self):
        # Malform DB state so the current file is not a dictionary
        DB["files"] = ["not_a_dictionary"]
        
        expected_detail_msg = "'str' object has no attribute 'get'"
        expected_error_msg = f"Cannot create rectangle: Default parent (first canvas of first file) not found or is invalid. Details: {expected_detail_msg}"

        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message=expected_error_msg,
            x=10.0, y=20.0, width=100.0, height=50.0
        )

    def test_create_rectangle_no_document_node_raises_figma_operation_error(self):
        # Malform DB state: remove 'document' from the file object
        DB["files"][0]["document"] = None
        
        expected_detail_msg = "Document node in first file is not a dictionary or is missing."
        expected_error_msg = f"Cannot create rectangle: Default parent (first canvas of first file) not found or is invalid. Details: {expected_detail_msg}"

        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message=expected_error_msg,
            x=10.0, y=20.0, width=100.0, height=50.0
        )

    def test_create_rectangle_document_with_no_children_raises_figma_operation_error(self):
        # Malform DB state: document has no children (canvases)
        DB["files"][0]["document"]["children"] = []
        
        expected_detail_msg = "Document node has no children (canvases)."
        expected_error_msg = f"Cannot create rectangle: Default parent (first canvas of first file) not found or is invalid. Details: {expected_detail_msg}"

        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message=expected_error_msg,
            x=10.0, y=20.0, width=100.0, height=50.0
        )

    def test_create_rectangle_default_parent_not_found_raises_figma_operation_error(self):
        # Malform DB state: currentPageID does not point to an existing node
        DB["files"][0]["document"]["currentPageID"] = "non-existent-page-id"
        DB['current_file_key'] = 'non-existent-page-id'
        
        expected_detail_msg = "First file entry in DB is not a dictionary."
        expected_error_msg = f"Cannot create rectangle: Default parent (first canvas of first file) not found or is invalid. Details: {expected_detail_msg}"
        self.assert_error_behavior(
            func_to_call=create_rectangle,
            expected_exception_type=custom_errors.FigmaOperationError,
            expected_message=expected_error_msg,
            x=10.0, y=20.0, width=100.0, height=50.0
        )
        
    def test_create_rectangle_default_parent_invalid_type_raises_figma_operation_error(self):
        # Modify the type of the default canvas to be invalid for parenting
        invalid_canvas_type = "TEXT_NODE_AS_CANVAS" # A clearly invalid type not in ValidParentNodeType
        
        # Ensure the default parent canvas exists and then malform its type
        if DB.get("files") and \
           isinstance(DB["files"], list) and \
           DB["files"][0] and \
           isinstance(DB["files"][0].get("document"), dict) and \
           isinstance(DB["files"][0]["document"].get("children"), list) and \
           DB["files"][0]["document"]["children"][0] and \
           isinstance(DB["files"][0]["document"]["children"][0], dict):
            
            default_canvas_dict = DB["files"][0]["document"]["children"][0]
            original_type = default_canvas_dict.get("type")
            default_canvas_dict["type"] = invalid_canvas_type # Malform the type
            
            # Construct the expected detail message from the ValueError
            from figma.SimulationEngine.models import ValidParentNodeType # Import for the message
            valid_types_list_str = [e.value for e in ValidParentNodeType]
            inner_error_msg = f"Default parent (canvas) is of an unexpected type '{invalid_canvas_type}'. Expected one of {valid_types_list_str}."
            
            expected_operation_error_msg = f"Cannot create rectangle: Default parent (first canvas of first file) not found or is invalid. Details: {inner_error_msg}"
            
            self.assert_error_behavior(
                func_to_call=create_rectangle,
                expected_exception_type=custom_errors.FigmaOperationError,
                expected_message=expected_operation_error_msg,
                x=10.0, y=20.0, width=100.0, height=50.0
                # parent_id is None to trigger default parent logic
            )
            
            # Restore original type if necessary for other tests, though tearDown should handle DB state.
            if original_type is not None:
                 default_canvas_dict["type"] = original_type
        else:
            self.fail("Default canvas for testing was not found or DB structure is unexpected.")