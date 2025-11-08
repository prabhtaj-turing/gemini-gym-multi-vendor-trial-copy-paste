"""
Pydantic models for Google Sheets API database validation.

This module defines the database schema for Google Sheets simulation,
extending and reusing models from GDrive for full interoperability.
Only includes models used for database structure validation.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
import sys

# Import shared models from GDrive for interoperability
sys.path.append("APIs")
from gdrive.SimulationEngine.db_models import (
    # Core models reused from GDrive for interoperability
    UserAboutModel,
    FilePermissionModel,
    DriveModel,
    CommentModel,
    ReplyModel,
    LabelModel,
    AccessProposalModel,
    CountersModel,
)


# ========================================
# Sheets-Specific Database Models
# ========================================

class DBSheetGridPropertiesModel(BaseModel):
    """Grid properties for a sheet (rows and columns)."""
    rowCount: int = Field(..., description="Number of rows in the sheet")
    columnCount: int = Field(..., description="Number of columns in the sheet")


class DBSheetPropertiesModel(BaseModel):
    """Properties of a sheet within a spreadsheet."""
    sheetId: int = Field(..., description="Unique sheet identifier")
    title: str = Field(..., description="Sheet title")
    index: int = Field(..., description="Sheet index/position")
    sheetType: str = Field(default="GRID", description="Sheet type (GRID, OBJECT, etc.)")
    gridProperties: DBSheetGridPropertiesModel = Field(
        default_factory=lambda: DBSheetGridPropertiesModel(rowCount=1000, columnCount=26),
        description="Grid dimensions"
    )


class DBSheetModel(BaseModel):
    """Model representing a sheet in the database."""
    properties: DBSheetPropertiesModel = Field(..., description="Sheet properties")


class DBSpreadsheetPropertiesModel(BaseModel):
    """Spreadsheet-level properties."""
    title: str = Field(..., description="Spreadsheet title")
    locale: Optional[str] = Field(default="en_US", description="Locale")
    timeZone: Optional[str] = Field(default="America/New_York", description="Time zone")


class SpreadsheetFileModel(BaseModel):
    """
    Model for spreadsheet files in the database.
    Extends base file properties with Sheets-specific data.
    Fully compatible with GDrive's FileModel for interoperability.
    """
    # Base file properties (same as GDrive FileModel)
    id: str = Field(..., description="File ID")
    driveId: Optional[str] = Field(default="", description="Drive ID")
    name: str = Field(..., description="File name")
    mimeType: str = Field(default="application/vnd.google-apps.spreadsheet", description="MIME type")
    createdTime: str = Field(..., description="Creation timestamp")
    modifiedTime: Optional[str] = Field(default=None, description="Modification timestamp")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    owners: List[str] = Field(default_factory=list, description="File owners")
    size: str = Field(default="0", description="File size in bytes")
    trashed: bool = Field(default=False, description="Whether file is trashed")
    starred: bool = Field(default=False, description="Whether file is starred")
    permissions: List[FilePermissionModel] = Field(default_factory=list, description="File permissions")
    
    # Sheets-specific properties
    properties: DBSpreadsheetPropertiesModel = Field(..., description="Spreadsheet properties")
    sheets: List[DBSheetModel] = Field(default_factory=list, description="List of sheets")
    data: Dict[str, List[List[Any]]] = Field(
        default_factory=dict,
        description="Sheet data storage. Key format: 'sheetId!startRow:endRow:startCol:endCol'"
    )


class UserDataModel(BaseModel):
    """
    User data model for Sheets with strict SpreadsheetFileModel validation.
    """
    about: UserAboutModel = Field(..., description="User about information")
    files: Dict[str, SpreadsheetFileModel] = Field(default_factory=dict, description="User files (must be valid SpreadsheetFileModels)")
    drives: Dict[str, DriveModel] = Field(default_factory=dict, description="User drives")
    comments: Dict[str, CommentModel] = Field(default_factory=dict, description="User comments")
    replies: Dict[str, ReplyModel] = Field(default_factory=dict, description="User replies")
    labels: Dict[str, LabelModel] = Field(default_factory=dict, description="User labels")
    accessproposals: Dict[str, AccessProposalModel] = Field(default_factory=dict, description="User access proposals")
    counters: CountersModel = Field(default_factory=CountersModel, description="User counters")


class GoogleSheetsDB(BaseModel):
    """
    Main database model for Google Sheets API simulation.
    Fully interoperable with GDrive, sharing the same core structure.
    """
    users: Dict[str, UserDataModel] = Field(
        default_factory=dict,
        description="Users data with nested structure"
    )
