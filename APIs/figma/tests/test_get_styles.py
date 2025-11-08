# figma/tests/test_get_styles.py

import unittest
from figma import get_styles, DB
from figma.SimulationEngine.custom_errors import NoDocumentOpenError, FigmaOperationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from typing import List, Dict, Any

class TestGetStyles(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up test environment for each test case."""
        self.DB = DB
        # Set the current_file_key by default to simplify tests
        self.DB['current_file_key'] = 'test_file_1'
        self.DB['files'] = []

    def tearDown(self):
        """Clean up after each test."""
        self.DB.clear()

    def _get_base_figma_file_structure(self) -> Dict[str, Any]:
        """
        Returns a base structure for a Figma file, reflecting the CORRECT schema
        where all style definitions are under globalVars.styles.
        """
        return {
            'fileKey': 'test_file_1',
            'name': 'Test Document',
            'document': {'id': '0:0', 'type': 'CANVAS', 'children': []},
            'globalVars': {
                'styles': {}, # This is the single source of truth for styles.
                'variables': {},
                'variableCollections': {}
            }
        }

    def _set_current_file(self, file_data: Dict[str, Any]):
        """Helper to set the DB state for a single test file."""
        self.DB['files'] = [file_data]

    ### Error Handling and Edge Cases ###

    def test_no_document_open(self):
        """Test raises NoDocumentOpenError if current_file_key is missing."""
        del self.DB['current_file_key']
        with self.assertRaisesRegex(NoDocumentOpenError, "No Figma document is currently open."):
            get_styles()

    def test_current_file_not_found(self):
        """Test raises FigmaOperationError if the file key points to a non-existent file."""
        self.DB['files'] = [] # No files in the list
        with self.assertRaisesRegex(FigmaOperationError, "Current file with key 'test_file_1' not found."):
            get_styles()

    def test_files_data_malformed_not_list(self):
        """Test raises FigmaOperationError if DB['files'] is not a list."""
        self.DB['files'] = "this is not a list"
        with self.assertRaisesRegex(FigmaOperationError, r"Current Figma file data is malformed \(expected list\)\."):
            get_styles()

    def test_malformed_file_data(self):
        """Test raises FigmaOperationError if file data is not a dictionary."""
        self.DB['files'] = ["not_a_dict"]
        with self.assertRaisesRegex(FigmaOperationError, "Current file with key 'test_file_1' not found."):
            get_styles()

    def test_global_vars_missing(self):
        """Test returns an empty list if 'globalVars' key is missing from the file."""
        figma_file = self._get_base_figma_file_structure()
        del figma_file['globalVars']
        self._set_current_file(figma_file)
        self.assertEqual(get_styles(), [])
        
    def test_malformed_global_vars_data(self):
        """Test raises FigmaOperationError if 'globalVars' is not a dict."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars'] = "not_a_dictionary"
        self._set_current_file(figma_file)
        with self.assertRaisesRegex(FigmaOperationError, r"Global variables data \('globalVars'\) in the document is malformed \(expected dict\)\."):
            get_styles()

    def test_styles_container_missing(self):
        """Test returns an empty list if 'styles' key is missing from 'globalVars'."""
        figma_file = self._get_base_figma_file_structure()
        del figma_file['globalVars']['styles']
        self._set_current_file(figma_file)
        self.assertEqual(get_styles(), [])

    def test_malformed_styles_container(self):
        """Test raises FigmaOperationError if 'styles' under 'globalVars' is not a dict."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars']['styles'] = "not_a_dictionary"
        self._set_current_file(figma_file)
        with self.assertRaisesRegex(FigmaOperationError, "Style definitions data under 'globalVars' is malformed \(expected dict\)."):
            get_styles()

    def test_no_styles_defined(self):
        """Test returns an empty list when no styles are defined."""
        figma_file = self._get_base_figma_file_structure() # Has empty 'styles' dict
        self._set_current_file(figma_file)
        self.assertEqual(get_styles(), [])

    ### Style Parsing Logic Tests ###

    def test_get_single_fill_style(self):
        """Test correctly parses a single FILL style."""
        figma_file = self._get_base_figma_file_structure()
        paint_object = {'type': 'SOLID', 'color': {'r': 1, 'g': 0, 'b': 0, 'a': 1}}
        figma_file['globalVars']['styles'] = {
            's1': {
                'key': 'k1', 'name': 'Primary Red', 'styleType': 'FILL', 'remote': False,
                'description': 'Main red color.', 'root': paint_object
            }
        }
        self._set_current_file(figma_file)
        
        result = get_styles()
        
        expected = [{
            'id': 's1', 'key': 'k1', 'name': 'Primary Red', 'styleType': 'FILL',
            'remote': False, 'description': 'Main red color.',
            'paints': [paint_object]
        }]
        self.assert_styles_equal(result, expected)

    def test_get_single_text_style(self):
        """Test correctly parses a single TEXT style and creates fontName."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars']['styles'] = {
            's2': {
                'key': 'k2', 'name': 'Heading 1', 'styleType': 'TEXT', 'remote': True,
                'root': {
                    'fontFamily': 'Inter', 'fontPostScriptName': 'Bold', 'fontSize': 32.0,
                    'lineHeightPx': 40
                }
            }
        }
        self._set_current_file(figma_file)
        result = get_styles()
        expected = [{
            'id': 's2', 'key': 'k2', 'name': 'Heading 1', 'styleType': 'TEXT', 'remote': True,
            'fontFamily': 'Inter', 'fontPostScriptName': 'Bold', 'fontSize': 32.0, 'lineHeightPx': 40,
            'fontName': {'family': 'Inter', 'style': 'Bold'}
        }]
        self.assert_styles_equal(result, expected)

    def test_get_single_effect_style(self):
        """Test correctly parses a single EFFECT style."""
        figma_file = self._get_base_figma_file_structure()
        effects_data = [{'type': 'DROP_SHADOW', 'radius': 10}]
        figma_file['globalVars']['styles'] = {
            's3': {
                'key': 'k3', 'name': 'Card Shadow', 'styleType': 'EFFECT', 'remote': False,
                'root': {'effects': effects_data, 'someOtherProp': 'value'}
            }
        }
        self._set_current_file(figma_file)
        result = get_styles()
        expected = [{
            'id': 's3', 'key': 'k3', 'name': 'Card Shadow', 'styleType': 'EFFECT', 'remote': False,
            'effects': effects_data, 'someOtherProp': 'value' # Expect root properties to be merged
        }]
        self.assert_styles_equal(result, expected)
        
    def test_skips_malformed_style_entries(self):
        """Test gracefully skips style entries that are not dicts or missing required keys."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars']['styles'] = {
            's1': "not_a_dict",
            's2': {'key': 'k2', 'name': 'Valid Style', 'styleType': 'FILL', 'root': {'type': 'SOLID'}},
            's3': {'key': 'k3', 'name': 'Missing Type'}, # Missing styleType
            's4': {'key': 'k4', 'styleType': 'FILL'}, # Missing name
        }
        self._set_current_file(figma_file)
        result = get_styles()
        
        # Only s2 should be parsed successfully
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 's2')
        
    def test_handles_style_with_missing_or_invalid_root(self):
        """Test returns base style data if 'root' is missing or not a dict."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars']['styles'] = {
            's1': {'key': 'k1', 'name': 'No Root', 'styleType': 'FILL'}, # Missing 'root'
            's2': {'key': 'k2', 'name': 'Invalid Root', 'styleType': 'TEXT', 'root': 123}, # 'root' is not a dict
        }
        self._set_current_file(figma_file)
        result = get_styles()
        expected = [
            {'id': 's1', 'key': 'k1', 'name': 'No Root', 'styleType': 'FILL', 'remote': False},
            {'id': 's2', 'key': 'k2', 'name': 'Invalid Root', 'styleType': 'TEXT', 'remote': False}
        ]
        self.assert_styles_equal(result, expected)

    def test_text_style_with_missing_font_properties(self):
        """Test that fontName is not created if font properties are missing."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars']['styles'] = {
            's1': {
                'key': 'k1', 'name': 'No Family', 'styleType': 'TEXT', 'remote': False,
                'root': {'fontPostScriptName': 'Bold', 'fontSize': 16.0} # Missing fontFamily
            }
        }
        self._set_current_file(figma_file)
        result = get_styles()
        self.assertEqual(len(result), 1)
        self.assertNotIn('fontName', result[0])
        self.assertEqual(result[0]['fontSize'], 16.0)

    def test_get_multiple_mixed_styles(self):
        """Test processes a mix of valid and invalid styles correctly."""
        figma_file = self._get_base_figma_file_structure()
        figma_file['globalVars']['styles'] = {
            'fill_style': {
                'key': 'k_fill', 'name': 'Background', 'styleType': 'FILL', 'remote': False,
                'root': {'type': 'SOLID', 'color': {'r': 0, 'g': 0, 'b': 0, 'a': 1}}
            },
            'text_style': {
                'key': 'k_text', 'name': 'Body', 'styleType': 'TEXT', 'remote': True,
                'root': {'fontFamily': 'Roboto', 'fontPostScriptName': 'Regular', 'fontSize': 16}
            },
            'malformed_style': {
                'key': 'k_malformed', # Missing name and styleType
            }
        }
        self._set_current_file(figma_file)
        result = get_styles()
        expected = [
            {
                'id': 'fill_style', 'key': 'k_fill', 'name': 'Background', 'styleType': 'FILL',
                'remote': False,
                'paints': [{'type': 'SOLID', 'color': {'r': 0, 'g': 0, 'b': 0, 'a': 1}}]
            },
            {
                'id': 'text_style', 'key': 'k_text', 'name': 'Body', 'styleType': 'TEXT',
                'remote': True, 'fontSize': 16,
                'fontFamily': 'Roboto', 'fontPostScriptName': 'Regular',
                'fontName': {'family': 'Roboto', 'style': 'Regular'}
            }
        ]
        self.assert_styles_equal(result, expected)

    def assert_styles_equal(self, actual_styles: List[Dict[str, Any]], expected_styles: List[Dict[str, Any]]):
        """
        Asserts that two lists of style dictionaries are equal, ignoring order.
        Also normalizes the presence of optional keys for robust comparison.
        """
        self.assertEqual(len(actual_styles), len(expected_styles),
                         f"Number of styles mismatch. Got {len(actual_styles)}, expected {len(expected_styles)}."
                         f"\nActual: {actual_styles}\nExpected: {expected_styles}")

        actual_sorted = sorted(actual_styles, key=lambda s: s['id'])
        expected_sorted = sorted(expected_styles, key=lambda s: s['id'])

        for actual, expected in zip(actual_sorted, expected_sorted):
            with self.subTest(style_id=actual.get('id')):
                 self.assertDictEqual(actual, expected)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)