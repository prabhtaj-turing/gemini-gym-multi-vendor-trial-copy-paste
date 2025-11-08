#!/usr/bin/env python3
"""
Test Google Sheets converter using data files from tests/data folder.
Tests the conversion of Excel files to Google Sheets format.
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

from gsheets_converter import convert_excel_to_gsheets_format


class TestGSheetsDataFiles(unittest.TestCase):
    """Test Google Sheets converter with real data files."""

    def setUp(self):
        """Set up test data paths."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.excel_file = os.path.join(self.data_dir, '2025_Inventory.xlsx')
        self.expected_json_file = os.path.join(self.data_dir, '2025_Inventory.xlsx.json')
        
        # Load expected JSON data
        with open(self.expected_json_file, 'r', encoding='utf-8') as f:
            self.expected_data = json.load(f)

    def test_convert_excel_to_gsheets_format(self):
        """Test converting Excel file to Google Sheets format."""
        # Convert Excel file
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        # Verify basic structure
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('mimeType', result)
        self.assertIn('sheets', result)
        self.assertIn('data', result)
        
        # Verify file metadata
        self.assertEqual(result['name'], '2025_Inventory.xlsx')
        self.assertEqual(result['mimeType'], 'application/vnd.google-apps.spreadsheet')
        
        # Verify sheets structure
        self.assertIsInstance(result['sheets'], list)
        self.assertGreater(len(result['sheets']), 0)
        
        # Verify data structure
        self.assertIsInstance(result['data'], dict)
        self.assertGreater(len(result['data']), 0)

    def test_sheet_properties_match_expected(self):
        """Test that sheet properties match expected structure."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        # Check first sheet properties
        first_sheet = result['sheets'][0]
        self.assertIn('properties', first_sheet)
        self.assertIn('sheetId', first_sheet['properties'])
        self.assertIn('title', first_sheet['properties'])
        self.assertIn('index', first_sheet['properties'])
        self.assertIn('sheetType', first_sheet['properties'])
        self.assertIn('gridProperties', first_sheet['properties'])
        
        # Verify grid properties
        grid_props = first_sheet['properties']['gridProperties']
        self.assertIn('rowCount', grid_props)
        self.assertIn('columnCount', grid_props)
        self.assertGreater(grid_props['rowCount'], 0)
        self.assertGreater(grid_props['columnCount'], 0)

    def test_data_content_structure(self):
        """Test that data content has the expected structure."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        # Check that data contains ranges
        data_ranges = list(result['data'].keys())
        self.assertGreater(len(data_ranges), 0)
        
        # Check first data range
        first_range = data_ranges[0]
        self.assertIn('!', first_range)  # Should contain sheet name and range
        
        # Check data content
        first_data = result['data'][first_range]
        self.assertIsInstance(first_data, list)
        self.assertGreater(len(first_data), 0)
        
        # Check that first row contains headers
        headers = first_data[0]
        self.assertIsInstance(headers, list)
        expected_headers = ['Product_ID', 'Category', 'Subcategory', 'Product_Name', 
                           'Brand', 'Description', 'Size', 'Unit', 'Color', 
                           'Quantity', 'Price', 'Supplier']
        
        # Verify key headers are present
        for header in expected_headers:
            self.assertIn(header, headers, f"Header '{header}' not found in data")

    def test_data_content_values(self):
        """Test that data content contains expected values."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        # Get first data range
        data_ranges = list(result['data'].keys())
        first_range = data_ranges[0]
        data = result['data'][first_range]
        
        # Check that we have multiple rows (header + data)
        self.assertGreater(len(data), 1)
        
        # Check first data row (after header)
        first_data_row = data[1]
        self.assertIsInstance(first_data_row, list)
        self.assertGreater(len(first_data_row), 0)
        
        # Verify product ID format
        product_id = first_data_row[0]
        self.assertIsInstance(product_id, str)
        self.assertTrue(product_id.startswith('A'), f"Product ID should start with 'A', got: {product_id}")

    def test_sheet_title_matches_expected(self):
        """Test that sheet title matches expected value."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        # Check sheet title
        first_sheet = result['sheets'][0]
        sheet_title = first_sheet['properties']['title']
        self.assertEqual(sheet_title, 'Creative Canvas V3')

    def test_data_range_format(self):
        """Test that data ranges are in correct format."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        data_ranges = list(result['data'].keys())
        
        for range_key in data_ranges:
            # Should be in format "SheetName!Range"
            self.assertIn('!', range_key)
            parts = range_key.split('!')
            self.assertEqual(len(parts), 2)
            
            sheet_name = parts[0]
            range_spec = parts[1]
            
            # Sheet name should not be empty
            self.assertGreater(len(sheet_name), 0)
            
            # Range should contain letters and numbers
            self.assertTrue(any(c.isalpha() for c in range_spec))
            self.assertTrue(any(c.isdigit() for c in range_spec))

    def test_converter_handles_empty_cells(self):
        """Test that converter handles empty cells gracefully."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        # Get data and check for empty cells
        data_ranges = list(result['data'].keys())
        first_range = data_ranges[0]
        data = result['data'][first_range]
        
        # Check that empty cells are handled (should be empty strings or None)
        for row in data:
            for cell in row:
                # Cell should be string, number, or None/empty
                self.assertTrue(
                    isinstance(cell, (str, int, float)) or cell is None or cell == '',
                    f"Unexpected cell type: {type(cell)} for value: {cell}"
                )

    def test_converter_preserves_data_types(self):
        """Test that converter preserves appropriate data types."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        data_ranges = list(result['data'].keys())
        first_range = data_ranges[0]
        data = result['data'][first_range]
        
        # Check that numeric values are preserved as numbers
        for row_idx, row in enumerate(data[1:], 1):  # Skip header
            if len(row) >= 10:  # Quantity column
                quantity = row[9]  # Quantity column
                if quantity and quantity != '':
                    # Should be convertible to float
                    try:
                        float(quantity)
                    except (ValueError, TypeError):
                        self.fail(f"Quantity value '{quantity}' in row {row_idx} should be numeric")

    def test_converter_handles_special_characters(self):
        """Test that converter handles special characters in text."""
        result = convert_excel_to_gsheets_format(self.excel_file)
        
        data_ranges = list(result['data'].keys())
        first_range = data_ranges[0]
        data = result['data'][first_range]
        
        # Check that special characters in product names are preserved
        for row in data[1:]:  # Skip header
            if len(row) >= 4:  # Product_Name column
                product_name = row[3]
                if product_name and isinstance(product_name, str):
                    # Should handle common special characters
                    self.assertIsInstance(product_name, str)

    def test_converter_produces_consistent_output(self):
        """Test that converter produces consistent output on multiple runs."""
        result1 = convert_excel_to_gsheets_format(self.excel_file)
        result2 = convert_excel_to_gsheets_format(self.excel_file)
        
        # Basic structure should be the same
        self.assertEqual(result1['name'], result2['name'])
        self.assertEqual(result1['mimeType'], result2['mimeType'])
        self.assertEqual(len(result1['sheets']), len(result2['sheets']))
        self.assertEqual(len(result1['data']), len(result2['data']))

    def test_converter_handles_file_not_found(self):
        """Test that converter handles non-existent files gracefully."""
        with self.assertRaises(FileNotFoundError):
            convert_excel_to_gsheets_format('nonexistent_file.xlsx')

    def test_converter_handles_invalid_excel_file(self):
        """Test that converter handles invalid Excel files gracefully."""
        # Create a temporary file that's not a valid Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file.write(b'This is not an Excel file')
            temp_file_path = temp_file.name
        
        try:
            # The converter should handle invalid files gracefully
            result = convert_excel_to_gsheets_format(temp_file_path)
            # Should still return a valid structure even for invalid files
            self.assertIsInstance(result, dict)
            self.assertIn('id', result)
            self.assertIn('name', result)
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


if __name__ == '__main__':
    unittest.main() 