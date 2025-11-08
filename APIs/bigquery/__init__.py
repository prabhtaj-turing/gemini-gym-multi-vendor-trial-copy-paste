"""
BigQuery API Simulation

This package provides a simulation of the BigQuery API functionality.
"""

import importlib
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from . import bigqueryAPI
from pydantic import ValidationError
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from . import bigqueryAPI
from .SimulationEngine.custom_errors import (
    DatasetNotFoundError,
    InvalidInputError,
    InvalidQueryError,
    ProjectNotFoundError,
    TableNotFoundError,
)
from .SimulationEngine.utils import parse_full_table_name, load_db_dict_to_sqlite
from bigquery.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "list_tables": "bigquery.bigqueryAPI.list_tables",
    "describe_table": "bigquery.bigqueryAPI.describe_table",
    "execute_query": "bigquery.bigqueryAPI.execute_query",
}
# Separate utils map for utility functions
_utils_map = {
    # Path Management
    "set_default_db_path": "bigquery.SimulationEngine.utils.set_default_db_path",
    "get_default_db_path": "bigquery.SimulationEngine.utils.get_default_db_path",
    "get_default_sqlite_db_dir": "bigquery.SimulationEngine.utils.get_default_sqlite_db_dir",
    
    # Table Operations
    "get_table_from_path": "bigquery.SimulationEngine.utils.get_table_from_path",
    "find_table_by_name": "bigquery.SimulationEngine.utils.find_table_by_name",
    "get_table_size_info": "bigquery.SimulationEngine.utils.get_table_size_info",
    "is_table_expired": "bigquery.SimulationEngine.utils.is_table_expired",
    "get_table_age": "bigquery.SimulationEngine.utils.get_table_age",
    "format_table_metadata": "bigquery.SimulationEngine.utils.format_table_metadata",
    
    # Type Conversion
    "bq_type_to_sqlite_type": "bigquery.SimulationEngine.utils.bq_type_to_sqlite_type",
    
    # Timestamp Utilities
    "get_current_timestamp_ms": "bigquery.SimulationEngine.utils.get_current_timestamp_ms",
    "convert_timestamp_to_milliseconds": "bigquery.SimulationEngine.utils.convert_timestamp_to_milliseconds",
    
    # Table Name Parsing
    "parse_full_table_name": "bigquery.SimulationEngine.utils.parse_full_table_name",
    
    # Database Operations
    "initialize_sqlite_db": "bigquery.SimulationEngine.utils.initialize_sqlite_db",
    "create_table_schema": "bigquery.SimulationEngine.utils.create_table_schema",
    "load_database_from_json": "bigquery.SimulationEngine.utils.load_database_from_json",
    "load_db_dict_to_sqlite": "bigquery.SimulationEngine.utils.load_db_dict_to_sqlite",
    
    # In-Memory DB Management
    "create_project": "bigquery.SimulationEngine.utils.create_project",
    "create_dataset": "bigquery.SimulationEngine.utils.create_dataset",
    "create_table": "bigquery.SimulationEngine.utils.create_table",
    "insert_rows": "bigquery.SimulationEngine.utils.insert_rows",
    
    # Data Validation
    "validate_and_normalize_phone_numbers_in_data": "bigquery.SimulationEngine.utils.validate_and_normalize_phone_numbers_in_data",
    "validate_phone_number_field": "bigquery.SimulationEngine.utils.validate_phone_number_field",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    global _function_map
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
