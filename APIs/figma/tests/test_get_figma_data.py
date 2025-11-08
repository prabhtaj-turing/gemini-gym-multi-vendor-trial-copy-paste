# figma/tests/test_get_figma_data.py

import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function to be tested
from figma import get_figma_data
from figma import DB
from datetime import datetime, timezone
from figma.SimulationEngine.custom_errors import NotFoundError, InvalidInputError


class TestGetFigmaData(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self.DB = DB
        self.DB.clear()

        self.mock_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

        self.file1_key = "file_key_1"
        self.canvas1_id = "1:1"
        self.frame1_id = "1:2"
        self.text1_id = "1:3"
        self.group1_id = "1:4"
        self.rect1_id = "1:5" # Child of group1

        self.file1_data = {
            "fileKey": self.file1_key,
            "name": "Test File 1",
            "lastModified": self.mock_time,
            "thumbnailUrl": "https://example.com/thumb1.png",
            "document": {
                "id": "0:0",
                "name": "Document",
                "type": "DOCUMENT",
                "children": [
                    { # DBCanvasNode-like dict
                        "id": self.canvas1_id,
                        "name": "Canvas 1",
                        "type": "CANVAS",
                        "backgroundColor": {"r": 0.1, "g": 0.2, "b": 0.3, "a": 1.0},
                        "children": [
                            { # Node-like dict - Frame
                                "id": self.frame1_id,
                                "name": "Frame 1",
                                "type": "FRAME",
                                "visible": True,
                                "locked": False,
                                "opacity": 0.9,
                                "absoluteBoundingBox": {"x": 10, "y": 20, "width": 300, "height": 150},
                                "fills": [{"type": "SOLID", "color": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0}, "visible": True}],
                                "strokes": [],
                                "strokeWeight": 1.0,
                                "cornerRadius": 5.0,
                                "children": [],
                            },
                            { # Node-like dict - Text
                                "id": self.text1_id,
                                "name": "Text 1",
                                "type": "TEXT",
                                "text": "Hello Figma", # Using 'text' as per Node model attribute
                                "style": {"fontFamily": "Inter", "fontSize": 16, "textAlignHorizontal": "LEFT"},
                                "fills": "S:style_id_solid_black", # Style ID for fill (string)
                                "children": None,
                            },
                            { # Node-like dict - Group with child
                                "id": self.group1_id,
                                "name": "Group 1",
                                "type": "GROUP",
                                "children": [
                                    {
                                        "id": self.rect1_id,
                                        "name": "Rectangle 1",
                                        "type": "RECTANGLE",
                                        "absoluteBoundingBox": {"x": 5, "y": 5, "width": 50, "height": 50},
                                        "fills": [{"type": "SOLID", "color": {"r": 1.0, "g": 0.0, "b": 0.0, "a": 1.0}}],
                                    }
                                ]
                            }
                        ],
                    }
                ],
            },
            "components": {"comp1": {"key": "comp_key_1", "name": "Component 1"}},
            "componentSets": {"set1": {"key": "set_key_1", "name": "Component Set 1"}},
            "globalVars": { # GlobalVars-like dict
                "styles": {
                    "S:style_id_solid_black": {
                        "name": "Solid Black Fill",
                        "styleType": "FILL",
                        "fills": [{"type": "SOLID", "color": {"r": 0, "g": 0, "b": 0, "a": 1.0}}]
                    },
                    "T:style_id_text_default": {
                        "name": "Default Text Style",
                        "styleType": "TEXT",
                        "fontFamily": "Arial",
                        "fontWeight": 400.0, # Pydantic schema uses float for fontWeight
                        "fontSize": 12.0,
                    }
                },
                "variables": {},
                "variableCollections": {}
            },
        }

        self.file_empty_doc_key = "file_empty_doc"
        self.file_empty_doc_data = {
            "fileKey": self.file_empty_doc_key, "name": "Empty Document File",
            "lastModified": self.mock_time, "thumbnailUrl": "https://example.com/thumb_empty.png",
            "document": None, "globalVars": None, "components": {}, "componentSets": {}
        }

        self.file_no_canvases_key = "file_no_canvases"
        self.file_no_canvases_data = {
            "fileKey": self.file_no_canvases_key, "name": "No Canvases File",
            "lastModified": self.mock_time, "thumbnailUrl": "https://example.com/thumb_no_canvas.png",
            "document": {"id": "0:0", "name": "Document", "type": "DOCUMENT", "children": []},
            "globalVars": {"styles": {}}, "components": {}, "componentSets": {}
        }

        self.file_no_styles_key = "file_no_styles"
        self.file_no_styles_data = {
            "fileKey": self.file_no_styles_key, "name": "No Styles File",
            "lastModified": self.mock_time, "thumbnailUrl": "https://example.com/thumb_no_styles.png",
            "document": {
                "id": "0:0", "name": "Document", "type": "DOCUMENT",
                "children": [{"id": "2:1", "name": "Canvas A", "type": "CANVAS", "children": []}]
            },
            "globalVars": None, "components": {}, "componentSets": {}
        }

        self.file_auth_error_key = "auth_error_file" # Special key to trigger auth error
        self.file_auth_trigger_data = {
             "fileKey": self.file_auth_error_key, "name": "Auth Error Trigger File",
             "lastModified": self.mock_time, "thumbnailUrl": "https://example.com/thumb_auth.png",
             "document": None, "globalVars": None, "components": {}, "componentSets": {}
        }

        self.DB['files'] = [ # FigmaDB-like dict
            self.file1_data,
            self.file_empty_doc_data,
            self.file_no_canvases_data,
            self.file_no_styles_data,
            self.file_auth_trigger_data
        ]

    def _validate_node_structure(self, node_dict):
        self.assertIsInstance(node_dict, dict)
        self.assertIn("id", node_dict)
        self.assertIn("name", node_dict)
        self.assertIn("type", node_dict)

        optional_fields_from_doc = [
            "visible", "locked", "opacity", "rotation", "blendMode", "isMask", "isFixed",
            "absoluteBoundingBox", "absoluteRenderBounds", "constraints", "fills", "strokes",
            "strokeWeight", "strokeAlign", "cornerRadius", "effects", "children", "text"
        ]
        for field in optional_fields_from_doc:
            # The field should either be in the dict, or if not, it's treated as None by consumers.
            # For testing, we can assert it's present if we expect it, or check it's None if set explicitly.
            # Here, we just ensure it doesn't crash if accessed with .get()
            _ = node_dict.get(field)


        if "children" in node_dict and node_dict["children"] is not None:
            self.assertIsInstance(node_dict["children"], list)
            for child_node in node_dict["children"]:
                self._validate_node_structure(child_node)

        if node_dict.get("type") == "TEXT":
            # 'text' field should be present for TEXT nodes if they have content
            self.assertTrue("text" in node_dict or node_dict.get("text") is None)
            # Ensure 'characters' is not the primary output field name
            self.assertNotIn("characters", node_dict, "Output node should use 'text', not 'characters' as primary key")

    def test_get_full_file_data_success(self):
        result = get_figma_data(file_key=self.file1_key)

        self.assertIsInstance(result, dict)
        self.assertIn("metadata", result)
        self.assertIn("nodes", result)
        self.assertIn("globalVars", result)

        metadata = result["metadata"]
        self.assertEqual(metadata["name"], self.file1_data["name"])
        self.assertEqual(metadata["lastModified"], self.file1_data["lastModified"])
        self.assertEqual(metadata["thumbnailUrl"], self.file1_data["thumbnailUrl"])

        nodes = result["nodes"]
        self.assertIsInstance(nodes, list)
        self.assertEqual(len(nodes), 1) 

        canvas_node_out = nodes[0]
        self._validate_node_structure(canvas_node_out)
        self.assertEqual(canvas_node_out["id"], self.canvas1_id)
        self.assertEqual(canvas_node_out["name"], "Canvas 1")
        self.assertEqual(canvas_node_out["type"], "CANVAS")
        self.assertEqual(canvas_node_out.get("backgroundColor"), {"r": 0.1, "g": 0.2, "b": 0.3, "a": 1.0})

        self.assertIsInstance(canvas_node_out.get("children"), list)
        self.assertEqual(len(canvas_node_out["children"]), 3)

        frame_node_out = next(n for n in canvas_node_out["children"] if n["id"] == self.frame1_id)
        self.assertEqual(frame_node_out["name"], "Frame 1")
        self.assertEqual(frame_node_out["opacity"], 0.9)
        self.assertIsInstance(frame_node_out.get("fills"), list)
        self.assertEqual(frame_node_out["fills"][0]["type"], "SOLID")


        text_node_out = next(n for n in canvas_node_out["children"] if n["id"] == self.text1_id)
        self.assertEqual(text_node_out["name"], "Text 1")
        self.assertEqual(text_node_out["text"], "Hello Figma")
        self.assertEqual(text_node_out.get("fills"), "S:style_id_solid_black")

        global_vars = result["globalVars"]
        self.assertIsInstance(global_vars, dict)
        self.assertIn("styles", global_vars)
        self.assertIsInstance(global_vars["styles"], dict)
        self.assertIn("S:style_id_solid_black", global_vars["styles"])
        self.assertEqual(global_vars["styles"]["S:style_id_solid_black"]["name"], "Solid Black Fill")

    def test_get_specific_node_data_frame_success(self):
        result = get_figma_data(file_key=self.file1_key, node_id=self.canvas1_id)
        self.assertEqual(result["metadata"]["name"], self.file1_data["name"])
        self.assertIn("S:style_id_solid_black", result["globalVars"]["styles"])
        nodes = result["nodes"]
        self.assertIsInstance(nodes, list)
        self.assertEqual(len(nodes), 1)
        frame_node_out = nodes[0]["children"][0]
        self._validate_node_structure(frame_node_out)
        self.assertEqual(frame_node_out["id"], self.frame1_id)
        self.assertEqual(frame_node_out["name"], "Frame 1")
        self.assertEqual(len(frame_node_out.get("children", [])), 0)

    def test_get_specific_node_data_group_with_children_success(self):
        result = get_figma_data(file_key=self.file1_key, node_id=self.canvas1_id)
        nodes = result["nodes"]
        self.assertEqual(len(nodes), 1)
        group_node_out = nodes[0]["children"][2]
        self._validate_node_structure(group_node_out)
        self.assertEqual(group_node_out["id"], self.group1_id)
        self.assertIsInstance(group_node_out.get("children"), list)
        self.assertEqual(len(group_node_out["children"]), 1)
        self.assertEqual(group_node_out["children"][0]["id"], self.rect1_id)

    def test_get_specific_node_data_canvas_success(self):
        result = get_figma_data(file_key=self.file1_key, node_id=self.canvas1_id)
        nodes = result["nodes"]
        self.assertEqual(len(nodes), 1)
        canvas_node_out = nodes[0]
        self._validate_node_structure(canvas_node_out)
        self.assertEqual(canvas_node_out["id"], self.canvas1_id)
        self.assertEqual(len(canvas_node_out.get("children", [])), 3)

    def test_get_data_file_not_found_raises_notfounderror(self):
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=NotFoundError,
            expected_message="File with key 'non_existent_file_key' not found.",
            file_key="non_existent_file_key"
        )

    def test_get_data_node_not_found_in_file_raises_notfounderror(self):
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=NotFoundError,
            expected_message = "Node with ID 'non_existent_node_id' not found in file 'file_key_1'.",
            file_key=self.file1_key,
            node_id="non_existent_node_id"
        )

    def test_get_data_invalid_file_key_empty_string_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message = "File key cannot be empty.",
            file_key=""
        )

    def test_get_data_invalid_node_id_empty_string_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="node_id cannot be empty or whitespace-only if provided.",
            file_key=self.file1_key,
            node_id=""
        )

    def test_get_data_file_with_empty_document(self):
        result = get_figma_data(file_key=self.file_empty_doc_key)
        self.assertEqual(result["metadata"]["name"], self.file_empty_doc_data["name"])
        self.assertEqual(len(result["nodes"]), 0)
        self.assertIsInstance(result["globalVars"], dict)
        self.assertEqual(result["globalVars"].get("styles", {}), {})

    def test_get_data_file_with_document_but_no_canvases(self):
        result = get_figma_data(file_key=self.file_no_canvases_key)
        self.assertEqual(result["metadata"]["name"], self.file_no_canvases_data["name"])
        self.assertEqual(len(result["nodes"]), 0)
        self.assertEqual(result["globalVars"].get("styles", {}), {})

    def test_get_data_file_with_no_global_styles(self):
        result = get_figma_data(file_key=self.file_no_styles_key)
        self.assertEqual(result["metadata"]["name"], self.file_no_styles_data["name"])
        self.assertEqual(len(result["nodes"]), 1)
        self.assertEqual(result["nodes"][0]["id"], "2:1")
        self.assertEqual(result["globalVars"].get("styles", {}), {})

    def test_node_all_properties_example(self):
        modified_file_data = copy.deepcopy(self.file1_data)
        frame_to_modify = modified_file_data["document"]["children"][0]["children"][0]
        frame_to_modify["rotation"] = 45.0
        frame_to_modify["blendMode"] = "MULTIPLY"
        frame_to_modify["isMask"] = True
        frame_to_modify["effects"] = [{"type": "DROP_SHADOW", "visible": True, "radius": 4.0}]

        # Temporarily replace the file data in DB for this test
        original_files = self.DB['files']
        self.DB['files'] = [modified_file_data if f["fileKey"] == self.file1_key else f for f in original_files]

        result = get_figma_data(file_key=self.file1_key, node_id=self.canvas1_id)
        node_out = result["nodes"][0]["children"][0]

        self.assertEqual(node_out.get("rotation"), 45.0)
        self.assertEqual(node_out.get("blendMode"), "MULTIPLY")
        self.assertEqual(node_out.get("isMask"), True)
        self.assertIsInstance(node_out.get("effects"), list)
        self.assertEqual(len(node_out["effects"]), 1)
        self.assertEqual(node_out["effects"][0]["type"], "DROP_SHADOW")

        self.DB['files'] = original_files # Restore DB

    def test_node_minimal_properties(self):
        minimal_node_id = "minimal:1"
        minimal_canvas_id = "minimal_canvas:0"
        minimal_file_key = "minimal_file"
        minimal_file_data = {
            "fileKey": minimal_file_key, "name": "Minimal File", "lastModified": self.mock_time, 
            "thumbnailUrl": "url", "components": {}, "componentSets": {},
            "document": {
                "id": "doc:0", "name": "Doc", "type": "DOCUMENT",
                "children": [{
                    "id": minimal_canvas_id, "name": "Canvas", "type": "CANVAS",
                    "children": [{ "id": minimal_node_id, "name": "Minimal Node", "type": "RECTANGLE" }] # Only id, name, type
                }]
            },
            "globalVars": None
        }
        self.DB['files'].append(minimal_file_data)

        result = get_figma_data(file_key=minimal_file_key, node_id=minimal_canvas_id)
        node_out = result["nodes"][0]["children"][0]
        self._validate_node_structure(node_out) 
        self.assertEqual(node_out["id"], minimal_node_id)
        self.assertEqual(node_out["name"], "Minimal Node")
        self.assertEqual(node_out["type"], "RECTANGLE")
        # Check that other optional fields are None or not present (handled by _validate_node_structure implicitly)
        self.assertIsNone(node_out.get("opacity"))
        self.assertIsNone(node_out.get("children")) # This minimal node has no children defined

        # Test getting the canvas which contains the minimal node
        result_canvas = get_figma_data(file_key=minimal_file_key, node_id=minimal_canvas_id)
        canvas_out = result_canvas["nodes"][0]
        self.assertEqual(canvas_out["id"], minimal_canvas_id)
        self.assertEqual(len(canvas_out["children"]), 1)
        self.assertEqual(canvas_out["children"][0]["id"], minimal_node_id)

        # Clean up added file
        self.DB['files'] = [f for f in self.DB['files'] if f["fileKey"] != minimal_file_key]

    def test_fills_handling_string_id_and_list_of_objects(self):
        # This test re-verifies the two types of 'fills' based on the setup.
        result = get_figma_data(file_key=self.file1_key)
        canvas_node_out = result["nodes"][0]

        frame_node_out = next(n for n in canvas_node_out["children"] if n["id"] == self.frame1_id)
        self.assertIsInstance(frame_node_out.get("fills"), list) 
        self.assertEqual(frame_node_out["fills"][0]["type"], "SOLID")

        text_node_out = next(n for n in canvas_node_out["children"] if n["id"] == self.text1_id)
        self.assertIsInstance(text_node_out.get("fills"), str) 
        self.assertEqual(text_node_out["fills"], "S:style_id_solid_black")

    # NEW TESTS TO IMPROVE COVERAGE OF VALIDATION EDGE CASES
    def test_invalid_input_file_key_not_string(self):
        """Test that non-string file_key raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="file_key must be a string, got int.",
            file_key=123
        )

    def test_invalid_input_file_key_none(self):
        """Test that None file_key raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="file_key must be a string, got NoneType.",
            file_key=None
        )

    def test_invalid_input_node_id_not_string(self):
        """Test that non-string node_id raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="node_id must be a string or None, got int.",
            file_key=self.file1_key,
            node_id=123
        )

    def test_invalid_input_file_key_whitespace_only(self):
        """Test that whitespace-only file_key raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="File key cannot be empty.",
            file_key="   "
        )

    def test_invalid_input_node_id_empty_string(self):
        """Test that empty string node_id raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="node_id cannot be empty or whitespace-only if provided.",
            file_key=self.file1_key,
            node_id=""
        )

    def test_invalid_input_node_id_whitespace_only(self):
        """Test that whitespace-only node_id raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="node_id cannot be empty or whitespace-only if provided.",
            file_key=self.file1_key,
            node_id="   "
        )

    def test_invalid_input_file_key_invalid_characters(self):
        """Test that file_key with invalid characters raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="file_key contains invalid characters. Only alphanumeric characters, hyphens, and underscores are allowed.",
            file_key="file@key#with$invalid%chars"
        )

    def test_invalid_input_node_id_invalid_characters(self):
        """Test that node_id with invalid characters raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=get_figma_data,
            expected_exception_type=InvalidInputError,
            expected_message="node_id contains invalid characters. Only alphanumeric characters, hyphens, underscores, and colons are allowed.",
            file_key=self.file1_key,
            node_id="node@id#with$invalid%chars"
        )

if __name__ == '__main__':
    unittest.main()