"""
Google Calendar API Simulation

This package provides a simulation of the Google Calendar API functionality.
"""
import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from google_calendar.SimulationEngine import utils

from . import AclResource
from . import CalendarListResource
from . import CalendarsResource
from . import ChannelsResource
from . import ColorsResource
from . import EventsResource 

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "delete_event": "google_calendar.EventsResource.delete_event",
  "get_event": "google_calendar.EventsResource.get_event",
  "import_event": "google_calendar.EventsResource.import_event",
  "create_event": "google_calendar.EventsResource.create_event",
  "list_event_instances": "google_calendar.EventsResource.list_event_instances",
  "list_events": "google_calendar.EventsResource.list_events",
  "move_event": "google_calendar.EventsResource.move_event",
  "patch_event": "google_calendar.EventsResource.patch_event",
  "quick_add_event": "google_calendar.EventsResource.quick_add_event",
  "update_event": "google_calendar.EventsResource.update_event",
  "watch_event_changes": "google_calendar.EventsResource.watch_events",
  "clear_primary_calendar": "google_calendar.CalendarsResource.clear_calendar",
  "delete_secondary_calendar": "google_calendar.CalendarsResource.delete_calendar",
  "get_calendar_metadata": "google_calendar.CalendarsResource.get_calendar",
  "create_secondary_calendar": "google_calendar.CalendarsResource.create_calendar",
  "patch_calendar_metadata": "google_calendar.CalendarsResource.patch_calendar",
  "update_calendar_metadata": "google_calendar.CalendarsResource.update_calendar",
  "get_calendar_and_event_colors": "google_calendar.ColorsResource.get_colors",
  "delete_access_control_rule": "google_calendar.AclResource.delete_rule",
  "get_access_control_rule": "google_calendar.AclResource.get_rule",
  "create_access_control_rule": "google_calendar.AclResource.create_rule",
  "list_access_control_rules": "google_calendar.AclResource.list_rules",
  "patch_access_control_rule": "google_calendar.AclResource.patch_rule",
  "update_access_control_rule": "google_calendar.AclResource.update_rule",
  "watch_access_control_rule_changes": "google_calendar.AclResource.watch_rules",
  "delete_calendar_list_entry": "google_calendar.CalendarListResource.delete_calendar_list",
  "get_calendar_list_entry": "google_calendar.CalendarListResource.get_calendar_list",
  "create_calendar_list_entry": "google_calendar.CalendarListResource.create_calendar_list",
  "list_calendar_list_entries": "google_calendar.CalendarListResource.list_calendar_lists",
  "patch_calendar_list_entry": "google_calendar.CalendarListResource.patch_calendar_list",
  "update_calendar_list_entry": "google_calendar.CalendarListResource.update_calendar_list",
  "watch_calendar_list_changes": "google_calendar.CalendarListResource.watch_calendar_lists",
  "stop_notification_channel": "google_calendar.ChannelsResource.stop_channel"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
