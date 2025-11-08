
from . import Buckets
from . import Channels

import os
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from google_cloud_storage.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "stop_notification_channel": "google_cloud_storage.Channels.stop",
  "delete_bucket": "google_cloud_storage.Buckets.delete",
  "restore_bucket": "google_cloud_storage.Buckets.restore",
  "relocate_bucket": "google_cloud_storage.Buckets.relocate",
  "get_bucket_details": "google_cloud_storage.Buckets.get",
  "get_bucket_iam_policy": "google_cloud_storage.Buckets.getIamPolicy",
  "get_bucket_storage_layout": "google_cloud_storage.Buckets.getStorageLayout",
  "create_bucket": "google_cloud_storage.Buckets.insert",
  "list_buckets": "google_cloud_storage.Buckets.list",
  "lock_bucket_retention_policy": "google_cloud_storage.Buckets.lockRetentionPolicy",
  "patch_bucket_attributes": "google_cloud_storage.Buckets.patch",
  "set_bucket_iam_policy": "google_cloud_storage.Buckets.setIamPolicy",
  "test_bucket_permissions": "google_cloud_storage.Buckets.testIamPermissions",
  "update_bucket_attributes": "google_cloud_storage.Buckets.update"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
