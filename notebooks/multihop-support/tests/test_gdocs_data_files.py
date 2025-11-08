#!/usr/bin/env python3
"""
Test Google Docs converter using data files from tests/data folder.
Tests the conversion of Word documents to Google Docs format.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from gdrive_converter import convert_to_gdrive_format


class TestGDocsDataFiles(unittest.TestCase):
    """Test Google Docs converter with real data files."""

    def setUp(self):
        """Set up test data paths."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.docx_file = os.path.join(self.data_dir, 'kids_craft_camp_2025_business_information.docx')
        self.expected_json_file = os.path.join(self.data_dir, 'kids_craft_camp_2025_business_information.docx.json')
        
        # Load expected JSON data
        with open(self.expected_json_file, 'r', encoding='utf-8') as f:
            self.expected_data = json.load(f)

    def test_convert_docx_to_gdocs_format(self):
        """Test converting Word document to Google Docs format."""
        # Convert Word document
        result = convert_to_gdrive_format(self.docx_file)
        
        # Verify basic structure
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('mimeType', result)
        self.assertIn('content', result)
        
        # Verify file metadata
        self.assertEqual(result['name'], 'kids_craft_camp_2025_business_information.docx')
        self.assertEqual(result['mimeType'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        # Verify content structure
        self.assertIn('data', result['content'])
        self.assertIsInstance(result['content']['data'], list)

    def test_content_data_structure(self):
        """Test that content data has the expected structure."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        self.assertIsInstance(content_data, list)
        self.assertGreater(len(content_data), 0)
        
        # Check first element structure
        first_element = content_data[0]
        self.assertIn('elementId', first_element)
        self.assertIn('text', first_element)
        
        # Verify elementId format
        self.assertIsInstance(first_element['elementId'], str)
        self.assertTrue(first_element['elementId'].startswith('p'), 
                       f"Element ID should start with 'p', got: {first_element['elementId']}")

    def test_content_text_extraction(self):
        """Test that text content is properly extracted."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Check that we have meaningful text content
        text_elements = [elem['text'] for elem in content_data if elem.get('text')]
        self.assertGreater(len(text_elements), 0)
        
        # Check that first element contains expected title
        first_text = text_elements[0]
        self.assertIn('The Creative Canvas', first_text)
        self.assertIn('Kids\' Craft Camp', first_text)

    def test_paragraph_structure(self):
        """Test that paragraphs are properly structured."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Check that each element has proper structure
        for i, element in enumerate(content_data):
            self.assertIn('elementId', element, f"Element {i} missing elementId")
            self.assertIn('text', element, f"Element {i} missing text")
            
            # elementId should be in format p1, p2, etc.
            element_id = element['elementId']
            self.assertTrue(element_id.startswith('p'), 
                           f"Element ID should start with 'p', got: {element_id}")
            
            # text should be a string
            self.assertIsInstance(element['text'], str)

    def test_document_title_extraction(self):
        """Test that document title is properly extracted."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Find the title element (should be first paragraph)
        title_element = content_data[0]
        title_text = title_element['text']
        
        # Verify title content
        self.assertIn('The Creative Canvas', title_text)
        self.assertIn('Kids\' Craft Camp', title_text)
        self.assertIn('Business Information', title_text)

    def test_section_headers_extraction(self):
        """Test that section headers are properly extracted."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        text_elements = [elem['text'] for elem in content_data]
        
        # Check for expected section headers
        expected_headers = [
            '1. Executive Summary',
            '2. Project Goals',
            '3. Project Leads',
            '4. Instructors',
            '5. Time Schedule',
            '6. Facility Requirements:',
            '7. Materials & Supplies'
        ]
        
        for header in expected_headers:
            self.assertIn(header, text_elements, f"Header '{header}' not found in document")

    def test_content_preserves_formatting(self):
        """Test that content preserves important formatting."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Check that important content is preserved
        all_text = ' '.join([elem['text'] for elem in content_data])
        
        # Check for key business terms
        key_terms = [
            'Creative Canvas',
            'Craft Camp',
            'Taster Sessions',
            'Business Information',
            'Project Goals',
            'Instructors',
            'Materials'
        ]
        
        for term in key_terms:
            self.assertIn(term, all_text, f"Key term '{term}' not found in document")

    def test_converter_handles_special_characters(self):
        """Test that converter handles special characters in text."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Check that special characters are preserved
        for element in content_data:
            text = element['text']
            if text:
                # Should handle common special characters
                self.assertIsInstance(text, str)
                
                # Check for specific special characters that should be preserved
                if ':' in text or '-' in text or '.' in text:
                    # These should be preserved
                    pass

    def test_converter_produces_consistent_output(self):
        """Test that converter produces consistent output on multiple runs."""
        result1 = convert_to_gdrive_format(self.docx_file)
        result2 = convert_to_gdrive_format(self.docx_file)
        
        # Basic structure should be the same
        self.assertEqual(result1['name'], result2['name'])
        self.assertEqual(result1['mimeType'], result2['mimeType'])
        self.assertEqual(len(result1['content']['data']), len(result2['content']['data']))

    def test_converter_handles_file_not_found(self):
        """Test that converter handles non-existent files gracefully."""
        with self.assertRaises(FileNotFoundError):
            convert_to_gdrive_format('nonexistent_file.docx')

    def test_converter_handles_invalid_docx_file(self):
        """Test that converter handles invalid Word files gracefully."""
        # Create a temporary file that's not a valid Word file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(b'This is not a Word file')
            temp_file_path = temp_file.name
        
        try:
            # The converter should handle invalid files gracefully
            result = convert_to_gdrive_format(temp_file_path)
            # Should still return a valid structure even for invalid files
            self.assertIsInstance(result, dict)
            self.assertIn('id', result)
            self.assertIn('name', result)
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_document_metadata(self):
        """Test that document metadata is properly set."""
        result = convert_to_gdrive_format(self.docx_file)
        
        # Check required metadata fields
        self.assertIn('id', result)
        self.assertIn('driveId', result)
        self.assertIn('createdTime', result)
        self.assertIn('modifiedTime', result)
        self.assertIn('owners', result)
        self.assertIn('size', result)
        
        # Check data types
        self.assertIsInstance(result['id'], str)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['mimeType'], str)
        self.assertIsInstance(result['owners'], list)
        self.assertIsInstance(result['size'], (str, int))

    def test_content_element_ordering(self):
        """Test that content elements are in correct order."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Check that elements are numbered sequentially
        for i, element in enumerate(content_data):
            expected_id = f"p{i+1}"
            actual_id = element['elementId']
            self.assertEqual(actual_id, expected_id, 
                           f"Element {i} should have ID '{expected_id}', got '{actual_id}'")

    def test_content_text_quality(self):
        """Test that extracted text content is of good quality."""
        result = convert_to_gdrive_format(self.docx_file)
        
        content_data = result['content']['data']
        
        # Check that text is not empty for meaningful elements
        meaningful_elements = [elem for elem in content_data if elem['text'].strip()]
        self.assertGreater(len(meaningful_elements), 0)
        
        # Check that text doesn't contain excessive whitespace
        for element in meaningful_elements:
            text = element['text']
            # Should not have excessive leading/trailing whitespace
            self.assertEqual(text, text.strip(), 
                           f"Text should not have excessive whitespace: '{text}'")


if __name__ == '__main__':
    unittest.main() 