"""SpreadsheetValues resource for Google Sheets API simulation.

This module provides methods for managing spreadsheet values, including reading
and writing cell values, ranges, and formulas. It simulates the Google Sheets
API functionality for value operations.

The SpreadsheetValues class provides the following operations:
- get: Retrieves values from a specific range
- update: Updates values in a specific range
- append: Appends values to a range
- clear: Clears values from a range
- batchGet: Retrieves values from multiple ranges
- batchUpdate: Updates values in multiple ranges
- batchClear: Clears values from multiple ranges
- batchGetByDataFilter: Retrieves values using data filters
- batchUpdateByDataFilter: Updates values using data filters
"""

from common_utils.tool_spec_decorator import tool_spec
import re
import builtins

from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import ValidationError

from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import validate_sheet_exists_in_spreadsheet

from ..SimulationEngine.models import ( # This import should also be present
    AppendSpecificArgsModel,
    DataFilterModel,
    ValueRangeModel,
    A1RangeInput
)

from ..SimulationEngine.custom_errors import InvalidFunctionParameterError
from ..SimulationEngine.utils import (
    get_dynamic_data, 
    update_dynamic_data, 
    range2ints, 
    split_sheet_and_range,
    normalize_for_comparison,
    extract_sheet_name,
    extract_range_part,
    parse_a1_notation_extended,
    is_range_subset,
    validate_sheet_name,
    parse_a1_range,
    gsheet_range
)

# Constants for validation
VALID_VALUE_INPUT_OPTIONS = {"RAW", "USER_ENTERED"}
VALID_RESPONSE_VALUE_RENDER_OPTIONS = {"FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"}
VALID_RESPONSE_DATETIME_RENDER_OPTIONS = {"SERIAL_NUMBER", "FORMATTED_STRING"}


@tool_spec(
    spec={
        'name': 'get_spreadsheet_values',
        'description': 'Gets values from a specific range in a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to retrieve values from.'
                },
                'range': {
                    'type': 'string',
                    'description': """ The A1 notation of the range to retrieve values from.
                    Supports various formats:
                        Basic ranges (without sheet name - uses first sheet):
                        - Single cell: "A1"
                        - Cell range: "A1:B2"
                        - Full column: "A:B"
                        - Full row: "1:2"
                        - Mixed range: "A2:Z" (from cell A2 to end of column Z)
                        
                        With sheet names (recommended for multi-sheet spreadsheets):
                        - Simple sheet: "Sheet1!A1:B2"
                        - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                        - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                        - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                        - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                        - Sheet-only: "Sheet1" (entire sheet)
                        
                        Note: If no sheet name specified, first sheet is automatically used.
                    """
                },
                'majorDimension': {
                    'type': 'string',
                    'description': """ The major dimension that results should use.
                    If not specified, defaults to "ROWS". Valid values: "ROWS", "COLUMNS". """
                },
                'valueRenderOption': {
                    'type': 'string',
                    'description': """ How values should be rendered in the output.
                    If not specified, defaults to "FORMATTED_VALUE". Valid values:
                    "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". """
                },
                'dateTimeRenderOption': {
                    'type': 'string',
                    'description': """ How dates, times, and durations should be rendered.
                    If not specified, defaults to "FORMATTED_STRING". Valid values:
                    "SERIAL_NUMBER", "FORMATTED_STRING". """
                }
            },
            'required': [
                'spreadsheet_id',
                'range'
            ]
        }
    }
)
def get(
    spreadsheet_id: str,
    range: str,
    majorDimension: Optional[str] = "ROWS",
    valueRenderOption: Optional[str] = "FORMATTED_VALUE",
    dateTimeRenderOption: Optional[str] = "FORMATTED_STRING",
) -> Dict[str, Any]:
    """Gets values from a specific range in a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to retrieve values from.
        range (str): The A1 notation of the range to retrieve values from. Supports various formats:
            
            Basic ranges (without sheet name - uses first sheet in spreadsheet):
            - Single cell: "A1"
            - Cell range: "A1:B2"
            - Full column: "A:B"
            - Full row: "1:2"
            - Mixed range: "A2:Z" (from cell A2 to end of column Z)
            
            With sheet names (recommended for multi-sheet spreadsheets):
            - Simple sheet: "Sheet1!A1:B2"
            - Default sheets: "Sheet2!A:A", "sheet1!1:10"
            - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
            - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
            - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
            - Sheet-only reference: "Sheet1" (returns entire sheet)
            
            Note: If no sheet name is specified (e.g., "A1:B2"), the system automatically 
            uses the first sheet in the spreadsheet data.
            
        majorDimension (Optional[str]): The major dimension that results should use.
            If not specified, defaults to "ROWS". Valid values: "ROWS", "COLUMNS".
        valueRenderOption (Optional[str]): How values should be rendered in the output.
            If not specified, defaults to "FORMATTED_VALUE". Valid values:
            "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA".
        dateTimeRenderOption (Optional[str]): How dates, times, and durations should be rendered.
            If not specified, defaults to "FORMATTED_STRING". Valid values:
            "SERIAL_NUMBER", "FORMATTED_STRING".

    Returns:
        Dict[str, Any]: A dictionary containing:
            - range (str): The A1 notation of the range that was retrieved.
            - majorDimension (str): The major dimension of the values
            - values (List[List[Any]]): The retrieved values

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `range` is not a string.
            - If `majorDimension` is not a string.
            - If `valueRenderOption` is not a string.
            - If `dateTimeRenderOption` is not a string.
        ValueError: In the following cases:
            - If `majorDimension`, `valueRenderOption`, or `dateTimeRenderOption` is provided with an unsupported value.
            - If the spreadsheet is not found (propagated from core logic).
            - If the `range` argument is invalid (e.g., fails A1RangeInput validation).
            - If the specified sheet name in the range does not exist in the spreadsheet.
    """
    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError(f"spreadsheet_id must be a string, got {type(spreadsheet_id).__name__}")
    if not isinstance(range, str):
        raise TypeError(f"range must be a string, got {type(range).__name__}")
    if not isinstance(majorDimension, str):
        raise TypeError(f"majorDimension must be a string, got {type(majorDimension).__name__}")
    if not isinstance(valueRenderOption, str):
        raise TypeError(f"valueRenderOption must be a string, got {type(valueRenderOption).__name__}")
    if not isinstance(dateTimeRenderOption, str):
        raise TypeError(f"dateTimeRenderOption must be a string, got {type(dateTimeRenderOption).__name__}")

    VALID_MAJOR_DIMENSIONS = ["ROWS", "COLUMNS"]
    if majorDimension not in VALID_MAJOR_DIMENSIONS:
        raise ValueError(f"Invalid majorDimension: '{majorDimension}'. Must be one of {VALID_MAJOR_DIMENSIONS}")

    VALID_VALUE_RENDER_OPTIONS = ["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]
    if valueRenderOption not in VALID_VALUE_RENDER_OPTIONS:
        raise ValueError(f"Invalid valueRenderOption: '{valueRenderOption}'. Must be one of {VALID_VALUE_RENDER_OPTIONS}")

    VALID_DATETIME_RENDER_OPTIONS = ["SERIAL_NUMBER", "FORMATTED_STRING"]
    if dateTimeRenderOption not in VALID_DATETIME_RENDER_OPTIONS:
        raise ValueError(f"Invalid dateTimeRenderOption: '{dateTimeRenderOption}'. Must be one of {VALID_DATETIME_RENDER_OPTIONS}")
    
    try:
        validated_range = A1RangeInput(range=range)
        range_value = validated_range.range
    except ValueError as e:
        raise ValueError(f"Invalid range: {e}")
    
    # --- End of Input Validation ---

    # --- Original Core Logic (unchanged) ---
    userId = "me"

    # This part assumes DB is populated correctly in the execution environment.
    # If DB is not structured as expected or userId/spreadsheet_id is not found,
    # it will raise errors like KeyError or TypeError, which are standard Python errors.
    # The specific "Spreadsheet not found" ValueError is handled below.
    if spreadsheet_id not in DB["users"][userId]["files"]: # type: ignore
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id] # type: ignore
    
    # Validate sheet name
    validate_sheet_name(range_value, spreadsheet["data"])
    
    # Validate that the sheet exists in the spreadsheet (input validation)
    # For read operations on empty spreadsheets, allow if the sheet structure exists
    validate_sheet_exists_in_spreadsheet(range_value, spreadsheet["data"], allow_empty_spreadsheet=True, spreadsheet=spreadsheet)
    
    # If the range exists in the data, return it
    if range_value in spreadsheet["data"]:
        values = spreadsheet["data"][range_value]
    else:
        # Get the data using the dynamic data function which handles sheet name normalization
        values = get_dynamic_data(range_value, spreadsheet)

    # Handle majorDimension parameter
    if majorDimension == "COLUMNS" and values:
        # Transpose the data when majorDimension is COLUMNS
        transposed_values = []
        if not all(isinstance(row, list) for row in values): # Ensure values is List[List[Any]]
             # Handle cases where values might not be as expected, e.g. if data is malformed
             # For simplicity, we'll just pass it through or raise an error if critical
             pass # Or raise an appropriate error / log a warning
        else:
            max_row_length = 0
            if values and any(values): # ensure values is not empty and has at least one non-empty row
                try:
                    max_row_length = max(len(row) for row in values if row) # Ensure row is not None
                except ValueError: # max() arg is an empty sequence
                    pass # max_row_length remains 0

            for i in builtins.range(max_row_length):
                new_row = []
                for row in values:
                    new_row.append(row[i] if i < len(row) else "")
                transposed_values.append(new_row)
            values = transposed_values


    # Process valueRenderOption parameter
    if valueRenderOption in ["UNFORMATTED_VALUE", "FORMULA"]:
        # Simple simulation of these options
        # In a real implementation, this would access the actual cell formatting and formulas
        for i, row in enumerate(values):
            for j, cell_value in enumerate(row):
                # For UNFORMATTED_VALUE, we would strip formatting here
                # For FORMULA, we would show the actual formula instead of the result
                if valueRenderOption == "FORMULA" and isinstance(cell_value, str):
                    if cell_value.startswith("FORMULA:"):
                        # Strip the FORMULA: prefix if it exists
                        values[i][j] = cell_value.replace("FORMULA:", "")
                elif valueRenderOption == "UNFORMATTED_VALUE" and isinstance(
                    cell_value, str
                ):
                    # Simple simulation: just convert formatted dates or numbers to a basic form
                    # In reality, this would use more complex formatting rules
                    try:
                        # If it looks like a number, convert to a number
                        values[i][j] = float(cell_value)
                    except (ValueError, TypeError):
                        pass

    # Process dateTimeRenderOption parameter
    if dateTimeRenderOption == "SERIAL_NUMBER":
        # Simple simulation: convert date strings to a serial number format
        # In a real implementation, this would convert actual date objects to Excel serial numbers

        excel_epoch = datetime(1899, 12, 30)
        for i, row in enumerate(values):
            for j, cell_value in enumerate(row):
                if isinstance(cell_value, str):
                    # Try to detect and convert date strings
                    # This is a simple example; a real implementation would be more robust
                    try:
                        date_obj = datetime.strptime(cell_value, "%Y-%m-%d")
                        delta = date_obj - excel_epoch
                        values[i][j] = delta.days + (delta.seconds / 86400)
                    except (ValueError, TypeError):
                        # Not a recognizable date format
                        pass

    return {"range": range_value, "majorDimension": majorDimension, "values": values}


@tool_spec(
    spec={
        'name': 'update_spreadsheet_values',
        'description': 'Updates values in a specific range of a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to update.'
                },
                'range': {
                    'type': 'string',
                    'description': """ The A1 notation of the range to update. Supports various formats:

                    Basic ranges (without sheet name - uses first sheet):
                    - Single cell: "A1"
                    - Cell range: "A1:B2"
                    - Full column: "A:B"
                    - Full row: "1:2"
                    - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                    With sheet names (recommended for multi-sheet spreadsheets):
                    - Simple sheet: "Sheet1!A1:B2"
                    - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                    - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                    - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                    - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                    
                    Note: If no sheet name specified, first sheet is automatically used.
                    """
                },
                'valueInputOption': {
                    'type': 'string',
                    'description': """ How the input data should be interpreted.
                    Valid values: "RAW" (values inserted as-is) or
                    "USER_ENTERED" (values parsed as if entered by user). """
                },
                'values': {
                    'type': 'array',
                    'description': 'The values to update in the range (list of rows). Each inner list represents a row.',
                    'items': {
                        'type': 'array',
                        'description': 'A row of cell values. Each cell can contain a string, number, boolean, or null value.',
                        'items': {
                            'anyOf': [
                                {'type': 'STRING', 'description': 'Text value'},
                                {'type': 'NUMBER', 'description': 'Numeric value'},
                                {'type': 'BOOLEAN', 'description': 'Boolean value'}
                            ],
                            'description': 'Cell value. Can be a string (text), number, boolean, or null (empty cell).'
                        }
                    }
                },
                'includeValuesInResponse': {
                    'type': 'boolean',
                    'description': 'Whether to include the updated values in the response. Defaults to False.'
                },
                'responseValueRenderOption': {
                    'type': 'string',
                    'description': """ How values should be rendered in the response. Defaults to "FORMATTED_VALUE".
                    Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". """
                },
                'responseDateTimeRenderOption': {
                    'type': 'string',
                    'description': """ How dates, times, and durations should be rendered in the response. Defaults to "SERIAL_NUMBER".
                    Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". """
                }
            },
            'required': [
                'spreadsheet_id',
                'range',
                'valueInputOption',
                'values'
            ]
        }
    }
)
def update(
    spreadsheet_id: str,
    range: str,
    valueInputOption: str,
    values: List[List[Union[str, int, float, bool, None]]],
    includeValuesInResponse: bool = False,
    responseValueRenderOption: str = "FORMATTED_VALUE",
    responseDateTimeRenderOption: str = "SERIAL_NUMBER",
) -> Dict[str, Any]:
    """Updates values in a specific range of a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to update.
        range (str): The A1 notation of the range to update. Supports various formats:
            
            Basic ranges (without sheet name - uses first sheet in spreadsheet):
            - Single cell: "A1"
            - Cell range: "A1:B2"
            - Full column: "A:B"
            - Full row: "1:2"
            - Mixed range: "A2:Z" (from cell A2 to end of column Z)
            
            With sheet names (recommended for multi-sheet spreadsheets):
            - Simple sheet: "Sheet1!A1:B2"
            - Default sheets: "Sheet2!A:A", "sheet1!1:10"
            - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
            - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
            - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
            
            Note: If no sheet name is specified (e.g., "A1:B2"), the system automatically 
            uses the first sheet in the spreadsheet data.
            
        valueInputOption (str): How the input data should be interpreted.
            Valid values: "RAW" (values inserted as-is) or
            "USER_ENTERED" (values parsed as if entered by user).
        values (List[List[Union[str, int, float, bool, None]]]): The values to update in the range. Each inner list represents a row.
            Each cell value can be:
            - str: Text value for the cell
            - int: Integer numeric value for the cell
            - float: Decimal numeric value for the cell
            - bool: Boolean value for the cell (True/False)
            - None: Empty cell value
        includeValuesInResponse (bool): Whether to include the updated values in the response. Defaults to False.
        responseValueRenderOption (str): How values should be rendered in the response. Defaults to "FORMATTED_VALUE".
            Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA".
        responseDateTimeRenderOption (str): How dates, times, and durations should be rendered in the response. Defaults to "SERIAL_NUMBER".
            Valid values: "SERIAL_NUMBER", "FORMATTED_STRING".

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The spreadsheet ID
            - updatedRange (str): The range that was updated
            - updatedRows (int): Number of rows updated
            - updatedColumns (int): Number of columns updated
            - values (List[List[Union[str, int, float, bool, None]]], optional): The updated values if includeValuesInResponse is True

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `range` is not a string.
            - If `valueInputOption` is not a string.
            - If `values` is not a list.
            - If any item in `values` is not a list (i.e., not a list of lists).
            - If `includeValuesInResponse` is not a boolean.
            - If `responseValueRenderOption` is not a string.
            - If `responseDateTimeRenderOption` is not a string.
        ValueError: In the following cases:
            - If `spreadsheet_id` is an empty string.
            - If `range` is an empty string.
            - If `valueInputOption` is not one of the allowed values ("RAW", "USER_ENTERED").
            - If `responseValueRenderOption` is not one of the allowed values ("FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA").
            - If `responseDateTimeRenderOption` is not one of the allowed values ("SERIAL_NUMBER", "FORMATTED_STRING").
            - If the `range` argument is invalid (e.g., fails A1RangeInput validation).
            - If the spreadsheet is not found (propagated from core logic).
            - If the specified sheet name in the range does not exist in the spreadsheet (for read operations).
            Note: For write operations like update, new sheets can be created if they don't exist.
    """
    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError("spreadsheet_id must be a string.")
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id cannot be empty.")

    if not isinstance(range, str):
        raise TypeError("range must be a string.")
    if not range:
        raise ValueError("range cannot be empty.")

    if not isinstance(valueInputOption, str):
        raise TypeError("valueInputOption must be a string.")
    if valueInputOption not in VALID_VALUE_INPUT_OPTIONS:
        raise ValueError(
            f"valueInputOption must be one of {list(VALID_VALUE_INPUT_OPTIONS)}. Got '{valueInputOption}'."
        )

    if not isinstance(values, list):
        raise TypeError("values must be a list.")
    if not all(isinstance(row, list) for row in values):
        raise TypeError("Each item in 'values' must be a list (representing a row).")

    if not isinstance(includeValuesInResponse, bool):
        raise TypeError("includeValuesInResponse must be a boolean.")

    if not isinstance(responseValueRenderOption, str):
        raise TypeError("responseValueRenderOption must be a string.")
    if responseValueRenderOption not in VALID_RESPONSE_VALUE_RENDER_OPTIONS:
        raise ValueError(
            f"responseValueRenderOption must be one of {list(VALID_RESPONSE_VALUE_RENDER_OPTIONS)}. Got '{responseValueRenderOption}'."
        )

    if not isinstance(responseDateTimeRenderOption, str):
        raise TypeError("responseDateTimeRenderOption must be a string.")
    if responseDateTimeRenderOption not in VALID_RESPONSE_DATETIME_RENDER_OPTIONS:
        raise ValueError(
            f"responseDateTimeRenderOption must be one of {list(VALID_RESPONSE_DATETIME_RENDER_OPTIONS)}. Got '{responseDateTimeRenderOption}'."
        )
    
    try:
        validated_range = A1RangeInput(range=range)
        range_value = validated_range.range
    except ValueError as e:
        raise ValueError(f"Invalid range: {e}")
    # --- End of Input Validation ---

    # --- Core Logic ---
    userId = "me"

    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    
    # Validate sheet name
    validate_sheet_name(range_value, spreadsheet["data"])
    
    # For update operations, allow empty spreadsheets and new sheets (write operations can create new sheets)
    validate_sheet_exists_in_spreadsheet(range_value, spreadsheet["data"], allow_empty_spreadsheet=True, allow_new_sheets=True)

    # Process valueInputOption parameter
    processed_values = []
    for row in values:
        processed_row = []
        for cell_value in row:
            processed_cell = cell_value

            # Handle USER_ENTERED mode - simulate parsing user input
            if valueInputOption == "USER_ENTERED" and isinstance(cell_value, str):
                # Convert string numbers to actual numbers
                if re.match(r"^-?\d+(\.\d+)?$", cell_value):
                    if "." in cell_value:
                        processed_cell = float(cell_value)
                    else:
                        processed_cell = int(cell_value)
                # Convert date strings to date objects (simplified example)
                elif re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", cell_value):
                    processed_cell = f"DATE:{cell_value}"
                elif cell_value.startswith("="):
                    processed_cell = cell_value
            processed_row.append(processed_cell)
        processed_values.append(processed_row)

    # spreadsheet["data"][range] = processed_values
    updated_any = update_dynamic_data(range_value, spreadsheet["data"], processed_values)
    updated_rows = len(processed_values) if updated_any else 0
    updated_columns = len(processed_values[0]) if updated_any and processed_values and processed_values[0] else 0

    response = {
        "id": spreadsheet_id,
        "updatedRange": range_value,
        "updatedRows": updated_rows,
        "updatedColumns": updated_columns,
    }

    if includeValuesInResponse:
        response_values = [row[:] for row in processed_values] # Create a copy

        if responseValueRenderOption == "UNFORMATTED_VALUE":
            for i, row_val in enumerate(response_values):
                for j, cell_val in enumerate(row_val):
                    if isinstance(cell_val, str):
                        if cell_val.startswith("DATE:"):
                            response_values[i][j] = cell_val.replace("DATE:", "")
        elif responseValueRenderOption == "FORMULA":
            for i, row_val in enumerate(response_values):
                for j, cell_val in enumerate(row_val):
                    if isinstance(cell_val, str) and cell_val.startswith("="):
                         response_values[i][j] = cell_val

        if responseDateTimeRenderOption == "SERIAL_NUMBER":
            excel_epoch = datetime(1899, 12, 30)
            for i, row_val in enumerate(response_values):
                for j, cell_val in enumerate(row_val):
                    if isinstance(cell_val, str) and cell_val.startswith("DATE:"):
                        date_str = cell_val.replace("DATE:", "")
                        try:
                            date_parts = date_str.split("/")
                            month, day, year = (
                                int(date_parts[0]),
                                int(date_parts[1]),
                                int(date_parts[2]),
                            )
                            date_obj = datetime(year, month, day)
                            delta = date_obj - excel_epoch
                            response_values[i][j] = delta.days + (delta.seconds / 86400.0)
                        except (ValueError, IndexError):
                            # If parsing fails, keep the original value
                            pass

        response["values"] = response_values

    return response


@tool_spec(
    spec={
        'name': 'append_spreadsheet_values',
        'description': 'Appends values to a range in a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to append values to.'
                },
                'range': {
                    'type': 'string',
                    'description': """ The A1 notation of the range to append values to. Supports various formats:

                    Basic ranges (without sheet name - uses first sheet):
                    - Single cell: "A1"
                    - Cell range: "A1:B2"
                    - Full column: "A:B"
                    - Full row: "1:2"
                    - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                    With sheet names (recommended for multi-sheet spreadsheets):
                    - Simple sheet: "Sheet1!A1:B2"
                    - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                    - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                    - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                    - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                    
                    Note: If no sheet name specified, first sheet is automatically used.
                    Values are appended after the last row of data in the specified range.
                    """
                },
                'valueInputOption': {
                    'type': 'string',
                    'description': "How the input data should be interpreted. Allowed: 'RAW', 'USER_ENTERED'."
                },
                'values': {
                    'type': 'array',
                    'description': 'The values to append to the range (list of rows). Each inner list represents a row.',
                    'items': {
                        'type': 'array',
                        'description': 'A row of cell values. Each cell can contain a string, number, boolean, or null value.',
                        'items': {
                            'anyOf': [
                                {'type': 'STRING', 'description': 'Text value'},
                                {'type': 'NUMBER', 'description': 'Numeric value'},
                                {'type': 'BOOLEAN', 'description': 'Boolean value'}
                            ],
                            'description': 'Cell value. Can be a string (text), number, boolean, or null (empty cell).'
                        }
                    }
                },
                'insertDataOption': {
                    'type': 'string',
                    'description': "How the input data should be inserted. Allowed: 'OVERWRITE', 'INSERT_ROWS'. Defaults to None (behaves like 'INSERT_ROWS' for appending)."
                },
                'includeValuesInResponse': {
                    'type': 'boolean',
                    'description': 'Whether to include the appended values in the response. Defaults to False.'
                },
                'responseValueRenderOption': {
                    'type': 'string',
                    'description': "How values should be rendered in the response. Allowed: 'FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA'. Defaults to FORMATTED_VALUE."
                },
                'responseDateTimeRenderOption': {
                    'type': 'string',
                    'description': "How dates, times, and durations should be rendered in the response. Allowed: 'SERIAL_NUMBER', 'FORMATTED_STRING'. Defaults to 'SERIAL_NUMBER'."
                },
                'majorDimension': {
                    'type': 'string',
                    'description': 'The major dimension of the values. Allowed: \'ROWS\' (default), \'COLUMNS\'. Defaults to "ROWS".'
                }
            },
            'required': [
                'spreadsheet_id',
                'range',
                'values'
            ]
        }
    }
)
def append(
    spreadsheet_id: str,
    range: str,
    valueInputOption: str,
    values: List[List[Union[str, int, float, bool, None]]],
    insertDataOption: Optional[str] = None,
    includeValuesInResponse: Optional[bool] = False,
    responseValueRenderOption: Optional[str] = 'FORMATTED_VALUE',
    responseDateTimeRenderOption: Optional[str] = 'SERIAL_NUMBER',
    majorDimension: Optional[str] = "ROWS"
) -> Dict[str, Any]:
    """Appends values to a range in a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to append values to.
        range (str): The A1 notation of the range to append values to. Supports various formats:
            
            Basic ranges (without sheet name - uses first sheet in spreadsheet):
            - Single cell: "A1"
            - Cell range: "A1:B2"
            - Full column: "A:B"
            - Full row: "1:2"
            - Mixed range: "A2:Z" (from cell A2 to end of column Z)
            
            With sheet names (recommended for multi-sheet spreadsheets):
            - Simple sheet: "Sheet1!A1:B2"
            - Default sheets: "Sheet2!A:A", "sheet1!1:10"
            - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
            - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
            - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
            
            Note: If no sheet name is specified (e.g., "A1:B2"), the system automatically 
            uses the first sheet in the spreadsheet data. Values will be appended after the 
            last row of data in the specified range.
            
        valueInputOption (str): How the input data should be interpreted. Allowed: 'RAW', 'USER_ENTERED'.
        values (List[List[Union[str, int, float, bool, None]]]): The values to append to the range. Each inner list represents a row.
            Each cell value can be:
            - str: Text value for the cell
            - int: Integer numeric value for the cell
            - float: Decimal numeric value for the cell
            - bool: Boolean value for the cell (True/False)
            - None: Empty cell value
        insertDataOption (Optional[str]): How the input data should be inserted. Allowed: 'OVERWRITE', 'INSERT_ROWS'. Defaults to None (behaves like 'INSERT_ROWS' for appending).
        includeValuesInResponse (Optional[bool]): Whether to include the appended values in the response. Defaults to False.
        responseValueRenderOption (Optional[str]): How values should be rendered in the response. Allowed: 'FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA'. Defaults to FORMATTED_VALUE.
        responseDateTimeRenderOption (Optional[str]): How dates, times, and durations should be rendered in the response. Allowed: 'SERIAL_NUMBER', 'FORMATTED_STRING'. Defaults to 'SERIAL_NUMBER'.
        majorDimension (Optional[str]): The major dimension of the values. Allowed: 'ROWS' (default), 'COLUMNS'. Defaults to "ROWS".

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The spreadsheet ID
            - updatedRange (str): The range that was updated
            - updatedRows (int): Number of rows updated
            - updatedColumns (int): Number of columns updated
            - values (List[List[Union[str, int, float, bool, None]]]): The appended values if includeValuesInResponse is True

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `range` is not a string.
            - If `valueInputOption` is not a string.
            - If `includeValuesInResponse` is not a boolean.
            - If `insertDataOption` is not a string (when provided).
            - If `responseValueRenderOption` is not a string (when provided).
            - If `responseDateTimeRenderOption` is not a string (when provided).
            - If `majorDimension` is not a string (when provided).
        pydantic.ValidationError: If `values` is not a list of lists, or if enum parameters
            (`valueInputOption`, `insertDataOption`, `responseValueRenderOption`,
            `responseDateTimeRenderOption`, `majorDimension`) have invalid values.
        ValueError: In the following cases:
            - If `spreadsheet_id` is an empty string.
            - If `range` is an empty string.
            - If the data and range sizes do not match.
            - If the spreadsheet is not found.
            Note: For write operations like append, new sheets can be created if they don't exist.
    """
    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError("Argument 'spreadsheet_id' must be a string.")
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id cannot be empty")
    if not isinstance(range, str):
        raise TypeError("Argument 'range' must be a string.")
    if not range:
        raise ValueError("range cannot be empty")
    if not isinstance(valueInputOption, str): # This check is for type, Pydantic handles value
        raise TypeError("valueInputOption must be a string")
    if not isinstance(includeValuesInResponse, bool):
        raise TypeError("Argument 'includeValuesInResponse' must be a boolean.")
    if insertDataOption is not None and not isinstance(insertDataOption, str):
        raise TypeError("insertDataOption must be a string if provided")
    if responseValueRenderOption is not None and not isinstance(responseValueRenderOption, str):
        raise TypeError("responseValueRenderOption must be a string if provided")
    if responseDateTimeRenderOption is not None and not isinstance(responseDateTimeRenderOption, str):
        raise TypeError("responseDateTimeRenderOption must be a string if provided")
    if majorDimension is not None and not isinstance(majorDimension, str):
        raise TypeError("majorDimension must be a string")

    # 2. Pydantic validation for enum-like parameters and complex structures like 'values'
    try:
        validated_args = AppendSpecificArgsModel(
            valueInputOption=valueInputOption,
            values=values,
            insertDataOption=insertDataOption,
            responseValueRenderOption=responseValueRenderOption,
            responseDateTimeRenderOption=responseDateTimeRenderOption,
            majorDimension=majorDimension
        )
        values = validated_args.values
    except ValidationError as e:
        raise e

    # Validate range format
    try:
        validated_range = A1RangeInput(range=range)
        # Use the original range string to preserve case sensitivity
        range_value = range
    except ValueError as e:
        raise ValueError(f"Invalid range: {e}")

    # --- End of Input Validation ---

    # --- Core Logic ---
    userId = "me" 
    if "users" not in DB: DB["users"] = {}
    if userId not in DB["users"]: DB["users"][userId] = {"files": {}}
    if "files" not in DB["users"][userId]: DB["users"][userId]["files"] = {}

    if spreadsheet_id not in DB["users"][userId]["files"]:
         raise ValueError("Spreadsheet not found")

    spreadsheet = DB['users'][userId]['files'][spreadsheet_id]
    if 'data' not in spreadsheet: 
        spreadsheet['data'] = {}
    
    # Validate sheet name
    validate_sheet_name(range_value, spreadsheet['data'])
    
    # For append operations, allow empty spreadsheets and new sheets (write operations can create new sheets)
    validate_sheet_exists_in_spreadsheet(range_value, spreadsheet['data'], allow_empty_spreadsheet=True, allow_new_sheets=True)
    
    # Process values based on valueInputOption
    processed_values = []
    for row in values:
        processed_row = []
        for cell_value in row:
            processed_cell = cell_value

            # Handle USER_ENTERED mode - simulate parsing user input
            if valueInputOption == "USER_ENTERED" and isinstance(cell_value, str):
                # Convert string numbers to actual numbers
                if re.match(r"^-?\d+(\.\d+)?$", cell_value):
                    if "." in cell_value:
                        processed_cell = float(cell_value)
                    else:
                        processed_cell = int(cell_value)
                # Convert date strings to date objects (simplified example)
                elif re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", cell_value):
                    processed_cell = f"DATE:{cell_value}"
                elif cell_value.startswith("="):
                    processed_cell = cell_value
            processed_row.append(processed_cell)
        processed_values.append(processed_row)
    
    # Adjust range to match the processed values
    if "!" in range_value:
        sheet_name, range_part = range_value.split("!")
    else:
        range_part = range_value
    col_start, row_start, col_end, row_end = parse_a1_range(range_part, spreadsheet['data'])
    range_shape = (row_end - row_start + 1, col_end - col_start + 1)
    values_shape = (len(processed_values), len(processed_values[0])) if len(processed_values) > 0 and len(processed_values[0]) > 0 else (0, 0)
    if range_shape != values_shape:
        range_shape = values_shape
        col_start, row_start, col_end, row_end = col_start, row_start, col_start + range_shape[1] - 1, row_start + range_shape[0] - 1
        range_part = gsheet_range(col_start, row_start, col_end, row_end)
        range_value = f"{sheet_name}!{range_part}"

    # Find the best matching key in the spreadsheet data
    original_key = None
    original_sheet_format = None
    containing_range_key = None
    
    # First try an exact match
    if range_value in spreadsheet['data']:
        original_key = range_value
        original_sheet_format = extract_sheet_name(range_value, spreadsheet['data'])
    else:
        # Get normalized parts of the target range
        target_sheet, target_range = normalize_for_comparison(range_value)
        
        # First look for a key with the same sheet name and range
        for stored_key in spreadsheet['data'].keys():
            stored_sheet, stored_range = normalize_for_comparison(stored_key)
            
            if stored_sheet == target_sheet and stored_range == target_range:
                original_key = stored_key
                original_sheet_format = extract_sheet_name(stored_key, spreadsheet['data'])
                break
        
        # If no exact match, check if the target range is a subset of any existing range
        if not original_key:
            for stored_key in spreadsheet['data'].keys():
                if is_range_subset(range_value, stored_key):
                    containing_range_key = stored_key
                    original_sheet_format = extract_sheet_name(stored_key, spreadsheet['data'])
                    break
            
            # If still no match, look for any key with the same sheet name
            if not containing_range_key:
                for stored_key in spreadsheet['data'].keys():
                    stored_sheet, _ = normalize_for_comparison(stored_key)
                    
                    if stored_sheet == target_sheet:
                        original_sheet_format = extract_sheet_name(stored_key, spreadsheet['data'])
                        break
    
    # Get existing data using dynamic data function
    current_data = get_dynamic_data(range_value, spreadsheet['data'])
    
    # Transpose values if needed
    append_values = processed_values
    if validated_args.majorDimension == "COLUMNS":
        append_values = [list(row_val) for row_val in zip(*processed_values)] if processed_values else []
    
    # Parse the range to extract cell references
    range_part = extract_range_part(range_value)
    
    # Extract row and column from cell reference
    def extract_row_col(cell):
        # Handle column-only references like 'A' or 'BC'
        if re.match(r'^[A-Za-z]+$', cell):
            return 1, cell  # Default to row 1
        
        # Handle regular cell references like 'A1' or 'BC123'
        match = re.match(r'([A-Za-z]+)(\d+)', cell)
        if match:
            col_str, row_str = match.groups()
            return int(row_str), col_str
        
        return None, None
    
    # Parse the range part
    if ':' in range_part:
        start_cell, end_cell = range_part.split(':')
    else:
        start_cell = end_cell = range_part
    
    # Extract row and column information
    start_row, start_col_str = extract_row_col(start_cell)
    end_row, end_col_str = extract_row_col(end_cell)
    
    # For column-only ranges like 'A:B', set default row values
    if start_row is None:
        start_row = 1
    if end_row is None:
        end_row = 1000  # Arbitrary large number
    
    # Use the original sheet format if found, otherwise use the input format
    sheet_format = original_sheet_format if original_sheet_format else extract_sheet_name(range_value, spreadsheet['data'])
    
    # Calculate new range for appended data
    if current_data and any(current_data):
        # If we have existing data, calculate where to append
        new_start_row = start_row + len(current_data)
        new_end_row = new_start_row + len(append_values) - 1
        
        # For OVERWRITE, use the original range key if found
        if validated_args.insertDataOption == "OVERWRITE":
            if original_key:
                updated_range = original_key
            else:
                updated_range = range_value
            
            # Replace existing data with new values
            spreadsheet['data'][updated_range] = append_values
        else:  # INSERT_ROWS or default behavior
            # For column-only ranges, we need to adjust the range format
            if re.match(r'^[A-Za-z]+$', start_cell) and re.match(r'^[A-Za-z]+$', end_cell):
                # For column ranges like A:B, use format A1:B{new_end_row}
                if original_key:
                    # If we found an original key, use its sheet format
                    expanded_range = f"{original_key.split('!')[0]}!{start_col_str}1:{end_col_str}{new_end_row}"
                    appended_range = f"{original_key.split('!')[0]}!{start_col_str}{new_start_row}:{end_col_str}{new_end_row}"
                else:
                    # Otherwise use the input format
                    expanded_range = f"{sheet_format}!{start_col_str}1:{end_col_str}{new_end_row}"
                    appended_range = f"{sheet_format}!{start_col_str}{new_start_row}:{end_col_str}{new_end_row}"
            else:
                # For normal cell ranges
                if original_key:
                    # If we found an original key, use its sheet format
                    expanded_range = f"{original_key.split('!')[0]}!{start_col_str}{start_row}:{end_col_str}{new_end_row}"
                    appended_range = f"{original_key.split('!')[0]}!{start_col_str}{new_start_row}:{end_col_str}{new_end_row}"
                else:
                    # Otherwise use the input format
                    expanded_range = f"{sheet_format}!{start_col_str}{start_row}:{end_col_str}{new_end_row}"
                    appended_range = f"{sheet_format}!{start_col_str}{new_start_row}:{end_col_str}{new_end_row}"
            
            # Combine existing data with new data
            combined_data = current_data + append_values
            
            # Handle the case where the target range is a subset of an existing range
            if containing_range_key:
                # Get the full data from the containing range
                full_data = spreadsheet['data'][containing_range_key]
                
                # Parse the ranges to determine the insertion point
                containing_range_part = extract_range_part(containing_range_key)
                target_range_part = extract_range_part(range_value)
                
                # Check if the target range is a column-only range like A:B
                is_column_only_range = re.match(r'^[A-Za-z]+:[A-Za-z]+$', target_range_part) is not None
                
                if is_column_only_range:
                    # For column-only ranges, append to the end
                    container_start_row, _, _, _ = parse_a1_notation_extended(containing_range_part, None)
                    insertion_index = len(full_data)
                    target_start_row = container_start_row + insertion_index
                else:
                    # Get the row indices
                    target_start_row, _, _, _ = parse_a1_notation_extended(target_range_part, None)
                    
                    # Calculate the insertion point relative to the containing range
                    # The target_start_row is 1-based, so we subtract 1 to get 0-based index
                    container_start_row, _, _, _ = parse_a1_notation_extended(containing_range_part, None)
                    insertion_index = target_start_row - container_start_row
                
                # Insert the new data at the insertion point
                # First part: rows before insertion point
                new_data = full_data[:insertion_index]
                # Add the new rows
                new_data.extend(append_values)
                # Add the remaining rows
                new_data.extend(full_data[insertion_index:])
                
                # Update the containing range with the new data
                spreadsheet['data'][containing_range_key] = new_data
                
                # Calculate the new end row for the containing range
                _, _, container_end_row, container_end_col = parse_a1_notation_extended(containing_range_part, None)
                new_end_row = container_end_row + len(append_values)
                
                # Update the containing range key to reflect the new size
                sheet_part = extract_sheet_name(containing_range_key, spreadsheet['data'])
                start_cell = containing_range_part.split(':')[0]
                start_col_str = re.match(r'([A-Za-z]+)', start_cell).group(1)
                end_cell = containing_range_part.split(':')[1]
                end_col_str = re.match(r'([A-Za-z]+)', end_cell).group(1)
                
                # Create the new range key
                new_range_key = f"{sheet_part}!{start_col_str}{container_start_row}:{end_col_str}{new_end_row}"
                
                # If the range key changed, update it
                if new_range_key != containing_range_key:
                    spreadsheet['data'][new_range_key] = new_data
                    del spreadsheet['data'][containing_range_key]
                
                # Set the updated range to the appended portion for the response
                updated_range = f"{sheet_part}!{start_col_str}{target_start_row}:{end_col_str}{target_start_row + len(append_values) - 1}"
            else:
                # Check if the target range is a column-only range like A:B
                target_range_part = extract_range_part(range_value)
                is_column_only_range = re.match(r'^[A-Za-z]+:[A-Za-z]+$', target_range_part) is not None
                
                if is_column_only_range and current_data:
                    # For column-only ranges with existing data, append to the end
                    # The start_row will be the row after the last row in current_data
                    start_row = start_row + len(current_data)
                    end_row = start_row + len(append_values) - 1
                    
                    # Recalculate the expanded range and appended range
                    sheet_format_with_bang = f"{sheet_format}!" if '!' not in sheet_format else sheet_format
                    expanded_range = f"{sheet_format_with_bang}{start_col_str}1:{end_col_str}{end_row}"
                    appended_range = f"{sheet_format_with_bang}{start_col_str}{start_row}:{end_col_str}{end_row}"
                
                # First, remove the old data entry if it exists directly in the dictionary
                if original_key and original_key in spreadsheet['data']:
                    del spreadsheet['data'][original_key]
                elif range_value in spreadsheet['data']:
                    del spreadsheet['data'][range_value]
                
                # Store the combined data under the expanded range key
                spreadsheet['data'][expanded_range] = combined_data
                
                # Set the updated range to the appended portion for the response
                updated_range = appended_range
    else:
        # If no existing data, use the original key if found, otherwise use the input range
        if original_key:
            updated_range = original_key
        else:
            updated_range = range_value
        
        spreadsheet['data'][updated_range] = append_values

    # Prepare response
    response_values_to_return = None
    if includeValuesInResponse:
        if validated_args.majorDimension == "COLUMNS" and append_values:
            response_values_to_return = [list(col) for col in zip(*append_values)] if append_values else []
        else:
            response_values_to_return = append_values

    response = {
        "id": spreadsheet_id,
        "updatedRange": updated_range,
        "updatedRows": len(append_values) if append_values else 0,
        "updatedColumns": len(append_values[0]) if append_values and append_values[0] else 0
    }
    if includeValuesInResponse:
        response["values"] = response_values_to_return
    return response


@tool_spec(
    spec={
        'name': 'clear_spreadsheet_values',
        'description': 'Clears values from a specific range in a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to clear values from.'
                },
                'range': {
                    'type': 'string',
                    'description': """ The A1 notation of the range to clear values from. Supports various formats:

                    Basic ranges (without sheet name - uses first sheet):
                    - Single cell: "A1"
                    - Cell range: "A1:B2"
                    - Full column: "A:B"
                    - Full row: "1:2"
                    - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                    With sheet names (recommended for multi-sheet spreadsheets):
                    - Simple sheet: "Sheet1!A1:B2"
                    - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                    - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                    - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                    - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                    - Sheet-only: "Sheet1" (entire sheet)
                    
                    Note: If no sheet name specified, first sheet is automatically used.
                    """
                }
            },
            'required': [
                'spreadsheet_id',
                'range'
            ]
        }
    }
)
def clear(spreadsheet_id: str, range: str) -> Dict[str, Any]:
    """Clears values from a specific range in a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to clear values from.
        range (str): The A1 notation of the range to clear values from. Supports various formats:
            
            Basic ranges (without sheet name - uses first sheet in spreadsheet):
            - Single cell: "A1"
            - Cell range: "A1:B2"
            - Full column: "A:B"
            - Full row: "1:2"
            - Mixed range: "A2:Z" (from cell A2 to end of column Z)

            With sheet names (recommended for multi-sheet spreadsheets):
            - Simple sheet: "Sheet1!A1:B2"
            - Default sheets: "Sheet2!A:A", "sheet1!1:10"
            - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
            - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
            - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
            - Sheet-only reference: "Sheet1" (clears entire sheet)
            
            Note: If no sheet name is specified (e.g., "A1:B2"), the system automatically 
            uses the first sheet in the spreadsheet data.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The spreadsheet ID
            - clearedRange (str): The range that was cleared

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `range` is not a string.
        ValueError: In the following cases:
            - If `spreadsheet_id` is an empty string.
            - If `range` is an empty string.
            - If the `range` argument is invalid (e.g., fails A1RangeInput validation).
            - If the spreadsheet is not found.
            - If the range doesn't have an explicit sheet name and the default sheet is not "Sheet1".
            Note: For write operations like clear, new sheets can be created if they don't exist.
    """
    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError(f"spreadsheet_id must be a string, got {type(spreadsheet_id).__name__}")
    if not isinstance(range, str):
        raise TypeError(f"range must be a string, got {type(range).__name__}")
    
    if not spreadsheet_id or not spreadsheet_id.strip():
        raise ValueError("spreadsheet_id cannot be empty")
    if not range or not range.strip():
        raise ValueError("range cannot be empty")
    
    try:
        validated_range = A1RangeInput(range=range)
        range_value = validated_range.range
    except ValueError as e:
        raise ValueError(f"Invalid range: {e}")
    
    # --- End of Input Validation ---

    # --- Core Logic ---
    userId = "me"
    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    
    # Validate sheet name
    validate_sheet_name(range_value, spreadsheet["data"])
    
    # For clear operations, allow empty spreadsheets and new sheets (write operations can create new sheets)
    validate_sheet_exists_in_spreadsheet(range_value, spreadsheet["data"], allow_empty_spreadsheet=True, allow_new_sheets=True)
    
    # Overlap-aware clearing: blank cells in any stored range that overlaps the target
    target_sheet, target_range_part = split_sheet_and_range(range_value, spreadsheet)
    t_start_col, t_start_row, t_end_col, t_end_row = parse_a1_notation_extended(target_range_part)

    overlap_found = False
    # Iterate over a snapshot of keys since we'll mutate values
    for stored_key in list(spreadsheet["data"].keys()):
        stored_sheet, stored_range_part = split_sheet_and_range(stored_key, spreadsheet)
        if stored_sheet.lower() != target_sheet.lower():
            continue

        s_start_col, s_start_row, s_end_col, s_end_row = parse_a1_notation_extended(stored_range_part)

        # Compute intersection
        inter_start_col = max(s_start_col, t_start_col)
        inter_end_col = min(s_end_col, t_end_col)
        inter_start_row = max(s_start_row, t_start_row)
        inter_end_row = min(s_end_row, t_end_row)

        if inter_start_col <= inter_end_col and inter_start_row <= inter_end_row:
            overlap_found = True
            values = spreadsheet["data"].get(stored_key, [])
            # Ensure we operate on a copy to avoid side effects
            new_values = [row[:] if isinstance(row, list) else [row] for row in values] if isinstance(values, list) else [[values]]

            # Blank intersection region within stored range coordinates
            for r in builtins.range(inter_start_row, inter_end_row + 1):
                row_idx = r - s_start_row
                if 0 <= row_idx < len(new_values):
                    row = new_values[row_idx]
                    # Some rows might be shorter; guard column indices
                    if not isinstance(row, list):
                        # Normalize non-list row to single-cell list
                        row = [row]
                        new_values[row_idx] = row
                    for c in builtins.range(inter_start_col, inter_end_col + 1):
                        col_idx = c - s_start_col
                        if 0 <= col_idx:
                            # Pad row with empty strings if needed
                            while col_idx >= len(row):
                                row.append("")
                            row[col_idx] = ""

            spreadsheet["data"][stored_key] = new_values

    # If no overlap with existing stored ranges, create a minimal cleared placeholder
    if not overlap_found:
        spreadsheet["data"][range_value] = [[""]]
    return {"id": spreadsheet_id, "clearedRange": range_value}


@tool_spec(
    spec={
        'name': 'batch_get_spreadsheet_values',
        'description': 'Gets values from multiple ranges in a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to retrieve values from.'
                },
                'ranges': {
                    'type': 'array',
                    'description': """ List of A1 notations of ranges to retrieve values from. Each range supports various formats:

                    Basic ranges (without sheet name - uses first sheet):
                    - Single cell: "A1"
                    - Cell range: "A1:B2"
                    - Full column: "A:B"
                    - Full row: "1:2"
                    - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                    With sheet names (recommended for multi-sheet spreadsheets):
                    - Simple sheet: "Sheet1!A1:B2"
                    - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                    - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                    - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                    - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                    - Sheet-only: "Sheet1" (entire sheet)
                    
                    Note: If no sheet name specified, first sheet is automatically used.
                    """,
                    'items': {
                        'type': 'string'
                    }
                },
                'majorDimension': {
                    'type': 'string',
                    'description': 'The major dimension that results should use. Valid values: "ROWS", "COLUMNS". If not provided, it is inherited from the spreadsheet.'
                },
                'valueRenderOption': {
                    'type': 'string',
                    'description': 'How values should be rendered in the output. Defaults to "FORMATTED_VALUE". Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA".'
                },
                'dateTimeRenderOption': {
                    'type': 'string',
                    'description': 'How dates, times, and durations should be rendered. Defaults to "SERIAL_NUMBER". Valid values: "SERIAL_NUMBER", "FORMATTED_STRING".'
                }
            },
            'required': [
                'spreadsheet_id',
                'ranges'
            ]
        }
    }
)
def batchGet(
    spreadsheet_id: str,
    ranges: List[str],
    majorDimension: Optional[str] = None,
    valueRenderOption: Optional[str] = 'FORMATTED_VALUE',
    dateTimeRenderOption: Optional[str] = 'SERIAL_NUMBER',
) -> Dict[str, Any]:
    """Gets values from multiple ranges in a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to retrieve values from.
        ranges (List[str]): List of A1 notations of ranges to retrieve values from. Each range supports various formats:
            
            Basic ranges (without sheet name - uses first sheet in spreadsheet):
            - Single cell: "A1"
            - Cell range: "A1:B2"
            - Full column: "A:B"
            - Full row: "1:2"
            - Mixed range: "A2:Z" (from cell A2 to end of column Z)

            With sheet names (recommended for multi-sheet spreadsheets):
            - Simple sheet: "Sheet1!A1:B2"
            - Default sheets: "Sheet2!A:A", "sheet1!1:10"
            - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
            - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
            - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
            - Sheet-only reference: "Sheet1" (returns entire sheet)
            
            Note: If no sheet name is specified (e.g., "A1:B2"), the system automatically 
            uses the first sheet in the spreadsheet data.
            
        majorDimension (Optional[str]): The major dimension that results should use. Valid values: "ROWS", "COLUMNS". If not provided, it is inherited from the spreadsheet.
        valueRenderOption (Optional[str]): How values should be rendered in the output. Defaults to "FORMATTED_VALUE". Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA".
        dateTimeRenderOption (Optional[str]): How dates, times, and durations should be rendered. Defaults to "SERIAL_NUMBER". Valid values: "SERIAL_NUMBER", "FORMATTED_STRING".

    Returns:
        Dict[str, Any]: A dictionary containing:
            - spreadsheetId (str): The spreadsheet ID
            - valueRanges (List[dict]): List of value ranges, each containing:
                - range (str): The A1 notation of the range
                - majorDimension (str): The major dimension of the values
                - values (List[List[Any]]): The retrieved values

    Raises:
        ValueError: If the spreadsheet is not found, or for invalid parameter values.
            - If the specified sheet name in any range does not exist in the spreadsheet.
        TypeError: For invalid parameter types.
    """
    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError(f"spreadsheet_id must be a string, got {type(spreadsheet_id).__name__}")
    if not isinstance(ranges, list):
        raise TypeError(f"ranges must be a list, got {type(ranges).__name__}")
    if not all(isinstance(r, str) for r in ranges):
        raise TypeError("all items in ranges must be strings.")

    if majorDimension is not None:
        if not isinstance(majorDimension, str):
            raise TypeError(f"majorDimension must be a string if provided, got {type(majorDimension).__name__}")
        VALID_MAJOR_DIMENSIONS = ["ROWS", "COLUMNS"]
        if majorDimension not in VALID_MAJOR_DIMENSIONS:
            raise ValueError(f"Invalid majorDimension: '{majorDimension}'. Must be one of {VALID_MAJOR_DIMENSIONS}")

    if valueRenderOption is not None:
        if not isinstance(valueRenderOption, str):
            raise TypeError(f"valueRenderOption must be a string if provided, got {type(valueRenderOption).__name__}")
        VALID_VALUE_RENDER_OPTIONS = ["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]
        if valueRenderOption not in VALID_VALUE_RENDER_OPTIONS:
            raise ValueError(f"Invalid valueRenderOption: '{valueRenderOption}'. Must be one of {VALID_VALUE_RENDER_OPTIONS}")
    
    if dateTimeRenderOption is not None:
        if not isinstance(dateTimeRenderOption, str):
            raise TypeError(f"dateTimeRenderOption must be a string if provided, got {type(dateTimeRenderOption).__name__}")
        VALID_DATETIME_RENDER_OPTIONS = ["SERIAL_NUMBER", "FORMATTED_STRING"]
        if dateTimeRenderOption not in VALID_DATETIME_RENDER_OPTIONS:
            raise ValueError(f"Invalid dateTimeRenderOption: '{dateTimeRenderOption}'. Must be one of {VALID_DATETIME_RENDER_OPTIONS}")

    for r in ranges:
        try:
            A1RangeInput(range=r)
        except ValidationError as e:
            # The root cause is a ValueError from the A1 validator, wrapped by Pydantic.
            # We'll re-raise a clear, consistent ValueError for the test to catch.
            raise ValueError(f"Invalid A1 notation in ranges: '{r}'") from e

    userId = "me"
    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    value_ranges = []
    for range_ in ranges:
        # Validate that the sheet exists in the spreadsheet (input validation)
        # For read operations on empty spreadsheets, allow if the sheet structure exists
        validate_sheet_exists_in_spreadsheet(range_, spreadsheet["data"], allow_empty_spreadsheet=True, spreadsheet=spreadsheet)
        
        #  Use the same logic as get() function for dynamic data retrieval
        if range_ in spreadsheet["data"]:
            values = spreadsheet["data"][range_]
        else:
            # Get the data using the dynamic data function which handles sheet name normalization
            values = get_dynamic_data(range_, spreadsheet)
        
        # Apply the same processing as the get() function
        # Handle majorDimension parameter
        if majorDimension == "COLUMNS" and values:
            # Transpose the data when majorDimension is COLUMNS
            transposed_values = []
            if not all(isinstance(row, list) for row in values): # Ensure values is List[List[Any]]
                 # Handle cases where values might not be as expected, e.g. if data is malformed
                 # For simplicity, we'll just pass it through or raise an error if critical
                 pass # Or raise an appropriate error / log a warning
            else:
                max_row_length = 0
                if values and any(values): # ensure values is not empty and has at least one non-empty row
                    try:
                        max_row_length = max(len(row) for row in values if row) # Ensure row is not None
                    except ValueError: # max() arg is an empty sequence
                        pass # max_row_length remains 0

                for i in builtins.range(max_row_length):
                    new_row = []
                    for row in values:
                        new_row.append(row[i] if i < len(row) else "")
                    transposed_values.append(new_row)
                values = transposed_values

        # Process valueRenderOption parameter
        if valueRenderOption == "UNFORMATTED_VALUE":
            # Convert all values to strings without formatting
            processed_values = []
            for row in values:
                processed_row = []
                for cell in row:
                    if isinstance(cell, (int, float)):
                        processed_row.append(str(cell))
                    elif cell is None:
                        processed_row.append("")
                    else:
                        processed_row.append(str(cell))
                processed_values.append(processed_row)
            values = processed_values
        elif valueRenderOption == "FORMULA":
            # For now, just return values as-is since we don't store formulas
            # In a real implementation, you might want to handle formula display
            pass

        # Process dateTimeRenderOption parameter
        if dateTimeRenderOption == "SERIAL_NUMBER":
            # Convert date/time values to serial numbers
            # For now, just return values as-is since we don't have complex date handling
            # In a real implementation, you would convert dates to Excel serial numbers
            pass

        value_ranges.append(
            {"range": range_, "majorDimension": majorDimension, "values": values}
        )
    return {"id": spreadsheet_id, "valueRanges": value_ranges}


@tool_spec(
    spec={
        'name': 'batch_update_spreadsheet_values',
        'description': 'Updates values in multiple ranges of a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to update.'
                },
                'valueInputOption': {
                    'type': 'string',
                    'description': """ How the input data should be interpreted.
                    Valid values:
                    - "RAW": Values are inserted as-is, without any parsing.
                    - "USER_ENTERED": Values are parsed as if entered into Sheets by a user.
                      Formulas are stored as formulas, strings that look like dates or times
                      may be converted to date/time values, plain numbers are converted to numbers. """
                },
                'data': {
                    'type': 'array',
                    'description': 'List of update requests, each a dictionary containing:',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'range': {
                                'type': 'string',
                                'description': """The A1 notation of the range to update.
                                Supports various formats:
                                Basic ranges (uses default sheet):
                                - Single cell: "A1"
                                - Cell range: "A1:B2"
                                - Full column: "A:B"
                                - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                                With sheet names:
                                - Simple sheet: "Sheet1!A1:B2"
                                - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                                - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                                - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                                """
                            },
                            'values': {
                                'type': 'array',
                                'description': 'The values to update in the range (list of rows). Cell value - can be string, number, boolean, or null',
                                'items': {
                                    'type': 'array',
                                    'items': {
                                        'anyOf': [
                                            {'type': 'STRING', 'description': 'Text value'},
                                            {'type': 'NUMBER', 'description': 'Numeric value'},
                                            {'type': 'BOOLEAN', 'description': 'Boolean value'}
                                        ],
                                        'description': 'Cell value. Can be a string (text), number, boolean, or null (empty cell).'
                                    }
                                }
                            }
                        },
                        'required': [
                            'range',
                            'values'
                        ]
                    }
                },
                'includeValuesInResponse': {
                    'type': 'boolean',
                    'description': 'Whether to include the updated values in the response. Defaults to False.'
                },
                'responseValueRenderOption': {
                    'type': 'string',
                    'description': """ How values should be rendered in the response. Defaults to "FORMATTED_VALUE".
                    Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". Only "UNFORMATTED_VALUE" is explicitly handled; "FORMULA" is not currently implemented. """
                },
                'responseDateTimeRenderOption': {
                    'type': 'string',
                    'description': """ How dates, times, and durations should be rendered in the response. Defaults to "SERIAL_NUMBER".
                    Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". Only "SERIAL_NUMBER" is explicitly handled; "FORMATTED_STRING" is not currently implemented. """
                }
            },
            'required': [
                'spreadsheet_id',
                'valueInputOption',
                'data'
            ]
        }
    }
)
def batchUpdate(
    spreadsheet_id: str,
    valueInputOption: str,
    data: List[Dict[str, Union[str, List[List[Union[str, int, float, bool]]]]]],
    includeValuesInResponse: bool = False,
    responseValueRenderOption: str = "FORMATTED_VALUE",
    responseDateTimeRenderOption: str = "SERIAL_NUMBER",
) -> Dict[str, Any]:
    """Updates values in multiple ranges of a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to update.
        valueInputOption (str): How the input data should be interpreted.
            Valid values:
            - "RAW": Values are inserted as-is, without any parsing.
            - "USER_ENTERED": Values are parsed as if entered into Sheets by a user.
              Formulas are stored as formulas, strings that look like dates or times
              may be converted to date/time values, plain numbers are converted to numbers.
        data (List[Dict[str, Union[str, List[List[Union[str, int, float, bool]]]]]]): List of update requests, each a dictionary containing:
            - range (str): The A1 notation of the range to update.
                Supports various formats:
                
                Basic ranges (without sheet name - uses first sheet in spreadsheet):
                - Single cell: "A1"
                - Cell range: "A1:B2"
                - Full column: "A:B"
                - Full row: "1:2"
                - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                With sheet names (recommended for multi-sheet spreadsheets):
                - Simple sheet: "Sheet1!A1:B2"
                - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                
                Note: If no sheet name is specified, uses first sheet in spreadsheet data.

            - values (List[List[Union[str, int, float, bool]]]): The values to update in the range (list of rows). Cell value - can be string, number, boolean, or null
        includeValuesInResponse (bool): Whether to include the updated values in the response. Defaults to False.
        responseValueRenderOption (str): How values should be rendered in the response. Defaults to "FORMATTED_VALUE".
            Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". Only "UNFORMATTED_VALUE" is explicitly handled; "FORMULA" is not currently implemented.
        responseDateTimeRenderOption (str): How dates, times, and durations should be rendered in the response. Defaults to "SERIAL_NUMBER".
            Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". Only "SERIAL_NUMBER" is explicitly handled; "FORMATTED_STRING" is not currently implemented.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The spreadsheet ID
            - updatedData (List[dict]): List of updated ranges, each containing:
                - range (str): The A1 notation of the range. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"
                - values (List[List[Union[str, int, float, bool]]]): The updated values. Cell value - can be string, number, boolean, or null

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `valueInputOption` is not a string.
            - If `data` is not a list.
            - If any item in `data` is not a dictionary.
            - If `includeValuesInResponse` is not a boolean.
            - If `responseValueRenderOption` is not a string.
            - If `responseDateTimeRenderOption` is not a string.
        ValueError: In the following cases:
            - If `spreadsheet_id` is an empty string.
            - If `valueInputOption` is not one of the allowed values ("RAW", "USER_ENTERED").
            - If `responseValueRenderOption` is not one of the allowed values ("FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA").
            - If `responseDateTimeRenderOption` is not one of the allowed values ("SERIAL_NUMBER", "FORMATTED_STRING").
            - If the spreadsheet is not found (propagated from core logic).
            Note: For write operations like batchUpdate, new sheets can be created if they don't exist.
        pydantic.ValidationError: If `data` is not a list of dictionaries conforming
            to the ValueRangeModel structure.
    """
    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError("Parameter 'spreadsheet_id' must be a string.")
    if not spreadsheet_id: # Additional check for empty string if it's an identifier
        raise ValueError("Parameter 'spreadsheet_id' cannot be empty.")

    if not isinstance(valueInputOption, str):
        raise TypeError("Parameter 'valueInputOption' must be a string.")
    allowed_value_input_options = ["RAW", "USER_ENTERED"]
    if valueInputOption not in allowed_value_input_options:
        raise ValueError(
            f"Invalid 'valueInputOption': {valueInputOption}. "
            f"Allowed options: {allowed_value_input_options}"
        )

    if not isinstance(data, list):
        raise TypeError("Parameter 'data' must be a list.")
    
    validated_data_models: List[ValueRangeModel] = []
    try:
        for i, item_dict in enumerate(data):
            if not isinstance(item_dict, dict):
                raise TypeError(f"Each item in 'data' list (at index {i}) must be a dictionary, got {type(item_dict).__name__}.")
            validated_data_models.append(ValueRangeModel(**item_dict))
    except ValidationError as e:
        # Re-raise the original Pydantic ValidationError.
        # This ensures the error message and structure are standard Pydantic V2.
        raise e # e.g., pydantic.ValidationError: 1 validation error for ValueRangeModel\nrange\n  Field required (type=missing)

    if not isinstance(includeValuesInResponse, bool):
        raise TypeError("Parameter 'includeValuesInResponse' must be a boolean.")

    if not isinstance(responseValueRenderOption, str):
        raise TypeError("Parameter 'responseValueRenderOption' must be a string.")
    allowed_response_value_options = ["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]
    if responseValueRenderOption not in allowed_response_value_options:
        raise ValueError(
            f"Invalid 'responseValueRenderOption': {responseValueRenderOption}. "
            f"Allowed options: {allowed_response_value_options}"
        )

    if not isinstance(responseDateTimeRenderOption, str):
        raise TypeError("Parameter 'responseDateTimeRenderOption' must be a string.")
    allowed_response_datetime_options = ["SERIAL_NUMBER", "FORMATTED_STRING"]
    if responseDateTimeRenderOption not in allowed_response_datetime_options:
        raise ValueError(
            f"Invalid 'responseDateTimeRenderOption': {responseDateTimeRenderOption}. "
            f"Allowed options: {allowed_response_datetime_options}"
        )
    # --- End of Input Validation ---

    # --- Original Core Logic (adapted for validated_data_models) ---
    userId = "me" # This is from the original function logic
    
    # This check depends on an external 'DB' variable.
    # Ensure 'DB' is defined and populated in the execution environment.
    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    updated_data = []

    for value_range_model in validated_data_models: # Use the validated Pydantic models
        range_value = value_range_model.range
        values = value_range_model.values # This is List[List[Any]]

        # For batch update operations, allow empty spreadsheets and new sheets (write operations can create new sheets)
        validate_sheet_exists_in_spreadsheet(range_value, spreadsheet["data"], allow_empty_spreadsheet=True, allow_new_sheets=True)

        # Process valueInputOption parameter for each range
        processed_values = []
        for row in values:
            processed_row = []
            for cell_value in row:
                processed_cell = cell_value

                # Handle USER_ENTERED mode - simulate parsing user input
                if valueInputOption == "USER_ENTERED" and isinstance(cell_value, str):
                    # Convert date strings (simplified example)
                    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", cell_value):
                        # In a real implementation, this would create an actual date object
                        # Here we just mark it as a date string
                        processed_cell = f"DATE:{cell_value}"
                    # Convert formulas (anything starting with =)
                    # For formulas, preserve them exactly as entered
                    elif cell_value.startswith("="):
                        processed_cell = cell_value
                processed_row.append(processed_cell)
            processed_values.append(processed_row)

        # Update the spreadsheet data with processed values using update_dynamic_data
        update_dynamic_data(range_value, spreadsheet["data"], processed_values)

        # Prepare response values if needed
        if includeValuesInResponse:
            response_values = processed_values.copy()
            # Apply responseValueRenderOption if specified
            if responseValueRenderOption == "UNFORMATTED_VALUE":
                for i, row in enumerate(response_values):
                    for j, cell_value in enumerate(row):
                        # Strip formatting information
                        if isinstance(cell_value, str):
                            if cell_value.startswith("DATE:"):
                                # Convert date string to number
                                response_values[i][j] = cell_value.replace("DATE:", "")
                            elif cell_value.startswith("FORMULA:"):
                                # Show the result of the formula instead
                                formula = cell_value.replace("FORMULA:", "")
                                # Simplified simulation of formula result
                                if "SUM" in formula:
                                    response_values[i][j] = 0  # Placeholder for sum result
                                else:
                                    response_values[i][j] = "RESULT"
            
            # Apply responseDateTimeRenderOption if specified
            if responseDateTimeRenderOption == "SERIAL_NUMBER":
                # Simulate converting dates to serial numbers
                excel_epoch = datetime(1899, 12, 30)
                for i, row in enumerate(response_values):
                    for j, cell_value in enumerate(row):
                        if isinstance(cell_value, str) and cell_value.startswith(
                            "DATE:"
                        ):
                            date_str = cell_value.replace("DATE:", "")
                            try:
                                # Parse the date string
                                date_parts = date_str.split("/")
                                month, day, year = (
                                    int(date_parts[0]),
                                    int(date_parts[1]),
                                    int(date_parts[2]),
                                )
                                date_obj = datetime(year, month, day)
                                # Calculate the Excel serial number
                                delta = date_obj - excel_epoch
                                response_values[i][j] = delta.days + (
                                    delta.seconds / 86400
                                )
                            except (ValueError, IndexError):
                                # If parsing fails, keep the original value
                                pass
            updated_data.append({"range": range_value, "values": response_values})
        else:
            updated_data.append({"range": range_value, "values": []})

    response = {"id": spreadsheet_id, "updatedData": updated_data}
    return response


@tool_spec(
    spec={
        'name': 'batch_clear_spreadsheet_values',
        'description': 'Clears values from multiple ranges in a spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to clear values from.'
                },
                'ranges': {
                    'type': 'array',
                    'description': """ List of A1 notations of ranges to clear. Each range supports various formats:

                    Basic ranges (without sheet name - uses first sheet):
                    - Single cell: "A1"
                    - Cell range: "A1:B2"
                    - Full column: "A:B"
                    - Full row: "1:2"
                    - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                    With sheet names (recommended for multi-sheet spreadsheets):
                    - Simple sheet: "Sheet1!A1:B2"
                    - Default sheets: "Sheet2!A:A", "sheet1!1:10"
                    - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                    - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                    - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                    - Sheet-only: "Sheet1" (entire sheet)
                    
                    Note: If no sheet name specified, first sheet is automatically used.
                    """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'spreadsheet_id',
                'ranges'
            ]
        }
    }
)
def batchClear(spreadsheet_id: str, ranges: List[str]) -> Dict[str, Any]:
    """Clears values from multiple ranges in a spreadsheet.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to clear values from.
        ranges (List[str]): List of A1 notations of ranges to clear. Each range supports various formats:
            
            Basic ranges (without sheet name - uses first sheet in spreadsheet):
            - Single cell: "A1"
            - Cell range: "A1:B2"
            - Full column: "A:B"
            - Full row: "1:2"
            - Mixed range: "A2:Z" (from cell A2 to end of column Z)

            With sheet names (recommended for multi-sheet spreadsheets):
            - Simple sheet: "Sheet1!A1:B2"
            - Default sheets: "Sheet2!A:A", "sheet1!1:10"
            - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
            - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
            - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
            - Sheet-only reference: "Sheet1" (clears entire sheet)
            
            Note: If no sheet name is specified (e.g., "A1:B2"), the system automatically 
            uses the first sheet in the spreadsheet data.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The spreadsheet ID
            - clearedRanges (List[dict]): List of cleared ranges, each containing:
                - clearedRange (str): The A1 notation of the range that was cleared

    Raises:
        ValueError: If the spreadsheet is not found
            Note: For write operations like batchClear, new sheets can be created if they don't exist.
    """
    userId = "me"
    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    cleared_ranges = []
    for range_ in ranges:
        # For batch clear operations, allow empty spreadsheets and new sheets (write operations can create new sheets)
        validate_sheet_exists_in_spreadsheet(range_, spreadsheet["data"], allow_empty_spreadsheet=True, allow_new_sheets=True)
        
        if range_ in spreadsheet["data"]:
            # Set to empty instead of deleting to maintain sheet structure
            spreadsheet["data"][range_] = [[""]]
        else:
            # If range doesn't exist, create it as empty
            spreadsheet["data"][range_] = [[""]]
        cleared_ranges.append({"clearedRange": range_})
    return {"id": spreadsheet_id, "clearedRanges": cleared_ranges}


@tool_spec(
    spec={
        'name': 'batch_get_spreadsheet_values_by_data_filter',
        'description': """ Retrieves values from a spreadsheet data store using data filters.
        
        Uses an API-aligned return structure. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to retrieve values from.'
                },
                'dataFilters': {
                    'type': 'array',
                    'description': """ List of data filter objects.
                    Each dictionary represents a DataFilter and can specify one of:
                    - {"a1Range": "Sheet1!A1:B2"} (primarily acted upon by this implementation). The a1Range should be an A1 notation. Which is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"
                    - {"gridRange": {"sheetId": 0, ...}}
                    - {"developerMetadataLookup": {"metadataKey": "key"}} (conceptual)
                    If None or empty, an empty "valueRanges" list is returned. """,
                    'items': {
                        'description': 'Data filter object that can specify one of: a1Range, gridRange, or developerMetadataLookup',
                        'anyOf': [
                                {
                                    'type': 'OBJECT',
                                    'description': 'Data filter with A1 notation range',
                                    'properties': {
                                        'a1Range': {
                                            'type': 'string',
                                            'description': 'A1 notation range (e.g., "Sheet1!A1:B2")'
                                        }
                                    },
                                    'required': ['a1Range']
                                },
                                {
                                    'type': 'OBJECT',
                                    'description': 'Data filter with grid range',
                                    'properties': {
                                        'gridRange': {
                                            'type': 'object',
                                            'description': 'Grid range object with sheetId and other properties',
                                            'properties': {
                                                'sheetId': {
                                                    'type': 'integer',
                                                    'description': 'The sheet ID this range is on'
                                                },
                                                'startRowIndex': {
                                                    'type': 'integer',
                                                    'description': 'The start row index (inclusive)'
                                                },
                                                'endRowIndex': {
                                                    'type': 'integer',
                                                    'description': 'The end row index (exclusive)'
                                                },
                                                'startColumnIndex': {
                                                    'type': 'integer',
                                                    'description': 'The start column index (inclusive)'
                                                },
                                                'endColumnIndex': {
                                                    'type': 'integer',
                                                    'description': 'The end column index (exclusive)'
                                                }
                                            },
                                            'required': ['sheetId']
                                        }
                                    },
                                    'required': ['gridRange']
                                },
                                {
                                    'type': 'OBJECT',
                                    'description': 'Data filter with developer metadata lookup',
                                    'properties': {
                                        'developerMetadataLookup': {
                                            'type': 'object',
                                            'description': 'Developer metadata lookup object',
                                            'properties': {
                                                'metadataKey': {
                                                    'type': 'string',
                                                    'description': 'The metadata key to look up'
                                                }
                                            },
                                            'required': ['metadataKey']
                                        }
                                    },
                                    'required': ['developerMetadataLookup']
                                }
                            ]
                        }
                },
                'majorDimension': {
                    'type': 'STRING',
                    'description': 'Major dimension for results ("ROWS" or "COLUMNS").'
                },
                'valueRenderOption': {
                    'type': 'STRING',
                    'description': 'How values should be represented in the output. Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". Defaults to "FORMATTED_VALUE".'
                },
                'dateTimeRenderOption': {
                    'type': 'STRING',
                    'description': 'How dates, times, and durations should be represented in the output. This is ignored if valueRenderOption is "FORMATTED_VALUE". Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". Defaults to "SERIAL_NUMBER".'
                },
                'userId': {
                    'type': 'STRING',
                    'description': 'The user ID to use for accessing the spreadsheet. Defaults to "me" if not provided.'
                }
            },
            'required': [
                'spreadsheet_id'
            ]
        }
    }
)
def batchGetByDataFilter(
    spreadsheet_id: str,
    dataFilters: Optional[List[Dict[str, Union[str, int, float, bool, None]]]] = None,
    majorDimension: Optional[str] = None,
    valueRenderOption: Optional[str] = "FORMATTED_VALUE",
    dateTimeRenderOption: Optional[str] = "SERIAL_NUMBER",
    userId: Optional[str] = "me"
) -> Dict[str, Union[str, List[Dict[str, Union[str, List[List[Union[str, int, float, bool, None]]]]]]]]:
    """
    Retrieves values from a spreadsheet data store using data filters.
    Uses an API-aligned return structure.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to retrieve values from.
        dataFilters (Optional[List[Dict[str, Union[str, int, float, bool, None]]]]): List of data filter objects.
            Each dictionary represents a DataFilter and can specify one of:
            - {"a1Range": "Sheet1!A1:B2"} (primarily acted upon by this implementation). The a1Range should be an A1 notation. Which is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"
            - {"gridRange": {"sheetId": 0, ...}}
            - {"developerMetadataLookup": {"metadataKey": "key"}} (conceptual)
            If None or empty, an empty "valueRanges" list is returned.
        majorDimension (Optional[str]): Major dimension for results ("ROWS" or "COLUMNS").
        valueRenderOption (Optional[str]): How values should be represented in the output. Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". Defaults to "FORMATTED_VALUE".
        dateTimeRenderOption (Optional[str]): How dates, times, and durations should be represented in the output. This is ignored if valueRenderOption is "FORMATTED_VALUE". Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". Defaults to "SERIAL_NUMBER".
        userId (Optional[str]): The user ID to use for accessing the spreadsheet. Defaults to "me" if not provided.

    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, List[List[Union[str, int, float, bool, None]]]]]]]]: API-aligned dictionary:
            - spreadsheetId (str): The spreadsheet ID.
            - valueRanges (List[Dict[str, Union[str, List[List[Union[str, int, float, bool, None]]]]]]): List of value ranges, each containing:
                - range (str): The A1 notation of the range. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"
                - majorDimension (str): The major dimension of the values (None if not specified)
                - values (List[List[Union[str, int, float, bool, None]]]): The retrieved values

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `dataFilters` is not a list.
            - If any item in `dataFilters` is not a dictionary.
            - If `userId` is not a string (when provided).
            - If `majorDimension` is not a string (when provided).
            - If `valueRenderOption` is not a string (when provided).
            - If `dateTimeRenderOption` is not a string (when provided).
        ValidationError: If an item in `dataFilters` is a dictionary but does not conform
            to the expected DataFilterModel structure (e.g., wrong type for 'a1Range').
        ValueError: In the following cases:
            - If `majorDimension` is provided with an unsupported string value.
            - If user context or `spreadsheet_id` is not found in the DB (propagated from original logic).
        InvalidFunctionParameterError: In the following cases:
            - If `valueRenderOption` is provided with an unsupported string value.
            - If `dateTimeRenderOption` is provided with an unsupported string value.
    """
    # Define allowed values for validation
    ALLOWED_MAJOR_DIMENSIONS = {"ROWS", "COLUMNS"}
    ALLOWED_VALUE_RENDER_OPTIONS = {"FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"}
    ALLOWED_DATETIME_RENDER_OPTIONS = {"SERIAL_NUMBER", "FORMATTED_STRING"}

    # --- Input Validation ---
    if not isinstance(spreadsheet_id, str):
        raise TypeError("spreadsheet_id must be a string.")

    if dataFilters is None:
        dataFilters = []
    if not isinstance(dataFilters, list):
        raise TypeError(f"dataFilters must be a list, got {type(dataFilters).__name__}")

    if userId is not None and not isinstance(userId, str):
        raise TypeError(f"userId must be a string if provided, got {type(userId).__name__}")

    try:
        user_context_db = DB['users'][userId if userId is not None else "me"]
        user_files = user_context_db['files']
    except KeyError:
        effective_userId = userId if userId is not None else "me"
        raise ValueError(
            f"User context for '{effective_userId}' or 'files' key not found in the DB. "
            f"Ensure DB is set up correctly."
        )

    if spreadsheet_id not in user_files:
        effective_userId = userId if userId is not None else "me"
        raise ValueError(
            f"Spreadsheet with ID '{spreadsheet_id}' not found for user " # Corrected this message to match test
            f"'{effective_userId}' in the DB."
        )

    if dataFilters:
        for i, filter_item_dict in enumerate(dataFilters):
            if not isinstance(filter_item_dict, dict):
                raise TypeError(f"DataFilter item at index {i} must be a dictionary, got {type(filter_item_dict).__name__}")
            try:
                _ = DataFilterModel(**filter_item_dict)
            except ValidationError as e: # Uses the alias correctly
                raise ValidationError(f"Invalid data filter at index {i}: {str(e)}")

    if majorDimension is not None:
        if not isinstance(majorDimension, str):
            raise TypeError("majorDimension must be a string if provided.")
        if majorDimension not in ALLOWED_MAJOR_DIMENSIONS:
            # MODIFIED: Ensure error message uses list ['ROWS', 'COLUMNS'] format
            # This matches the specific test expectation for error string comparison.
            raise ValueError(f"majorDimension must be one of {['ROWS', 'COLUMNS']} if provided. Got: '{majorDimension}'.")

    if valueRenderOption is not None:
        if not isinstance(valueRenderOption, str):
            raise TypeError(f"valueRenderOption must be a string if provided, got {type(valueRenderOption).__name__}")
        if valueRenderOption not in ALLOWED_VALUE_RENDER_OPTIONS:
            raise InvalidFunctionParameterError(
                # Using list() for consistency, though the test might expect a specific order.
                # The tests for this specific error are not failing, but good to be aware.
                f"valueRenderOption must be one of {list(ALLOWED_VALUE_RENDER_OPTIONS)}. Got: '{valueRenderOption}'"
            )

    if dateTimeRenderOption is not None:
        if not isinstance(dateTimeRenderOption, str):
            raise TypeError(f"dateTimeRenderOption must be a string if provided, got {type(dateTimeRenderOption).__name__}")
        if dateTimeRenderOption not in ALLOWED_DATETIME_RENDER_OPTIONS:
            raise InvalidFunctionParameterError(
                f"dateTimeRenderOption must be one of {list(ALLOWED_DATETIME_RENDER_OPTIONS)}. Got: '{dateTimeRenderOption}'"
            )

    # --- Core Logic --- (remains unchanged from your provided file)
    spreadsheet = user_files[spreadsheet_id]
    value_ranges = []

    for filter_item in dataFilters:
        if "a1Range" in filter_item:
            range_str = filter_item["a1Range"]
            if "data" in spreadsheet and range_str in spreadsheet["data"]:
                values = spreadsheet["data"][range_str]
                if majorDimension == "COLUMNS":
                    # Ensure values is a list of lists before transposing
                    if values and all(isinstance(row, list) for row in values):
                        values = list(map(list, zip(*values)))
                    else: # Handle case where values might not be suitable for transpose
                        values = [] 
                value_ranges.append({
                    "range": range_str,
                    "majorDimension": majorDimension,
                    "values": values
                })

    return {
        "spreadsheetId": spreadsheet_id,
        "valueRanges": value_ranges
    }


@tool_spec(
    spec={
        'name': 'batch_update_spreadsheet_values_by_data_filter',
        'description': 'Updates values in a spreadsheet using data filters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to update.'
                },
                'valueInputOption': {
                    'type': 'string',
                    'description': 'Determines how input data should be interpreted. Valid values: "RAW" (values are stored as-is), "USER_ENTERED" (values are parsed as if entered by a user). "INPUT_VALUE_OPTION_UNSPECIFIED" is not allowed and must not be used.'
                },
                'data': {
                    'type': 'array',
                    'description': 'List of update requests, each containing the param dataFilter or range, not both:',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'values': {
                                'type': 'array',
                                'description': 'The values to update in the range. This should be added regardless of the format of the request.',
                                'items': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                }
                            },
                            'dataFilter': {
                                'type': 'object',
                                'description': 'The data filter with:',
                                'properties': {
                                    'a1Range': {
                                        'type': 'string',
                                        'description': 'The A1 notation of the range. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"'
                                    }
                                },
                                'required': [
                                    'a1Range'
                                ]
                            },
                            'range': {
                                'type': 'string',
                                'description': """The A1 notation of the range. Supports various formats:
                                    Basic ranges (uses default sheet):
                                    - Single cell: "A1"
                                    - Cell range: "A1:B2"
                                    - Full column: "A:B"
                                    - Mixed range: "A2:Z" (from cell A2 to end of column Z)

                                    With sheet names:
                                    - Simple sheet: "Sheet1!A1:B2"
                                    - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                                    - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                                    - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
                                """
                            }
                        },
                        'required': [
                            'values'
                        ]
                    }
                },
                'includeValuesInResponse': {
                    'type': 'boolean',
                    'description': 'Whether to include the updated values in the response. Defaults to False.'
                },
                'responseValueRenderOption': {
                    'type': 'string',
                    'description': 'Determines how values in the response should be rendered. Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". Defaults to "FORMATTED_VALUE".'
                },
                'responseDateTimeRenderOption': {
                    'type': 'string',
                    'description': 'Determines how dates, times, and durations in the response should be rendered. This is ignored if responseValueRenderOption is "FORMATTED_VALUE". Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". Defaults to "SERIAL_NUMBER".'
                }
            },
            'required': [
                'spreadsheet_id',
                'valueInputOption',
                'data'
            ]
        }
    }
)
def batchUpdateByDataFilter(
    spreadsheet_id: str,
    valueInputOption: str,
    data: List[Dict[str, Any]],
    includeValuesInResponse: bool = False,
    responseValueRenderOption: str = "FORMATTED_VALUE",
    responseDateTimeRenderOption: str = "SERIAL_NUMBER",
) -> Dict[str, Any]:
    """
    Updates values in a spreadsheet using data filters.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to update.
        valueInputOption (str): Determines how input data should be interpreted. Valid values: "RAW" (values are stored as-is), "USER_ENTERED" (values are parsed as if entered by a user). "INPUT_VALUE_OPTION_UNSPECIFIED" is not allowed and must not be used.
        data (List[Dict[str, Any]]): List of update requests, each containing the param dataFilter or range, not both:
            - values (List[List[Any]]): The values to update in the range. This should be added regardless of the format of the request.
            - dataFilter (Optional[dict]): The data filter with:
                - a1Range (str): The A1 notation of the range. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"
            - range (Optional[str]): The A1 notation of the range.
                Supports various formats:
                Basic ranges (uses default sheet):
                - Single cell: "A1"
                - Cell range: "A1:B2"
                - Full column: "A:B"
                - Mixed range: "A2:Z" (from cell A2 to end of column Z)
                With sheet names:
                - Simple sheet: "Sheet1!A1:B2"
                - Sheet with spaces: "'My Sheet'!A1:B2" (use single quotes)
                - Sheet with apostrophes: "'John''s Sheet'!A1" (escape apostrophes with double apostrophes)
                - Sheet with special characters: "'Data-Sheet (2024)'!A1:D10"
        includeValuesInResponse (bool): Whether to include the updated values in the response. Defaults to False.
        responseValueRenderOption (str): Determines how values in the response should be rendered. Valid values: "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA". Defaults to "FORMATTED_VALUE".
        responseDateTimeRenderOption (str): Determines how dates, times, and durations in the response should be rendered. This is ignored if responseValueRenderOption is "FORMATTED_VALUE". Valid values: "SERIAL_NUMBER", "FORMATTED_STRING". Defaults to "SERIAL_NUMBER".

    Returns:
        Dict[str, Any]: A dictionary containing:
            - spreadsheetId (str): The spreadsheet ID
            - updatedData (List[dict]): List of updated ranges, each containing:
                - range (str): The A1 notation of the range. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"
                - values (List[List[Any]]): The updated values

    Raises:
        TypeError: In the following cases:
            - If `spreadsheet_id` is not a string.
            - If `valueInputOption` is not a string.
            - If `data` is not a list.
            - If any item in `data` is not a dictionary.
            - If `includeValuesInResponse` is not a boolean.
            - If `responseValueRenderOption` is not a string.
            - If `responseDateTimeRenderOption` is not a string.
            - If any 'dataFilter' is not a dictionary.
            - If 'values' is not a list of lists, or any item in 'values' is not a list.
        ValueError: In the following cases:
            - If `spreadsheet_id` is an empty string.
            - If `valueInputOption` is not one of the allowed values ("RAW", "USER_ENTERED").
            - If `responseValueRenderOption` is not one of the allowed values ("FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA").
            - If `responseDateTimeRenderOption` is not one of the allowed values ("SERIAL_NUMBER", "FORMATTED_STRING").
            - If any item in `data` does not contain either 'dataFilter' (with 'a1Range') or 'range'.
            - If the spreadsheet is not found (propagated from core logic).
        ValidationError: If the structure of an item in `data` is invalid in a way not covered above.
    """
    # --- Input Validation ---
    VALID_VALUE_INPUT_OPTIONS = {"RAW", "USER_ENTERED"}
    VALID_RESPONSE_VALUE_RENDER_OPTIONS = {"FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"}
    VALID_RESPONSE_DATETIME_RENDER_OPTIONS = {"SERIAL_NUMBER", "FORMATTED_STRING"}

    if not isinstance(spreadsheet_id, str):
        raise TypeError("spreadsheet_id must be a string.")
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id cannot be empty.")

    if not isinstance(valueInputOption, str):
        raise TypeError("valueInputOption must be a string.")
    if valueInputOption not in VALID_VALUE_INPUT_OPTIONS:
        raise ValueError(f"valueInputOption must be one of {list(VALID_VALUE_INPUT_OPTIONS)}. Got '{valueInputOption}'.")

    if not isinstance(data, list):
        raise TypeError("data must be a list.")

    if not isinstance(includeValuesInResponse, bool):
        raise TypeError("includeValuesInResponse must be a boolean.")

    if not isinstance(responseValueRenderOption, str):
        raise TypeError("responseValueRenderOption must be a string.")
    if responseValueRenderOption not in VALID_RESPONSE_VALUE_RENDER_OPTIONS:
        raise ValueError(f"responseValueRenderOption must be one of {list(VALID_RESPONSE_VALUE_RENDER_OPTIONS)}. Got '{responseValueRenderOption}'.")

    if not isinstance(responseDateTimeRenderOption, str):
        raise TypeError("responseDateTimeRenderOption must be a string.")
    if responseDateTimeRenderOption not in VALID_RESPONSE_DATETIME_RENDER_OPTIONS:
        raise ValueError(f"responseDateTimeRenderOption must be one of {list(VALID_RESPONSE_DATETIME_RENDER_OPTIONS)}. Got '{responseDateTimeRenderOption}'.")

    userId = "me"
    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    updated_data = []
    for i, data_filter_value_range in enumerate(data):
        if not isinstance(data_filter_value_range, dict):
            raise TypeError(f"Each item in 'data' must be a dictionary (at index {i}).")
        # Determine range
        if "dataFilter" in data_filter_value_range:
            data_filter = data_filter_value_range["dataFilter"]
            if not isinstance(data_filter, dict):
                raise TypeError(f"'dataFilter' must be a dictionary (at index {i}).")
            if "a1Range" not in data_filter:
                raise ValueError(f"'dataFilter' must contain 'a1Range' (at index {i}).")
            range_ = data_filter["a1Range"]
        elif "range" in data_filter_value_range:
            range_ = data_filter_value_range["range"]
        else:
            raise ValueError(f"Each item in 'data' must contain either 'dataFilter' or 'range' (at index {i}).")
        # Validate values
        values = data_filter_value_range.get("values")
        if not isinstance(values, list):
            raise TypeError(f"'values' must be a list of lists (at index {i}).")
        if not all(isinstance(row, list) for row in values):
            raise TypeError(f"Each item in 'values' must be a list (at index {i}).")

        # Process valueInputOption (simulate USER_ENTERED parsing)
        processed_values = []
        for row in values:
            processed_row = []
            for cell_value in row:
                processed_cell = cell_value
                if valueInputOption == "USER_ENTERED" and isinstance(cell_value, str):
                    # Convert string numbers to actual numbers
                    if re.match(r"^-?\d+(\.\d+)?$", cell_value):
                        if "." in cell_value:
                            processed_cell = float(cell_value)
                        else:
                            processed_cell = int(cell_value)
                    # Convert date strings to date objects (simplified example)
                    elif re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", cell_value):
                        processed_cell = f"DATE:{cell_value}"
                    elif cell_value.startswith("="):
                        processed_cell = cell_value
                processed_row.append(processed_cell)
            processed_values.append(processed_row)

        spreadsheet["data"][range_] = processed_values

        response_values = None
        if includeValuesInResponse:
            response_values = [row[:] for row in processed_values]  # Copy
            # Handle responseValueRenderOption
            if responseValueRenderOption == "UNFORMATTED_VALUE":
                for i_row, row_val in enumerate(response_values):
                    for j, cell_val in enumerate(row_val):
                        if isinstance(cell_val, str):
                            if cell_val.startswith("DATE:"):
                                response_values[i_row][j] = cell_val.replace("DATE:", "")
            elif responseValueRenderOption == "FORMULA":
                for i_row, row_val in enumerate(response_values):
                    for j, cell_val in enumerate(row_val):
                        if isinstance(cell_val, str) and cell_val.startswith("="):
                            response_values[i_row][j] = cell_val
            # Handle responseDateTimeRenderOption
            if responseDateTimeRenderOption == "SERIAL_NUMBER":
                excel_epoch = datetime(1899, 12, 30)
                for i_row, row_val in enumerate(response_values):
                    for j, cell_val in enumerate(row_val):
                        if isinstance(cell_val, str) and cell_val.startswith("DATE:"):
                            date_str = cell_val.replace("DATE:", "")
                            try:
                                date_parts = date_str.split("/")
                                month, day, year = (
                                    int(date_parts[0]),
                                    int(date_parts[1]),
                                    int(date_parts[2]),
                                )
                                date_obj = datetime(year, month, day)
                                delta = date_obj - excel_epoch
                                response_values[i_row][j] = delta.days + (delta.seconds / 86400.0)
                            except (ValueError, IndexError):
                                pass
        updated_data.append({"range": range_, "values": response_values if includeValuesInResponse else []})

    return {"spreadsheetId": spreadsheet_id, "updatedData": updated_data}


@tool_spec(
    spec={
        'name': 'batch_clear_spreadsheet_values_by_data_filter',
        'description': 'Clears values from a spreadsheet using data filters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to clear values from.'
                },
                'dataFilters': {
                    'type': 'array',
                    'description': 'List of data filters, each containing:',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'a1Range': {
                                'type': 'string',
                                'description': 'The A1 notation of the range to clear. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"'
                            }
                        },
                        'required': [
                            'a1Range'
                        ]
                    }
                }
            },
            'required': [
                'spreadsheet_id',
                'dataFilters'
            ]
        }
    }
)
def batchClearByDataFilter(spreadsheet_id: str, dataFilters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Clears values from a spreadsheet using data filters.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet to clear values from.
        dataFilters (List[Dict[str, Any]]): List of data filters, each containing:
            - a1Range (str): The A1 notation of the range to clear. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"

    Returns:
        Dict[str, Any]: A dictionary containing:
            - spreadsheetId (str): The spreadsheet ID
            - clearedRanges (List[str]): List of cleared ranges in A1 notation. The A1 notation is a syntax used to define a cell or range of cells with a string that contains the sheet name plus the starting and ending cell coordinates using column letters and row numbers like: "Sheet1!A1:D3" or "A1:D3"

    Raises:
        ValueError: If the spreadsheet is not found
    """
    userId = "me"
    if spreadsheet_id not in DB["users"][userId]["files"]:
        raise ValueError("Spreadsheet not found")

    spreadsheet = DB["users"][userId]["files"][spreadsheet_id]
    cleared_ranges = []

    for data_filter in dataFilters:
        range_ = data_filter["a1Range"]
        # Always set to a single empty cell
        spreadsheet["data"][range_] = [[""]]
        cleared_ranges.append(range_)

    return {"spreadsheetId": spreadsheet_id, "clearedRanges": cleared_ranges}
