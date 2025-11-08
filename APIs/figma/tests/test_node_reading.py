import unittest
from unittest.mock import patch
from copy import deepcopy

from common_utils.error_handling import get_package_error_mode
from figma.node_reading import get_node_info
from figma.SimulationEngine.custom_errors import NodeNotFoundError, FigmaOperationError, InvalidInputError
from figma.SimulationEngine.db import DB as OG_DB # Use an alias to avoid conflict with mocked 'DB'
from common_utils.base_case import BaseTestCaseWithErrorHandler

from figma.SimulationEngine.db import DB as GLOBAL_DB
from figma.node_reading import get_selection
from figma.SimulationEngine.custom_errors import NoSelectionError, FigmaOperationError

# --- Unit Tests for get_node_info ---
@unittest.skipIf(get_node_info is None, "Skipping unit tests: get_node_info couldn't be imported.")
class TestGetNodeInfoUnit(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self.mock_db_scaffold = {
            "files": [{"file_key":"test_key", "document": {"id": "0:0", "name": "Test Document", "type": "DOCUMENT", "children": []}}],
            "current_file_key":"test_key"
        }

    def _create_mock_node_data(self, node_id, **kwargs):
        base_node = {
            "id": node_id, "name": "Mock Node", "type": "FRAME", "visible": True, "locked": False,
            "opacity": 1.0, "absoluteBoundingBox": {"x": 0, "y": 0, "width": 100, "height": 100},
            "fills": [], "strokes": [], "strokeWeight": 0.0, "strokeAlign": "INSIDE", "effects": [],
            "children": None,
        }
        base_node.update(kwargs)
        return base_node

    # Corrected patch targets to where get_node_info (in figma.node_reading) looks them up
    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_get_simple_frame_node_success(self, mock_utils, mock_node_reading_db):
        node_id = "1:1"
        mock_node_data = self._create_mock_node_data(
            node_id, name="Test Frame", type="FRAME",
            absoluteBoundingBox={"x": 10, "y": 20, "width": 200, "height": 100},
            fills=[{"type": "SOLID", "color": {"r": 1, "g": 0, "b": 0, "a": 1}, "visible": True}],
            strokeWeight=2.0, strokeAlign="CENTER", opacity=0.8, locked=True
        )
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        # Configure the mocked DB (as seen by get_node_info) for initial checks
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file


        result = get_node_info(node_id)
        self.assertEqual(result['id'], node_id)
        self.assertEqual(result['name'], "Test Frame")
        # ... (rest of assertions from your previous successful test)
        self.assertDictEqual(result['absoluteBoundingBox'], {"x": 10.0, "y": 20.0, "width": 200.0, "height": 100.0})
        self.assertEqual(len(result['fills']), 1)
        self.assertEqual(result['fills'][0]['type'], "SOLID")
        self.assertIsNone(result['layoutMode'])


    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_get_text_node_with_styles(self, mock_utils, mock_node_reading_db):
        node_id = "2:1"
        mock_node_data = self._create_mock_node_data(
            node_id, name="Hello Text", type="TEXT", characters="Hello World",
            style={"fontFamily": "Arial", "fontPostScriptName": "Arial-BoldMT", "fontSize": 24.0}
        )
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = {"id": "0:1"}
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)
        self.assertEqual(result['type'], "TEXT")
        self.assertEqual(result['characters'], "Hello World")
        self.assertEqual(result['fontSize'], 24.0)
        self.assertDictEqual(result['fontName'], {"family": "Arial", "style": "Arial-BoldMT"})
        self.assertEqual(result['parentId'], "0:1")

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_get_node_with_children_recursive(self, mock_utils, mock_node_reading_db):
        parent_id, child1_id, child2_id = "P:1", "C1:1", "C2:1"
        mock_child2 = self._create_mock_node_data(child2_id, name="Child 2", type="RECTANGLE")
        mock_child1 = self._create_mock_node_data(child1_id, name="Child 1", type="TEXT", characters="child text")
        mock_parent = self._create_mock_node_data(parent_id, name="Parent", children=[mock_child1, mock_child2])

        # get_node_from_db is only called for the parent_id by get_node_info
        mock_utils.get_node_from_db.return_value = mock_parent
        mock_utils.get_parent_of_node_from_db.side_effect = lambda db, nid: {"id": parent_id} if nid in [child1_id, child2_id] else None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(parent_id) # Call with parent_id
        self.assertEqual(result['id'], parent_id) # Check parent
        self.assertEqual(len(result['children']), 2)
        self.assertEqual(result['children'][0]['id'], child1_id) # Check child1
        self.assertEqual(result['children'][0]['parentId'], parent_id)
        self.assertEqual(result['children'][1]['id'], child2_id) # Check child2
        self.assertEqual(result['children'][1]['parentId'], parent_id)


    @patch('figma.node_reading.DB', spec=dict) # Corrected patch target
    @patch('figma.node_reading.utils') # Corrected patch target
    def test_error_invalid_node_id(self, mock_utils, mock_node_reading_db):
        # These assertions don't actually need the mocks as the error is raised before DB/utils are used.
        self.assert_error_behavior(get_node_info, InvalidInputError, "Node ID must be a non-empty string.", nodeId=None)
        self.assert_error_behavior(get_node_info, InvalidInputError, "Node ID must be a non-empty string.", nodeId="")

    @patch('figma.node_reading.DB', None) # Patch DB as None where get_node_info looks for it
    @patch('figma.node_reading.utils') # Mock utils, though it might not be reached
    def test_error_db_malformed_db_is_none(self, mock_utils_not_used_if_db_none):
        self.assert_error_behavior(
            get_node_info,
            FigmaOperationError,
            "Figma data source (DB) must be a dictionary and contain a 'files' list.", # Exact message
            nodeId="1:1"
        )

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_node_not_found(self, mock_utils, mock_node_reading_db):
        node_id = "999:999"
        mock_utils.get_node_from_db.return_value = None # This is key for this test
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        self.assert_error_behavior(get_node_info, NodeNotFoundError, f"Node with ID '{node_id}' not found.", nodeId=node_id)

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_pydantic_validation_triggered(self, mock_utils, mock_node_reading_db):
        node_id = "V:ERR"
        bad_bbox_data = {"x": 10, "y": 10, "width": "not-a-number", "height": 10}
        mock_node_data_invalid = self._create_mock_node_data(node_id, absoluteBoundingBox=bad_bbox_data)

        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data_invalid
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        self.assert_error_behavior(
            get_node_info,
            FigmaOperationError,
            "Data validation error for node 'V:ERR': Details: Input should be a valid number, unable to parse string as a number",
            nodeId=node_id
        )
        if get_package_error_mode() == "raise":
            with self.assertRaises(FigmaOperationError) as context:
                get_node_info(node_id)
            self.assertIn("Input should be a valid number", str(context.exception))
    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_db_malformed_files_not_list(self, mock_utils, mock_node_reading_db):
        mock_node_reading_db.get.return_value = "not_a_list" # DB.get('files') returns a string
        self.assert_error_behavior(
            get_node_info, FigmaOperationError,
            "Figma data source (DB) must be a dictionary and contain a 'files' list.", nodeId="1:1"
        )

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_db_malformed_files_empty_list(self, mock_utils, mock_node_reading_db):
        mock_node_reading_db.get.return_value = [] # DB.get('files') returns empty list
        mock_node_reading_db.__getitem__.side_effect = lambda key: [] if key == 'files' else self.mock_db_scaffold[key]
        self.assert_error_behavior(
            get_node_info, FigmaOperationError,
            "Validation failed: The current file is missing a valid 'document' object.", nodeId="1:1"
        )

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_db_malformed_file_item_not_dict(self, mock_utils, mock_node_reading_db):
        mock_files_list = ["not_a_dict"]
        mock_node_reading_db.get.return_value = mock_files_list
        mock_node_reading_db.__getitem__.side_effect = lambda key: mock_files_list if key == 'files' else self.mock_db_scaffold[key]
        self.assert_error_behavior(
            get_node_info, FigmaOperationError,
            "Validation failed: The current file is missing a valid 'document' object.", nodeId="1:1"
        )

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_db_malformed_document_key_missing(self, mock_utils, mock_node_reading_db):
        mock_files_list = [{"no_document_key": True}]
        mock_node_reading_db.get.return_value = mock_files_list
        mock_node_reading_db.__getitem__.side_effect = lambda key: mock_files_list if key == 'files' else self.mock_db_scaffold[key]
        self.assert_error_behavior(
            get_node_info, FigmaOperationError,
            "Validation failed: The current file is missing a valid 'document' object.", nodeId="1:1"
        )

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_error_db_malformed_document_not_dict(self, mock_utils, mock_node_reading_db):
        mock_files_list = [{"document": "not_a_dict"}]
        mock_node_reading_db.get.return_value = mock_files_list
        mock_node_reading_db.__getitem__.side_effect = lambda key: mock_files_list if key == 'files' else self.mock_db_scaffold[key]
        self.assert_error_behavior(
            get_node_info, FigmaOperationError,
            "Validation failed: The current file is missing a valid 'document' object.", nodeId="1:1"
        )

    # --- Test Default Value Applications and Optional Fields ---
    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_node_with_minimal_data_and_defaults(self, mock_utils, mock_node_reading_db):
        node_id = "min:1"
        # Provide only the absolute minimum required by _create_mock_node_data (id)
        # and rely on get_node_info's internal defaults for many fields.
        minimal_node_data = {"id": node_id} # Intentionally missing name, type, etc.
                                           # from what _create_mock_node_data usually adds.

        mock_utils.get_node_from_db.return_value = minimal_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)

        self.assertEqual(result['id'], node_id)
        self.assertEqual(result['name'], 'Unnamed Node') # Default
        self.assertEqual(result['type'], 'UNKNOWN')     # Default
        self.assertEqual(result['visible'], True)        # Default
        self.assertEqual(result['locked'], False)       # Default
        self.assertEqual(result['opacity'], 1.0)         # Default
        self.assertDictEqual(result['absoluteBoundingBox'], {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}) # Defaults
        self.assertEqual(result['fills'], [])            # Default
        self.assertEqual(result['strokes'], [])          # Default
        self.assertEqual(result['strokeWeight'], 0.0)    # Default
        self.assertEqual(result['strokeAlign'], 'INSIDE') # Default
        self.assertEqual(result['effects'], [])          # Default
        self.assertIsNone(result['children'])
        self.assertIsNone(result['parentId'])
        self.assertIsNone(result['characters'])
        self.assertIsNone(result['fontSize'])
        self.assertIsNone(result['fontName'])
        self.assertIsNone(result['componentId'])
        self.assertIsNone(result['layoutMode'])

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_node_fills_strokes_effects_empty_or_none(self, mock_utils, mock_node_reading_db):
        node_id = "empty_styles:1"
        test_cases_data = [
            ("fills_none", {"id": node_id, "fills": None}),
            ("fills_empty_list", {"id": node_id, "fills": []}),
            ("strokes_none", {"id": node_id, "strokes": None}),
            ("strokes_empty_list", {"id": node_id, "strokes": []}),
            ("effects_none", {"id": node_id, "effects": None}),
            ("effects_empty_list", {"id": node_id, "effects": []}),
        ]

        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_parent_of_node_from_db.return_value = None

        for desc, data in test_cases_data:
            with self.subTest(description=desc):
                mock_utils.get_node_from_db.return_value = self._create_mock_node_data(node_id, **data)
                result = get_node_info(node_id)
                if "fills" in desc: self.assertEqual(result['fills'], [])
                if "strokes" in desc: self.assertEqual(result['strokes'], [])
                if "effects" in desc: self.assertEqual(result['effects'], [])

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_paint_item_defaults(self, mock_utils, mock_node_reading_db):
        node_id = "paint_defaults:1"
        mock_node_data = self._create_mock_node_data(node_id, fills=[
            {"color": {"r": 0.5}} # Missing type, visible, g,b,a in color
        ])
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)
        self.assertEqual(len(result['fills']), 1)
        fill_item = result['fills'][0]
        self.assertEqual(fill_item['type'], 'UNKNOWN') # Default
        self.assertEqual(fill_item['visible'], True)    # Default
        self.assertIsNone(fill_item['opacity'])      # Optional
        self.assertDictEqual(fill_item['color'], {"r": 0.5, "g": 0.0, "b": 0.0, "a": 1.0}) # Defaults for g,b,a

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_effect_item_defaults(self, mock_utils, mock_node_reading_db):
        node_id = "effect_defaults:1"
        mock_node_data = self._create_mock_node_data(node_id, effects=[
            {"offset": {"x": 1}} # Missing type, visible, radius, color, offset.y
        ])
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)
        self.assertEqual(len(result['effects']), 1)
        effect_item = result['effects'][0]
        self.assertEqual(effect_item['type'], 'UNKNOWN')
        self.assertEqual(effect_item['visible'], True)
        self.assertEqual(effect_item['radius'], 0.0) # Default
        self.assertIsNone(effect_item['color'])
        self.assertDictEqual(effect_item['offset'], {"x": 1.0, "y": 0.0}) # Default for y

    # --- Test Text/Instance/Frame Specific Logic Branches ---
    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_text_node_minimal_style_and_no_text_key(self, mock_utils, mock_node_reading_db):
        node_id = "text_min:1"
        mock_node_data = self._create_mock_node_data(node_id, type="TEXT",
            # No 'characters' or 'text' key
            style={} # Empty style dict
        )
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)
        self.assertEqual(result['type'], "TEXT")
        self.assertIsNone(result['characters'])
        self.assertIsNone(result['fontSize'])
        self.assertIsNone(result['fontName']) # Because family and style both missing from style dict

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_text_node_fontname_partial(self, mock_utils, mock_node_reading_db):
        node_id = "text_partial_font:1"
        mock_node_data = self._create_mock_node_data(node_id, type="TEXT", style={"fontFamily": "Roboto"})
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)
        self.assertIsNotNone(result['fontName'])
        self.assertEqual(result['fontName']['family'], "Roboto")
        self.assertEqual(result['fontName']['style'], "Regular") # Defaulted

    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_instance_node_no_component_id(self, mock_utils, mock_node_reading_db):
        node_id = "instance_no_comp:1"
        mock_node_data = self._create_mock_node_data(node_id, type="INSTANCE") # componentId missing
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        result = get_node_info(node_id)
        self.assertEqual(result['type'], "INSTANCE")
        self.assertIsNone(result['componentId'])


    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_frame_node_layout_mode_none_or_missing(self, mock_utils, mock_node_reading_db):
        test_cases_data = [
            ("layoutMode_missing", self._create_mock_node_data("f:1", type="FRAME")),
            ("layoutMode_NONE", self._create_mock_node_data("f:2", type="FRAME", layoutMode="NONE")),
        ]
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_parent_of_node_from_db.return_value = None

        for desc, data in test_cases_data:
            with self.subTest(description=desc):
                mock_utils.get_node_from_db.return_value = data
                result = get_node_info(data['id'])
                self.assertEqual(result['type'], "FRAME")
                self.assertEqual(result.get('layoutMode'), data.get('layoutMode')) # Will be None if missing, or "NONE"
                self.assertIsNone(result['itemSpacing'])
                self.assertIsNone(result['paddingLeft']) # All auto-layout specific props should be None


    # --- Test Children Logic ---
    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    def test_node_children_variations(self, mock_utils, mock_node_reading_db):
        node_id = "children_vars:1"
        child_ok_id = "child_ok:1"
        mock_child_ok = self._create_mock_node_data(child_ok_id, name="OK Child")

        test_cases_data = [
            ("children_key_missing", self._create_mock_node_data(node_id)), # 'children' key not in node_data
            ("children_is_none", self._create_mock_node_data(node_id, children=None)),
            ("children_empty_list", self._create_mock_node_data(node_id, children=[])),
            ("children_with_invalid_item_not_dict", self._create_mock_node_data(node_id, children=["not_a_dict", mock_child_ok])),
            ("children_with_invalid_item_no_id", self._create_mock_node_data(node_id, children=[{"name":"no_id_child"}, mock_child_ok])),
        ]
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        # Parent of child_ok_id will be node_id for the valid cases
        mock_utils.get_parent_of_node_from_db.side_effect = lambda db, nid: {"id": node_id} if nid == child_ok_id else None


        for desc, data in test_cases_data:
            with self.subTest(description=desc):
                mock_utils.get_node_from_db.return_value = data
                result = get_node_info(data['id'])
                if desc in ["children_key_missing", "children_is_none", "children_empty_list"]:
                    self.assertIsNone(result['children'])
                elif desc in ["children_with_invalid_item_not_dict", "children_with_invalid_item_no_id"]:
                    self.assertIsNotNone(result['children'])
                    self.assertEqual(len(result['children']), 1) # Only mock_child_ok should be processed
                    self.assertEqual(result['children'][0]['id'], child_ok_id)


    # --- Test Generic Exception during Formatting ---
    @patch('figma.node_reading.DB', spec=dict)
    @patch('figma.node_reading.utils')
    @patch('figma.node_reading.FigmaNodeDetails') # Patch the Pydantic model itself
    def test_error_unexpected_exception_during_formatting(self, MockFigmaNodeDetails, mock_utils, mock_node_reading_db):
        node_id = "fmt_err:1"
        mock_node_data = self._create_mock_node_data(node_id)
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file
        mock_utils.get_node_from_db.return_value = mock_node_data
        mock_utils.get_parent_of_node_from_db.return_value = None
        mock_node_reading_db.get.return_value = self.mock_db_scaffold['files']
        mock_node_reading_db.__getitem__.side_effect = self.mock_db_scaffold.__getitem__
        mock_file = self.mock_db_scaffold['files'][0]
        mock_node_reading_db.configure_mock(**self.mock_db_scaffold)
        mock_utils.get_current_file.return_value = mock_file

        # Make FigmaNodeDetails instantiation raise an unexpected error
        MockFigmaNodeDetails.side_effect = RuntimeError("Unexpected Pydantic crash")

        expected_msg_part = f"An unexpected error occurred while formatting node data for '{node_id}': Unexpected Pydantic crash"
        self.assert_error_behavior(
            get_node_info, FigmaOperationError,
            expected_msg_part, nodeId=node_id
        )


# # --- Integration Tests ---
# skip_ig_test = True
# db_files = OG_DB.get('files',{})
# if db_files and isinstance(db_files[0], dict):
#     db_child = db_files[0].get('document', {}).get('children',[])
#     if db_child and isinstance(db_child[0], dict) and db_child[0].get('id') == '1516:368':
#         skip_ig_test = False

# @unittest.skipIf(get_node_info is None or skip_ig_test, "Skipping integration: get_node_info missing or real DB empty.")
# class TestGetNodeInfoIntegration(BaseTestCaseWithErrorHandler):

#     # For integration tests, we allow get_node_info to use the real DB and utils
#     # imported as OG_DB and figma.SimulationEngine.utils respectively.
#     # The `get_node_info` function itself should import `DB` and `utils` from `figma.SimulationEngine.*`

#     def test_get_info_for_frame_node_1516_9022(self):
#         node_id = "1516:9022"
#         # Assuming get_node_info internally uses DB and utils from figma.SimulationEngine
#         result = get_node_info(node_id)

#         self.assertEqual(result['id'], node_id)
#         self.assertEqual(result['name'], "Main Dashboard Screen")
#         self.assertEqual(result['type'], "FRAME")
#         self.assertEqual(result['opacity'], 1.0)
#         self.assertDictEqual(result['absoluteBoundingBox'], {"x": -2000.0, "y": -574.0, "width": 1440.0, "height": 1024.0})
#         self.assertTrue(len(result['fills']) > 0)
#         self.assertEqual(result['fills'][0]['type'], "SOLID")
#         self.assertDictEqual(result['fills'][0]['color'], {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
#         self.assertEqual(result['layoutMode'], "VERTICAL")
#         self.assertEqual(result['itemSpacing'], 16.0)
#         self.assertEqual(result['paddingLeft'], 20.0)
#         self.assertTrue(isinstance(result['children'], list) and len(result['children']) > 0, "Expected children list")
#         self.assertEqual(result['parentId'], "1516:368")

#     def test_get_info_for_text_node_1516_9023(self):
#         node_id = "1516:9023"
#         result = get_node_info(node_id)
#         self.assertEqual(result['id'], node_id)
#         self.assertEqual(result['name'], "Page Title")
#         self.assertEqual(result['type'], "TEXT")
#         self.assertEqual(result['characters'], "Dashboard Overview")
#         self.assertEqual(result['fontSize'], 32.0)
#         self.assertDictEqual(result['fontName'], {"family": "Helvetica Neue", "style": "HelveticaNeue-Bold"})
#         self.assertEqual(result['parentId'], "1516:9022")
#         self.assertEqual(result['fills'][0]['type'], "SOLID")
#         self.assertAlmostEqual(result['fills'][0]['color']['r'], 0.11372549086809158)

#     def test_get_info_for_instance_node_I1517_9056(self):
#         node_id = "I1517:9056;130:5121"
#         result = get_node_info(node_id)
#         self.assertEqual(result['id'], node_id)
#         self.assertEqual(result['name'], "Button Primary")
#         self.assertEqual(result['type'], "INSTANCE")
#         self.assertEqual(result['componentId'], "C:130:5000,Purity UI Dashboard - Chakra UI Dashboard")
#         self.assertEqual(result['parentId'], "1516:9022")
#         self.assertIsNone(result['layoutMode'])
#         self.assertIsNone(result['itemSpacing'])

#     def test_get_info_for_vector_node_VEC_101_2(self):
#         node_id = "VEC:101:2"
#         result = get_node_info(node_id)
#         self.assertEqual(result['id'], node_id)
#         self.assertEqual(result['name'], "Decorative Line")
#         self.assertEqual(result['type'], "VECTOR")
#         self.assertEqual(len(result['strokes']), 1)
#         self.assertEqual(result['strokes'][0]['type'], "SOLID")
#         self.assertDictEqual(result['strokes'][0]['color'], {"r": 0.8, "g": 0.8, "b": 0.8, "a": 1.0})
#         self.assertEqual(result['strokeWeight'], 1.0)
#         self.assertEqual(result['strokeAlign'], "CENTER")
#         self.assertEqual(result['parentId'], "1516:9022")

#     def test_integration_node_not_found_in_real_db(self):
#         node_id = "THIS_NODE_DOES_NOT_EXIST_IN_DB_PY"
#         self.assert_error_behavior(
#             get_node_info,
#             NodeNotFoundError,
#             f"Node with ID '{node_id}' not found.",
#             nodeId=node_id
#         )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)



class TestGetSelection(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a baseline DB structure for each test.
        """
        self.doc_node_data = {
            "id": "0:0", "name": "Test Document", "type": "DOCUMENT", "scrollBehavior": "SCROLLS",
            "children": [
                {
                    "id": "canvas1:0", "name": "Canvas 1", "type": "CANVAS", "scrollBehavior": "SCROLLS",
                    "backgroundColor": {"r": 1, "g": 1, "b": 1, "a": 1},
                    "children": [
                        {"id": "frame1:1", "name": "Frame 1 on C1", "type": "FRAME",
                         "children": [
                             {"id": "text1:2", "name": "Text 1 in F1", "type": "TEXT", "children": []},
                             {"id": "rect1:3", "name": "Rect 1 in F1", "type": "RECTANGLE", "children": []}
                         ]},
                        {"id": "frame1:2", "name": "Frame 2 on C1", "type": "FRAME", "children": []},
                        {"id": "comp1:4", "name": None, "type": "COMPONENT", "children": []}
                    ]
                },
                {
                    "id": "canvas2:0", "name": "Canvas 2", "type": "CANVAS", "scrollBehavior": "SCROLLS",
                    "backgroundColor": {"r": 0.9, "g": 0.9, "b": 0.9, "a": 1},
                    "children": [
                        {"id": "frame2:1", "name": "Frame 1 on C2", "type": "FRAME", "children": []}
                    ]
                }
            ]
        }
        self.base_db_state = {
            "files": [{"fileKey": "testFileKey1", "name": "Test File", "document": deepcopy(self.doc_node_data)}],
            "current_selection_node_ids": [],
            "current_file_key":"testFileKey1"
        }
        GLOBAL_DB.clear()
        GLOBAL_DB.update(deepcopy(self.base_db_state))

    def tearDown(self):
        """Clean up by clearing the global DB state."""
        GLOBAL_DB.clear()

    # --- Happy Path Tests ---
    def test_no_selection_raises_no_selection_error(self):
        GLOBAL_DB["current_selection_node_ids"] = []
        self.assert_error_behavior(
            get_selection,
            NoSelectionError,
            "No nodes are currently selected."
        )

        GLOBAL_DB.pop("current_selection_node_ids", None)
        self.assert_error_behavior(
            get_selection,
            NoSelectionError,
            "No nodes are currently selected."
        )

    def test_single_item_selected_frame(self):
        GLOBAL_DB["current_selection_node_ids"] = ["frame1:1"]
        selection = get_selection()
        current_error_mode = get_package_error_mode()
        if current_error_mode == "raise":
            self.assertEqual(len(selection), 1)
            self.assertDictEqual(selection[0], {
                'id': "frame1:1", 'name': "Frame 1 on C1", 'type': "FRAME", 'parentId': "canvas1:0"
            })
        elif current_error_mode == "error_dict":
            self.assertIsInstance(selection, list)
            self.assertEqual(len(selection), 1)
            self.assertDictEqual(selection[0], {
                'id': "frame1:1", 'name': "Frame 1 on C1", 'type': "FRAME", 'parentId': "canvas1:0"
            })


    def test_single_item_selected_text_deeply_nested(self):
        GLOBAL_DB["current_selection_node_ids"] = ["text1:2"]
        selection = get_selection()
        self.assertEqual(len(selection), 1)
        self.assertDictEqual(selection[0], {
            'id': "text1:2", 'name': "Text 1 in F1", 'type': "TEXT", 'parentId': "frame1:1"
        })

    def test_multiple_items_selected(self):
        GLOBAL_DB["current_selection_node_ids"] = ["frame1:1", "text1:2", "frame2:1"]
        selection = get_selection()
        self.assertEqual(len(selection), 3)
        
        expected_selection_details = [
            {'id': "frame1:1", 'name': "Frame 1 on C1", 'type': "FRAME", 'parentId': "canvas1:0"},
            {'id': "text1:2", 'name': "Text 1 in F1", 'type': "TEXT", 'parentId': "frame1:1"},
            {'id': "frame2:1", 'name': "Frame 1 on C2", 'type': "FRAME", 'parentId': "canvas2:0"}
        ]
        selection_set = [frozenset(s.items()) for s in selection]
        expected_set = [frozenset(e.items()) for e in expected_selection_details]
        for item_fset in expected_set:
            self.assertIn(item_fset, selection_set)

    def test_selected_item_with_no_name_defaults_to_empty_string(self):
        GLOBAL_DB["current_selection_node_ids"] = ["comp1:4"]
        selection = get_selection()
        self.assertEqual(len(selection), 1)
        self.assertDictEqual(selection[0], {
            'id': "comp1:4", 'name': "", 'type': "COMPONENT", 'parentId': "canvas1:0"
        })

    def test_selected_item_is_canvas_parent_is_document(self):
        GLOBAL_DB["current_selection_node_ids"] = ["canvas1:0"]
        selection = get_selection()
        self.assertEqual(len(selection), 1)
        self.assertDictEqual(selection[0], {
            'id': "canvas1:0", 'name': "Canvas 1", 'type': "CANVAS", 'parentId': "0:0"
        })

    # --- Error Condition Tests using assert_error_behavior ---
    def test_files_key_missing_in_db(self):
        GLOBAL_DB.pop("files", None)
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Figma file data is missing, not a list, or empty in DB."
        )

    def test_files_list_is_not_a_list(self):
        GLOBAL_DB["files"] = "not_a_list"
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Figma file data is missing, not a list, or empty in DB."
        )

    def test_files_list_empty_in_db(self):
        GLOBAL_DB["files"] = []
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Figma file data is missing, not a list, or empty in DB."
        )

    def test_file_data_entry_not_a_dictionary(self):
        GLOBAL_DB["files"] = ["not_a_dictionary"]
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Figma file data entry is not a dictionary."
        )

    def test_document_key_missing_in_file_data(self):
        GLOBAL_DB["files"][0].pop("document", None)
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Document data is missing or not a dictionary in the Figma file."
        )

    def test_document_data_not_a_dictionary(self):
        GLOBAL_DB["files"][0]["document"] = "not_a_dictionary"
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Document data is missing or not a dictionary in the Figma file."
        )
  
    def test_document_fails_pydantic_validation_missing_id(self):
        malformed_doc = deepcopy(self.doc_node_data)
        del malformed_doc["id"]
        GLOBAL_DB["files"][0]["document"] = malformed_doc
        GLOBAL_DB["current_selection_node_ids"] = ["anyID"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Document root node is missing a valid ID."
        )

    def test_selected_node_id_not_string_in_list(self):
        GLOBAL_DB["current_selection_node_ids"] = [12345]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Invalid node ID type in selection list: <class 'int'>. Must be a string."
        )

    def test_selected_node_id_not_found_in_document(self):
        GLOBAL_DB["current_selection_node_ids"] = ["nonExistentID:999"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Selected node ID 'nonExistentID:999' not found within the document's canvases or their children."
        )

    def test_found_node_data_results_in_id_none(self):
        GLOBAL_DB["files"][0]["document"]["children"][0]["children"][0]["id"] = None
        GLOBAL_DB["current_selection_node_ids"] = ["frame1:1"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Selected node ID 'frame1:1' not found within the document's canvases or their children."
        )

    @patch('figma.node_reading.utils.find_node_by_id')
    def test_found_node_with_missing_id_key_raises_error(self, mock_find_node_by_id):
        node_id_to_find = "frame1:1"
        GLOBAL_DB["current_selection_node_ids"] = [node_id_to_find]
        
        malformed_node_found = {"name": "Malformed Node", "type": "FRAME"} # No 'id' key
        mock_find_node_by_id.return_value = malformed_node_found
        
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            f"Found node for ID '{node_id_to_find}' is missing a valid 'id' string property."
        )

    @patch('figma.node_reading.utils.find_node_by_id')
    def test_found_node_with_non_string_id_raises_error(self, mock_find_node_by_id):
        node_id_to_find = "frame1:1"
        GLOBAL_DB["current_selection_node_ids"] = [node_id_to_find]

        malformed_node_found = {"id": 12345, "name": "Malformed Node", "type": "FRAME"}
        mock_find_node_by_id.return_value = malformed_node_found

        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            f"Found node for ID '{node_id_to_find}' is missing a valid 'id' string property."
        )

    def test_found_node_data_results_in_type_none(self):
        node_name = GLOBAL_DB["files"][0]["document"]["children"][0]["children"][0]["name"] # "Frame 1 on C1"
        node_id_for_error_msg = GLOBAL_DB["files"][0]["document"]["children"][0]["children"][0]["id"] # "frame1:1"
        GLOBAL_DB["files"][0]["document"]["children"][0]["children"][0]["type"] = None
        GLOBAL_DB["current_selection_node_ids"] = ["frame1:1"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            f"Found node 'frame1:1' (ID: {node_id_for_error_msg}) is missing a valid 'type' string property."
        )
    
    def test_document_root_selected_is_not_found_by_default_search(self):
        # get_selection searches in doc_model.children. "0:0" (document ID) won't be found.
        GLOBAL_DB["current_selection_node_ids"] = ["0:0"] # Document ID
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Selected node ID '0:0' not found within the document's canvases or their children."
        )

    def test_parent_node_data_results_in_parent_id_none(self):
        # Select "frame1:1". Its parent is "canvas1:0".
        # Corrupt "canvas1:0" in the DB so its 'id' field becomes None in the source data.
        GLOBAL_DB["files"][0]["document"]["children"][0]["id"] = None # canvas1:0's id set to None
        GLOBAL_DB["current_selection_node_ids"] = ["frame1:1"]
        self.assert_error_behavior(
            get_selection,
            FigmaOperationError,
            "Could not find a valid parent with a string ID for selected node 'frame1:1'."
        )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
