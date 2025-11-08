
"""
Google Drive API Simulation

This package provides a simulation of the Google Drive API functionality.
It allows for basic file operations and management in a simulated environment.
"""

from . import About
from . import Apps
from . import Changes
from . import Channels
from . import Comments
from . import Drives
from . import Files
from . import Permissions
from . import Replies
from . import SimulationEngine

# from .SimulationEngine.db import DB, load_state, save_state, DriveAPI
from .SimulationEngine.db import DB, load_state, save_state, load_state, save_state
from .SimulationEngine.utils import (
    _ensure_user,
    _ensure_apps,
    _ensure_changes,
    _ensure_channels,
    _ensure_file,
    _parse_query,
    _apply_query_filter,
    _delete_descendants,
    _has_drive_role,
    _update_user_usage,
    _get_user_quota,
)
from .SimulationEngine.counters import _next_counter

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from gdrive.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "copy_file": "gdrive.Files.copy",
  "create_file_or_folder": "gdrive.Files.create",
  "delete_file_permanently": "gdrive.Files.delete",
  "empty_files_from_trash": "gdrive.Files.emptyTrash",
  "export_google_doc": "gdrive.Files.export",
  "generate_file_ids": "gdrive.Files.generateIds",
  "get_file_metadata_or_content": "gdrive.Files.get",
  "list_user_files": "gdrive.Files.list",
  "update_file_metadata_or_content": "gdrive.Files.update",
  "subscribe_to_file_changes": "gdrive.Files.watch",
  "create_shared_drive": "gdrive.Drives.create",
  "delete_shared_drive": "gdrive.Drives.delete",
  "get_shared_drive_metadata": "gdrive.Drives.get",
  "hide_shared_drive": "gdrive.Drives.hide",
  "list_user_shared_drives": "gdrive.Drives.list",
  "unhide_shared_drive": "gdrive.Drives.unhide",
  "update_shared_drive_metadata": "gdrive.Drives.update",
  "create_file_comment": "gdrive.Comments.create",
  "get_file_comment": "gdrive.Comments.get",
  "list_comments": "gdrive.Comments.list",
  "update_file_comment": "gdrive.Comments.update",
  "delete_file_comment": "gdrive.Comments.delete",
  "get_drive_account_info": "gdrive.About.get",
  "create_permission": "gdrive.Permissions.create",
  "delete_permission": "gdrive.Permissions.delete",
  "get_permission": "gdrive.Permissions.get",
  "list_permissions": "gdrive.Permissions.list",
  "update_permission": "gdrive.Permissions.update",
  "get_app_details": "gdrive.Apps.get",
  "list_installed_apps": "gdrive.Apps.list",
  "stop_channel_watch": "gdrive.Channels.stop",
  "get_changes_start_page_token": "gdrive.Changes.getStartPageToken",
  "list_changes": "gdrive.Changes.list",
  "watch_changes": "gdrive.Changes.watch",
  "create_comment_reply": "gdrive.Replies.create",
  "delete_comment_reply": "gdrive.Replies.delete",
  "get_comment_reply": "gdrive.Replies.get",
  "list_comment_replies": "gdrive.Replies.list",
  "update_comment_reply": "gdrive.Replies.update",
  "get_file_content": "gdrive.Files.get_content",
  "create_file_revision": "gdrive.Files.create_revision",
  "update_file_content": "gdrive.Files.update_content",
  "export_file_content": "gdrive.Files.export_content",
  "list_file_revisions": "gdrive.Files.list_revisions"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())