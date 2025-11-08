"""Gemini-CLI shell tool implementations.

This module provides the main shell API functions for executing commands
in the simulated workspace environment with all advanced features from terminal.
"""
from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

from typing import Dict, Any, Optional, List, Union
import os
import platform
import subprocess
import time
import uuid
import shutil
import tempfile
import copy  # deep copy for state snapshot
import logging
import inspect

from .SimulationEngine.db import DB
from common_utils.log_complexity import log_complexity
from .SimulationEngine.custom_errors import (
    InvalidInputError, 
    WorkspaceNotAvailableError,
    CommandExecutionError,
    ShellSecurityError,
    ProcessNotFoundError,
    MetadataError
)
from .SimulationEngine.utils import (
    validate_command_security,
    dehydrate_db_to_directory,
    update_db_file_system_from_temp,
    get_shell_command,
    _normalize_path_for_db,
    resolve_target_path_for_cd,
    conditional_common_file_system_wrapper,
    conditional_common_file_system_wrapper,
    collect_pre_command_metadata_state,
    collect_post_command_metadata_state,
    preserve_unchanged_change_times
)
from common_utils import (
    prepare_command_environment,
    expand_variables,
    handle_env_command,
    session_manager
)
from .SimulationEngine.file_utils import _is_within_workspace

# --- Logger Setup for this shell_api.py module ---
logger = logging.getLogger(__name__)

def _log_shell_message(level: int, message: str, exc_info: bool = False) -> None:
    """Logs a message with caller info (function:lineno) from within this module."""
    log_message = message
    try:
        # Get the frame of the function within shell_api.py that called this helper.
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        if caller_frame and caller_frame.f_code:
            func_name = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            log_message = f"{func_name}:{line_no} - {message}"
    except Exception: # Fallback if frame inspection fails.
        pass

    # Log using the standard levels; defaults to DEBUG.
    if level == logging.ERROR: logger.error(log_message, exc_info=exc_info)
    elif level == logging.WARNING: logger.warning(log_message, exc_info=exc_info)
    elif level == logging.INFO: logger.info(log_message)
    else: logger.debug(log_message)


# --- Session State for Persistent Sandbox ---
# Note: Session state is now managed by common_utils.session_manager
# These local variables are kept for backward compatibility but delegate to shared state
SESSION_SANDBOX_DIR: Optional[str] = None
SESSION_INITIALIZED: bool = False
_SANDBOX_TEMP_DIR_OBJ: Optional[tempfile.TemporaryDirectory] = None
# -----------------------------------------


def end_session() -> Dict[str, Any]:
    """
    Ends the current terminal session, syncs file changes, and cleans up the sandbox.

    This function should be called when a series of terminal commands is complete.
    It synchronizes any modifications made in the persistent sandbox environment
    back to the in-memory database and then removes the temporary sandbox directory.

    Note: This now delegates to the shared session manager, which coordinates
    cleanup across all terminal-like APIs (cursor, gemini_cli, terminal).

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome of the session cleanup.
    """
    global SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ

    _log_shell_message(logging.INFO, "Requesting shared session cleanup via session_manager...")
    
    # Delegate to shared session manager
    # Need to wrap update_db_file_system_from_temp to match expected signature
    def update_func_wrapper(temp_root, original_state, workspace_root, command):
        return update_db_file_system_from_temp(
            DB, temp_root, original_state, workspace_root, 
            preserve_metadata=True, command=command
        )
    
    result = session_manager.end_shared_session(
        api_name="gemini_cli",
        db_instance=DB,
        update_func=update_func_wrapper,
        normalize_path_func=_normalize_path_for_db
    )
    
    # Update local state to reflect shared state
    SESSION_SANDBOX_DIR = None
    SESSION_INITIALIZED = False
    _SANDBOX_TEMP_DIR_OBJ = None
    
    _log_shell_message(
        logging.INFO if result['success'] else logging.ERROR,
        f"Session cleanup result: {result['message']}"
    )
    
    return result


# Shell execution constants
DEFAULT_COMMAND_TIMEOUT = 60  # seconds
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB
OUTPUT_UPDATE_INTERVAL = 1.0  # seconds

@log_complexity
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'run_shell_command',
        'description': """ Execute a shell command in the workspace environment with all advanced features.
        
        This function executes shell commands with proper security validation,
        process management, and workspace integration. Commands are executed
        in a temporary environment that mirrors the workspace state.
        
        IMPORTANT: For any command that expects user interaction or uses a pager
        (like git diff, git log, less, head, tail, more, etc.), you MUST append
        ' | cat' to the command string yourself before passing it to this function.
        Failure to do so will cause the command to hang or fail.
        
        """,
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The shell command to execute. Must be a valid shell command.'
                },
                'description': {
                    'type': 'string',
                    'description': "Brief description of the command's purpose."
                },
                'directory': {
                    'type': 'string',
                    'description': """ Directory to execute the command in, relative to
                    workspace root. If not provided, uses current working directory. """
                },
                'background': {
                    'type': 'boolean',
                    'description': """ Whether to run the command in background.
                    Background commands return immediately with a process ID. """
                }
            },
            'required': [
                'command'
            ]
        }
    }
)
def run_shell_command(
    command: str,
    *,
    description: Optional[str] = None,
    directory: Optional[str] = None,
    background: Optional[bool] = False
) -> Dict[str, Any]:
    """Execute a shell command in the workspace environment with all advanced features.
    
    This function executes shell commands with proper security validation,
    process management, and workspace integration. Commands are executed
    in a temporary environment that mirrors the workspace state.
    
    IMPORTANT: For any command that expects user interaction or uses a pager
    (like git diff, git log, less, head, tail, more, etc.), you MUST append
    ' | cat' to the command string yourself before passing it to this function.
    Failure to do so will cause the command to hang or fail.
    
    Args:
        command (str): The shell command to execute. Must be a valid shell command.
        description (Optional[str]): Brief description of the command's purpose.
        directory (Optional[str]): Directory to execute the command in, relative to
            workspace root. If not provided, uses current working directory.
        background (Optional[bool]): Whether to run the command in background.
            Background commands return immediately with a process ID.
            
    Returns:
        Dict[str, Any]: Dictionary containing execution results:
            - command (str): The executed command
            - directory (str): Directory where command was executed
            - stdout (str): Standard output from the command
            - stderr (str): Standard error from the command
            - returncode (Optional[int]): Exit code (None for background processes)
            - pid (Optional[int]): OS process ID (None for foreground commands)
            - process_group_id (Optional[str]): Process group ID (same as pid for background)
            - signal (Optional[str]): Signal that terminated the process (currently always None)
            - message (str): Human-readable status message
            
    Raises:
        InvalidInputError: If command or parameters are invalid.
        WorkspaceNotAvailableError: If workspace is not properly configured.
        ShellSecurityError: If command is blocked for security reasons.
        CommandExecutionError: If command execution fails.
        MetadataError: If metadata operations fail in strict mode.
    """
    # Use global DB state and session variables
    global DB, SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ

    # Initialize result dict with all required keys
    result_dict: Dict[str, Any] = {
        'command': command,
        'directory': "",
        'stdout': "", 
        'stderr': "", 
        'returncode': None, 
        'pid': None,
        'process_group_id': None,
        'signal': None,
        'message': "Initialization error."
    }

    # Parameter validation
    if not isinstance(command, str):
        raise InvalidInputError("'command' must be a string")
    
    if not command.strip():
        raise InvalidInputError("'command' cannot be empty")
    
    if description is not None and not isinstance(description, str):
        raise InvalidInputError("'description' must be a string or None")
        
    if background is not None and not isinstance(background, bool):
        raise InvalidInputError("'background' must be a boolean or None")
    
    # Set defaults
    background = background if background is not None else False
    
    # --- Get current workspace root and CWD ---
    current_workspace_root = DB.get("workspace_root")
    if not current_workspace_root:
        result_dict['message'] = "Operation failed: workspace_root is not configured."
        _log_shell_message(logging.ERROR, result_dict['message'])
        raise WorkspaceNotAvailableError(result_dict['message'])

    # --- Initialize Persistent Sandbox on First Run ---
    # Use shared session manager to coordinate sandbox across all terminal-like APIs
    shared_session_info = session_manager.get_shared_session_info()
    
    if not shared_session_info["initialized"] or not shared_session_info["exists"]:
        try:
            _log_shell_message(logging.INFO, "Initializing shared sandbox session via session_manager...")
            SESSION_SANDBOX_DIR = session_manager.initialize_shared_session(
                api_name="gemini_cli",
                workspace_root=current_workspace_root,
                db_instance=DB,
                dehydrate_func=dehydrate_db_to_directory
            )
            SESSION_INITIALIZED = True
            _log_shell_message(logging.INFO, f"Shared sandbox initialized at: {SESSION_SANDBOX_DIR}")
        except Exception as e:
            _log_shell_message(logging.ERROR, f"Failed to initialize shared sandbox: {e}", exc_info=True)
            raise CommandExecutionError(f"Failed to set up the execution environment: {e}")
    else:
        # Reuse existing shared sandbox created by another API
        SESSION_SANDBOX_DIR = shared_session_info["sandbox_dir"]
        SESSION_INITIALIZED = True
        _log_shell_message(
            logging.INFO, 
            f"Reusing existing sandbox from '{shared_session_info['active_api']}': {SESSION_SANDBOX_DIR}"
        )
    # -------------------------------------------------

    # Normalize paths for internal use
    current_workspace_root_norm = _normalize_path_for_db(current_workspace_root)
    current_cwd_norm = _normalize_path_for_db(DB.get("cwd", current_workspace_root_norm))
    
    # Handle directory parameter (validation + resolution)
    if directory is not None:
        # Validate type and ensure it's relative to workspace root
        if not isinstance(directory, str):
            raise InvalidInputError("'directory' must be a string or None")
        if os.path.isabs(directory):
            raise InvalidInputError("'directory' must be relative to workspace root")

        # Resolve the target directory
        target_dir = os.path.join(current_workspace_root_norm, directory)
        target_dir_norm = _normalize_path_for_db(target_dir)
        
        # Check if directory exists in file system
        file_system = DB.get("file_system", {})
        if target_dir_norm not in file_system or not file_system[target_dir_norm].get("is_directory", False):
            raise InvalidInputError(f"Directory '{directory}' does not exist in workspace")
        
        # Use the target directory for execution
        execution_cwd = target_dir_norm
    else:
        # Use current working directory
        execution_cwd = current_cwd_norm
    
    # Update directory in result
    result_dict['directory'] = execution_cwd
    
    validate_command_security(command)

    # --- Handle internal commands ---
    stripped_command = command.strip()

    # Handle environment variable commands
    if stripped_command in ('env',) or stripped_command.startswith(('export ', 'unset ')):
        env_result = handle_env_command(stripped_command, DB)
        # Ensure all required keys are present
        for key in ['command', 'directory', 'stdout', 'stderr', 'returncode', 'pid', 'process_group_id', 'signal', 'message']:
            if key not in env_result:
                env_result[key] = result_dict[key] if key in result_dict else (None if key in ['pid', 'returncode'] else "")
        return env_result

    # Handle cd and pwd as before
    # Only handle simple cd commands internally (not compound commands with &&, ||, ;, |)
    is_simple_cd = (stripped_command == "cd" or stripped_command.startswith("cd ")) and \
                   not any(op in command for op in ['&&', '||', ';', '|'])
    
    if is_simple_cd:
        _log_shell_message(logging.INFO, f"Handling internal 'cd': {command}")
        parts = stripped_command.split(maxsplit=1)
        target_arg = parts[1] if len(parts) > 1 else "/" # Default 'cd' target

        # Resolve target path within the workspace
        new_cwd_path = resolve_target_path_for_cd(
            current_cwd_norm,
            target_arg,
            current_workspace_root_norm,
            DB.get("file_system", {})
        )
        if new_cwd_path:
            DB["cwd"] = new_cwd_path # Update current working directory state
            result_dict['directory'] = _normalize_path_for_db(DB.get('cwd'))
            result_dict['message'] = f"Current directory changed to {result_dict['directory']}"
            result_dict['returncode'] = 0
            return result_dict
        else:
            result_dict['message'] = f"cd: Failed to change directory to '{target_arg}'. Path may be invalid or outside workspace."
            result_dict['stderr'] = f"cd: '{target_arg}': No such directory"
            result_dict['returncode'] = 1
            _log_shell_message(logging.WARNING, result_dict['message'])
            return result_dict  # Return error result instead of raising exception

    if stripped_command == "pwd":
        _log_shell_message(logging.INFO, "Handling internal 'pwd'")
        pwd_path = _normalize_path_for_db(DB.get('cwd', current_workspace_root_norm))
        result_dict['message'] = f"Current directory: {pwd_path}"
        result_dict['stdout'] = pwd_path # Output path to stdout
        result_dict['returncode'] = 0
        return result_dict
    # --- End internal command handling ---

    # --- Prepare for external command execution ---
    if not SESSION_SANDBOX_DIR:
        raise CommandExecutionError("Session sandbox is not initialized. Cannot execute external commands.")

    process_executed_without_launch_error = False
    command_message = ""

    # Preserve current workspace state before potential modifications
    original_filesystem_state = DB.get("file_system", {}).copy()
    # current_workspace_root_norm and current_cwd_norm are already captured

    try:
        exec_env_root = SESSION_SANDBOX_DIR
        _log_shell_message(logging.INFO, f"Using persistent sandbox for execution: {exec_env_root}")

        # Sync any new files from DB to sandbox before command execution
        # This handles cases where tests add files directly to DB
        for db_path, db_entry in DB.get("file_system", {}).items():
            if db_path.startswith(current_workspace_root_norm):
                rel_path = os.path.relpath(db_path, current_workspace_root_norm) if db_path != current_workspace_root_norm else '.'
                sandbox_path = os.path.join(exec_env_root, rel_path)
                
                # If file exists in DB but not in sandbox, create it
                if not os.path.exists(sandbox_path):
                    try:
                        if db_entry.get("is_directory"):
                            os.makedirs(sandbox_path, exist_ok=True)
                            if "metadata" in db_entry:
                                from .SimulationEngine.utils import _apply_file_metadata
                                _apply_file_metadata(sandbox_path, db_entry["metadata"], strict_mode=False)
                        else:
                            # Create parent directory if needed
                            parent_dir = os.path.dirname(sandbox_path)
                            if parent_dir and not os.path.exists(parent_dir):
                                os.makedirs(parent_dir, exist_ok=True)
                            
                            # Write file content
                            content_lines = db_entry.get("content_lines", [])
                            with open(sandbox_path, 'w', encoding='utf-8') as f:
                                f.writelines(content_lines)
                            
                            # Apply metadata if available
                            if "metadata" in db_entry:
                                from .SimulationEngine.utils import _apply_file_metadata
                                _apply_file_metadata(sandbox_path, db_entry["metadata"], strict_mode=False)
                    except Exception as e:
                        _log_shell_message(logging.WARNING, f"Failed to sync {db_path} to sandbox: {e}")

        pre_command_state_temp = collect_pre_command_metadata_state(
            DB.get("file_system", {}),
            exec_env_root,
            current_workspace_root_norm
        )

        # Determine the correct CWD within the execution environment
        if execution_cwd.startswith(current_workspace_root_norm):
            relative_cwd = os.path.relpath(execution_cwd, current_workspace_root_norm)
        else:
            # Fallback if CWD was somehow outside root
            _log_shell_message(logging.WARNING, f"Current directory '{execution_cwd}' is outside workspace root '{current_workspace_root_norm}'. Using environment root for command.")
            relative_cwd = "."

        # Construct the path for the subprocess CWD
        subprocess_cwd_physical = _normalize_path_for_db(os.path.join(exec_env_root, relative_cwd))

        # Verify the execution CWD exists
        if not os.path.isdir(subprocess_cwd_physical):
            _log_shell_message(logging.WARNING, f"Execution environment CWD '{subprocess_cwd_physical}' does not exist. Creating directory structure.")
            # Create the missing directory structure
            try:
                os.makedirs(subprocess_cwd_physical, exist_ok=True)
                _log_shell_message(logging.INFO, f"Created missing directory: {subprocess_cwd_physical}")
            except Exception as e:
                _log_shell_message(logging.ERROR, f"Failed to create directory '{subprocess_cwd_physical}': {e}")
                # Fall back to using the temp directory root
                subprocess_cwd_physical = exec_env_root
                if not os.path.isdir(subprocess_cwd_physical):
                    _log_shell_message(logging.ERROR, f"Even temp directory root '{exec_env_root}' does not exist!")
                    raise CommandExecutionError(f"Execution environment setup failed: temp directory '{exec_env_root}' does not exist")

        # Create any missing parent directories for output redirection
        try:
            from .SimulationEngine.utils import _extract_last_unquoted_redirection_target
            redir_target = _extract_last_unquoted_redirection_target(command.strip())
        except Exception:
            redir_target = None
        if redir_target:
            output_file = redir_target
            # Convert relative path to absolute
            if not os.path.isabs(output_file):
                output_file = os.path.join(subprocess_cwd_physical, output_file)
            # Create parent directory if needed
            parent_dir = os.path.dirname(output_file)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    _log_shell_message(logging.INFO, f"Created parent directory for output redirection: {parent_dir}")
                except Exception as e:
                    _log_shell_message(logging.ERROR, f"Failed to create parent directory '{parent_dir}': {e}")
                    raise CommandExecutionError(f"Failed to create parent directory for output redirection: {e}")

        _log_shell_message(logging.INFO, f"Executing command '{command}' in CWD '{subprocess_cwd_physical}' (Background: {background})")

        # Prepare environment and expand variables
        cmd_env = prepare_command_environment(DB, subprocess_cwd_physical, execution_cwd)
        # Apply gemini_cli-specific shell_config overrides
        shell_config = DB.get('shell_config', {})
        config_env = shell_config.get('environment_variables', {})
        if config_env:
            cmd_env.update(config_env)

        # Don't expand variables in the command string, let bash handle it
        expanded_command = command.strip()
        
        # Check for and fix tar commands that create archives in the same directory
        from .SimulationEngine.utils import detect_and_fix_tar_command
        expanded_command = detect_and_fix_tar_command(expanded_command, subprocess_cwd_physical)

        if not expanded_command:
            result_dict['message'] = "Operation failed: Command string is empty."
            _log_shell_message(logging.ERROR, result_dict['message'])
            raise InvalidInputError(result_dict['message'])

        # --- Execute the command ---
        process_obj: Union[subprocess.Popen, subprocess.CompletedProcess, None] = None
        
        # Get platform-specific shell command
        shell_cmd = get_shell_command(expanded_command)
        
        if background:
            try:
                # Launch background process with environment
                with open(os.devnull, 'wb') as devnull:
                    process_obj = subprocess.Popen(
                        shell_cmd,
                        cwd=subprocess_cwd_physical,
                        stdout=devnull,
                        stderr=devnull,
                        env=cmd_env,
                        text=True
                    )
                process_executed_without_launch_error = True
                result_dict['pid'] = process_obj.pid
                result_dict['process_group_id'] = str(process_obj.pid)
                result_dict['returncode'] = None
                command_message = f"Command '{command}' launched successfully in background (PID: {process_obj.pid})."
            except FileNotFoundError:
                command_message = f"Launch failed: Command not found."
                _log_shell_message(logging.ERROR, command_message)
                result_dict['message'] = command_message
                result_dict['returncode'] = 127
                raise CommandExecutionError(result_dict['message'])
            except Exception as e:
                command_message = f"Launch failed for background process '{command}': {type(e).__name__} - {e}"
                _log_shell_message(logging.ERROR, command_message, exc_info=True)
                result_dict['message'] = command_message
                result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])
        else: # Foreground execution
            try:
                # Run foreground process with environment
                process_obj = subprocess.run(
                    shell_cmd,
                    cwd=subprocess_cwd_physical,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False,
                    env=cmd_env,
                    timeout=DEFAULT_COMMAND_TIMEOUT
                )
                process_executed_without_launch_error = True
                command_message = f"Command completed with exit code {process_obj.returncode}."
                result_dict['stdout'] = process_obj.stdout
                result_dict['stderr'] = process_obj.stderr
                result_dict['returncode'] = process_obj.returncode
                if process_obj.returncode != 0:
                    # Restore workspace state before raising, and include both streams in the error message
                    _log_shell_message(logging.WARNING, f"Command '{command}' failed with exit code {process_obj.returncode}. Restoring pre-execution workspace state.")
                    DB["workspace_root"] = current_workspace_root_norm
                    DB["cwd"] = current_cwd_norm
                    DB["file_system"] = original_filesystem_state
                    stderr_text = process_obj.stderr or ""
                    stdout_text = process_obj.stdout or ""
                    detailed_message = (
                        f"Command failed with exit code {process_obj.returncode}.\n"
                        f"--- STDOUT ---\n{stdout_text}\n"
                        f"--- STDERR ---\n{stderr_text}"
                    )
                    result_dict['message'] = detailed_message
                    raise CommandExecutionError(detailed_message)
            except subprocess.TimeoutExpired:
                raise CommandExecutionError(f"Command timed out after {DEFAULT_COMMAND_TIMEOUT} seconds")
            except FileNotFoundError:
                command_message = f"Execution failed: Command not found."
                _log_shell_message(logging.ERROR, command_message)
                result_dict['message'] = command_message
                result_dict['returncode'] = 127
                raise CommandExecutionError(result_dict['message'])
            except Exception as e:
                command_message = f"Execution failed for foreground process '{command}': {type(e).__name__} - {e}"
                _log_shell_message(logging.ERROR, command_message, exc_info=True)
                result_dict['message'] = command_message
                if result_dict.get('returncode') is None: result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])

        # --- Post-execution state update ---
        if process_executed_without_launch_error:
            _log_shell_message(logging.INFO, f"Command '{command}' execution finished. Updating workspace state.")
            try:
                post_command_state_temp = collect_post_command_metadata_state(
                    DB.get("file_system", {}),
                    exec_env_root,
                    current_workspace_root_norm
                )
                
                # Update the main workspace state from the execution environment
                update_db_file_system_from_temp(
                    DB,
                    exec_env_root,
                    original_filesystem_state,
                    current_workspace_root_norm,
                    command=command
                )

                # Preserve original change_time for files that didn't actually change during command execution
                preserve_unchanged_change_times(
                    DB.get("file_system", {}),
                    pre_command_state_temp,
                    post_command_state_temp,
                    original_filesystem_state,
                    current_workspace_root_norm,
                    exec_env_root
                )
            except MetadataError as me:
                # Handle metadata operation failures in strict mode
                result_dict['message'] = f"Command failed: {str(me)}"
                result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])

            # Determine final success status
            if background:
                if result_dict['pid'] is not None:
                    result_dict['message'] = command_message + " Workspace state updated."
            else:
                if result_dict['returncode'] is not None and isinstance(process_obj, subprocess.CompletedProcess):
                    result_dict['message'] = command_message + " Workspace state updated."
                    if process_obj.returncode != 0:
                        result_dict['message'] += f" (Note: Non-zero exit code {process_obj.returncode})."
        else:
            # Command failed to launch; restore pre-execution state
            _log_shell_message(logging.WARNING, f"Command '{command}' failed to launch. Restoring pre-execution workspace state.")
            DB["workspace_root"] = current_workspace_root_norm
            DB["cwd"] = current_cwd_norm
            DB["file_system"] = original_filesystem_state

    except PermissionError as e:
        # Errors related to execution environment setup/cleanup
        _log_shell_message(logging.ERROR, f"Execution environment error: {type(e).__name__} - {e}", exc_info=True)
        additional_msg = f" Error managing execution environment ({type(e).__name__})."
        result_dict['message'] = (result_dict.get('message') or f"Operation failed (environment error: {type(e).__name__})") + additional_msg
        if result_dict.get('returncode') is None: result_dict['returncode'] = 1
        raise CommandExecutionError(result_dict['message'])
    except CommandExecutionError as ce:
        # Preserve detailed command outputs without re-wrapping
        raise ce
    except Exception as e:
         # Catch-all for other unexpected errors
        _log_shell_message(logging.ERROR, f"Unexpected error during command execution phase for '{command}': {type(e).__name__} - {e}", exc_info=True)
        result_dict['message'] = f"Operation failed unexpectedly: {type(e).__name__} - {e}"
        if result_dict.get('returncode') is None: result_dict['returncode'] = 1

        # Attempt emergency state restoration
        _log_shell_message(logging.INFO, "Attempting emergency restoration of workspace state.")
        DB["workspace_root"] = current_workspace_root_norm
        DB["cwd"] = current_cwd_norm
        DB["file_system"] = original_filesystem_state
        raise CommandExecutionError(result_dict['message'])
    finally:
        # Cleanup is now handled by end_session(), so we no longer clean up the temp dir here.
        _log_shell_message(logging.DEBUG, "Command execution block finished. Sandbox cleanup is deferred to end_session().")

        # Final state restoration safeguard
        if DB.get("cwd") != current_cwd_norm:
            _log_shell_message(logging.WARNING, f"Restoring CWD to '{current_cwd_norm}' (was '{DB.get('cwd')}').")
            DB["cwd"] = current_cwd_norm
        if DB.get("workspace_root") != current_workspace_root_norm:
             _log_shell_message(logging.WARNING, f"Restoring workspace_root to '{current_workspace_root_norm}' (was '{DB.get('workspace_root')}').")
             DB["workspace_root"] = current_workspace_root_norm

        _log_shell_message(logging.DEBUG, f"run_shell_command finished. Final CWD='{DB.get('cwd')}'")

    # Consistency check
    if result_dict.get('pid') is not None and result_dict.get('returncode') is not None:
        _log_shell_message(logging.WARNING, "Result indicates both background (pid) and foreground (returncode) execution.")

    return result_dict

