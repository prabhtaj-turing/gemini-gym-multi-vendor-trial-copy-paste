
# jira/__init__.py
from .SimulationEngine.db import DB, load_state, save_state,load_state, save_state
from jira.SimulationEngine import utils
from jira import SimulationEngine

from . import ApplicationPropertiesApi
from . import ApplicationRoleApi
from . import AttachmentApi
from . import AvatarApi
from . import ComponentApi
from . import DashboardApi
from . import FilterApi
from . import GroupApi
from . import GroupsPickerApi
from . import IssueApi
from . import IssueLinkApi
from . import IssueLinkTypeApi
from . import IssueTypeApi
from . import JqlApi
from . import LicenseValidatorApi
from . import MyPermissionsApi
from . import MyPreferencesApi
from . import PermissionsApi
from . import PermissionSchemeApi
from . import PriorityApi
from . import ProjectApi
from . import ProjectCategoryApi
from . import ReindexApi
from . import ResolutionApi
from . import RoleApi
from . import SearchApi
from . import SecurityLevelApi
from . import ServerInfoApi
from . import SettingsApi
from . import StatusApi
from . import StatusCategoryApi
from . import UserApi
from . import UserAvatarsApi
from . import VersionApi
from . import WebhookApi
from . import WorkflowApi

# Define __all__ for 'from gmail import *'
# Explicitly lists the public API components intended for import *.
import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "get_all_project_categories": "jira.ProjectCategoryApi.get_project_categories",
  "get_project_category_by_id": "jira.ProjectCategoryApi.get_project_category",
  "create_issue": "jira.IssueApi.create_issue",
  "get_issue_by_id": "jira.IssueApi.get_issue",
  "update_issue_by_id": "jira.IssueApi.update_issue",
  "delete_issue_by_id": "jira.IssueApi.delete_issue",
  "bulk_delete_issues": "jira.IssueApi.bulk_delete_issues",
  "assign_issue_to_user": "jira.IssueApi.assign_issue",
  "perform_bulk_issue_operations": "jira.IssueApi.bulk_issue_operation",
  "search_issues_for_picker": "jira.IssueApi.issue_picker",
  "get_issue_create_metadata": "jira.IssueApi.get_create_meta",
  "get_all_permission_schemes": "jira.PermissionSchemeApi.get_permission_schemes",
  "get_permission_scheme_by_id": "jira.PermissionSchemeApi.get_permission_scheme",
  "get_all_statuses": "jira.StatusApi.get_statuses",
  "get_status_by_id": "jira.StatusApi.get_status",
  "get_all_security_levels": "jira.SecurityLevelApi.get_security_levels",
  "get_security_level_by_id": "jira.SecurityLevelApi.get_security_level",
  "search_issues_jql": "jira.SearchApi.search_issues",
  "create_project_component": "jira.ComponentApi.create_component",
  "get_component_by_id": "jira.ComponentApi.get_component",
  "update_component_by_id": "jira.ComponentApi.update_component",
  "delete_component_by_id": "jira.ComponentApi.delete_component",
  "get_user_avatars_by_username": "jira.UserAvatarsApi.get_user_avatars",
  "get_application_properties": "jira.ApplicationPropertiesApi.get_application_properties",
  "update_application_property_by_id": "jira.ApplicationPropertiesApi.update_application_property",
  "get_all_priorities": "jira.PriorityApi.get_priorities",
  "get_priority_by_id": "jira.PriorityApi.get_priority",
  "get_all_status_categories": "jira.StatusCategoryApi.get_status_categories",
  "get_status_category_by_id": "jira.StatusCategoryApi.get_status_category",
  "get_all_issue_types": "jira.IssueTypeApi.get_issue_types",
  "get_issue_type_by_id": "jira.IssueTypeApi.get_issue_type",
  "create_issue_type": "jira.IssueTypeApi.create_issue_type",
  "get_user_by_username_or_account_id": "jira.UserApi.get_user",
  "create_user": "jira.UserApi.create_user",
  "delete_user_by_username_or_key": "jira.UserApi.delete_user",
  "find_users": "jira.UserApi.find_users",
  "get_group_by_name": "jira.GroupApi.get_group",
  "update_group_members_by_name": "jira.GroupApi.update_group",
  "create_group": "jira.GroupApi.create_group",
  "delete_group_by_name": "jira.GroupApi.delete_group",
  "create_issue_link": "jira.IssueLinkApi.create_issue_link",
  "get_all_dashboards": "jira.DashboardApi.get_dashboards",
  "get_dashboard_by_id": "jira.DashboardApi.get_dashboard",
  "get_all_issue_link_types": "jira.IssueLinkTypeApi.get_issue_link_types",
  "get_issue_link_type_by_id": "jira.IssueLinkTypeApi.get_issue_link_type",
  "get_server_info": "jira.ServerInfoApi.get_server_info",
  "get_all_resolutions": "jira.ResolutionApi.get_resolutions",
  "get_resolution_by_id": "jira.ResolutionApi.get_resolution",
  "get_all_settings": "jira.SettingsApi.get_settings",
  "get_all_permissions": "jira.PermissionsApi.get_permissions",
  "get_version_by_id": "jira.VersionApi.get_version",
  "create_version": "jira.VersionApi.create_version",
  "delete_version_by_id": "jira.VersionApi.delete_version_and_replace_values",
  "get_version_related_issue_counts_by_id": "jira.VersionApi.get_version_related_issue_counts",
  "create_webhooks": "jira.WebhookApi.create_or_get_webhooks",
  "get_all_webhooks": "jira.WebhookApi.get_webhooks",
  "delete_webhooks_by_ids": "jira.WebhookApi.delete_webhooks",
  "find_groups_for_picker": "jira.GroupsPickerApi.find_groups",
  "create_project": "jira.ProjectApi.create_project",
  "get_all_projects": "jira.ProjectApi.get_projects",
  "get_project_by_key": "jira.ProjectApi.get_project",
  "get_project_avatars_by_key": "jira.ProjectApi.get_project_avatars",
  "get_project_components_by_key": "jira.ProjectApi.get_project_components",
  "delete_project_by_key": "jira.ProjectApi.delete_project",
  "get_all_filters": "jira.FilterApi.get_filters",
  "get_filter_by_id": "jira.FilterApi.get_filter",
  "update_filter_by_id": "jira.FilterApi.update_filter",
  "get_current_user_preferences": "jira.MyPreferencesApi.get_my_preferences",
  "update_current_user_preferences": "jira.MyPreferencesApi.update_my_preferences",
  "get_all_roles": "jira.RoleApi.get_roles",
  "get_role_by_id": "jira.RoleApi.get_role",
  "get_current_user_permissions": "jira.MyPermissionsApi.get_current_user_permissions",
  "upload_avatar": "jira.AvatarApi.upload_avatar",
  "upload_temporary_avatar": "jira.AvatarApi.upload_temporary_avatar",
  "crop_temporary_avatar": "jira.AvatarApi.crop_temporary_avatar",
  "validate_license": "jira.LicenseValidatorApi.validate_license",
  "get_jql_autocomplete_suggestions": "jira.JqlApi.get_jql_autocomplete_data",
  "start_reindex": "jira.ReindexApi.start_reindex",
  "get_reindex_status": "jira.ReindexApi.get_reindex_status",
  "get_all_application_roles": "jira.ApplicationRoleApi.get_application_roles",
  "get_application_role_by_key": "jira.ApplicationRoleApi.get_application_role_by_key",
  "get_all_workflows": "jira.WorkflowApi.get_workflows",
  "get_attachment_metadata": "jira.AttachmentApi.get_attachment_metadata",
  "delete_attachment": "jira.AttachmentApi.delete_attachment",
  "add_attachment": "jira.AttachmentApi.add_attachment",
  "list_issue_attachments": "jira.AttachmentApi.list_issue_attachments",
  "download_attachment": "jira.AttachmentApi.download_attachment",
  "get_attachment_content": "jira.AttachmentApi.get_attachment_content"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
