"""
models.py
------------------

Pydantic (v1) models describing the JSON file that keeps persistent
state for the DuckDB‐backed MySQL simulator.

Example JSON
============

{
  "attached": {
    "main_db": {
      "sanitized": "main_db",
      "path": "main_db.duckdb"
    },
    "inventory_db": {
      "sanitized": "inventory_db",
      "path": "inventory_db.duckdb"
    }
  },
  "current": "main",
  "primary_internal_name": "main_db"
}
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, validator


# ---------------------------------------------------------------------------
# Validators / helpers
# ---------------------------------------------------------------------------
_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


def _validate_db_name(name: str) -> str:
    if not _DB_NAME_RE.match(name) or name in {".", ".."}:
        raise ValueError("invalid MySQL database name")
    return name


# ---------------------------------------------------------------------------
# Core Database Content Models
# ---------------------------------------------------------------------------

class CustomerRecord(BaseModel):
    """Model for customer table records"""
    id: int = Field(..., ge=1, description="Customer ID (positive integer)")
    first_name: str = Field(..., min_length=1, max_length=100, description="Customer first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Customer last name") 
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$', description="Customer email address")
    city: str = Field(..., min_length=1, max_length=100, description="Customer city")

class OrderRecord(BaseModel):
    """Model for order table records"""
    id: int = Field(..., ge=1, description="Order ID (positive integer)")
    order_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Order date in YYYY-MM-DD format")
    customer_id: int = Field(..., ge=1, description="Customer ID reference")
    total_amount: Union[float, int] = Field(..., ge=0, description="Order total amount")
    
    @validator('order_date')
    def validate_order_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Order date must be in YYYY-MM-DD format')

class ProductRecord(BaseModel):
    """Model for product table records"""
    id: int = Field(..., ge=1, description="Product ID (positive integer)")
    sku: str = Field(..., min_length=1, max_length=50, description="Product SKU")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    unit_price: Union[float, int] = Field(..., ge=0, description="Product unit price")

class StockLevelRecord(BaseModel):
    """Model for stock level table records"""
    product_id: int = Field(..., ge=1, description="Product ID reference")
    warehouse: str = Field(..., min_length=1, max_length=50, description="Warehouse identifier")
    quantity: int = Field(..., ge=0, description="Stock quantity")

class DatabaseTable(BaseModel):
    """Model for a database table with its records"""
    table_name: str = Field(..., min_length=1, description="Table name")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="Table records")
    
class DatabaseSchema(BaseModel):
    """Model for a complete database with all its tables"""
    database_name: str = Field(..., description="Database name")
    tables: Dict[str, DatabaseTable] = Field(default_factory=dict, description="Database tables")
    
    @validator('database_name')
    def validate_db_name_field(cls, v):
        return _validate_db_name(v)

# ---------------------------------------------------------------------------
# Simulation State Models  
# ---------------------------------------------------------------------------
class AttachedEntry(BaseModel):
    """
    One entry inside the ``attached`` mapping.

    Attributes
    ----------
    sanitized:
        File-system safe alias actually used when the database is ATTACHed
        to DuckDB.
    path:
        Relative path to the ``*.duckdb`` file from the simulator’s
        database_directory.
    """

    sanitized: str = Field(..., description="sanitized DuckDB alias")
    path: str = Field(..., description="relative path to *.duckdb file")

    # basic sanity check
    _db_name = validator("sanitized", allow_reuse=True)(_validate_db_name)


class SimulationSnapshot(BaseModel):
    """
    Root model that mirrors the JSON snapshot persisted by DuckDBManager.

    Attributes
    ----------
    attached:
        Mapping of user-visible database names to their corresponding
        `AttachedEntry`.
    current:
        Alias currently selected with `USE` (often `"main"`).
    primary_internal_name:
        The internal name DuckDB assigned to the main database file
        (helps during result-patching).
    """

    attached: Dict[str, AttachedEntry]
    current: str
    primary_internal_name: str

    # Validation for keys in `attached`
    @validator("attached", pre=True)
    def _validate_keys(cls, v):
        if not isinstance(v, dict):
            raise TypeError("attached must be an object")
        for key in v:
            _validate_db_name(key)
        return v


# ---------------------------------------------------------------------------
# Root Database Model - Comprehensive MySQL Database Structure Validation
# ---------------------------------------------------------------------------

class MySQLDB(BaseModel):
    """
    Validates entire MySQL database simulation structure including:
    - Database management state (attached databases, current context)
    - Sample data schemas for testing and validation
    
    This model ensures database structure integrity and validates
    all database content against expected schemas.
    """
    # Core simulation state
    attached: Dict[str, AttachedEntry] = Field(
        default_factory=dict, 
        description="Attached database mappings"
    )
    current: str = Field(
        default="main", 
        description="Currently active database alias"
    )
    primary_internal_name: str = Field(
        default="main", 
        description="Primary internal database name"
    )
    
    # Sample database schemas for validation
    databases: Dict[str, DatabaseSchema] = Field(
        default_factory=dict,
        description="Database schemas with their table structures"
    )
    
    # Validation metadata
    version: str = Field(
        default="1.0",
        description="Database schema version"
    )
    last_updated: Optional[str] = Field(
        None,
        description="Last update timestamp in ISO format"
    )
    
    @validator("attached", pre=True)
    def _validate_attached_structure(cls, v):
        """Validate attached database structure"""
        if not isinstance(v, dict):
            raise TypeError("attached must be an object")
        for key in v:
            _validate_db_name(key)
        return v
    
    @validator("current")
    def _validate_current_db(cls, v):
        """Validate current database name"""
        if not v or not isinstance(v, str):
            raise ValueError("current database must be a non-empty string")
        return v
    
    @validator("primary_internal_name")
    def _validate_primary_name(cls, v):
        """Validate primary internal name"""
        if not v or not isinstance(v, str):
            raise ValueError("primary_internal_name must be a non-empty string")
        return v
    
    @validator("last_updated")
    def _validate_timestamp(cls, v):
        """Validate timestamp format if provided"""
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError("last_updated must be in ISO format")
        return v
    
    @validator("databases")
    def _validate_database_schemas(cls, v):
        """Validate database schemas structure"""
        if not isinstance(v, dict):
            raise TypeError("databases must be a dictionary")
        
        # Validate each database schema
        for db_name, schema in v.items():
            if not _validate_db_name(db_name):
                raise ValueError(f"Invalid database name: {db_name}")
            if not isinstance(schema, DatabaseSchema):
                raise TypeError(f"Database {db_name} must be a DatabaseSchema instance")
        
        return v
    
    class Config:
        str_strip_whitespace = True
        validate_assignment = True

