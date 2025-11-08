
# linkedin/__init__.py

# --- Resources from 'linkedin' ---
from . import Organizations
from . import Me

from . import OrganizationAcls
from . import Posts
from .SimulationEngine import db, models

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from linkedin.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "get_organizations_by_vanity_name": "linkedin.Organizations.get_organizations_by_vanity_name",
  "create_organization": "linkedin.Organizations.create_organization",
  "update_organization_by_id": "linkedin.Organizations.update_organization",
  "delete_organization_by_id": "linkedin.Organizations.delete_organization",
  "delete_organization_by_vanity_name": "linkedin.Organizations.delete_organization_by_vanity_name",
  "get_organization_acls_by_role_assignee": "linkedin.OrganizationAcls.get_organization_acls_by_role_assignee",
  "create_organization_acl": "linkedin.OrganizationAcls.create_organization_acl",
  "update_organization_acl": "linkedin.OrganizationAcls.update_organization_acl",
  "delete_organization_acl": "linkedin.OrganizationAcls.delete_organization_acl",
  "create_post": "linkedin.Posts.create_post",
  "get_post_by_id": "linkedin.Posts.get_post",
  "find_posts_by_author": "linkedin.Posts.find_posts_by_author",
  "update_post": "linkedin.Posts.update_post",
  "delete_post_by_id": "linkedin.Posts.delete_post",
  "get_my_profile": "linkedin.Me.get_me",
  "create_my_profile": "linkedin.Me.create_me",
  "update_my_profile": "linkedin.Me.update_me",
  "delete_my_profile": "linkedin.Me.delete_me"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
