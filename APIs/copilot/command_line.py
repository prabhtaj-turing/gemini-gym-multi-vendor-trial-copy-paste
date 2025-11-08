from common_utils.tool_spec_decorator import tool_spec
from common_utils.terminal_filesystem_utils import prepare_command_environment, handle_env_command
from common_utils import session_manager
import os
import re
import logging
import warnings
import tempfile
import subprocess
import inspect
import shutil
from typing import Any, Dict, List, Optional, Union

# Import DB from SimulationEngine (this stays as it's Copilot-specific)
from .SimulationEngine.db import DB
from .SimulationEngine import utils, custom_errors

FOREGROUND_COMMAND_TIMEOUT_SECONDS = 120
logger = logging.getLogger(__name__)

# --- Session State for Persistent Sandbox ---
# Note: Session state is now managed by common_utils.session_manager
# These local variables are kept for backward compatibility but delegate to shared state
SESSION_SANDBOX_DIR: Optional[str] = None
SESSION_INITIALIZED: bool = False
_SANDBOX_TEMP_DIR_OBJ: Optional[tempfile.TemporaryDirectory] = None
# -----------------------------------------

# It's assumed you have this helper function in the same file
def _log_init_message(level: int, message: str, exc_info: bool = False) -> None:
    log_message = message
    try:
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        if caller_frame and caller_frame.f_code:
            func_name = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            log_message = f"{func_name}:{line_no} - {message}"
    except Exception:
        pass
    if level == logging.ERROR: logger.error(log_message, exc_info=exc_info)
    elif level == logging.WARNING: logger.warning(log_message, exc_info=exc_info)
    elif level == logging.INFO: logger.info(log_message)
    else: logger.debug(log_message)


def end_session() -> Dict[str, Any]:
    """
    Ends the current terminal session, syncs file changes, and cleans up the sandbox.

    This function should be called when a series of terminal commands is complete.
    It synchronizes any modifications made in the persistent sandbox environment
    back to the in-memory database and then removes the temporary sandbox directory.

    Note: This now delegates to the shared session manager, which coordinates
    cleanup across all terminal-like APIs (cursor, copilot, terminal, gemini_cli).

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome of the session cleanup.
    """
    global SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ

    _log_init_message(logging.INFO, "Requesting shared session cleanup via session_manager...")
    
    # Delegate to shared session manager
    # Need to wrap update_db_file_system_from_temp to match expected signature
    def update_func_wrapper(temp_root, original_state, workspace_root, command):
        return utils.update_db_file_system_from_temp(
            temp_root, original_state, workspace_root, command=command
        )
    
    result = session_manager.end_shared_session(
        api_name="copilot",
        db_instance=DB,
        update_func=update_func_wrapper,
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


@tool_spec(
    spec={
        'name': 'run_in_terminal',
        'description': """ Run a shell command in a terminal with persistent state and environment.
        
        This function executes shell commands in a persistent terminal environment. Commands like 'cd', 'pwd',
        and environment management ('export', 'unset', 'env') are handled internally and persist across calls.
        The terminal state, working directory, and environment variables persist across tool calls, making this
        ideal for multi-step workflows. External commands are executed using explicit bash invocation with full
        system PATH inheritance.
        
        Key features: persistent sandbox sessions, environment variable support, metadata preservation,
        background process tracking, and support for complex shell syntax including multi-line strings and heredocs.
        
        For long-running processes (e.g., servers), set `is_background=True` and use the returned terminal ID
        with `get_terminal_output` to check output.
        
        IMPORTANT: For commands using pagers (e.g., `git log`, `less`), disable the pager (e.g., `git --no-pager log`)
        or pipe to cat (e.g., `git log | cat`). Failure to handle pagers will cause the command to hang. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': """ The shell command to execute. This is a required parameter.
                    If the command typically uses a pager (e.g., `git log`, `man`, `less`),
                    you MUST modify the command to disable the pager (e.g., `git --no-pager log`)
                    or pipe its output to a non-pager command (e.g., `git log | cat`).
                    Failure to do so may lead to stalled execution or unexpected behavior. """
                },
                'is_background': {
                    'type': 'boolean',
                    'description': """ If true, the command runs as a background process, and the
                    method returns immediately with a terminal ID. If false (default), the
                    command runs in the foreground, and the method waits for completion before
                    returning output. Defaults to false. """
                }
            },
            'required': [
                'command'
            ]
        }
    }
)
def run_in_terminal(command: str, is_background: bool = False) -> Dict[str, Any]:
    """Run a shell command in a terminal with persistent state and environment.

    This function executes shell commands in a persistent terminal environment. Commands like 'cd', 'pwd',
    and environment management ('export', 'unset', 'env') are handled internally and persist across calls.
    External commands are executed using explicit bash invocation in a persistent sandbox session managed
    by the session_manager, ensuring consistent state and environment variable inheritance.
    
    The terminal state, working directory, and environment variables persist across tool calls, making
    this ideal for multi-step workflows. This tool should be used instead of printing shell code blocks
    and asking the user to run them.

    IMPORTANT: For commands that use a pager (e.g., `git log`, `man`, `less`), you MUST modify
    the command to disable the pager (e.g., `git --no-pager log`) or pipe output to cat
    (e.g., `git log | cat`). Failure to handle pagers will cause the command to hang.

    For long-running or indefinite processes (e.g., servers, watchers), set `is_background=True`.

    Args:
        command (str): The shell command to execute. Commands are passed directly to bash without
            pre-parsing validation, supporting complex syntax including multi-line strings, heredocs,
            and nested quotes. Internal commands (cd, pwd, export, unset, env) are intercepted and
            handled specially to maintain persistent state.
        is_background (bool): If True, runs the command as a background process and returns immediately
            with a terminal_id. If False (default), runs in foreground and waits for completion.
            Background processes can be monitored using 'get_terminal_output' with the returned terminal_id.

    Returns:
        Dict[str, Any]: Result of the terminal command execution with the following keys:
            status_message (str): Status of the command execution (e.g., 'Command started in background
                with ID X', 'Command executed successfully', 'Current directory changed to /path').
            terminal_id (Optional[str]): Process ID if run in background (is_background=True), used with
                'get_terminal_output' to fetch subsequent output. None for foreground commands.
            stdout (Optional[str]): Standard output for foreground commands. None for background commands.
            stderr (Optional[str]): Standard error for foreground commands. None for background commands.
            exit_code (Optional[int]): Exit code for foreground commands. None for background commands
                (exit code available later via 'get_terminal_output').

    Raises:
        InvalidInputError: If the command is empty, whitespace-only, not a string type,
            or if `is_background` is not a boolean type.
        TerminalNotAvailableError: If the sandbox session cannot be initialized due to permissions
            or system errors.
        CommandExecutionError: If a command fails to execute, cd fails, or a foreground command
            encounters a critical error. The exception includes stdout and stderr details.
    """

    global DB, SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ

    if not isinstance(command, str):
        error_msg = f"Command parameter must be a string, got {type(command).__name__}."
        _log_init_message(logging.ERROR, error_msg)
        raise custom_errors.InvalidInputError(error_msg)
    
    if not isinstance(is_background, bool):
        error_msg = f"is_background parameter must be a boolean, got {type(is_background).__name__}."
        _log_init_message(logging.ERROR, error_msg)
        raise custom_errors.InvalidInputError(error_msg)

    if not command or command.isspace():
        _log_init_message(logging.ERROR, "Command string is empty or whitespace.")
        raise custom_errors.InvalidInputError("Command string cannot be empty.")

    current_workspace_root = DB.get("workspace_root")
    if not current_workspace_root:
        _log_init_message(logging.ERROR, "Operation failed: workspace_root is not configured.")
        raise custom_errors.TerminalNotAvailableError("Workspace root is not configured, terminal unavailable.")

    current_workspace_root_norm = utils._normalize_path_for_db(current_workspace_root)
    current_cwd_norm = utils._normalize_path_for_db(DB.get("cwd", current_workspace_root_norm))

    # --- Handle internal commands ---
    stripped_command = command.strip()
    
    # Handle environment variable commands
    if stripped_command in ('env',) or stripped_command.startswith(('export ', 'unset ')):
        env_result = handle_env_command(stripped_command, DB)
        # Generate appropriate status message
        status_msg = "Environment command executed"
        if stripped_command.startswith('export '):
            status_msg = f"Variable exported: {stripped_command[7:]}"
        elif stripped_command.startswith('unset '):
            status_msg = f"Variable unset: {stripped_command[6:]}"
        elif stripped_command == 'env':
            status_msg = "Environment variables listed"
        # Map to Copilot's expected format
        return {
            'status_message': status_msg,
            'terminal_id': None,
            'stdout': env_result.get('stdout', ''),
            'stderr': env_result.get('stderr', ''),
            'exit_code': env_result.get('returncode', 0)
        }

    if stripped_command == "cd" or stripped_command.startswith("cd "):
        _log_init_message(logging.INFO, f"Handling internal 'cd': {command}")
        parts = stripped_command.split(maxsplit=1)
        target_arg = parts[1] if len(parts) > 1 else "/"
        new_cwd_path = utils.resolve_target_path_for_cd(
            current_cwd_norm, target_arg, current_workspace_root_norm, DB.get("file_system", {})
        )
        if new_cwd_path:
            DB["cwd"] = new_cwd_path
            return {'status_message': f"Current directory changed to {utils._normalize_path_for_db(DB.get('cwd'))}",
                    'terminal_id': None, 'stdout': None, 'stderr': None, 'exit_code': 0}
        else:
            _log_init_message(logging.WARNING, f"cd: Failed to change directory to '{target_arg}'.")
            raise custom_errors.CommandExecutionError(
                f"cd: Failed to change directory to '{target_arg}'. Path may be invalid or outside workspace."
            )

    if stripped_command == "pwd":
        _log_init_message(logging.INFO, "Handling internal 'pwd'")
        pwd_path = utils._normalize_path_for_db(DB.get('cwd', current_workspace_root_norm))
        return {'status_message': f"Current directory: {pwd_path}", 'terminal_id': None,
                'stdout': pwd_path, 'stderr': None, 'exit_code': 0}

    # --- Initialize Persistent Sandbox on First Run ---
    # Use shared session manager to coordinate sandbox across all terminal-like APIs
    shared_session_info = session_manager.get_shared_session_info()
    
    if not shared_session_info["initialized"] or not shared_session_info["exists"]:
        try:
            _log_init_message(logging.INFO, "Initializing shared sandbox session via session_manager...")
            SESSION_SANDBOX_DIR = session_manager.initialize_shared_session(
                api_name="copilot",
                workspace_root=current_workspace_root,
                db_instance=DB,
                dehydrate_func=utils.dehydrate_db_to_directory
            )
            SESSION_INITIALIZED = True
            _log_init_message(logging.INFO, f"Shared sandbox initialized at: {SESSION_SANDBOX_DIR}")
        except Exception as e:
            _log_init_message(logging.ERROR, f"Failed to initialize shared sandbox: {e}", exc_info=True)
            raise custom_errors.TerminalNotAvailableError(f"Failed to set up the execution environment: {e}")
    else:
        # Reuse existing shared sandbox created by another API
        SESSION_SANDBOX_DIR = shared_session_info["sandbox_dir"]
        SESSION_INITIALIZED = True
        _log_init_message(
            logging.INFO, 
            f"Reusing existing sandbox from '{shared_session_info['active_api']}': {SESSION_SANDBOX_DIR}"
        )
    # -------------------------------------------------

    if not SESSION_SANDBOX_DIR:
        raise custom_errors.TerminalNotAvailableError("Session sandbox is not initialized. Cannot execute external commands.")

    process_executed_without_launch_error = False
    command_message = ""

    # Preserve current workspace state before potential modifications
    original_filesystem_state = DB.get("file_system", {}).copy()

    try:
        exec_env_root = SESSION_SANDBOX_DIR
        _log_init_message(logging.INFO, f"Using persistent sandbox for execution: {exec_env_root}")

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

        # Collect metadata state before command execution
        pre_command_state_temp = utils.collect_pre_command_metadata_state(
            DB.get("file_system", {}),
            exec_env_root,
            current_workspace_root_norm
        )

        if current_cwd_norm.startswith(current_workspace_root_norm):
            relative_cwd = os.path.relpath(current_cwd_norm, current_workspace_root_norm)
        else:
            _log_init_message(logging.WARNING, f"Current directory '{current_cwd_norm}' is outside workspace root '{current_workspace_root_norm}'. Using environment root for command.")
            relative_cwd = "."

        subprocess_cwd_physical = utils._normalize_path_for_db(os.path.join(exec_env_root, relative_cwd))

        # Verify the execution CWD exists
        if not os.path.isdir(subprocess_cwd_physical):
            _log_init_message(logging.WARNING, f"Execution environment CWD '{subprocess_cwd_physical}' does not exist. Creating directory structure.")
            try:
                os.makedirs(subprocess_cwd_physical, exist_ok=True)
                _log_init_message(logging.INFO, f"Created missing directory: {subprocess_cwd_physical}")
            except Exception as e:
                _log_init_message(logging.ERROR, f"Failed to create directory '{subprocess_cwd_physical}': {e}")
                subprocess_cwd_physical = exec_env_root
                if not os.path.isdir(subprocess_cwd_physical):
                    _log_init_message(logging.ERROR, f"Even temp directory root '{exec_env_root}' does not exist!")
                    raise custom_errors.CommandExecutionError(f"Execution environment setup failed: temp directory '{exec_env_root}' does not exist")

        # Create any missing parent directories for output redirection
        try:
            redir_target = utils._extract_last_unquoted_redirection_target(stripped_command)
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
                    _log_init_message(logging.INFO, f"Created parent directory for output redirection: {parent_dir}")
                except Exception as e:
                    _log_init_message(logging.ERROR, f"Failed to create parent directory '{parent_dir}': {e}")
                    raise custom_errors.CommandExecutionError(f"Failed to create parent directory for output redirection: {e}")

        _log_init_message(logging.INFO, f"Executing command '{command}' in CWD '{subprocess_cwd_physical}' (Background: {is_background})")

        # Prepare environment and expand variables
        cmd_env = prepare_command_environment(DB, subprocess_cwd_physical, current_cwd_norm)

        # If running inside a Conda environment, propagate CONDA-related variables from parent
        conda_env_vars = ['CONDA_PREFIX', 'CONDA_DEFAULT_ENV', 'CONDA_EXE', 'CONDA_PYTHON_EXE', 'CONDA_SHLVL', 'CONDA_PROMPT_MODIFIER']
        for var in conda_env_vars:
            if var in os.environ:
                cmd_env[var] = os.environ[var]

        # Also propagate PATH if in Conda, to ensure correct binaries
        if 'CONDA_PREFIX' in os.environ and 'PATH' in os.environ:
            cmd_env['PATH'] = os.environ['PATH']

        # Don't expand variables in the command string, let bash handle it
        expanded_command = command.strip()
        
        # Prepare environment with PATH inheritance
        cmd_env = prepare_command_environment(DB, subprocess_cwd_physical, current_cwd_norm)
        
        # If running inside a Conda environment, propagate CONDA-related variables from parent
        conda_env_vars = ['CONDA_PREFIX', 'CONDA_DEFAULT_ENV', 'CONDA_EXE', 'CONDA_PYTHON_EXE', 'CONDA_SHLVL', 'CONDA_PROMPT_MODIFIER']
        for var in conda_env_vars:
            if var in os.environ:
                cmd_env[var] = os.environ[var]
        
        # Also propagate PATH if in Conda, to ensure correct binaries
        if 'CONDA_PREFIX' in os.environ and 'PATH' in os.environ:
            cmd_env['PATH'] = os.environ['PATH']
        
        # --- Main Execution Logic ---
        status_msg, term_id, std_out, std_err, exit_c = "", None, None, None, None

        if is_background:
            # Launch background process with explicit bash invocation
            stdout_log = os.path.join(exec_env_root, 'stdout.log')
            stderr_log = os.path.join(exec_env_root, 'stderr.log')
            exitcode_log = os.path.join(exec_env_root, 'exitcode.log')
            
            # Use OS-appropriate command syntax
            if os.name == 'nt':  # Windows
                stdout_log_esc = stdout_log.replace('\\', '\\\\').replace('"', '\\"')
                stderr_log_esc = stderr_log.replace('\\', '\\\\').replace('"', '\\"')
                exitcode_log_esc = exitcode_log.replace('\\', '\\\\').replace('"', '\\"')
                wrapped_command = f'({expanded_command}) > "{stdout_log_esc}" 2> "{stderr_log_esc}" & echo %ERRORLEVEL% > "{exitcode_log_esc}"'
                process_obj = subprocess.Popen(
                    wrapped_command,
                    cwd=subprocess_cwd_physical,
                    shell=True,
                    start_new_session=True,
                    env=cmd_env
                )
            else:  # Unix/Linux/macOS
                wrapped_command = f"exec > \"{stdout_log}\" 2> \"{stderr_log}\"; ({expanded_command}); echo $? > \"{exitcode_log}\""
                process_obj = subprocess.Popen(
                    ['/bin/bash', '-c', wrapped_command],
                    cwd=subprocess_cwd_physical,
                    start_new_session=True,
                    env=cmd_env
                )
            
            process_obj = subprocess.Popen(
                wrapped_command, cwd=subprocess_cwd_physical, shell=True, start_new_session=True, env=cmd_env
            )
            term_id = str(process_obj.pid)
            DB["background_processes"][term_id] = {
                "pid": process_obj.pid, "command": command, "exec_dir": exec_env_root,
                "stdout_path": stdout_log, "stderr_path": stderr_log, "exitcode_path": exitcode_log,
                "last_stdout_pos": 0, "last_stderr_pos": 0,
            }
            status_msg = f"Command '{command}' started in background with ID {term_id}."
            _log_init_message(logging.INFO, status_msg)
        else:
            # Foreground execution with explicit bash invocation
            try:
                process_obj = subprocess.run(
                    command, cwd=subprocess_cwd_physical, capture_output=True, text=True,
                    encoding='utf-8', errors='replace', check=False, shell=True,
                    timeout=FOREGROUND_COMMAND_TIMEOUT_SECONDS, env=cmd_env
                )
                exit_c, std_out, std_err = process_obj.returncode, process_obj.stdout, process_obj.stderr
                if exit_c == 0:
                    status_msg = f"Command '{command}' executed successfully."
                else:
                    status_msg = f"Command '{command}' completed with exit code {exit_c}."
                    if ("not found" in std_err.lower() or 
                        "no such file" in std_err.lower() or 
                        "is not recognized as an internal or external command" in std_err.lower() or
                        exit_c == 127):
                         _log_init_message(logging.WARNING, f"Command might not be found or other execution error. Stderr: {std_err.strip()}")
                _log_init_message(logging.INFO, f"{status_msg} Stdout: {len(std_out)} chars, Stderr: {len(std_err)} chars.")
                
                # Update DB with changes from temp directory, preserving metadata
                utils.update_db_file_system_from_temp(exec_env_root, original_filesystem_state, current_workspace_root_norm, command=command)
                
                # Collect post-command state for metadata preservation
                post_command_state_temp = utils.collect_post_command_metadata_state(
                    DB.get("file_system", {}),
                    exec_env_root,
                    current_workspace_root_norm
                )
                
                # Preserve unchanged file timestamps
                utils.preserve_unchanged_change_times(
                    DB.get("file_system", {}),
                    pre_command_state_temp,
                    post_command_state_temp,
                    original_filesystem_state,
                    current_workspace_root_norm,
                    exec_env_root
                )
                
                _log_init_message(logging.INFO, "Workspace state updated after foreground command completion.")
            except subprocess.TimeoutExpired:
                _log_init_message(logging.ERROR, f"Foreground command '{command}' timed out after {FOREGROUND_COMMAND_TIMEOUT_SECONDS} seconds.")
                utils.update_db_file_system_from_temp(exec_env_root, original_filesystem_state, current_workspace_root_norm, command=command)
                raise custom_errors.CommandExecutionError(f"Command '{command}' timed out.")
        
        return {
            'status_message': status_msg, 'terminal_id': term_id, 'stdout': std_out if std_out else None,
            'stderr': std_err if std_err else None, 'exit_code': exit_c
        }

    except (custom_errors.InvalidInputError, custom_errors.CommandExecutionError):
        DB["file_system"] = original_filesystem_state
        raise
    except Exception as e:
        _log_init_message(logging.ERROR, f"Unexpected error during command execution for '{command}': {type(e).__name__} - {e}", exc_info=True)
        DB["file_system"] = original_filesystem_state
        raise custom_errors.CommandExecutionError(f"An unexpected error occurred: {type(e).__name__} - {e}")
    finally:
        # No cleanup of session sandbox - it persists across commands
        # Session cleanup should be done explicitly via end_session()
        
        if "cd " not in stripped_command and stripped_command != "cd":
            if DB.get("cwd") != current_cwd_norm:
                _log_init_message(logging.WARNING, f"Restoring CWD to '{current_cwd_norm}' (was '{DB.get('cwd')}').")
                DB["cwd"] = current_cwd_norm
        if DB.get("workspace_root") != current_workspace_root_norm:
             _log_init_message(logging.WARNING, f"Restoring workspace_root to '{current_workspace_root_norm}' (was '{DB.get('workspace_root')}').")
             DB["workspace_root"] = current_workspace_root_norm
        _log_init_message(logging.DEBUG, f"run_in_terminal finished. Final CWD='{DB.get('cwd')}'")


@tool_spec(
    spec={
        'name': 'get_terminal_output',
        'description': """ Retrieves the output and status for a terminal process.
        
        This function is used to get the standard output (stdout), standard error (stderr),
        running status, and exit code of a terminal command that was previously
        started.
        
        When called, it attempts to read any new output generated by the process
        since the last call for the same `terminal_id`. If the process has finished,
        this function will retrieve any output, the final exit code. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'terminal_id': {
                    'type': 'string',
                    'description': """ The ID of the background terminal process. This ID should
                    have been returned by the function that initiated the background process.
                    It must be a string containing only digits. """
                }
            },
            'required': [
                'terminal_id'
            ]
        }
    }
)
def get_terminal_output(terminal_id: str) -> Dict[str, Any]:
    """Retrieves the output and status for a terminal process.

    This function is used to get the standard output (stdout), standard error (stderr),
    running status, and exit code of a terminal command that was previously
    started.

    When called, it attempts to read any new output generated by the process
    since the last call for the same `terminal_id`. If the process has finished,
    this function will retrieve any output, the final exit code.

    Args:
        terminal_id (str): The ID of the background terminal process. This ID should
            have been returned by the function that initiated the background process.
            It must be a string containing only digits.

    Returns:
        Dict[str, Any]: A dictionary containing the output and status information:
            - "terminal_id" (str): The ID of the terminal for which output was retrieved.
            - "stdout" (str): A chunk of standard output from the command since the
              last retrieval. If the process just finished, this includes all remaining
              unread output.
            - "stderr" (str): A chunk of standard error output from the command since
              the last retrieval. If the process just finished, this includes all
              remaining unread error output. Can also contain messages if the process
              terminated unexpectedly.
            - "is_still_running" (bool): True if the process is still active,
              False if it has completed or terminated.
            - "exit_code" (Optional[int]): The exit code of the command if it has
              finished. This will be None if the process is still running.
              An exit code of -1 may indicate an unexpected termination where
              the standard exit code could not be retrieved.

    Raises:
        TypeError: If `terminal_id` is not a string.
        InvalidInputError: If `terminal_id` is empty, consists only
            of whitespace, or is not a string containing only digits.
        InvalidTerminalIdError: If the provided `terminal_id` does not
            correspond to any known or active background process.
        OutputRetrievalError: If an error occurs while trying to
            access the output files or if the execution environment for the
            terminal process is found to be in an inconsistent state (e.g.,
            execution directory deleted prematurely). This can also be raised
            for other unexpected errors during output retrieval.
    """
    global DB

    # --- NEW: Input Validation Block ---
    if not isinstance(terminal_id, str):
        raise TypeError("Terminal ID must be a string.")
    
    if not terminal_id or not terminal_id.strip():
        raise custom_errors.InvalidInputError("Terminal ID cannot be empty or whitespace.")

    if not terminal_id.isdigit():
        raise custom_errors.InvalidInputError(f"Terminal ID '{terminal_id}' is invalid; it must be a string containing only digits.")
    # --- END: Input Validation Block ---

    if terminal_id not in DB.get("background_processes", {}):
        raise custom_errors.InvalidTerminalIdError(f"Terminal ID '{terminal_id}' is invalid or does not exist.")

    proc_info = DB["background_processes"][terminal_id]
    stdout_chunk = ""
    stderr_chunk = ""
    is_running = True
    exit_code = None

    try:
        # The signal of completion is the existence of the exitcode file.
        if os.path.exists(proc_info["exitcode_path"]):
            is_running = False
            with open(proc_info["exitcode_path"], "r", encoding='utf-8', errors='replace') as f:
                exit_code = int(f.read().strip())

            # Read any final output that hasn't been consumed
            with open(proc_info["stdout_path"], "r", encoding='utf-8', errors='replace') as f:
                f.seek(proc_info["last_stdout_pos"])
                stdout_chunk = f.read()

            with open(proc_info["stderr_path"], "r", encoding='utf-8', errors='replace') as f:
                f.seek(proc_info["last_stderr_pos"])
                stderr_chunk = f.read()

            # Process is finished, perform cleanup
            shutil.rmtree(proc_info["exec_dir"], ignore_errors=True)
            del DB["background_processes"][terminal_id]
            _log_init_message(logging.INFO, f"Cleaned up resources for finished terminal ID {terminal_id}.")

        else: # Process is still running
            # Check if the process is truly running on the system
            try:
                os.kill(int(terminal_id), 0)
            except OSError:
                # Process doesn't exist, but exitcode file wasn't written. This indicates an abrupt termination.
                is_running = False
                exit_code = -1 # Or some other indicator of an abnormal exit
                stderr_chunk = "Process terminated unexpectedly without writing an exit code."
                
                # Cleanup
                shutil.rmtree(proc_info["exec_dir"], ignore_errors=True)
                del DB["background_processes"][terminal_id]
                _log_init_message(logging.WARNING, f"Process {terminal_id} disappeared. Cleaned up resources.")
            
            if is_running:
                with open(proc_info["stdout_path"], "r", encoding='utf-8', errors='replace') as f:
                    f.seek(proc_info["last_stdout_pos"])
                    stdout_chunk = f.read()
                    proc_info["last_stdout_pos"] = f.tell()

                with open(proc_info["stderr_path"], "r", encoding='utf-8', errors='replace') as f:
                    f.seek(proc_info["last_stderr_pos"])
                    stderr_chunk = f.read()
                    proc_info["last_stderr_pos"] = f.tell()

    except FileNotFoundError:
        # This could happen if the exec_dir was deleted externally
        del DB["background_processes"][terminal_id]
        raise custom_errors.OutputRetrievalError(
            f"Could not retrieve output for terminal {terminal_id}; execution environment may have been manually deleted."
        )
    except Exception as e:
        _log_init_message(logging.ERROR, f"Error retrieving output for {terminal_id}: {e}", exc_info=True)
        raise custom_errors.OutputRetrievalError(f"An unexpected error occurred while retrieving output for terminal {terminal_id}: {e}")

    return {
        "terminal_id": terminal_id,
        "stdout": stdout_chunk,
        "stderr": stderr_chunk,
        "is_still_running": is_running,
        "exit_code": exit_code,
    }
