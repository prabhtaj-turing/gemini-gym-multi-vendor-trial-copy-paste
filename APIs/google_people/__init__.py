# google_people/__init__.py
"""
Google People API Simulation

This package provides a simulation of the Google People API functionality.
It allows for contact management and profile operations in a simulated environment.
"""
import importlib
import json
import os
import tempfile

from . import contact_groups
from . import other_contacts
# Import the main modules
from . import people
from common_utils.init_utils import create_error_simulator, resolve_function_import
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.error_handling import get_package_error_mode
from google_people.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    # People resource methods
    "get_contact": "google_people.people.get_contact",
    "create_contact": "google_people.people.create_contact",
    "update_contact": "google_people.people.update_contact",
    "delete_contact": "google_people.people.delete_contact",
    "list_connections": "google_people.people.list_connections",
    "search_people": "google_people.people.search_people",
    "get_batch_get": "google_people.people.get_batch_get",

    # Contact groups methods
    "get_contact_group": "google_people.contact_groups.get",
    "create_contact_group": "google_people.contact_groups.create",
    "update_contact_group": "google_people.contact_groups.update",
    "delete_contact_group": "google_people.contact_groups.delete",
    "list_contact_groups": "google_people.contact_groups.list",
    "modify_contact_group_members": "google_people.contact_groups.modify_members",

    # Other people resource methods
    "get_other_contact": "google_people.other_contacts.get_other_contact",
    "list_other_contacts": "google_people.other_contacts.list_other_contacts",
    "search_other_contacts": "google_people.other_contacts.search_other_contacts",

    # Directory people methods
    "get_directory_person": "google_people.people.get_directory_person",
    "list_directory_people": "google_people.people.list_directory_people",
    "search_directory_people": "google_people.people.search_directory_people",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))


__all__ = list(_function_map.keys())
