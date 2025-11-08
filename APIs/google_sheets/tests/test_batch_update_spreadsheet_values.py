"""
Test cases for batch_update_spreadsheet_values functionality.
Tests the proper updating of overlapping ranges in Google Sheets API simulation.
"""

import unittest

from google_sheets.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import batch_update_spreadsheet_values

class TestBatchUpdateSpreadsheetValues(BaseTestCaseWithErrorHandler):
    """Test batch_update_spreadsheet_values method for proper range updating."""

    def setUp(self):
        """Set up test data before each test."""
        # Clear and initialize the database
        DB.clear()
        DB["users"] = {
            "me": {
                "files": {}
            }
        }
        
        # Create a test spreadsheet
        self.spreadsheet_id = "test_spreadsheet_123"
        DB["users"]["me"]["files"][self.spreadsheet_id] = {
            "id": self.spreadsheet_id,
            "data": {
                "Sheet1!A1:B5": [
                    ["question", "answer"],
                    ["What is 2+2?", ""],
                    ["What is the capital of France?", "Paris"],
                    ["Who wrote Hamlet?", "William Shakespeare"],
                    ["What is the area of a circle?", "πr²"]
                ]
            }
        }

    def test_single_cell_update_within_existing_range(self):
        """Test updating a single cell that's part of an existing range."""
        # Update cell B2 (row 1, column 1) with value "4"
        data = [{"range": "Sheet1!B2", "values": [["4"]]}]
        
        result = batch_update_spreadsheet_values(
            spreadsheet_id=self.spreadsheet_id,
            valueInputOption="RAW",
            data=data,
            includeValuesInResponse=True
        )
        
        # Verify the response
        self.assertEqual(result["id"], self.spreadsheet_id)
        self.assertEqual(len(result["updatedData"]), 1)
        self.assertEqual(result["updatedData"][0]["range"], "Sheet1!B2")
        self.assertEqual(result["updatedData"][0]["values"], [["4"]])
        
        # Verify the data was updated in the existing range
        spreadsheet = DB["users"]["me"]["files"][self.spreadsheet_id]
        self.assertIn("Sheet1!A1:B5", spreadsheet["data"])
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][1][1], "4")  # B2 should be "4"
        
        # Verify no separate B2 entry was created
        self.assertNotIn("Sheet1!B2", spreadsheet["data"])

    def test_update_cell_outside_existing_range(self):
        """Test updating a cell that's not part of any existing range."""
        # Update cell D1 (outside the existing A1:B5 range)
        data = [{"range": "Sheet1!D1", "values": [["New Data"]]}]
        
        result = batch_update_spreadsheet_values(
            spreadsheet_id=self.spreadsheet_id,
            valueInputOption="RAW",
            data=data,
            includeValuesInResponse=True
        )
        
        # Verify the response
        self.assertEqual(result["updatedData"][0]["range"], "Sheet1!D1")
        
        # Verify a new entry was created for D1
        spreadsheet = DB["users"]["me"]["files"][self.spreadsheet_id]
        self.assertIn("Sheet1!D1", spreadsheet["data"])
        self.assertEqual(spreadsheet["data"]["Sheet1!D1"], [["New Data"]])
        
        # Verify the original range is unchanged
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][1][1], "")  # B2 should still be empty

    def test_update_multiple_ranges_mixed(self):
        """Test updating both overlapping and non-overlapping ranges."""
        data = [
            {"range": "Sheet1!B2", "values": [["Updated"]]},  # Overlaps with A1:B5
            {"range": "Sheet1!D1", "values": [["New"]]}      # Doesn't overlap
        ]
        
        result = batch_update_spreadsheet_values(
            spreadsheet_id=self.spreadsheet_id,
            valueInputOption="RAW",
            data=data,
            includeValuesInResponse=True
        )
        
        # Verify both updates
        spreadsheet = DB["users"]["me"]["files"][self.spreadsheet_id]
        
        # B2 should be updated in the existing A1:B5 range
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][1][1], "Updated")
        self.assertNotIn("Sheet1!B2", spreadsheet["data"])
        
        # D1 should have its own entry
        self.assertIn("Sheet1!D1", spreadsheet["data"])
        self.assertEqual(spreadsheet["data"]["Sheet1!D1"], [["New"]])

    def test_update_preserves_other_cells(self):
        """Test that updating one cell doesn't affect other cells in the range."""
        # Get original data
        spreadsheet = DB["users"]["me"]["files"][self.spreadsheet_id]
        original_data = [row[:] for row in spreadsheet["data"]["Sheet1!A1:B5"]]
        
        # Update only B2
        data = [{"range": "Sheet1!B2", "values": [["Updated"]]}]
        
        batch_update_spreadsheet_values(
            spreadsheet_id=self.spreadsheet_id,
            valueInputOption="RAW",
            data=data
        )
        
        # Verify B2 was updated
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][1][1], "Updated")
        
        # Verify other cells are unchanged
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][0], original_data[0])  # Header row
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][2], original_data[2])  # Row 3
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][3], original_data[3])  # Row 4
        self.assertEqual(spreadsheet["data"]["Sheet1!A1:B5"][4], original_data[4])  # Row 5

    def test_update_nonexistent_spreadsheet(self):
        """Test updating a non-existent spreadsheet."""
        self.assert_error_behavior(
            batch_update_spreadsheet_values,
            ValueError,
            "Spreadsheet not found",
            spreadsheet_id="nonexistent",
            valueInputOption="RAW",
            data=[{"range": "Sheet1!A1", "values": [["test"]]}]
        )

    def test_update_with_invalid_value_input_option(self):
        """Test updating with invalid valueInputOption."""
        data = [{"range": "Sheet1!B2", "values": [["test"]]}]
        
        self.assert_error_behavior(
            batch_update_spreadsheet_values,
            ValueError,
            "Invalid 'valueInputOption': INVALID_OPTION. Allowed options: ['RAW', 'USER_ENTERED']",
            spreadsheet_id=self.spreadsheet_id,
            valueInputOption="INVALID_OPTION",
            data=data
        )

    def test_update_with_invalid_range_format(self):
        """Test updating with invalid range format."""
        data = [{"range": "InvalidRange!@#$", "values": [["test"]]}]
        
        self.assert_error_behavior(
            batch_update_spreadsheet_values,
            ValueError,
            "not enough values to unpack (expected 2, got 1)",
            spreadsheet_id=self.spreadsheet_id,
            valueInputOption="RAW",
            data=data
        )


if __name__ == "__main__":
    unittest.main()