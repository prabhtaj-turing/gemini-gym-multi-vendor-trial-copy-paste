from common_utils.tool_spec_decorator import tool_spec
import os
import logging
from typing import Any, Dict, Optional, Union  # Common type hints
import tempfile
import subprocess
import shlex
import inspect
from pathlib import Path
import shutil

# Import the DB object and utility functions
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import CommandExecutionError
from .SimulationEngine import utils
from .SimulationEngine.custom_errors import MetadataError
from .SimulationEngine.utils import with_common_file_system  # Import the decorator

# Import the environment manager
from common_utils import (
    prepare_command_environment,
    expand_variables,
    handle_env_command,
    session_manager
)

# --- Logger Setup for this __init__.py module ---
# Get a logger instance specific to this top-level module.
logger = logging.getLogger(__name__) # Will typically be 'terminal' if run as package

def _log_init_message(level: int, message: str, exc_info: bool = False) -> None:
    """Logs a message with caller info (function:lineno) from within this module."""
    log_message = message
    try:
        # Get the frame of the function within __init__.py that called this helper.
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

def _realpath_or_original(path: str) -> str:
    """Return os.path.realpath(path) when possible, otherwise the original path."""
    try:
        return os.path.realpath(path)
    except (OSError, TypeError):
        return path


def _is_within_directory(path: str, root: str) -> bool:
    """Return True when path is within root (after realpath normalization)."""
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


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

    _log_init_message(logging.INFO, "Requesting shared session cleanup via session_manager...")
    
    # Delegate to shared session manager
    result = session_manager.end_shared_session(
        api_name="terminal",
        db_instance=DB,
        update_func=utils.update_db_file_system_from_temp,
        normalize_path_func=utils._normalize_path_for_db
    )
    
    # Update local state to reflect shared state
    SESSION_SANDBOX_DIR = None
    SESSION_INITIALIZED = False
    _SANDBOX_TEMP_DIR_OBJ = None
    
    _log_init_message(
        logging.INFO if result['success'] else logging.ERROR,
        f"Session cleanup result: {result['message']}"
    )
    
    return result


# --- Function Implementations ---
@with_common_file_system
@tool_spec(
    spec={
        'name': 'run_command',
        'description': """ Executes the provided terminal command in the current workspace context.
        
        Use this function to run shell commands. You need to provide the exact
        command string to be executed. Note that commands like 'cd', 'pwd', and
        environment commands ('export', 'unset', 'env') are handled internally;
        other commands are executed externally and may modify the workspace files.
        
        IMPORTANT: For any command that expects user interaction or uses a pager
        (like git diff, git log, less, more, etc.), you MUST append
        ' | cat' to the command string yourself before passing it to this function.
        Failure to do so will cause the command to hang or fail.
        
        For commands that are intended to run for a long time or indefinitely
        (e.g., starting a server, running a watch process), set the
        `is_background` parameter to True. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': """ The exact terminal command string to execute. Remember
                    to append ' | cat' for interactive/pager commands. """
                },
                'is_background': {
                    'type': 'boolean',
                    'description': """ Set to True to run the command as a
                    background process (e.g., for servers or watchers). Defaults to False,
                    running the command in the foreground and waiting for completion. """
                }
            },
            'required': [
                'command'
            ]
        }
    }
)
def run_command(command: str, is_background: bool = False) -> Dict[str, Any]:
    """Executes the provided terminal command in the current workspace context.

    Use this function to run shell commands. You need to provide the exact
    command string to be executed. Note that commands like 'cd', 'pwd', and
    environment commands ('export', 'unset', 'env') are handled internally;
    other commands are executed externally and may modify the workspace files.

    IMPORTANT: For any command that expects user interaction or uses a pager
    (like git diff, git log, less, more, etc.), you MUST append
    ' | cat' to the command string yourself before passing it to this function.
    Failure to do so will cause the command to hang or fail.

    For commands that are intended to run for a long time or indefinitely
    (e.g., starting a server, running a watch process), set the
    `is_background` parameter to True.

    Args:
        command (str): The exact terminal command string to execute. Remember
                       to append ' | cat' for interactive/pager commands.
        is_background (bool, optional): Set to True to run the command as a
            background process (e.g., for servers or watchers). Defaults to False,
            running the command in the foreground and waiting for completion.

    Returns:
        Dict[str, Any]: A dictionary describing the outcome:
            - 'message' (str): A status message about the execution.
            - 'stdout' (str): Captured standard output (foreground only).
            - 'stderr' (str): Captured standard error (foreground only).
            - 'returncode' (Optional[int]): The command's exit code
                                           (foreground only).
            - 'pid' (Optional[int]): The process ID if run in the background.

    Raises:
        ValueError: If workspace_root is not configured or the command string is empty/invalid.
        CommandExecutionError: If a command fails to launch, `cd` fails, or a foreground command returns a non-zero exit code.
    """
    # Use global DB state and session variables
    global DB, utils, SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ

    result_dict: Dict[str, Any] = {
        'message': "Initialization error.",
        'stdout': "", 'stderr': "", 'returncode': None, 'pid': None
    }

    # --- Get current workspace root and CWD ---
    current_workspace_root = DB.get("workspace_root")
    if not current_workspace_root:
        result_dict['message'] = "Operation failed: workspace_root is not configured."
        _log_init_message(logging.ERROR, result_dict['message'])
        raise ValueError(result_dict['message'])

    # --- Initialize Persistent Sandbox on First Run ---
    # Check three conditions to determine if we need to (re-)initialize the sandbox:
    # 1. Session not initialized yet
    # 2. Sandbox directory variable not set
    # 3. Physical directory doesn't exist (cleanup may have occurred)
    # Use shared session manager to coordinate sandbox across all terminal-like APIs
    shared_session_info = session_manager.get_shared_session_info()
    
    if not shared_session_info["initialized"] or not shared_session_info["exists"]:
        try:
            _log_init_message(logging.INFO, "Initializing shared sandbox session via session_manager...")
            SESSION_SANDBOX_DIR = session_manager.initialize_shared_session(
                api_name="terminal",
                workspace_root=current_workspace_root,
                db_instance=DB,
                dehydrate_func=utils.dehydrate_db_to_directory
            )
            SESSION_INITIALIZED = True
            _log_init_message(logging.INFO, f"Shared sandbox initialized at: {SESSION_SANDBOX_DIR}")
        except Exception as e:
            _log_init_message(logging.ERROR, f"Failed to initialize shared sandbox: {e}", exc_info=True)
            raise CommandExecutionError(f"Failed to set up the execution environment: {e}")
    else:
        # Reuse existing shared sandbox created by another API
        SESSION_SANDBOX_DIR = shared_session_info["sandbox_dir"]
        SESSION_INITIALIZED = True
        _log_init_message(
            logging.INFO, 
            f"Reusing existing sandbox from '{shared_session_info['active_api']}': {SESSION_SANDBOX_DIR}"
        )
    # -------------------------------------------------

    # Normalize paths for internal use
    current_workspace_root_norm = utils._normalize_path_for_db(current_workspace_root)
    current_cwd_norm = utils._normalize_path_for_db(DB.get("cwd", current_workspace_root_norm))

    # --- Handle internal commands ---
    stripped_command = command.strip()

    # Handle environment variable commands
    if stripped_command in ('env',) or stripped_command.startswith(('export ', 'unset ')):
        return handle_env_command(stripped_command, DB)

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
        _log_init_message(logging.INFO, f"Using persistent sandbox for execution: {exec_env_root}")
        exec_env_root_real = _realpath_or_original(exec_env_root)

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
                                utils._apply_file_metadata(sandbox_path, db_entry["metadata"], strict_mode=False)
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
                                utils._apply_file_metadata(sandbox_path, db_entry["metadata"], strict_mode=False)
                    except Exception as e:
                        _log_init_message(logging.WARNING, f"Failed to sync {db_path} to sandbox: {e}")

        pre_command_state_temp = utils.collect_pre_command_metadata_state(
            DB.get("file_system", {}),
            exec_env_root,
            current_workspace_root_norm
        )
        
        # Determine the correct CWD within the execution environment
        if current_cwd_norm.startswith(current_workspace_root_norm):
            relative_cwd = os.path.relpath(current_cwd_norm, current_workspace_root_norm)
        else:
            # Fallback if CWD was somehow outside root
            _log_init_message(logging.WARNING, f"Current directory '{current_cwd_norm}' is outside workspace root '{current_workspace_root_norm}'. Using environment root for command.")
            relative_cwd = "."

        # Construct the path for the subprocess CWD
        subprocess_cwd_physical = utils._normalize_path_for_db(os.path.join(exec_env_root, relative_cwd))
        subprocess_cwd_real = _realpath_or_original(subprocess_cwd_physical)

        # Verify the execution CWD exists
        if not os.path.isdir(subprocess_cwd_real):
            _log_init_message(logging.WARNING, f"Execution environment CWD '{subprocess_cwd_physical}' does not exist. Creating directory structure.")
            # Create the missing directory structure
            try:
                os.makedirs(subprocess_cwd_physical, exist_ok=True)
                _log_init_message(logging.INFO, f"Created missing directory: {subprocess_cwd_physical}")
            except Exception as e:
                _log_init_message(logging.ERROR, f"Failed to create directory '{subprocess_cwd_physical}': {e}")
                # Fall back to using the temp directory root
                subprocess_cwd_physical = exec_env_root
                subprocess_cwd_real = _realpath_or_original(subprocess_cwd_physical)
                if not os.path.isdir(subprocess_cwd_physical):
                    _log_init_message(logging.ERROR, f"Even temp directory root '{exec_env_root}' does not exist!")
                    raise CommandExecutionError(f"Execution environment setup failed: temp directory '{exec_env_root}' does not exist")

        # Create any missing parent directories for output redirection
        try:
            # For complex commands, disable the redirection helper to avoid race conditions.
            if '&&' in command or '||' in command or ';' in command or '\n' in command:
                 redir_target = None
            else:
                 redir_target = utils._extract_last_unquoted_redirection_target(command.strip())
        except Exception:
            redir_target = None
        if redir_target:
            output_file = redir_target
            # Only create parent directories for RELATIVE paths
            # Absolute paths (like /sumy/file.txt) will be resolved within the bash sandbox
            # and should not trigger os.makedirs on the host filesystem
            if not os.path.isabs(output_file):
                # Convert relative path to absolute within the sandbox
                output_file = os.path.join(subprocess_cwd_physical, output_file)
                # Create parent directory if needed
                parent_dir = os.path.dirname(output_file)
                if parent_dir and not os.path.exists(parent_dir):
                    try:
                        os.makedirs(parent_dir, exist_ok=True)
                        _log_init_message(logging.INFO, f"Created parent directory for output redirection: {parent_dir}")
                    except Exception as e:
                        _log_init_message(logging.ERROR, f"Failed to create parent directory '{parent_dir}': {e}")
                        raise CommandExecutionError(f"Failed to create parent directory for output redirection: {e}")
            else:
                # Absolute paths in the simulated environment need to be mapped to workspace paths
                # e.g., /sumy/file.txt -> workspace_root/sumy/file.txt
                if output_file.startswith('/') and not output_file.startswith('//'):
                    relative_target = output_file.lstrip('/')
                    workspace_root = current_workspace_root_norm
                    output_file = os.path.join(workspace_root, relative_target)
                    _log_init_message(logging.DEBUG, f"Mapped output redirection path: {redir_target} -> {output_file}")
                    
                    # Create parent directory if needed
                    parent_dir = os.path.dirname(output_file)
                    if parent_dir and not os.path.exists(parent_dir):
                        try:
                            os.makedirs(parent_dir, exist_ok=True)
                            _log_init_message(logging.INFO, f"Created parent directory for output redirection: {parent_dir}")
                        except Exception as e:
                            _log_init_message(logging.ERROR, f"Failed to create parent directory '{parent_dir}': {e}")
                            raise CommandExecutionError(f"Failed to create parent directory for output redirection: {e}")
                else:
                    # Other absolute paths will be resolved within the bash environment
                    _log_init_message(logging.DEBUG, f"Absolute output redirection path detected: {output_file} - letting bash handle it")

        _log_init_message(logging.INFO, f"Executing command '{command}' in CWD '{subprocess_cwd_physical}' (Background: {is_background})")

        # Prepare environment and expand variables
        cmd_env = prepare_command_environment(DB, subprocess_cwd_physical, current_cwd_norm)

        # Prepare command for execution
        expanded_command = command.strip()
        
        # Preprocess 'cd' commands to map absolute paths to workspace paths
        # In the simulated environment, '/' maps to workspace_root from DB
        # When user does 'cd /sumy', map to 'cd workspace_root/sumy'
        if stripped_command.startswith('cd /'):
            # Extract the cd target
            cd_parts = stripped_command.split(maxsplit=1)
            if len(cd_parts) == 2:
                cd_target = cd_parts[1]
                # Map absolute path to workspace path using DB's workspace_root
                # e.g., 'cd /sumy' becomes 'cd /home/dyouk/.../workspace/sumy'
                if cd_target.startswith('/') and not cd_target.startswith('//'):
                    # Remove leading slash to make it relative, then join with workspace root
                    relative_target = cd_target.lstrip('/')
                    workspace_root = current_workspace_root_norm
                    workspace_target = os.path.join(workspace_root, relative_target)
                    expanded_command = f"cd {workspace_target}"
                    _log_init_message(logging.DEBUG, f"Mapped cd target: {cd_target} -> {workspace_target}")
        
        # For foreground commands, append a command to get the CWD after execution.
        if not is_background:
            # Check if command contains a heredoc (<<, <<-, <<<)
            # Heredocs cannot have || appended after EOF delimiter - it breaks the syntax
            has_heredoc = any(heredoc_pattern in expanded_command for heredoc_pattern in ['<<', '<<<'])

            if has_heredoc:
                # For heredocs, we can't safely append || and the marker
                # Just run the heredoc as-is (CWD tracking will still work from the marker in non-heredoc commands)
                _log_init_message(logging.INFO, f"Heredoc detected in command - skipping marker append to preserve syntax")
            else:
                # Using a newline is safer than a semicolon for chaining.
                # Use a unique marker to easily find the path in output.
                pwd_marker = "CURS_PWD_MARKER_V1"
                # Use 'set -e' to exit on first error, and capture exit code of main command
                expanded_command = (
                    f"set -e\n"
                    f"main_exit_code=0\n"
                    f"{expanded_command} || main_exit_code=$?\n"
                    f"set +e\n"
                    f"echo \"{pwd_marker}:$(pwd)\"\n"
                    f"exit $main_exit_code"
                )
        
        # Check for and fix tar commands that create archives in the same directory
        expanded_command = utils.detect_and_fix_tar_command(expanded_command, subprocess_cwd_physical)

        if not expanded_command:
            result_dict['message'] = "Operation failed: Command string is empty."
            _log_init_message(logging.ERROR, result_dict['message'])
            raise ValueError(result_dict['message'])

        # --- Execute the command ---
        process_obj: Union[subprocess.Popen, subprocess.CompletedProcess, None] = None
        
        if is_background:
            try:
                # Launch background process with environment
                with open(os.devnull, 'wb') as devnull:
                    process_obj = subprocess.Popen(
                        ['/bin/bash', '-c', expanded_command],
                        cwd=subprocess_cwd_physical,
                        stdout=devnull,
                        stderr=devnull,
                        env=cmd_env
                    )
                process_executed_without_launch_error = True
                result_dict['pid'] = process_obj.pid
                result_dict['returncode'] = None
                command_message = f"Command '{command}' launched successfully in background (PID: {process_obj.pid})."
            except FileNotFoundError:
                command_message = f"Launch failed: Command not found."
                _log_init_message(logging.ERROR, command_message)
                result_dict['message'] = command_message; result_dict['returncode'] = 127
                raise CommandExecutionError(result_dict['message'])
            except Exception as e:
                command_message = f"Launch failed for background process '{command}': {type(e).__name__} - {e}"
                _log_init_message(logging.ERROR, command_message, exc_info=True)
                result_dict['message'] = command_message; result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])
        else: # Foreground execution
            try:
                # Run foreground process with environment
                process_obj = subprocess.run(
                    ['/bin/bash', '-c', expanded_command],
                    cwd=subprocess_cwd_physical,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False,
                    env=cmd_env
                )
                process_executed_without_launch_error = True
                command_message = f"Command completed with exit code {process_obj.returncode}."

                # --- Post-command CWD update ---
                stdout_lines = process_obj.stdout.splitlines()
                new_physical_cwd = None
                pwd_marker = "CURS_PWD_MARKER_V1"

                # Check if the last line is our marker (complete on its own line)
                # OR if the marker is concatenated to the last line (no preceding newline)
                if stdout_lines and stdout_lines[-1].startswith(f"{pwd_marker}:"):
                    new_physical_cwd = stdout_lines[-1][len(pwd_marker)+1:]
                    del stdout_lines[-1]  # Remove marker line
                elif stdout_lines and f"{pwd_marker}:" in stdout_lines[-1]:
                    # Marker is concatenated to the end of the last line
                    last_line = stdout_lines[-1]
                    marker_pos = last_line.find(f"{pwd_marker}:")
                    new_physical_cwd = last_line[marker_pos + len(pwd_marker) + 1:]
                    # Remove the marker part from the line
                    stdout_lines[-1] = last_line[:marker_pos]
                
                # Reconstruct stdout
                if not stdout_lines:
                    cleaned_stdout = ""
                else:
                    cleaned_stdout = '\n'.join(stdout_lines)
                    # Heuristic to preserve trailing newline
                    if process_obj.stdout.count('\n') > len(stdout_lines):
                        cleaned_stdout += '\n'
                
                # For pwd command, map physical sandbox path back to logical workspace path in output
                stdout_stripped = cleaned_stdout.strip()
                if stripped_command.strip() == 'pwd' and stdout_stripped:
                    stdout_real = _realpath_or_original(stdout_stripped)
                    # Replace the physical sandbox path with the logical workspace path
                    if _is_within_directory(stdout_real, exec_env_root_real):
                        relative_path = os.path.relpath(stdout_real, exec_env_root_real)
                        if relative_path == '.':
                            logical_cwd = current_workspace_root_norm
                        else:
                            logical_cwd = os.path.join(current_workspace_root_norm, relative_path)
                        cleaned_stdout = logical_cwd + '\n' if cleaned_stdout.endswith('\n') else logical_cwd
                
                result_dict['stdout'] = cleaned_stdout

                if new_physical_cwd and os.path.isdir(new_physical_cwd):
                    # Convert physical sandbox path back to logical workspace path
                    new_physical_cwd_real = _realpath_or_original(new_physical_cwd)
                    if os.path.isdir(new_physical_cwd_real) and _is_within_directory(new_physical_cwd_real, exec_env_root_real):
                        relative_new_cwd = os.path.relpath(new_physical_cwd_real, exec_env_root_real)

                        if relative_new_cwd == '.':
                            logical_new_cwd = current_workspace_root_norm
                        else:
                            logical_new_cwd = os.path.join(current_workspace_root_norm, relative_new_cwd)
                        
                        normalized_logical_cwd = utils._normalize_path_for_db(logical_new_cwd)
                        if DB.get("cwd") != normalized_logical_cwd:
                            DB["cwd"] = normalized_logical_cwd
                            _log_init_message(logging.INFO, f"run_command updated CWD to: {normalized_logical_cwd}")
                    else:
                        _log_init_message(logging.WARNING, f"Could not map new CWD '{new_physical_cwd}' back to workspace root.")
                # --- End CWD update ---

                result_dict['stderr'] = process_obj.stderr
                result_dict['returncode'] = process_obj.returncode
                if process_obj.returncode != 0:
                    _log_init_message(logging.WARNING, f"Command '{command}' failed with exit code {process_obj.returncode}. Restoring pre-execution workspace state.")
                    DB["workspace_root"] = current_workspace_root_norm
                    DB["cwd"] = current_cwd_norm
                    DB["file_system"] = original_filesystem_state
                    stderr_text = process_obj.stderr or ""
                    stdout_text = cleaned_stdout or ""
                    
                    # Check if this is a cd command and provide a more specific error message
                    if stripped_command.startswith('cd ') or stripped_command == 'cd':
                        detailed_message = f"Failed to change directory: {stripped_command}\nError: {stderr_text}"
                    else:
                        detailed_message = (
                            f"Command failed with exit code {process_obj.returncode}.\n"
                            f"--- STDOUT ---\n{stdout_text}\n"
                            f"--- STDERR ---\n{stderr_text}"
                        )
                    result_dict['message'] = detailed_message
                    raise CommandExecutionError(detailed_message)
                else:
                    pass  # Command succeeded, continue to state update

            except FileNotFoundError:
                command_message = f"Execution failed: Command not found."
                _log_init_message(logging.ERROR, command_message)
                result_dict['message'] = command_message; result_dict['returncode'] = 127
                raise CommandExecutionError(result_dict['message'])
            except Exception as e:
                command_message = f"Execution failed for foreground process '{command}': {type(e).__name__} - {e}"
                _log_init_message(logging.ERROR, command_message, exc_info=True)
                result_dict['message'] = command_message
                if result_dict.get('returncode') is None: result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])

        # --- Post-execution state update ---
        if process_executed_without_launch_error:
            _log_init_message(logging.INFO, f"Command '{command}' execution finished. Updating workspace state.")
            try:
                post_command_state_temp = utils.collect_post_command_metadata_state(
                    DB.get("file_system", {}),
                    exec_env_root,
                    current_workspace_root_norm
                )
                
                # Update the main workspace state from the execution environment
                utils.update_db_file_system_from_temp(
                    exec_env_root,
                    original_filesystem_state,
                    current_workspace_root_norm,
                    command=command
                )

                # Preserve original change_time for files that didn't actually change during command execution
                utils.preserve_unchanged_change_times(
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
            if is_background:
                if result_dict['pid'] is not None:
                    result_dict['message'] = command_message + " Workspace state updated."
            else:
                if result_dict['returncode'] is not None and isinstance(process_obj, subprocess.CompletedProcess):
                    # Success if zero exit or policy allows this non-zero code
                    if process_obj.returncode == 0:
                        result_dict['success'] = True
                    else:
                        result_dict['success'] = utils.common_utils.should_treat_nonzero_as_success(command, process_obj.returncode)
                    result_dict['message'] = command_message + " Workspace state updated."
                    if process_obj.returncode != 0 and not utils.common_utils.should_treat_nonzero_as_success(command, process_obj.returncode):
                        result_dict['message'] += f" (Note: Non-zero exit code {process_obj.returncode})."
        else:
            # Command failed to launch; restore pre-execution state
            _log_init_message(logging.WARNING, f"Command '{command}' failed to launch. Restoring pre-execution workspace state.")
            DB["workspace_root"] = current_workspace_root_norm
            DB["cwd"] = current_cwd_norm
            DB["file_system"] = original_filesystem_state

    except PermissionError as e:
        # Errors related to execution environment setup/cleanup
        _log_init_message(logging.ERROR, f"Execution environment error: {type(e).__name__} - {e}", exc_info=True)
        additional_msg = f" Error managing execution environment ({type(e).__name__})."
        result_dict['message'] = (result_dict.get('message') or f"Operation failed (environment error: {type(e).__name__})") + additional_msg
        if result_dict.get('returncode') is None: result_dict['returncode'] = 1
        raise CommandExecutionError(result_dict['message'])
    except CommandExecutionError as ce:
        # Preserve detailed command outputs without re-wrapping
        raise ce
    except Exception as e:
         # Catch-all for other unexpected errors
        _log_init_message(logging.ERROR, f"Unexpected error during command execution phase for '{command}': {type(e).__name__} - {e}", exc_info=True)
        result_dict['message'] = f"Operation failed unexpectedly: {type(e).__name__} - {e}"
        if result_dict.get('returncode') is None: result_dict['returncode'] = 1

        # Attempt emergency state restoration
        _log_init_message(logging.INFO, "Attempting emergency restoration of workspace state.")
        DB["workspace_root"] = current_workspace_root_norm
        DB["cwd"] = current_cwd_norm
        DB["file_system"] = original_filesystem_state
        raise CommandExecutionError(result_dict['message'])

    finally:
        # Cleanup is now handled by end_session(), so we no longer clean up the temp dir here.
        _log_init_message(logging.DEBUG, "Command execution block finished. Sandbox cleanup is deferred to end_session().")

        _log_init_message(logging.DEBUG, f"run_command finished. Final CWD='{DB.get('cwd')}'")

    # Consistency check
    if result_dict.get('pid') is not None and result_dict.get('returncode') is not None:
        _log_init_message(logging.WARNING, "Result indicates both background (pid) and foreground (returncode) execution.")

    # Add 'success' field for backward compatibility
    # Success is determined by returncode == 0 for foreground commands
    if result_dict.get('returncode') is not None:
        result_dict['success'] = result_dict['returncode'] == 0
    elif result_dict.get('pid') is not None:
        # For background processes, consider them successful if they launched
        result_dict['success'] = True
    else:
        # Default to False if we can't determine success
        result_dict['success'] = False

    return result_dict
