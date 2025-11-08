"""
Common utilities for API modules.

This file makes common_utils a Python package.
"""
import os
from .call_logger import log_function_call, set_runtime_id, clear_log_file
from .init_utils import apply_decorators, resolve_function_import, create_error_simulator
# from .docstring_tests import TestDocstringStructure, run_tests_for_package, merge_csv_reports
from .error_handling import handle_api_errors
from .ErrorSimulation import ErrorSimulator
from .log_complexity import log_complexity
from .mutation_manager import MutationManager
from .authentication_manager import AuthenticationManager, auth_manager, get_auth_manager
from .error_manager import ErrorManager, error_manager, get_error_manager
from .framework_feature_manager import framework_feature_manager
from .framework_feature import FrameworkFeature
from .terminal_filesystem_utils import (
    prepare_command_environment,
    expand_variables,
    handle_env_command
)
from .tool_installer import (
    detect_environment,
    check_tool_installed,
    install_tool_via_apt,
    install_multiple_tools,
    install_common_devtools,
    ensure_tool_available,
    get_install_command,
    get_latest_version,
    get_download_url
)

LOG_RECORDS_FETCHED = False

# Get the directory of the google-api-gen-2 directory
gen_api_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CENTRAL_CONFIG_FILE = os.path.join(gen_api_dir, "default_framework_config.json")

__all__ = [
    'log_function_call',
    'set_runtime_id',
    'clear_log_file',
    'apply_decorators',
    'TestDocstringStructure',
    'run_tests_for_package',
    'merge_csv_reports',
    'handle_api_errors',
    'ErrorSimulator',
    'log_complexity',
    'resolve_function_import',
    'LOG_RECORDS_FETCHED', 
    'MutationManager',
    'AuthenticationManager',
    'ErrorManager',
    'auth_manager',
    'get_auth_manager',
    'error_manager',
    'get_error_manager',
    'FrameworkFeature',
    'framework_feature_manager',
    'prepare_command_environment',
    'expand_variables',
    'handle_env_command',
    'detect_environment',
    'check_tool_installed',
    'install_tool_via_apt',
    'install_multiple_tools',
    'install_common_devtools',
    'ensure_tool_available',
    'get_install_command',
    'get_latest_version',
    'get_download_url'
    'validate_schema_fc_checkers',
] 
