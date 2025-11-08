#!/usr/bin/env python3
"""
Test Google Slides converter using data files from tests/data folder.
Tests the conversion of PowerPoint files to Google Slides format.
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

from gslides_converter import convert_pptx_to_gslides_format


class TestGSlidesDataFiles(unittest.TestCase):
    """Test Google Slides converter with real data files."""

    def setUp(self):
        """Set up test data paths."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.pptx_file = os.path.join(self.data_dir, 'Summer_Spark!_2025_seasonal_overview.pptx')
        self.expected_json_file = os.path.join(self.data_dir, 'Summer_Spark!_2025_seasonal_overview.pptx.json')
        
        # Load expected JSON data
        with open(self.expected_json_file, 'r', encoding='utf-8') as f:
            self.expected_data = json.load(f)

    def test_convert_pptx_to_gslides_format(self):
        """Test converting PowerPoint file to Google Slides format."""
        # Convert PowerPoint file
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Verify basic structure
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('mimeType', result)
        self.assertIn('presentationId', result)
        self.assertIn('title', result)
        self.assertIn('slides', result)
        
        # Verify file metadata
        self.assertEqual(result['name'], 'Summer_Spark!_2025_seasonal_overview.pptx')
        self.assertEqual(result['mimeType'], 'application/vnd.google-apps.presentation')
        self.assertEqual(result['title'], 'Summer_Spark!_2025_seasonal_overview')
        
        # Verify slides structure
        self.assertIsInstance(result['slides'], list)
        self.assertGreater(len(result['slides']), 0)

    def test_slide_structure(self):
        """Test that slides have the expected structure."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Check first slide structure
        first_slide = result['slides'][0]
        self.assertIn('objectId', first_slide)
        self.assertIn('pageType', first_slide)
        self.assertIn('pageProperties', first_slide)
        self.assertIn('slideProperties', first_slide)
        self.assertIn('pageElements', first_slide)
        
        # Verify page type
        self.assertEqual(first_slide['pageType'], 'SLIDE')
        
        # Verify page elements
        self.assertIsInstance(first_slide['pageElements'], list)
        self.assertGreater(len(first_slide['pageElements']), 0)

    def test_page_element_structure(self):
        """Test that page elements have the expected structure."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        first_slide = result['slides'][0]
        first_element = first_slide['pageElements'][0]
        
        # Check element structure
        self.assertIn('objectId', first_element)
        self.assertIn('size', first_element)
        self.assertIn('transform', first_element)
        self.assertIn('shape', first_element)
        
        # Check size structure
        size = first_element['size']
        self.assertIn('width', size)
        self.assertIn('height', size)
        self.assertIn('magnitude', size['width'])
        self.assertIn('unit', size['width'])
        
        # Check transform structure
        transform = first_element['transform']
        self.assertIn('scaleX', transform)
        self.assertIn('scaleY', transform)
        self.assertIn('translateX', transform)
        self.assertIn('translateY', transform)
        self.assertIn('unit', transform)

    def test_shape_structure(self):
        """Test that shapes have the expected structure."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        first_slide = result['slides'][0]
        
        # Find text elements
        text_elements = [elem for elem in first_slide['pageElements'] 
                        if elem['shape'].get('shapeType') == 'TEXT_BOX']
        
        if text_elements:
            text_element = text_elements[0]
            shape = text_element['shape']
            
            # Check shape structure
            self.assertIn('shapeType', shape)
            self.assertEqual(shape['shapeType'], 'TEXT_BOX')
            
            # Check text structure
            if 'text' in shape:
                text = shape['text']
                self.assertIn('textElements', text)
                self.assertIsInstance(text['textElements'], list)

    def test_text_elements_structure(self):
        """Test that text elements have the expected structure."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        first_slide = result['slides'][0]
        
        # Find text elements
        text_elements = [elem for elem in first_slide['pageElements'] 
                        if elem['shape'].get('shapeType') == 'TEXT_BOX']
        
        if text_elements:
            text_element = text_elements[0]
            shape = text_element['shape']
            
            if 'text' in shape and 'textElements' in shape['text']:
                text_elements_list = shape['text']['textElements']
                
                for text_elem in text_elements_list:
                    if 'textRun' in text_elem:
                        text_run = text_elem['textRun']
                        self.assertIn('content', text_run)
                        self.assertIn('style', text_run)
                        
                        # Check style structure
                        style = text_run['style']
                        self.assertIn('fontFamily', style)
                        self.assertIn('fontSize', style)

    def test_slide_content_extraction(self):
        """Test that slide content is properly extracted."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Extract all text content from slides
        all_text = []
        for slide in result['slides']:
            for element in slide['pageElements']:
                if element['shape'].get('shapeType') == 'TEXT_BOX':
                    shape = element['shape']
                    if 'text' in shape and 'textElements' in shape['text']:
                        for text_elem in shape['text']['textElements']:
                            if 'textRun' in text_elem:
                                all_text.append(text_elem['textRun']['content'])
        
        # Check that we have meaningful text content
        self.assertGreater(len(all_text), 0)
        
        # Check for expected content
        all_text_combined = ' '.join(all_text)
        expected_terms = ['Creative Canvas', 'Summer Spark', 'Marketing']
        
        for term in expected_terms:
            self.assertIn(term, all_text_combined, f"Expected term '{term}' not found in slides")

    def test_slide_count(self):
        """Test that the correct number of slides is extracted."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Should have multiple slides
        self.assertGreater(len(result['slides']), 1)
        
        # Check that each slide has proper structure
        for i, slide in enumerate(result['slides']):
            self.assertIn('objectId', slide, f"Slide {i} missing objectId")
            self.assertIn('pageType', slide, f"Slide {i} missing pageType")
            self.assertIn('pageElements', slide, f"Slide {i} missing pageElements")

    def test_presentation_metadata(self):
        """Test that presentation metadata is properly set."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Check required metadata fields
        self.assertIn('id', result)
        self.assertIn('driveId', result)
        self.assertIn('createdTime', result)
        self.assertIn('modifiedTime', result)
        self.assertIn('owners', result)
        self.assertIn('size', result)
        self.assertIn('permissions', result)
        
        # Check data types
        self.assertIsInstance(result['id'], str)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['mimeType'], str)
        self.assertIsInstance(result['presentationId'], str)
        self.assertIsInstance(result['title'], str)
        self.assertIsInstance(result['owners'], list)
        self.assertIsInstance(result['size'], (str, int))

    def test_page_size_structure(self):
        """Test that page size has the expected structure."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        self.assertIn('pageSize', result)
        page_size = result['pageSize']
        
        self.assertIn('width', page_size)
        self.assertIn('height', page_size)
        
        # Check width structure
        width = page_size['width']
        self.assertIn('magnitude', width)
        self.assertIn('unit', width)
        self.assertIsInstance(width['magnitude'], (int, float))
        self.assertEqual(width['unit'], 'EMU')
        
        # Check height structure
        height = page_size['height']
        self.assertIn('magnitude', height)
        self.assertIn('unit', height)
        self.assertIsInstance(height['magnitude'], (int, float))
        self.assertEqual(height['unit'], 'EMU')

    def test_converter_handles_special_characters(self):
        """Test that converter handles special characters in text."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Extract all text content
        all_text = []
        for slide in result['slides']:
            for element in slide['pageElements']:
                if element['shape'].get('shapeType') == 'TEXT_BOX':
                    shape = element['shape']
                    if 'text' in shape and 'textElements' in shape['text']:
                        for text_elem in shape['text']['textElements']:
                            if 'textRun' in text_elem:
                                all_text.append(text_elem['textRun']['content'])
        
        # Check that special characters are preserved
        for text in all_text:
            if text:
                # Should handle common special characters
                self.assertIsInstance(text, str)

    def test_converter_produces_consistent_output(self):
        """Test that converter produces consistent output on multiple runs."""
        result1 = convert_pptx_to_gslides_format(self.pptx_file)
        result2 = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Basic structure should be the same
        self.assertEqual(result1['name'], result2['name'])
        self.assertEqual(result1['mimeType'], result2['mimeType'])
        self.assertEqual(result1['title'], result2['title'])
        self.assertEqual(len(result1['slides']), len(result2['slides']))

    def test_converter_handles_file_not_found(self):
        """Test that converter handles non-existent files gracefully."""
        with self.assertRaises(FileNotFoundError):
            convert_pptx_to_gslides_format('nonexistent_file.pptx')

    def test_converter_handles_invalid_pptx_file(self):
        """Test that converter handles invalid PowerPoint files gracefully."""
        # Create a temporary file that's not a valid PowerPoint file
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as temp_file:
            temp_file.write(b'This is not a PowerPoint file')
            temp_file_path = temp_file.name
        
        try:
            # The converter should handle invalid files gracefully
            result = convert_pptx_to_gslides_format(temp_file_path)
            # Should still return a valid structure even for invalid files
            self.assertIsInstance(result, dict)
            self.assertIn('id', result)
            self.assertIn('name', result)
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_slide_object_id_format(self):
        """Test that slide object IDs are in correct format."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        for i, slide in enumerate(result['slides']):
            object_id = slide['objectId']
            # Should be in format slide1_page1, slide2_page2, etc.
            expected_format = f"slide{i+1}_page{i+1}"
            self.assertEqual(object_id, expected_format, 
                           f"Slide {i} should have objectId '{expected_format}', got '{object_id}'")

    def test_element_object_id_format(self):
        """Test that element object IDs are in correct format."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        for slide_idx, slide in enumerate(result['slides']):
            for elem_idx, element in enumerate(slide['pageElements']):
                object_id = element['objectId']
                # Should be in format element1_slide1, element2_slide1, etc.
                expected_format = f"element{elem_idx+1}_slide{slide_idx+1}"
                self.assertEqual(object_id, expected_format, 
                               f"Element {elem_idx} in slide {slide_idx} should have objectId '{expected_format}', got '{object_id}'")

    def test_text_content_quality(self):
        """Test that extracted text content is of good quality."""
        result = convert_pptx_to_gslides_format(self.pptx_file)
        
        # Extract all text content
        all_text = []
        for slide in result['slides']:
            for element in slide['pageElements']:
                if element['shape'].get('shapeType') == 'TEXT_BOX':
                    shape = element['shape']
                    if 'text' in shape and 'textElements' in shape['text']:
                        for text_elem in shape['text']['textElements']:
                            if 'textRun' in text_elem:
                                content = text_elem['textRun']['content']
                                if content.strip():
                                    all_text.append(content)
        
        # Check that we have meaningful text content
        self.assertGreater(len(all_text), 0)
        
        # Check that text doesn't contain excessive whitespace
        for text in all_text:
            if text:
                # Should not have excessive leading/trailing whitespace
                # Allow for some whitespace as it might be intentional formatting
                stripped_text = text.strip()
                if stripped_text:  # Only check non-empty text
                    # Check that the text is not just whitespace
                    self.assertNotEqual(text, ' ' * len(text), 
                                       f"Text should not be just whitespace: '{text}'")


if __name__ == '__main__':
    unittest.main() 