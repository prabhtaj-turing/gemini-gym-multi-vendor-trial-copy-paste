
"""
Salesforce API Simulation Package

This package provides a simulation of the Salesforce API for testing and development purposes.
It includes modules for handling various Salesforce objects and operations.

Modules:
    - Task: Simulates Salesforce Task operations
    - Event: Simulates Salesforce Event operations
    - Query: Provides query functionality for Salesforce objects
    - SimulationEngine: Core engine for API simulation
"""

from . import Task
from . import Event
from . import Query

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from salesforce.SimulationEngine import utils
from salesforce import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "create_event": "salesforce.Event.create",
  "delete_event": "salesforce.Event.delete",
  "describe_event_layout": "salesforce.Event.describeLayout",
  "describe_event_object": "salesforce.Event.describeSObjects",
  "get_deleted_events": "salesforce.Event.getDeleted",
  "get_updated_events": "salesforce.Event.getUpdated",
  "query_events": "salesforce.Event.query",
  "retrieve_event_details": "salesforce.Event.retrieve",
  "search_events": "salesforce.Event.search",
  "undelete_event": "salesforce.Event.undelete",
  "update_event": "salesforce.Event.update",
  "upsert_event": "salesforce.Event.upsert",
  "execute_soql_query": "salesforce.Query.get",
  "parse_where_clause_conditions": "salesforce.Query.parse_conditions",
  "create_task": "salesforce.Task.create",
  "delete_task": "salesforce.Task.delete",
  "describe_task_layout": "salesforce.Task.describeLayout",
  "describe_task_object": "salesforce.Task.describeSObjects",
  "get_deleted_tasks": "salesforce.Task.getDeleted",
  "get_updated_tasks": "salesforce.Task.getUpdated",
  "query_tasks": "salesforce.Task.query",
  "retrieve_task_details": "salesforce.Task.retrieve",
  "search_tasks": "salesforce.Task.search",
  "undelete_task": "salesforce.Task.undelete",
  "update_task": "salesforce.Task.update",
  "upsert_task": "salesforce.Task.upsert"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
