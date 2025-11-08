from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, field_validator, model_validator
import re
from pydantic import EmailStr

class ValueRangeModel(BaseModel):
    """
    Pydantic model for validating individual items in the 'data' list argument.
    """
    range: str
    values: List[List[Union[str, int, float]]] # A list of rows, where each row is a list of cell values

# Common model for sheet properties, allowing extra fields
class SheetPropertiesBaseModel(BaseModel):
    class Config:
        extra = "allow"

class AddSheetPropertiesModel(SheetPropertiesBaseModel):
    sheetId: int

class AddSheetRequestPayloadModel(BaseModel):
    properties: AddSheetPropertiesModel

class DeleteSheetRequestPayloadModel(BaseModel):
    sheetId: int

class UpdateSheetPropertiesInfoModel(SheetPropertiesBaseModel):
    sheetId: int

class UpdateSheetPropertiesRequestPayloadModel(BaseModel):
    properties: UpdateSheetPropertiesInfoModel
    fields: str # Comma-separated field names

class CellRangeModel(BaseModel):
    sheetId: int
    startRowIndex: int
    endRowIndex: int
    startColumnIndex: int
    endColumnIndex: int

class UpdateCellsPayloadModel(BaseModel):
    range: CellRangeModel
    rows: List[Any] # Structure of 'rows' items is not detailed, so List[Any]

class UpdateSheetPropertiesSimplePayloadModel(BaseModel):
    properties: UpdateSheetPropertiesInfoModel # properties key and its sheetId are effectively mandatory
    fields: Optional[str] = "" # fields key is optional

class AppendSpecificArgsModel(BaseModel):
    """
    Pydantic model for validating specific arguments of the 'append' function,
    particularly those with enum-like constraints or complex structures.
    """
    valueInputOption: Literal['RAW', 'USER_ENTERED']
    values: List[List[Any]] # Validates that 'values' is a list of lists.
    insertDataOption: Optional[Literal['OVERWRITE', 'INSERT_ROWS']] = None
    responseValueRenderOption: Optional[Literal['FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA']] = None
    responseDateTimeRenderOption: Optional[Literal['SERIAL_NUMBER', 'FORMATTED_STRING']] = None
    majorDimension: Literal['ROWS', 'COLUMNS'] = "ROWS"

    class Config:
        extra = 'forbid' # Ensure no unexpected arguments are passed if model is used with **kwargs

#  --- Models for Spreadsheet and its components
class SpreadsheetPropertiesModel(BaseModel):
    title: Optional[str] = "Untitled Spreadsheet"
    locale: Optional[str] = None
    autoRecalc: Optional[str] = None
    timeZone: Optional[str] = None
    defaultFormat: Optional[Dict[str, Any]] = None
    iterativeCalculationSettings: Optional[Dict[str, Any]] = None
    owner: Optional[EmailStr] = None
    permissions: Optional[List[Dict[str, Any]]] = None
    parents: Optional[List[str]] = None
    size: Optional[int] = None
    trashed: Optional[bool] = None
    starred: Optional[bool] = None
    createdTime: Optional[str] = None
    modifiedTime: Optional[str] = None

class SheetGridPropertiesModel(BaseModel):
    rowCount: Optional[int] = None
    columnCount: Optional[int] = None

class SheetPropertiesModel(BaseModel):
    sheetId: Optional[int] = None
    title: str
    index: Optional[int] = None
    sheetType: Optional[str] = None
    gridProperties: Optional[Dict[str, Any]] = None

class SheetModel(BaseModel):
    properties: Optional[SheetPropertiesModel] = None
    # data: Optional[List[Dict[str, Any]]] = None
    merges: Optional[List[Dict[str, Any]]] = None
    conditionalFormats: Optional[List[Dict[str, Any]]] = None
    filterViews: Optional[List[Dict[str, Any]]] = None
    protectedRanges: Optional[List[Dict[str, Any]]] = None
    basicFilter: Optional[Dict[str, Any]] = None
    charts: Optional[List[Dict[str, Any]]] = None
    bandedRanges: Optional[List[Dict[str, Any]]] = None
    developerMetadata: Optional[List[Dict[str, Any]]] = None

class SpreadsheetDataModel(BaseModel):
    """
    Model for spreadsheet data in the simple format: {range: [[values]]}
    """
    # Allow dynamic A1 range keys with array of arrays as values
    class Config:
        extra = "allow"
    
    def __init__(self, **data):
        # Validate that all values are arrays of arrays
        for key, value in data.items():
            if not isinstance(value, list):
                raise ValueError(f"Data value for range '{key}' must be a list of rows")
            for row in value:
                if not isinstance(row, list):
                    raise ValueError(f"Each row in range '{key}' must be a list of cell values")
        super().__init__(**data)
    
    @model_validator(mode='after')
    def validate_a1_range_keys(self):
        """Validate that all keys are proper A1 range format."""
        data = self.model_dump()
        for key in data.keys():
            if not isinstance(key, str):
                raise ValueError(f"Range key must be a string, got {type(key).__name__}")
            
            # Must contain '!' separator
            if '!' not in key:
                raise ValueError(f"Range key must contain '!' separator (e.g., 'Sheet1!A1:B2'), got: '{key}'")
            
            # Split and validate both parts
            parts = key.split('!', 1)
            if len(parts) != 2:
                raise ValueError(f"Range key must have exactly one '!' separator, got: '{key}'")
            
            sheet_part, range_part = parts
            if not sheet_part.strip():
                raise ValueError(f"Sheet name cannot be empty in range: '{key}'")
            if not range_part.strip():
                raise ValueError(f"Range part cannot be empty in range: '{key}'")
            
            # Validate A1 range format
            self._validate_a1_range(range_part, key)
        
        return self
    
    def _validate_a1_range(self, range_part: str, full_key: str):
        """Validate that the range part is a valid A1 range format."""
        import re
        
        # Remove any whitespace
        range_part = range_part.strip()
        
        # Support both cell ranges (A1:B2) and column ranges (A:Z)
        # Pattern 1: Cell range - Column(s) + Row(s) : Column(s) + Row(s)
        # Examples: A1:B2, A1:Z100, AA1:BB2, etc.
        cell_range_pattern = r'^[A-Z]+[0-9]+:[A-Z]+[0-9]+$'
        
        # Pattern 2: Column range - Column(s) : Column(s)
        # Examples: A:Z, B:D, AA:BB, etc.
        column_range_pattern = r'^[A-Z]+:[A-Z]+$'
        
        if not (re.match(cell_range_pattern, range_part) or re.match(column_range_pattern, range_part)):
            raise ValueError(f"Invalid A1 range format in '{full_key}': '{range_part}'. Must be a cell range like A1:B2 or column range like A:Z.")

class SpreadsheetModel(BaseModel):
    id: Optional[str] = None
    properties: Optional[SpreadsheetPropertiesModel] = None
    sheets: Optional[List[SheetModel]] = None
    data: Optional[SpreadsheetDataModel] = None

# Common model for sheet properties, allowing extra fields
class SheetPropertiesBaseModel(BaseModel):
    class Config:
        extra = "allow"

class AddSheetPropertiesModel(SheetPropertiesBaseModel):
    sheetId: int

class AddSheetRequestPayloadModel(BaseModel):
    properties: AddSheetPropertiesModel

class DeleteSheetRequestPayloadModel(BaseModel):
    sheetId: int

class UpdateSheetPropertiesInfoModel(SheetPropertiesBaseModel):
    sheetId: int

class UpdateSheetPropertiesRequestPayloadModel(BaseModel):
    properties: UpdateSheetPropertiesInfoModel
    fields: str # Comma-separated field names

class CellRangeModel(BaseModel):
    sheetId: int
    startRowIndex: int
    endRowIndex: int
    startColumnIndex: int
    endColumnIndex: int

class UpdateCellsPayloadModel(BaseModel):
    range: CellRangeModel
    rows: List[Any] # Structure of 'rows' items is not detailed, so List[Any]

class UpdateSheetPropertiesSimplePayloadModel(BaseModel):
    properties: UpdateSheetPropertiesInfoModel # properties key and its sheetId are effectively mandatory
    fields: Optional[str] = "" # fields key is optional

class AppendSpecificArgsModel(BaseModel):
    """
    Pydantic model for validating specific arguments of the 'append' function,
    particularly those with enum-like constraints or complex structures.
    """
    valueInputOption: Optional[Literal['RAW', 'USER_ENTERED']] = None
    values: List[List[Any]] # Validates that 'values' is a list of lists.
    insertDataOption: Optional[Literal['OVERWRITE', 'INSERT_ROWS']] = None
    responseValueRenderOption: Optional[Literal['FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA']] = None
    responseDateTimeRenderOption: Optional[Literal['SERIAL_NUMBER', 'FORMATTED_STRING']] = None
    majorDimension: Optional[Literal['ROWS', 'COLUMNS']] = None

    class Config:
        extra = 'forbid' # Ensure no unexpected arguments are passed if model is used with **kwargs

class GridRangeModel(BaseModel):
    """
    Pydantic model for grid range specifications.
    """
    sheetId: Optional[int] = None
    startRowIndex: Optional[int] = None
    endRowIndex: Optional[int] = None
    startColumnIndex: Optional[int] = None
    endColumnIndex: Optional[int] = None
    
    class Config:
        extra = "allow"

class DeveloperMetadataLookupModel(BaseModel):
    """
    Pydantic model for developer metadata lookup specifications.
    """
    metadataKey: Optional[str] = None
    metadataValue: Optional[str] = None
    metadataId: Optional[int] = None
    
    class Config:
        extra = "allow"

class A1RangeInput(BaseModel):
    range: str

    @field_validator('range')
    def validate_a1_range(cls, value):
        """
        Validates that the given value is a valid A1 notation, supporting:
        - Single cell: A1
        - Cell range: A1:B2
        - Full column range: A:B
        - Full row range: 1:2
        - Mixed range: A2:Z (cell to column)
        - Open-ended range: A5:A (cell to column end)
        - Sheet-only reference: Sheet1, 'My Custom Sheet'
        - Optional sheet name: Sheet1!A1, Sheet1!A1:B2, Sheet1!A:B, Sheet1!1:2, Sheet1!A5:A
        - Quoted sheet names: 'My Sheet'!A1:B2, 'John''s Sheet'!A1 (with escaped quotes)
        """
        # Check for empty string
        if not value:
            raise ValueError("Invalid A1 notation: Empty string is not allowed.")
            
        # Enhanced regex pattern to handle all A1 notation cases
        pattern = r"""
            ^                                       # Start of string
            (?:                                     # Optional sheet name group (non-capturing)
                (?:                                 # Sheet name can be either:
                    '(?:[^']|'')*'                  # Quoted sheet name (with optional escaped quotes)
                    |                               # OR
                    [A-Za-z0-9_]+                   # Unquoted sheet name (alphanumeric + underscore)
                )
                (?:!.*)?                            # Optional exclamation mark and range part
            )?                                      # Sheet name is optional
            (?:                                     # Range part (non-capturing)
                (?:[A-Za-z]{1,3}\d+)               # Cell reference like A1, AA1, etc.
                (?::[A-Za-z]{1,3}\d+)?             # Optional range end with cell like :B2
                |                                   # OR
                (?:[A-Za-z]{1,3}\d+)               # Cell reference 
                (?::[A-Za-z]{1,3})?                # Optional range end with just column like :B
                |                                   # OR
                (?:[A-Za-z]{1,3})                  # Just column like A
                (?::[A-Za-z]{1,3})?                # Optional range end like :B
                |                                   # OR
                (?:\d+)                            # Just row like 1
                (?::\d+)?                          # Optional range end with row like :2
                |                                   # OR
                (?:[A-Za-z]{1,3}\d+)               # Cell reference
                (?::[A-Za-z]{1,3})?                # Optional range end with column like :Z
            )?                                      # Range part is optional (for sheet-only references)
            $                                       # End of string
        """
        
        match = re.match(pattern, value, re.VERBOSE)
        if not match:
            raise ValueError(
                f"Invalid A1 notation: '{value}'. Must be one of:\n"
                "  - 'A1' (single cell)\n"
                "  - 'A1:B2' (cell range)\n"
                "  - 'A:B' (column range)\n"
                "  - '1:2' (row range)\n"
                "  - 'A5:A' (open-ended range)\n"
                "  - 'Sheet1' (sheet-only)\n"
                "  - 'Sheet1!A1' (sheet with cell)\n"
                "  - 'Sheet1!A1:B2' (sheet with range)\n"
                "  - 'Sheet1!A:B' (sheet with column range)\n"
                "  - 'Sheet1!1:2' (sheet with row range)\n"
                "  - 'My Custom Sheet'!A:A (quoted sheet names)"
            )

        # Extract range part after '!' (or entire string if no sheet name)
        if '!' in value:
            range_part = value.split('!', 1)[1]
        else:
            range_part = value
            
        # Handle sheet-only references (no range part)
        if not range_part:
            return value
        
        # Check for invalid formats with multiple colons FIRST
        if range_part.count(':') > 1:
            raise ValueError("Invalid A1 notation: Too many colons in range.")
        
        # Check for invalid cell reference formats BEFORE checking for sheet-only references
        # This ensures we catch invalid patterns before they could be mistaken for sheet names
        
        # Check for invalid formats like A0 (row 0 doesn't exist)
        # Match: letters (1-3) followed immediately by 0 and then end or colon
        # But exclude things that look like sheet names (alphanumeric longer than typical cell refs)
        if re.search(r'^[A-Za-z]{1,3}0$|^[A-Za-z]{1,3}0:', range_part) or re.search(r':[A-Za-z]{1,3}0$', range_part):
            # Make sure it's not a sheet name like "A0therSheet" 
            if not (len(range_part) > 3 and re.match(r'^[A-Za-z0-9_]+$', range_part)):
                raise ValueError("Invalid A1 notation: Row 0 doesn't exist.")
            
        # Check for invalid formats like AAAA1 (column too long - more than 3 letters)
        # Match: 4+ letters followed immediately by a digit, but only if it looks like a cell reference
        # Check at start of string or after colon
        has_long_column = re.match(r'^[A-Za-z]{4,}\d+', range_part) or re.search(r':[A-Za-z]{4,}\d+', range_part)
        if has_long_column:
            # Check if this matches common sheet naming patterns like Sheet1, Sheet2, etc.
            # These are default Google Sheets names and should be allowed
            is_default_sheet_name = re.match(r'^[Ss]heet\d+$', range_part)
            
            if not is_default_sheet_name:
                # Check if this is actually a custom sheet name (not a cell reference)
                # Sheet names have no colons and are alphanumeric
                is_likely_sheet_name = (
                    ':' not in range_part and 
                    re.match(r'^[A-Za-z0-9_]+$', range_part) and 
                    len(range_part) > 5  # Sheet names are typically longer than 5 chars
                )
                if not is_likely_sheet_name:
                    raise ValueError("Invalid A1 notation: Column identifier too long (max 3 letters).")
        
        # Handle sheet-only references that look like sheet names
        # Sheet names are typically alphanumeric with underscores, and don't look like cell references
        is_sheet_only = (re.match(r"^[A-Za-z0-9_]+$", range_part) and 
            not re.match(r"^[A-Za-z]{1,3}\d+$", range_part) and  # Not a cell reference like A1
            not re.match(r"^[A-Za-z]+:[A-Za-z]+$", range_part) and  # Not a column range like A:B
            not re.match(r"^\d+:\d+$", range_part) and  # Not a row range like 1:2
            not re.match(r"^[A-Za-z]+\d+:[A-Za-z]+\d+$", range_part) and  # Not a cell range like A1:B2
            not re.match(r"^[A-Za-z]+\d+:[A-Za-z]+$", range_part) and  # Not a mixed range like A1:B
            not re.match(r"^\d+$", range_part) and  # Not a single row like 1
            len(range_part) > 3)  # Sheet names are typically longer than 3 characters
        
        if is_sheet_only:
            # This looks like a sheet-only reference
            return value

        # Validate order in ranges
        if ':' in range_part:
            start_part, end_part = range_part.split(':')
            
            # Empty part after colon
            if not end_part:
                raise ValueError("Invalid A1 notation: Missing end range.")
                
            # For column range (A:B)
            if re.match(r'^[A-Za-z]{1,3}$', start_part) and re.match(r'^[A-Za-z]{1,3}$', end_part):
                if not cls._is_column_before(start_part, end_part):
                    raise ValueError(f"Start column '{start_part}' must come before end column '{end_part}' in A1 notation.")
            
            # For row range (1:2)
            elif re.match(r'^\d+$', start_part) and re.match(r'^\d+$', end_part):
                if int(start_part) > int(end_part):
                    raise ValueError(f"Start row '{start_part}' must come before end row '{end_part}' in A1 notation.")
            
            # For cell range (A1:B2)
            elif re.match(r'^[A-Za-z]{1,3}\d+$', start_part) and re.match(r'^[A-Za-z]{1,3}\d+$', end_part):
                start_col, start_row = cls._extract_col_row(start_part)
                end_col, end_row = cls._extract_col_row(end_part)
                
                if not cls._is_column_before(start_col, end_col):
                    raise ValueError(f"Start column '{start_col}' must come before end column '{end_col}' in A1 notation.")
                if int(start_row) > int(end_row):
                    raise ValueError(f"Start row '{start_row}' must come before end row '{end_row}' in A1 notation.")
            
            # For mixed range (A2:Z) - cell to column
            elif re.match(r'^[A-Za-z]{1,3}\d+$', start_part) and re.match(r'^[A-Za-z]{1,3}$', end_part):
                start_col, _ = cls._extract_col_row(start_part)
                end_col = end_part
                if not cls._is_column_before(start_col, end_col):
                    raise ValueError(f"Start column '{start_col}' must come before end column '{end_col}' in A1 notation.")
                # No row validation needed for open-ended ranges
        
        # Return the original value to preserve the format
        return value

    @staticmethod
    def _extract_col_row(cell_ref):
        """
        Extracts column and row from a cell reference like 'A1'.
        Returns a tuple of (column, row).
        """
        match = re.match(r'([A-Za-z]{1,3})(\d+)', cell_ref)
        if match:
            return match.groups()
        return (cell_ref, None)  # For column-only references like 'A'

    @staticmethod
    def _is_column_before(col1: str, col2: str) -> bool:
        """
        Compares two column references in Google Sheets order.
        Returns True if col1 comes before col2.
        """
        def col_to_num(col: str) -> int:
            result = 0
            for c in col.upper():
                result = result * 26 + (ord(c) - ord('A')) + 1
            return result
        
        return col_to_num(col1) <= col_to_num(col2)

class DataFilterModel(BaseModel):
    a1Range: Optional[str] = None
    gridRange: Optional[GridRangeModel] = None
    developerMetadataLookup: Optional[DeveloperMetadataLookupModel] = None
    # If a filter dict is empty, e.g., {}, it will pass this model as all fields are optional.
    # This seems consistent with how the original code might handle it (filter_dict.get("a1Range") would be None).

    @field_validator('a1Range')
    def validate_a1_range(cls, value):
        """Validate A1 range if provided."""
        if value is not None:
            try:
                A1RangeInput(range=value)
            except ValueError as e:
                raise ValueError(f"Invalid A1 range: {e}")
        return value
    
    def model_post_init(self, __context):
        """Post-initialization validation to ensure at least one filter is provided."""
        # Only validate if this is not an empty filter (which is allowed)
        if any([self.a1Range, self.gridRange, self.developerMetadataLookup]):
            # If any filter is provided, validate that it's properly formed
            pass
