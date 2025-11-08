"""
MongoDB API Simulation

This package provides a simulation of the MongoDB API functionality.
It allows for basic query execution and data manipulation in a simulated environment.
"""
import importlib
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from pydantic import ValidationError
from . import collection_management
from . import connection_server_management
from . import database_operations
from . import data_operations

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from mongodb.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "switch_connection": "mongodb.connection_server_management.switch_connection",
    "list_databases": "mongodb.database_operations.list_databases",
    "drop_database": "mongodb.database_operations.drop_database",
    "list_collections": "mongodb.collection_management.list_collections",
    "create_collection": "mongodb.collection_management.create_collection",
    "rename_collection": "mongodb.collection_management.rename_collection",
    "drop_collection": "mongodb.collection_management.drop_collection",
    "collection_schema": "mongodb.collection_management.collection_schema",
    "collection_storage_size": "mongodb.collection_management.collection_storage_size",
    "collection_indexes": "mongodb.collection_management.collection_indexes",
    "create_index": "mongodb.collection_management.create_index",
    "find": "mongodb.data_operations.find",
    "count": "mongodb.data_operations.count",
    "aggregate": "mongodb.data_operations.aggregate",
    "insert_many": "mongodb.data_operations.insert_many",
    "update_many": "mongodb.data_operations.update_many",
    "delete_many": "mongodb.data_operations.delete_many",
}

# Separate utils map for utility functions
_utils_map = {
    # ID Generation
    "generate_object_id": "mongodb.SimulationEngine.utils.generate_object_id",
    
    # Connection Helpers
    "get_active_connection": "mongodb.SimulationEngine.utils.get_active_connection",
    "get_active_database": "mongodb.SimulationEngine.utils.get_active_database",
    
    # Audit & Logging
    "log_operation": "mongodb.SimulationEngine.utils.log_operation",
    
    # Metadata Management
    "maintain_index_metadata": "mongodb.SimulationEngine.utils.maintain_index_metadata",
    "update_collection_metrics": "mongodb.SimulationEngine.utils.update_collection_metrics",
    
    # Data Validation
    "sanitize_document": "mongodb.SimulationEngine.utils.sanitize_document",
    "validate_document_references": "mongodb.SimulationEngine.utils.validate_document_references",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
