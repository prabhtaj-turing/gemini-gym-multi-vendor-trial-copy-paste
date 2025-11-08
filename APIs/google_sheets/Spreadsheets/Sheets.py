"""Sheets resource for Google Sheets API simulation.

This module provides methods for managing sheets within a spreadsheet. It simulates
the Google Sheets API functionality for sheet operations.


"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from ..SimulationEngine.db import DB

@tool_spec(
    spec={
        'name': 'copy_sheet_to_spreadsheet',
        'description': 'Copies a sheet to a new spreadsheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to copy the sheet from.'
                },
                'sheet_id': {
                    'type': 'integer',
                    'description': 'The ID of the sheet to copy.'
                },
                'destination_spreadsheet_id': {
                    'type': 'string',
                    'description': 'The ID of the spreadsheet to copy the sheet to.'
                }
            },
            'required': [
                'spreadsheet_id',
                'sheet_id',
                'destination_spreadsheet_id'
            ]
        }
    }
)
def copyTo(
    spreadsheet_id: str,
    sheet_id: int,
    destination_spreadsheet_id: str,
) -> Dict[str, Any]:
    
    """Copies a sheet to a new spreadsheet.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet to copy the sheet from.
        sheet_id (int): The ID of the sheet to copy.
        destination_spreadsheet_id (str): The ID of the spreadsheet to copy the sheet to.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - sheetId (int): The ID of the new sheet
            - title (str): The title of the new sheet
            - index (int): The index of the new sheet in the destination spreadsheet
            - sheetType (str): The type of the new sheet
            - gridProperties (dict): The grid properties of the new sheet

    Raises:
        TypeError: If any parameter is not a string
        ValueError: If the source spreadsheet or sheet is not found
        ValueError: If the destination spreadsheet is not found
    """

    # Input validation - type checking
    if not isinstance(spreadsheet_id, str):
        raise TypeError("spreadsheet_id must be a string")
    if not isinstance(sheet_id, int):
        raise TypeError("sheet_id must be an integer")
    if not isinstance(destination_spreadsheet_id, str):
        raise TypeError("destination_spreadsheet_id must be a string")

    userId = "me"
    if spreadsheet_id not in DB['users'][userId]['files']:
        raise ValueError("Spreadsheet not found")
    
    spreadsheet = DB['users'][userId]['files'][spreadsheet_id]
    sheet = next((s for s in spreadsheet['sheets'] if s['properties']['sheetId'] == sheet_id), None)
    if not sheet:
        raise ValueError("Sheet not found")
    
    if destination_spreadsheet_id not in DB['users'][userId]['files']:
        raise ValueError("Destination spreadsheet not found")
        
    # Calculate the correct index for the new sheet in the destination spreadsheet
    destination_spreadsheet = DB['users'][userId]['files'][destination_spreadsheet_id]
    new_sheet_index = len(destination_spreadsheet['sheets'])

    # Create a new sheet in the destination spreadsheet
    # Generate a unique integer sheetId
    existing_sheet_ids = [s['properties']['sheetId'] for s in destination_spreadsheet['sheets']]
    # Convert any string sheetIds to integers for comparison, skip non-numeric strings
    integer_sheet_ids = []
    for sid in existing_sheet_ids:
        if isinstance(sid, int):
            integer_sheet_ids.append(sid)
        elif isinstance(sid, str) and sid.isdigit():
            integer_sheet_ids.append(int(sid))
    new_sheet_id = max(integer_sheet_ids, default=-1) + 1
    
    new_sheet = {
        "properties": {
            "sheetId": new_sheet_id,
            "title": sheet['properties']['title'],
            "index": new_sheet_index,
            "sheetType": sheet['properties']['sheetType'],
            "gridProperties": sheet['properties']['gridProperties']
        }
    }
    
    destination_spreadsheet['sheets'].append(new_sheet)
    
    # Return the properties of the new sheet
    return {
        "sheetId": new_sheet_id,
        "title": sheet['properties']['title'],
        "index": new_sheet_index,
        "sheetType": sheet['properties']['sheetType'],
        "gridProperties": sheet['properties']['gridProperties']
    }
    
    
    