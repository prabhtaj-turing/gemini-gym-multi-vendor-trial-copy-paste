"""
Targeted tests to cover the remaining coverage gaps for 100% coverage.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, Mock
from .generic_media_base_exception import GenericMediaBaseTestCase
from generic_media.SimulationEngine import file_utils, utils, db
from generic_media.SimulationEngine.llm_interface import GeminiEmbeddingManager


class TestCoverageGaps(GenericMediaBaseTestCase):
    """Tests to cover the specific missing lines for 100% coverage."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
        super().tearDown()

    def test_db_reset_with_dict_values(self):
        """Test db.reset_db function with dict values - covers db.py line 54."""
        # Add some dict values to the DB to test the reset functionality
        db.DB['test_dict'] = {'key1': 'value1', 'key2': 'value2'}
        db.DB['test_list'] = ['item1', 'item2']
        
        # Reset the database
        db.reset_db()
        
        # Verify that dict was cleared (this hits line 54)
        self.assertEqual(db.DB.get('test_dict', {}), {})
        self.assertEqual(db.DB.get('test_list', []), [])

    def test_file_utils_unicode_decode_all_fail(self):
        """Test file_utils.read_file when all encoding attempts fail - covers lines 103-105."""
        # Create a text file with content that will fail all encoding attempts
        problematic_file = os.path.join(self.temp_dir, "problematic.txt")
        
        # Mock the open function to simulate UnicodeDecodeError for all encodings
        original_open = open
        
        def mock_open_func(path, mode='r', encoding=None, **kwargs):
            if path == problematic_file and 'r' in mode:
                # Always raise UnicodeDecodeError for text mode
                raise UnicodeDecodeError('utf-8', b'', 0, 1, 'mock error')
            return original_open(path, mode, encoding=encoding, **kwargs)
        
        # Create the file first
        with open(problematic_file, 'wb') as f:
            f.write(b'test content')
        
        with patch('builtins.open', side_effect=mock_open_func):
            with self.assertRaises(ValueError) as context:
                file_utils.read_file(problematic_file)
            
            # This should hit lines 103, 104, and 105
            self.assertIn("Could not decode file", str(context.exception))

    @patch('generic_media.SimulationEngine.llm_interface.genai.Client')
    def test_llm_interface_no_cache_all_empty_filtered(self, mock_client_class):
        """Test llm_interface when no cache and all texts are empty after filtering - covers line 81."""
        manager = GeminiEmbeddingManager("test_api_key")  # No cache
        
        # Test with only empty strings (this should hit line 81)
        result = manager.embed_content(
            "test-model", 
            ["", "", ""], 
            "CLASSIFICATION", 
            128
        )
        
        expected = {"embedding": [[0.0] * 128, [0.0] * 128, [0.0] * 128]}
        self.assertEqual(result, expected)
        
        # Should not call the API client
        mock_client_class.assert_not_called()

    def test_utils_generic_create_missing_id(self):
        """Test utils._generic_create with missing id - covers line 222."""
        resource_data = {"name": "test", "value": "test_value"}  # No 'id' field
        
        with self.assertRaises(ValueError) as context:
            utils._generic_create("test_resources", resource_data)
        
        # This should hit line 222
        self.assertIn("Resource data must contain an 'id' field", str(context.exception))

    def test_utils_generic_create_duplicate_id(self):
        """Test utils._generic_create with duplicate id - covers line 226."""
        # First, add a resource to the database
        existing_resource = {"id": "test_id", "name": "existing"}
        db.DB["test_resources"] = [existing_resource]
        
        # Try to create another resource with the same id
        duplicate_resource = {"id": "test_id", "name": "duplicate"}
        
        with self.assertRaises(ValueError) as context:
            utils._generic_create("test_resources", duplicate_resource)
        
        # This should hit line 226
        self.assertIn("Resource with id test_id already exists in test_resources", str(context.exception))


if __name__ == '__main__':
    unittest.main() 